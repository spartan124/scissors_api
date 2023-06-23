import unittest

from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from api import create_app
from ..config.config import config_dict
from ..db import db
from ..models import User, Url, save
from ..test import create_user
import validators
from flask import request, current_app

class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config=config_dict["test"])
        self.appctx = self.app.app_context()
        self.appctx.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.drop_all()
        self.appctx.pop()
        self.app = None
        self.client = None
    
    def test_url_shortening(self):
        user = create_user()
        save(user)
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        
        # Create a new URL to be shortened
        original_url = 'https://example.com/long-url'
        
        data = {
            'original_url': original_url
        }

        # Perform the URL shortening request
        response = self.client.post('/shorten', json=data, headers=headers)

        assert response.status_code == 201
        assert 'shortened_url' in response.json
        assert 'short_code' in response.json

        shortened_url = response.json['shortened_url']

        # Verify that the shortened URL is valid
        assert validators.url(original_url)
        assert validators.url(shortened_url)

        # # Create a new request to access the shortened URL
        # redirect_response = self.client.get(f'/{short_code}')

        # assert redirect_response.status_code == 302
        # assert redirect_response.headers['Location'] == original_url

    def test_redirect_url(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create a URL for the user
        url_data = {'original_url': 'https://example.com'}
        response = self.client.post('/shorten', json=url_data, headers=headers)
        assert response.status_code == 201
        
        # Extract the shortcode from the response
        short_code = response.json['short_code']
        
        redirect_response = self.client.get(f'/{short_code}')

        assert redirect_response.status_code == 302
        assert redirect_response.headers['Location'] == 'https://example.com'

        
        
    def test_url_history(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create multiple URLs for the user
        urls = [
            {'original_url': 'https://example.com/url1'},
            {'original_url': 'https://example.com/url2'},
            {'original_url': 'https://example.com/url3'}
        ]
        
        for url_data in urls:
            response = self.client.post('/shorten', json=url_data, headers=headers)
            assert response.status_code == 201
        
        # Perform the URL history request
        response = self.client.get('/history', headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, dict)
        
        # Verify that the returned URLs match the created URLs
        returned_urls = response.json
        assert len(returned_urls) == len(urls)
    
    def test_get_url_by_shortcode(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create a URL for the user
        url_data = {'original_url': 'https://example.com'}
        response = self.client.post('/shorten', json=url_data, headers=headers)
        assert response.status_code == 201
        
        # Extract the shortcode from the response
        short_code = response.json['short_code']
        
        response = self.client.get(f'/shortened/{short_code}', headers=headers)
        
        assert response.status_code == 200
        url = Url.query.filter_by(short_code=short_code).first()

        assert response.json == f'http://localhost/{url.short_code}'
        
    def test_delete_url_by_shortcode(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create a URL for the user
        url_data = {'original_url': 'https://example.com'}
        response = self.client.post('/shorten', json=url_data, headers=headers)
        assert response.status_code == 201
        
        # Extract the shortcode from the response
        short_code = response.json['short_code']
        
        # Perform the delete URL request
        response = self.client.delete(f'/shortened/{short_code}', headers=headers)
        
        assert response.status_code == 200
        assert response.json['message'] == 'Url successfully deleted'
        
        # Verify that the URL is deleted
        url = Url.query.filter_by(short_code=short_code).first()
        assert url is None

    def test_get_qr_code_for_url_shortcode(self):
        # Create a URL in the database
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        # Perform the login request to get the access token and refresh token
        login_response = self.client.post('/auth/login', json=data)
        access_token = login_response.json['access_token']
        refresh_token = login_response.json['refresh_token']
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create a URL for the user
        url_data = {'original_url': 'https://example.com'}
        response = self.client.post('/shorten', json=url_data, headers=headers)

        short_code = response.json['short_code']
        # Perform the GET request to generate the QR code
        qr_response = self.client.get('/{short_code}/qrcode', headers=headers)
        
        assert qr_response.status_code == 200
        assert qr_response.headers['Content-Type'] == 'application/json'
