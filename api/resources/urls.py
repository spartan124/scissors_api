from datetime import datetime
import qrcode
import socket  
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
import matplotlib
from . import generate_short_code, get_geolocation, normalize_url

matplotlib.use('Agg')

url_ns = Namespace("Url OPs", description="URL Shortener API Operations...", path="/")

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


@limiter.limit("5/second")
@url_ns.route('/shorten')
class URLShortener(Resource):
    @url_ns.expect(url_request_model, validate=True)
    @url_ns.doc(
        params={
            'original_url': 'The original URL to be shortened',
            'short_code': 'Optional custom short code for the URL'
        },
        responses={
            200: 'Ok',
            201: 'Success',
            400: 'Invalid URL',
            401: 'Unauthorized',
            500: 'Server error'
        },
        examples={
            'Example 1': {
                'summary': 'Shorten a URL',
                'description': 'Shorten the given URL and return the shortened URL.',
                'request': {
                    'original_url': 'https://example.com',
                    'short_code': 'custom-short-code'
                },
                'response': {
                    'shortened_url': 'http://localhost:5000/abcd',
                    'short_code': 'abcd'
                }
            }
        }
    )
    @jwt_required_with_blacklist
    def post(self):
        """
        Create a new shortened URL.
        """
        original_url = request.json.get('original_url')
        
        normalized_url = normalize_url(original_url)
        base_url = request.host_url

        
        if not validators.url(normalized_url):
            return {'message': 'Invalid URL'}, 400
        
        short_code = request.json.get('short_code')
        check_shortcode = Url.query.filter_by(short_code=short_code).first()
        if check_shortcode:
            abort(409, message="Custom shortcode already exists")
            
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

@limiter.limit("5/second")    
@url_ns.route('/<short_code>')
class URLRedirect(Resource):  
    @cache.cached(timeout=30)
    @url_ns.doc(responses={
        302: 'Redirect to the original URL',
        404: 'URL not found'
    },
        params={
        'short_code': 'Shortened URL'
    },
        examples={
        'Example 1': {
            'summary': 'Redirect to original URL',
            'description': 'Redirect to the original URL for the given short code.',
            'response': 'Redirect to https://example.com',
        }
    }
    )
   
    def get(self, short_code):
        """
        Redirect to the original url for the given short code.

        Args:
            short_code (_type_): Shortened URL
        """
        url = Url.query.filter_by(short_code=short_code).first()
        
        if url:
             
            hostname=socket.gethostname()   
            ip_address =socket.gethostbyname(hostname)   
            geolocation_data = get_geolocation(ip_address)
            click = Click(url_id=url.id, click_source=geolocation_data)
            save(click)
            
            original_url = url.original_url
            url.last_used_at = datetime.utcnow()
            url.click_count += 1
            update(url)
            return redirect(original_url)
        
        return {"message": "Url not found"}, 404
    
   
@limiter.limit("5/second")
@url_ns.route("/shortened/<short_code>")   
class ShortUrl(Resource):
    @url_ns.doc(responses={
        200: 'Shortened URL',
        404: 'Invalid shortcode'
    },
        params={
        'short_code': 'Url shortcode'
    },
        examples={
        'Example 1': {
            'summary': 'Get shortened URL',
            'description': 'Get the shortened URL using the shortcode.',
            'response': 'https://example.com/abcd',
        }
    }
    )
    @jwt_required_with_blacklist
    @cache.cached(timeout=30)   
    def get(self, short_code):
        """
        Get shortened url using the shortcode
        """
        url = Url.query.filter_by(short_code=short_code).first()
        base_url = request.host_url

        if not url:
            abort(404, message="Invalid shortcode")
        
        shortened_url = f"{base_url}{url.short_code}"

        return shortened_url, 200
    
    
    @url_ns.doc(description="Delete a url from the database using the shortcode",
        params={
        'short_code': 'Target Url shortcode'
        },
        responses={
        200: 'Success message',
        404: 'Url not found'
    }              
    )
    @jwt_required_with_blacklist
    def delete(self, short_code):
        
        user = get_jwt_identity()
        user_id = user['id']
        
        url = Url.query.filter_by(short_code=short_code, user_id=user_id).first()
        if (url and user):
            delete(url)
            return {"message": "Url successfully deleted"}
        abort(404, message="Url not found")

@limiter.limit("5/second")
@url_ns.route("/<short_code>/qrcode")
class GenerateQrCode(Resource):
    @url_ns.doc(description="Generate a QR code for a shortened URL using the shortcode", 
        params={
        'short_code': 'Target url shortcode'
        },
        responses={
        200: 'QR code image',
        404: 'URL not found'
    })
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Generate a QR code for a shortened URL using the shortcode
        Returns:
            Response: QR code image in PNG format
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
        
@limiter.limit("5/second")   
@url_ns.route('/analytics/<short_code>')
class ShortUrlAnalytics(Resource):
    @url_ns.doc(
        params={
        'short_code': 'Randomly generated shortcode'
    },
        responses={
        200: 'Analytics image',
        404: 'URL or user not found'
    },
        description="Get analytics for a shortened URL using the shortcode"
    )
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self, short_code):
        """
        Get analytics for shortened url

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

@limiter.limit("50/second")    
@url_ns.route('/history')    
class UrlHistory(Resource):
    @url_ns.doc(responses={
        200: 'URLs history as a dictionary',
    },
        description="Get all URLs generated by a specific user"
    )
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self):
        
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
    
    
    