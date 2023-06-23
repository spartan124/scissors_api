import json
from flask import g
from flask_jwt_extended import (create_access_token, create_refresh_token, get_jwt,
                                get_jwt_identity, jwt_required)
from flask_restx import Namespace, Resource, abort, fields
from werkzeug.security import check_password_hash, generate_password_hash
from ..config.config import cache

from ..auth import jwt_refresh_token_required_with_blacklist, blacklist_token, jwt_required_with_blacklist

from ..models import User, delete, save, update

namespace = Namespace("Auth Ops", description="namespace for Users authentication and Operations", path='/auth')


signup_model = namespace.model(
    "UserSignUp",
    {
        "full_name": fields.String(required=True, description="User's full name"),
        "username": fields.String(required=True, description="User's username"),
        "email": fields.String(required=True, description="User's email address"),
        "password": fields.String(required=True, description="User's Account Password"),
       

    }
)

user_model = namespace.model(
    "UserModel",
    {
        "id": fields.Integer(description="User's ID"),
        "full_name": fields.String(required=True, description="User's name"),
        "email": fields.String(required=True, description="User's email"),
        "username": fields.String(required=True, description="User's username"),

    }
)

login_model = namespace.model(
    "Login", {
        "email": fields.String(required=True, description="User's email"),
        "password": fields.String(required=True, description="User's password"),
    }
)

@namespace.route('/signup')
class Signup(Resource):
    @namespace.expect(signup_model)
    @namespace.marshal_with(user_model)
    @namespace.doc(description="Signup a new User account")
    def post(self):
        """Sign up a new user account
        """
        
        data = namespace.payload
        
        full_name = data["full_name"]
        username = data['username']
        email = data['email']
        password_hash = generate_password_hash(data["password"])
        
        new_user = User.query.filter_by(username=username).first()
        
        if new_user:
            abort(403, message = "A user with that username already exists!!!")
        
        new_user = User(
            full_name = full_name,
            username = username,
            email = email,
            password_hash = password_hash
        )
        
        save(new_user)
        return new_user, 201
  
@namespace.route('/login')
class Login(Resource):
    @namespace.expect(login_model)
    @namespace.doc(
        description="Sign in a user and generate access & refresh tokens.",
        
        responses={
            201: 'User is logged in and access and refresh tokens generated',
            403: 'Invalid login credentials.'
        }
    )
    def post(self):
        """Generate JWT access and refresh tokens
        """
        
        data = namespace.payload
        
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if (user is not None) and (check_password_hash(user.password_hash, password)):
            access_token = create_access_token(identity={'id': user.id, 'email': user.email})
            refresh_token = create_refresh_token(identity={'id': user.id, 'email': user.email})
            response = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': user.username
            }
            
            return response, 201
        
        else:
            abort(403, message="Invalid login credentials. Check credentials and try again.")
        
@namespace.route('/refresh')
class Refresh(Resource):
    @jwt_refresh_token_required_with_blacklist
    def post(self):
        user = get_jwt_identity()
        id = user['id']
        email = user['email']
        access_token = create_access_token(identity={'id': id, 'email': email})
        response = {
            'access_token':access_token
        }
        return response, 201

@namespace.route('/logout')
class Logout(Resource):
    @jwt_required_with_blacklist
    def post(self):
        """
        Logout and Blacklist jwt_token
        """
        jwt_token = get_jwt()
        blacklist_token(json.dumps(jwt_token))
        return {"message": "Logged out successfully!"}, 200
@namespace.route('/user')
class UserData(Resource):
    @jwt_required_with_blacklist
    @cache.cached(timeout=60)
    def get(self):
        """Get logged in user
        """
        user= get_jwt_identity()
        email = user['email']
        userdata = User.query.filter_by(email=email).first()
        if userdata is not None:
            return {'username': userdata.username}, 200
        return {'message': 'User not found'}, 404