
from ..db import db
from flask_restx import abort
from .users import User
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from .urls import Url, Click


def save(self):
    db.session.add(self)
    db.session.commit()
    
def update(self):
    db.session.commit()
    
def delete(self):
        db.session.delete(self)
        db.session.commit()
