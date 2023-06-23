from ..models import User

from werkzeug.security import generate_password_hash

def create_user(full_name='Test Admin', username='tadmin', email='tadmin@test.com', password_hash=generate_password_hash('password')):
    user = User(
        full_name=full_name,
        username=username,
        email=email,
        password_hash=password_hash
    )
    return user