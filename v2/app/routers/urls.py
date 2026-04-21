"""URL shortening, redirect, QR code, analytics and history routes."""
from __future__ import annotations

import base64
import io
import json
import logging
import re
import secrets
import string
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import httpx
import matplotlib
import qrcode
import validators
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import cache_delete, cache_get, cache_set
from ..core.config import get_settings
from ..core.database import get_db
from ..dependencies import get_current_user
from ..models.url import Click, Url
from ..models.user import User
from ..schemas.url import (
    AnalyticsData,
    ShortenRequest,
    ShortenResponse,
    UrlHistoryItem,
    UrlOut,
)

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

router = APIRouter(tags=["URLs"])
settings = get_settings()
logger = logging.getLogger(__name__)

_CACHE_KEY_REDIRECT = "redirect:{}"
_CACHE_KEY_URL = "url:{}"
_CACHE_KEY_HISTORY = "history:{}"
_CACHE_KEY_ANALYTICS = "analytics:{}"
_CACHE_KEY_QR = "qr:{}"


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

_CHARS = string.ascii_letters + string.digits
_SHORT_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,20}$")


def _generate_short_code(length: int = 6) -> str:
    return "".join(secrets.choice(_CHARS) for _ in range(length))


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(parsed._replace(path=parsed.path.rstrip("/")))


async def _get_geolocation(ip: str) -> str:
    """Non-blocking GeoIP lookup – returns empty string on any failure."""
    api_key = settings.GEOIPIFY_API_KEY
    if not api_key:
        return ""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                "https://geo.ipify.org/api/v2/country,city",
                params={"apiKey": api_key, "ipAddress": ip},
            )
            data = resp.json()
            loc = data.get("location", {})
            region = loc.get("region", "")
            country = loc.get("country", "")
            return f"{region}, {country}" if region and country else ""
    except Exception:
        return ""


async def _record_click(url_id: int, click_source: str, db: AsyncSession) -> None:
    """Background task: record a click and increment counter."""
    try:
        click = Click(url_id=url_id, click_source=click_source)
        db.add(click)

        result = await db.execute(select(Url).where(Url.id == url_id))
        url_obj = result.scalar_one_or_none()
        if url_obj:
            url_obj.click_count = (url_obj.click_count or 0) + 1
            url_obj.last_used_at = datetime.now(timezone.utc)

        await db.commit()
    except Exception as exc:
        logger.warning("_record_click failed: %s", exc)
        await db.rollback()


# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #

