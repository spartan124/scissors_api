from datetime import datetime
import qrcode
from flask_restx import Resource, Namespace, fields, abort
from flask import jsonify, make_response, render_template, request, redirect, send_file
from ..models import Url, Click, save, delete, update
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..config.config import cache, limiter
from .. import limiter
from api.auth import jwt_required_with_blacklist
from io import BytesIO
import base64
import requests
import validators
import matplotlib.pyplot as plt
import io
from . import generate_short_code, get_geolocation, normalize_url

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
    @jwt_required_with_blacklist
    def post(self):
        """
        Create a new shortened URL.
        """
        original_url = request.json.get('original_url')
        
        normalized_url = normalize_url(original_url)
        base_url = request.host_url

        
        if not validators.url(original_url):
            return {'message': 'Invalid URL'}, 400
        
        short_code = request.json.get('short_code')
        user = get_jwt_identity()
        user_id = user['id']
        
        
        url = Url.query.filter_by(original_url=normalized_url, user_id=user_id).first()
        
        if url:
            shortened_url = f"{base_url}{url.short_code}"
        
        else:    
            
            if short_code is None or short_code in ["", "string"]:
                
                short_code = generate_short_code()
            
        
                url = Url(
                    original_url=normalized_url,
                    short_code=short_code,
                    user_id=user_id
                )

                save(url)
            else:
                url = Url(
                    original_url=normalized_url,
                    short_code=short_code,
                    user_id=user_id
                    )
                save(url)
            
            shortened_url = f"{base_url}{url.short_code}"
            
            
        return {'shortened_url': shortened_url, 'short_code': url.short_code }, 201
        
    # @url_ns.marshal_with(url_response_model)
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self):
        """Get all shortened urls

        Returns:
            List: List of all shortened urls
        """
        urls = Url.query.all()
        
        base_url = request.host_url
        
        shortened_urls = []
        
        for url in urls:
            shortened_url = f"{base_url}{url.short_code}"
            shortened_urls.append(shortened_url)
        
        return {'shortened url': shortened_urls}

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
            print("This is the geo data ", geolocation_data)
            click = Click(url_id=url.id, click_source=geolocation_data)
            save(click)
            
            original_url = url.original_url
            url.last_used_at = datetime.utcnow()
            url.click_count += 1
            update(url)
            return redirect(original_url)
        
        return {"message": "Url not found"}, 404
    
    
@url_ns.route("/shortened/<short_code>")   
class ShortUrl(Resource):
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Get shortened url using the shortcode

        Args:
            short_code (string): randomly generated shortcode

        Returns:
            string: shortened url
        """
        url = Url.query.filter_by(short_code=short_code).first()
        base_url = request.host_url

        if not url:
            abort(404, message="Invalid shortcode")
        
        shortened_url = f"{base_url}{url.short_code}"

        return shortened_url, 200
    
    @jwt_required_with_blacklist
    def delete(self, short_code):
        """
        Delete a url from data base using the shortcode

        Args:
            short_code (string): randomly generated shortcode

        Returns:
            string: success message or error message
        """
        user = get_jwt_identity()
        user_id = user['id']
        
        url = Url.query.filter_by(short_code=short_code, user_id=user_id).first()
        if (url and user):
            delete(url)
            return {"message": "Url successfully deleted"}
        abort(404, message="Url not found")

@url_ns.route("/<short_code>/qrcode")
class GenerateQrCode(Resource):
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Get a shortened url QRCode using the shortcode

        Args:
            short_code (string): randomly generated shortcode

        Returns:
            img/png : Image data of the requested url shortcode
        """
        
        url = Url.query.filter_by(short_code=short_code).first()
        base_url = request.host_url

        if url:
            shortened_url = f"{base_url}{short_code}"
            qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            )
            qr.add_data(shortened_url)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="seagreen", back_color="white")

            # Save QR code image to a BytesIO object
            qr_buffer = BytesIO()
            qr_image.save(qr_buffer)
            qr_buffer.seek(0)

            response = make_response(send_file(qr_buffer, mimetype='image/png'))
            response.headers.set('Content-Disposition', 'attachment', filename='qrcode.png')
            return response
        
    
@url_ns.route('/analytics/<short_code>')
class ShortUrlAnalytics(Resource):
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Get analytics for shortened url

        Args:
            short_code (string): randomly generated shortcode

        Returns:
            img/png : Image data showing analytics.
        """
        user = get_jwt_identity()
        user_id = user["id"]
        
        url = Url.query.filter_by(short_code=short_code, user_id=user_id).first()
        if url is None:
            return {'message':"Url not found"}, 404
        
        clicks = Click.query.filter_by(url_id=url.id).all()
        click_data = {}
        for click in clicks:
            if click.click_source in click_data:
                click_data[click.click_source] += 1
            else:
                click_data[click.click_source] = 1
    
        if url and user['id']:
            locations = list(click_data.keys())
            click_counts = list(click_data.values())
            
            plt.bar(locations, click_counts)
            plt.xlabel('Location')
            plt.ylabel('Number of Clicks')
            plt.title('Clicks per Location')
            
            image_buffer = io.BytesIO()
            plt.savefig(image_buffer, format='png')
            plt.close()
            image_buffer.seek(0)
            
            return send_file(image_buffer, mimetype='image/png')
            
        return {"message": "User is not authorized to view this Url's analytics."}, 404
    
@url_ns.route('/history')    
class UrlHistory(Resource):
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self):
        """
        Get all Urls generated by a Specific User

        Returns:
            dict: Returns a dict object
        """
        user = get_jwt_identity()
        user_id = user['id']
        
        urls = Url.query.filter_by(user_id=user_id).all()
        
        history = []
        
        for url in urls:
            history.append({
                'short_code': url.short_code,
                'shortened_url': f"{request.host_url}{url.short_code}"
            })

        history_dict = {item['short_code']: item['shortened_url'] for item in history}

        return jsonify(history_dict)
    
    
    