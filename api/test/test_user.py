import unittest

from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token
from api import create_app
from ..config.config import config_dict
from ..db import db
from ..models import User, save
from ..test import create_user

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
    
    def test_user_registration(self):
        user = create_user()
        
        data = {
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'password': user.password_hash
        }
        
        response = self.client.post("/auth/signup", json=data)
        user = User.query.filter_by(email='tadmin@test.com').first()
        assert user.email == "tadmin@test.com"
        assert user.username == 'tadmin'
        assert response.status_code == 201
    
    def test_duplicate_user_signup(self):
        user = create_user()
        save(user)
        data = {
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'password': user.password_hash
        }
        response = self.client.post('/auth/signup', json=data)
        self.assertEqual(response.status_code, 403)

        
    def test_user_login(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'password'
        password_hash = generate_password_hash(password)

        data = {
            'email': email,
            'password': password
        }

        response = self.client.post('/auth/login', json=data)

        assert response.status_code == 201
        assert response.json['username'] == 'tadmin'
        
        # Verify the password using the password hash
        assert check_password_hash(user.password_hash, password)
    
    def test_invalid_login(self):
        user = create_user()
        save(user)
        
        email = 'tadmin@test.com'
        password = 'incorrect_password'  # Use an incorrect password
        password_hash = generate_password_hash(password)
        
        data = {
            'email': email,
            'password': password
        }
        
        response = self.client.post('auth/login', json=data)
        
        assert response.status_code == 401
        assert response.json['message'] == 'Invalid login credentials. Check credentials and try again.'

        
    def test_refresh_token(self):
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
        
        # Create a new request to refresh the access token using the refresh token
        refresh_data = {
            'refresh_token': refresh_token
        }

        refresh_response = self.client.post('/auth/refresh', json=refresh_data, headers=headers)

        assert refresh_response.status_code == 201
        assert 'access_token' in refresh_response.json

        # Verify that the new access token is different from the previous one
        new_access_token = refresh_response.json['access_token']
        assert new_access_token != access_token

    def test_logout(self):
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

        # Create a new request to logout and blacklist the access token
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        logout_response = self.client.post('/auth/logout', headers=headers)

        assert logout_response.status_code == 200
        assert logout_response.json['message'] == 'Logged out successfully!'

        # Create a new request to access a protected route using the blacklisted token
        protected_response = self.client.get('/auth/user', headers=headers)

        assert protected_response.status_code == 401
        assert protected_response.json['message'] == 'Token has been revoked'
