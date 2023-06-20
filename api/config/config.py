import os
from datetime import timedelta
from flask_caching import Cache, SimpleCache
from decouple import config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
# import redis

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
# redis_client = redis.Redis(host='redis://red-ci88lv18g3nfucemlqg0', port=6379, db=0)

CACHE_TYPE = 'SimpleCache'
# CACHE_REDIS_URL = 'redis://red-ci88lv18g3nfucemlqg0:6379/'
CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds

cache = Cache(config={'CACHE_TYPE': CACHE_TYPE}, with_jinja2_ext=False)

simCache = SimpleCache()
limiter = Limiter(
    get_remote_address,
    storage= simCache,
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window"
)


class Config:
    SECRET_KEY = config("SECRET_KEY", "secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=120)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=272)
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    ERROR_INCLUDE_MESSAGE = False
    IPSTACK_ACCESS_KEY = config('IPSTACK_ACCESS_KEY')
    IPSTACK_API_URL = 'http://api.ipstack.com/'
    
    
    



class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "db.sqlite3")
    


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"

class ProdConfig(Config):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = config('POSTGRESQL')


config_dict = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
