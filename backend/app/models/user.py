# from ..config.db import db


# class User(db.Model):

#     __tablename__ = "users"

#     id = db.Column(db.Integer, primary_key=True)
#     full_name = db.Column(db.String(100))
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.Text, nullable=False)
#     role = db.Column(db.String(20), nullable=False)
#     created_at = db.Column(
#         db.DateTime,
#         server_default=db.func.now()
#     )






from ..config.db import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    
    # THIS IS THE MISSING LINE:
    profile_picture = db.Column(db.Text, default='default_avatar.png')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)