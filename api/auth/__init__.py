from datetime import timedelta
from functools import wraps

from flask_jwt_extended import jwt_required, get_jwt, verify_jwt_in_request
import json
from ..config.config import simCache




def blacklist_token(token):
    simCache.set(token, 'blacklisted', timeout=timedelta(days=1).total_seconds())
    
def jwt_required_with_blacklist(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        jwt_token = get_jwt()
        if simCache.get(json.dumps(jwt_token)):
            return {"message": "Token has been revoked"}, 401
        return fn(*args, **kwargs)
    return wrapper

def jwt_refresh_token_required_with_blacklist(fn):
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        jwt_token = get_jwt()
        if jwt_token and simCache.get(json.dumps(jwt_token)):
            return {'message':'Refresh token has been revoked'}, 401
        return fn(*args, **kwargs)
    return decorated_function
