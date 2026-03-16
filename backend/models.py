"""SQLAlchemy models for users and mission progress tracking."""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db

class User(db.Model):
    """Player account with username and hashed passphrase."""
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw): self.password_hash = generate_password_hash(raw)
    def check_password(self, raw): return check_password_hash(self.password_hash, raw)

class Progress(db.Model):
    """Per-room progress for a user, including timing and attempts."""
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    room = db.Column(db.String(100), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)     # First entry timestamp for the room
    succeeded_at = db.Column(db.DateTime, nullable=True)   # First successful completion time
    attempts = db.Column(db.Integer, default=0)            # Attempt counter for the room

    __table_args__ = (db.UniqueConstraint('user_id', 'room', name='uq_user_room'),)
