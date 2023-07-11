from datetime import timedelta
from functools import wraps

from flask_jwt_extended import jwt_required, get_jwt, verify_jwt_in_request
import json
from ..config.config import redis_client




def blacklist_token(token):
    redis_client.setex(token, 'blacklisted', timeout=timedelta(days=1).total_seconds())
    
def jwt_required_with_blacklist(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        jwt_token = get_jwt()
        if redis_client.get(json.dumps(jwt_token)):
            return {"message": "Token has been revoked"}, 401
        return fn(*args, **kwargs)
    return wrapper

def jwt_refresh_token_required_with_blacklist(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        jwt_token = get_jwt()
        if jwt_token and redis_client.get(json.dumps(jwt_token)):
            return {'message':'Refresh token has been revoked'}, 401
        return fn(*args, **kwargs)
    return decorated_function
