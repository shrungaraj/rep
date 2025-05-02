from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    instagram_username = db.Column(db.String(64))
    instagram_password_hash = db.Column(db.String(256))
    instagram_token = db.Column(db.String(512))
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = db.relationship('Source', backref='user', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='user', lazy=True, cascade="all, delete-orphan")
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade="all, delete-orphan")


class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'account' or 'hashtag'
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'))
    instagram_post_id = db.Column(db.String(100), nullable=False)
    instagram_post_url = db.Column(db.String(255))
    caption = db.Column(db.Text)
    media_urls = db.Column(JSON)
    status = db.Column(db.String(20), default='pending')  # pending, posted, failed
    scheduled_time = db.Column(db.DateTime)
    posted_time = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with the source
    source = db.relationship('Source', backref='posts')


class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    auto_repost = db.Column(db.Boolean, default=False)
    repost_delay = db.Column(db.Integer, default=0)  # in minutes
    add_credit = db.Column(db.Boolean, default=True)
    credit_text = db.Column(db.String(255), default="Reposted from @{source}")
    check_interval = db.Column(db.Integer, default=60)  # in minutes
    post_limit_per_day = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
