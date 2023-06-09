from flask import Flask
from flask_restx import Api
from .db import db
from .config.config import config_dict, cache, limiter
from .auth.views import namespace as auth_namespace
from .resources.urls import url_ns
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_jwt_extended.exceptions import JWTExtendedException
from .resources import simple_geoip
from flask_cors import CORS



def create_app(config=config_dict['prod']):
    app = Flask(__name__)
    
    app.config.from_object(config)
    
    
    db.init_app(app)
    cache.init_app(app)
    CORS(app)
    simple_geoip.init_app(app)
    limiter.init_app(app)
    
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
              description='A url shortening services API to shorten, redirect and view shortened url analytics.',
              authorizations=authorizations,
              security='Bearer Auth'
            )
    
    # @api.errorhandler(JWTExtendedException)
    # def handle_jwt_exceptions(error):
    #     return {'message': str(error)}, getattr(error, 'code', 401)
    
    api.add_namespace(auth_namespace)
    api.add_namespace(url_ns)
    
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            

        }
        
    with app.app_context():
        # Create database tables
        db.create_all()
        
    return app


    
    