from flask import jsonify
import requests
import string
import random
from ..config.config import Config
from urllib.parse import urlparse, urlunparse
from flask_simple_geoip import SimpleGeoIP

simple_geoip = SimpleGeoIP()

def generate_short_code():
    """Generate a random shortcode.
    """
    chars = string.ascii_letters + string.digits
    short_code = ''.join(random.choice(chars) for _ in range(6))
    return short_code



def normalize_url(url):
    parsed_url = urlparse(url)
    normalized_url = urlunparse(parsed_url._replace(path=parsed_url.path.rstrip('/')))
    return normalized_url

def get_geolocation(ip_address):
    location = simple_geoip.get_geoip_data(ip_address)
    region = location.get('region')
    country = location.get('country')
    return region, country