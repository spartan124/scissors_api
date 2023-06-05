
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt_identity, jwt_required)
from flask_restx import Namespace, Resource, abort, fields
from werkzeug.security import check_password_hash, generate_password_hash

from ..models import User, delete, save, update

namespace = Namespace("auth", description="namespace for Users authentication and Operations")

signup_model = namespace.model(
    "UserSignUp",
    {
        "full_name": fields.String(required=True, description="User's full name"),
        "username": fields.String(required=True, description="User's username"),
        "email": fields.String(required=True, description="User's email address"),
        "phone": fields.String(required=True, description="User's Phone number"),
        "password": fields.String(required=True, description="User's Account Password"),
        # "role": fields.String(required=True, description="User's role")

    }
)

user_model = namespace.model(
    "UserModel",
    {
        "id": fields.Integer(description="User's ID"),
        "full_name": fields.String(required=True, description="User's name"),
        "email": fields.String(required=True, description="User's email"),
        "username": fields.String(required=True, description="User's username"),
        "phone": fields.String(required=True, description="User's Phone number")

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
        phone = data['phone']
        password_hash = generate_password_hash(data["password"])
        
        new_user = User.query.filter_by(username=username).first()
        
        if new_user:
            abort(403, message = "A user with that username already exists!!!")
        
        new_user = User(
            full_name = full_name,
            username = username,
            email = email,
            phone = phone,
            password_hash = password_hash
        )
        
        save(new_user)
        return new_user, 201
  
@namespace.route('/login')
class Login(Resource):
    @namespace.expect(login_model)
    @namespace.doc(description="Login a teacher, an admin or a student account and generate access & refresh tokens.")
    def post(self):
        """Generate JWT access and refresh tokens
        """
        
        data = namespace.payload
        
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if (user is not None) and (check_password_hash(user.password_hash, password)):
            access_token = create_access_token(identity=user.email)
            refresh_token = create_refresh_token(identity=user.email)
            
            response = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            
            return response, 201
        
        else:
            abort(403, message="Invalid login credentials. Check credentials and try again.")
        
@namespace.route('/refresh')
class Refresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        email = get_jwt_identity()
        access_token = create_access_token(identity=email)
        response = {
            'access_token':access_token
        }
        return response, 201

