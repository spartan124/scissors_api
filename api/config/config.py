import os
from datetime import timedelta
from flask_caching import Cache, SimpleCache
from decouple import config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


redis_client = redis.Redis(
  host='redis-15144.c292.ap-southeast-1-1.ec2.cloud.redislabs.com',
  port=15144,
  db=0,
  password=config("REDIS_PASS")
  )

CACHE_DEFAULT_TIMEOUT = 300  # Cache timeout in seconds

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'}, with_jinja2_ext=False)

simCache = SimpleCache()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "50 per hour"],
   
   
    strategy="fixed-window",
)


class Config:
    SECRET_KEY = config("SECRET_KEY", "secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=120)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=272)
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    ERROR_INCLUDE_MESSAGE = False    
    GEOIPIFY_API_KEY = config('GEOIPIFY_API_KEY')
    
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
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = config('POSTGRESQL')


config_dict = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