@router.get("/history", response_model=list[UrlHistoryItem])
async def get_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Return all shortened URLs created by the current user."""
    cache_key = _CACHE_KEY_HISTORY.format(current_user.id)
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(select(Url).where(Url.user_id == current_user.id))
    urls = result.scalars().all()

    base_url = str(request.base_url)
    history = [
        {"short_code": u.short_code, "shortened_url": f"{base_url}{u.short_code}"}
        for u in urls
    ]
    await cache_set(cache_key, json.dumps(history), settings.CACHE_TTL_LONG)
    return history


@router.post("/shorten", response_model=ShortenResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(
    payload: ShortenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new shortened URL (authenticated)."""
    normalized = _normalize_url(payload.original_url)

    if not validators.url(normalized):
        raise HTTPException(status_code=400, detail="Invalid URL")

    base_url = str(request.base_url)

    # If user already shortened this URL, return existing entry
    result = await db.execute(
        select(Url).where(Url.original_url == normalized, Url.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {"shortened_url": f"{base_url}{existing.short_code}", "short_code": existing.short_code}

    # Validate custom shortcode availability
    short_code = payload.short_code
    if short_code and _SHORT_CODE_RE.match(short_code):
        conflict = await db.execute(select(Url).where(Url.short_code == short_code))
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Custom shortcode already exists")
    else:
        if short_code and not _SHORT_CODE_RE.match(short_code):
            raise HTTPException(
                status_code=400,
                detail="Custom short code must be 3-20 alphanumeric characters (hyphens/underscores allowed)",
            )
        # Auto-generate a unique shortcode
        short_code = None
        for _ in range(5):
            candidate = _generate_short_code()
            check = await db.execute(select(Url).where(Url.short_code == candidate))
            if not check.scalar_one_or_none():
                short_code = candidate
                break
        if short_code is None:
            raise HTTPException(status_code=503, detail="Could not generate a unique short code. Please try again.")

    url_obj = Url(
        original_url=normalized,
        short_code=short_code,
        user_id=current_user.id,
    )
    db.add(url_obj)
    await db.commit()
    await db.refresh(url_obj)

    shortened_url = f"{base_url}{url_obj.short_code}"
    return {"shortened_url": shortened_url, "short_code": url_obj.short_code}


@router.get("/{short_code}", include_in_schema=True)
async def redirect_url(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Redirect to the original URL. Cached in Redis for sub-millisecond lookup."""
    cache_key = _CACHE_KEY_REDIRECT.format(short_code)

    # Hot path: Redis cache hit (~0.5 ms)
    cached = await cache_get(cache_key)
    if cached:
        ip = request.client.host if request.client else "0.0.0.0"
        background_tasks.add_task(_lookup_and_record_click, short_code, ip, db)
        return RedirectResponse(url=cached, status_code=302)

    # Cold path: DB lookup
    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    original_url = url_obj.original_url
    url_id = url_obj.id

    # Cache the original URL for future redirects
    await cache_set(cache_key, original_url, settings.CACHE_TTL_REDIRECT)

    ip = request.client.host if request.client else "0.0.0.0"
    background_tasks.add_task(_record_click_with_geo, url_id, ip, db)

    return RedirectResponse(url=original_url, status_code=302)


async def _lookup_and_record_click(short_code: str, ip: str, db: AsyncSession) -> None:
    """Background: look up URL by short_code and record a click."""
    try:
        result = await db.execute(select(Url).where(Url.short_code == short_code))
        url_obj = result.scalar_one_or_none()
        if url_obj:
            geo = await _get_geolocation(ip)
            await _record_click(url_obj.id, geo, db)
    except Exception as exc:
        logger.warning("_lookup_and_record_click failed: %s", exc)


async def _record_click_with_geo(url_id: int, ip: str, db: AsyncSession) -> None:
    geo = await _get_geolocation(ip)
    await _record_click(url_id, geo, db)


@router.get("/shortened/{short_code}", response_model=str)
async def get_shortened_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    """Return the full shortened URL for the given short code."""
    cache_key = _CACHE_KEY_URL.format(short_code)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="Invalid shortcode")

    shortened_url = f"{request.base_url}{url_obj.short_code}"
    await cache_set(cache_key, shortened_url, settings.CACHE_TTL_SHORT)
    return shortened_url


@router.delete("/shortened/{short_code}")
async def delete_url(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a shortened URL (owner only)."""
    result = await db.execute(
        select(Url).where(Url.short_code == short_code, Url.user_id == current_user.id)
    )
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    await db.delete(url_obj)
    await db.commit()

    # Invalidate caches
    await cache_delete(_CACHE_KEY_REDIRECT.format(short_code))
    await cache_delete(_CACHE_KEY_URL.format(short_code))
    await cache_delete(_CACHE_KEY_HISTORY.format(current_user.id))
    await cache_delete(_CACHE_KEY_ANALYTICS.format(short_code))
    await cache_delete(_CACHE_KEY_QR.format(short_code))

    return {"message": "Url successfully deleted"}


@router.get("/{short_code}/qrcode")
async def generate_qr_code(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a PNG QR code for the shortened URL."""
    cache_key = _CACHE_KEY_QR.format(short_code)
    cached_b64 = await cache_get(cache_key)
    if cached_b64:
        png_bytes = base64.b64decode(cached_b64)
        return Response(content=png_bytes, media_type="image/png")

    result = await db.execute(select(Url).where(Url.short_code == short_code))
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    shortened_url = f"{request.base_url}{short_code}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(shortened_url)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="seagreen", back_color="white")

    buf = io.BytesIO()
    qr_image.save(buf, format="PNG")
    buf.seek(0)
    png_bytes = buf.read()

    await cache_set(cache_key, base64.b64encode(png_bytes).decode(), settings.CACHE_TTL_LONG)

    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=qrcode.png"},
    )


@router.get("/analytics/{short_code}", response_model=AnalyticsData)
async def get_analytics(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return JSON analytics (clicks by source) for a shortened URL."""
    cache_key = _CACHE_KEY_ANALYTICS.format(short_code)
    cached = await cache_get(cache_key)
    if cached:
        return json.loads(cached)

    result = await db.execute(
        select(Url).where(Url.short_code == short_code, Url.user_id == current_user.id)
    )
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    clicks_result = await db.execute(select(Click).where(Click.url_id == url_obj.id))
    clicks = clicks_result.scalars().all()

    click_data: dict[str, int] = {}
    for click in clicks:
        src = click.click_source or "Unknown"
        click_data[src] = click_data.get(src, 0) + 1

    response_data = {
        "short_code": short_code,
        "original_url": url_obj.original_url,
        "total_clicks": url_obj.click_count,
        "clicks_by_source": click_data,
    }
    await cache_set(cache_key, json.dumps(response_data), settings.CACHE_TTL_LONG)
    return response_data


@router.get("/analytics/{short_code}/chart")
async def get_analytics_chart(
    short_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Return a PNG bar chart of clicks per source location."""
    result = await db.execute(
        select(Url).where(Url.short_code == short_code, Url.user_id == current_user.id)
    )
    url_obj = result.scalar_one_or_none()
    if not url_obj:
        raise HTTPException(status_code=404, detail="URL not found")

    clicks_result = await db.execute(select(Click).where(Click.url_id == url_obj.id))
    clicks = clicks_result.scalars().all()

    click_data: dict[str, int] = {}
    for click in clicks:
        src = click.click_source or "Unknown"
        click_data[src] = click_data.get(src, 0) + 1

    fig, ax = plt.subplots()
    if click_data:
        ax.bar(list(click_data.keys()), list(click_data.values()))
    ax.set_xlabel("Location")
    ax.set_ylabel("Number of Clicks")
    ax.set_title("Clicks per Location")

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
