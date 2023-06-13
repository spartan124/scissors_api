import requests
import string
import random
from ..config.config import Config
from urllib.parse import urlparse, urlunparse

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
        response = requests.get(f'{Config.IPSTACK_API_URL}/{ip_address}?access_key={Config.IPSTACK_ACCESS_KEY}')
        if response.status_code == 200:
            data = response.json()
            if 'city' in data and 'country_name' in data:
                return f'{data["city"]}, {data["country_name"]}'
        return ''