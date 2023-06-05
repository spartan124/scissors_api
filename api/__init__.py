from flask import Flask
from flask_restx import Api
from .db import db
from .config.config import config_dict
from .auth.views import namespace as auth_namespace
from .resources.urls import url_ns
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_jwt_extended.exceptions import JWTExtendedException
import redis

cache = Cache()

def create_app(config=config_dict['dev']):
    app = Flask(__name__)
    
    app.config.from_object(config)
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    
    db.init_app(app)
    cache.init_app(app)
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    migrate = Migrate(app, db)
    
    jwt = JWTManager(app)
    authorizations= {
        "Bearer Auth": {
            'type': 'apiKey',
            'in':'header',
            'name':'Authorization',
            'description': 'Add a JWT token to the header with ** Bearer &lt;JWT&gt; token to authorize **'
        }
    }
    
    api = Api(app,
              title='Scissors API',
              description='A url shortening services API to explore the Nigerian region',
              authorizations=authorizations,
              security='Bearer Auth'
            )
    
    @api.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        return {'message': str(error)}, getattr(error, 'code', 401)
    
    api.add_namespace(auth_namespace)
    api.add_namespace(url_ns)
    
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            

        }
    return app
