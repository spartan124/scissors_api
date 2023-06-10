from ..db import db
from datetime import datetime


class Click(db.Model):
    __tablename__ = "click"
    
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    click_source = db.Column(db.String(255))

class Url(db.Model):
    __tablename__ = 'url'
    
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False, unique=True)
    short_code = db.Column(db.String(20), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    last_used_at = db.Column(db.DateTime)
    click_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    clicks = db.relationship('Click', backref='url', lazy=True)



    def __init__(self, short_code, original_url, user_id):
        self.short_code = short_code
        self.original_url = original_url
        self.user_id = user_id
        
