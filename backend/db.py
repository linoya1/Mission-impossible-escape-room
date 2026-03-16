"""Database setup and SQLAlchemy initialization helpers."""
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "game.db")


def init_db(app):
    """Configure the app's database URI and initialize SQLAlchemy."""
    uri = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)