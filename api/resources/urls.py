from datetime import datetime
import qrcode
from ..config.config import Config
from flask_restx import Resource, Namespace, fields, abort
from flask import make_response, render_template, request, redirect, send_file
from ..models import Url, save, delete, update
from flask_jwt_extended import jwt_required, get_jwt_identity
import string
import random
# from flask_caching import cache
from io import BytesIO
import base64
import requests


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

def generate_short_code():
    """Generate a random shortcode.
    """
    chars = string.ascii_letters + string.digits
    short_code = ''.join(random.choice(chars) for _ in range(6))
    return short_code

def get_geolocation(ip_address):
        response = requests.get(f'{Config.IPSTACK_API_URL}/{ip_address}?access_key={Config.IPSTACK_ACCESS_KEY}')
        if response.status_code == 200:
            data = response.json()
            if 'city' in data and 'country_name' in data:
                return f'{data["city"]}, {data["country_name"]}'
        return ''

@url_ns.route('/shorten')

class URLShortener(Resource):
    @url_ns.expect(url_request_model, validate=True)
    @jwt_required()
    def post(self):
        """
        Create a new shortened URL.
        """
        original_url = request.json.get('original_url')
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
        
        return {'shortened_url': shortened_url}, 201
    
    @url_ns.marshal_with(url_response_model)
    @jwt_required()
    def get(self):
        """Get all shortened urls

        Returns:
            _type_: _description_
        """
        url = Url.query.all()
        return url
    
@url_ns.route('/<short_code>')
class URLRedirect(Resource):
    # @cache.cached(timeout=60) #cache the result for 60 seconds
   
    def get(self, short_code):
        """
        Redirect to the original url for the given short code.

        Args:
            short_code (_type_): Shortened URL
        """
        url = Url.query.filter_by(short_code=short_code).first()
        if url:
            original_url = url.original_url
            url.last_used_at = datetime.utcnow()
            url.click_count += 1
            url.click_source = get_geolocation(request.remote_addr)
            update(url)
            return redirect(original_url)
        
        return {"message": "Url not found"}, 404
    
    
@url_ns.route("/shortened/<short_code>")   
class OriginalUrl(Resource):
    @jwt_required()
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

@url_ns.route('/analytics/<short_code>')
class ShortUrlAnalytics(Resource):
    @jwt_required()
    def get(self, short_code):
        
        url = Url.query.filter_by(short_code=short_code).first()
        
        if url:
            return {
                'original_url': url.original_url,
                'click_count': url.click_count,
                'created_at': url.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'last_used_at': url.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if url.last_used_at else None,
                'click_source': url.click_source
  
            }
        return {"message": "URL not found"}, 404
    
    