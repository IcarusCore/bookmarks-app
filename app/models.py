from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    real_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)  # Added unique=True to prevent duplicate emails
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='pending')
    theme = db.Column(db.String(50), default='cyberpunk')
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True)

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    server_url = db.Column(db.String(200))
    domain_url = db.Column(db.String(200))
    image_url = db.Column(db.String(200))