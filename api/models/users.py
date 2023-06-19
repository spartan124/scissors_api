from ..db import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(80), nullable=False, unique=True)
    full_name = db.Column(db.String(256), unique=False, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    urls = db.relationship('Url', backref='users', lazy=True)
