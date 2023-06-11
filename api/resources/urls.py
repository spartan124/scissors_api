from datetime import datetime
import qrcode
from flask_restx import Resource, Namespace, fields, abort
from flask import make_response, render_template, request, redirect, send_file
from ..models import Url, Click, save, delete, update
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..config.config import cache, limiter
from .. import limiter
# from flask_caching import cache
from io import BytesIO
import base64
import requests
from . import is_url_valid, generate_short_code, get_geolocation

url_ns = Namespace("", description="URL Shortener API Operations...")



url_request_model = url_ns.model('URLRequest', {
    'original_url': fields.String(required=True, description='Original URL'),
    'short_code': fields.String(description='Shortened URL'),

})

url_response_model = url_ns.model('URLResponse', {
    'short_code': fields.String(required=True, description='Shortened URL'),
    'original_url': fields.String(required=True, description='Original URL'),
    'id': fields.Integer(required=True, description='URL ID'),
    'created_at': fields.String(required=True, description='Timestamp')
})


@limiter.limit("10/minute")
@url_ns.route('/shorten')
class URLShortener(Resource):
    @url_ns.expect(url_request_model, validate=True)
    @jwt_required()
    def post(self):
        """
        Create a new shortened URL.
        """
        original_url = request.json.get('original_url')
        
        if not is_url_valid(original_url):
            return {'message': 'Invalid URL'}, 400
        
        short_code = request.json.get('short_code')
        user_id = get_jwt_identity()
        
        base_url = request.host_url
        
        url = Url.query.filter_by(original_url=original_url).first()
        
        if url:
            shortened_url = f"{base_url}{url.short_code}"
        
            
        # Generate a short code
        if short_code is None or short_code in ["", "string"]:
            
            short_code = generate_short_code()
        
    
            url = Url(
                original_url=original_url,
                short_code=short_code,
                user_id=user_id
            )

            save(url)
        else:
            url = Url(
                original_url=original_url,
                short_code=short_code,
                user_id=user_id
                )
            save(url)
        
        shortened_url = f"{base_url}{short_code}"
        
        
        return {'shortened_url': shortened_url}, 201
    
    @url_ns.marshal_with(url_response_model)
    @jwt_required()
    @cache.cached(timeout=60)
    def get(self):
        """Get all shortened urls

        Returns:
            _type_: _description_
        """
        url = Url.query.all()
        return url

@limiter.limit("5/second")    
@url_ns.route('/<short_code>')
class URLRedirect(Resource):  
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Redirect to the original url for the given short code.

        Args:
            short_code (_type_): Shortened URL
        """
        url = Url.query.filter_by(short_code=short_code).first()
        
        if url:
            ip_address = request.remote_addr
            geolocation_data = get_geolocation(ip_address)
            click = Click(url_id=url.id, click_source=geolocation_data)
            save(click)
            
            original_url = url.original_url
            url.last_used_at = datetime.utcnow()
            url.click_count += 1
            update(url)
            return redirect(original_url)
        
        return {"message": "Url not found"}, 404
    
    
@url_ns.route("/shortened/<short_code>")   
class OriginalUrl(Resource):
    @jwt_required()
    @cache.cached(timeout=60)
    def get(self, short_code):
        url = Url.query.filter_by(short_code=short_code).first()
        
        if not url:
            abort(404, message="Invalid shortcode")
        
        original_url = url.original_url
        return original_url, 200
    
    def delete(self, short_code):
        url = Url.query.filter_by(short_code=short_code).first()
        if url:
            delete(url)
            return {"message": "Url successfully deleted"}
        abort(404, message="Url not found")

@url_ns.route("/<short_code>/qrcode")
class GenerateQrCode(Resource):
    @jwt_required()
    @cache.cached(timeout=60)
    def get(self, short_code):
        
        url = Url.query.filter_by(short_code=short_code).first()
        
        base_url = request.host_url
        shortened_url = f"{base_url}{short_code}"
        if url:
            qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            )
            qr.add_data(shortened_url)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Save QR code image to a BytesIO object
            qr_buffer = BytesIO()
            qr_image.save(qr_buffer)
            qr_buffer.seek(0)

            response = make_response(send_file(qr_buffer, mimetype='image/png'))
            response.headers.set('Content-Disposition', 'attachment', filename='qrcode.png')
            return response
        
    
@url_ns.route('/analytics/<short_code>')
class ShortUrlAnalytics(Resource):
    @jwt_required()
    @cache.cached(timeout=60)
    def get(self, short_code):
        
        url = Url.query.filter_by(short_code=short_code).first()
        
        clicks = Click.query.filter_by(url_id=url.id).all()
        click_data = {}
        for click in clicks:
            if click.click_source in click_data:
                click_data[click.click_source] += 1
            else:
                click_data[click.click_source] = 1
    
        if url:
            return {
                'original_url': url.original_url,
                'click_count': url.click_count,
                'created_at': url.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'last_used_at': url.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if url.last_used_at else None,
                'click_data': click_data
  
            }
        return {"message": "URL not found"}, 404
@url_ns.route('/history')    
class UrlHistory(Resource):
    @jwt_required()
    @cache.cached(timeout=60)
    def get(self):
        """
        Get a specifi user's url link history
        """
        user_id = get_jwt_identity()
        
        urls = Url.query.filter_by(user_id=user_id).all()
        
        history = []
        
        for url in urls:
            history.append({
                'shortened_url': f"{request.host_url}{url.short_code}",
                'original_url': url.original_url
            })

        return {'history': history}
    
    
    