"""Progress helpers for starting rooms and marking successful completion."""
from datetime import datetime
from .db import db
from .models import Progress

def start_progress(user_id: int, room: str) -> Progress:
    """Start or continue a room attempt, tracking start time and attempts."""
    row = Progress.query.filter_by(user_id=user_id, room=room).first()
    if not row:
        row = Progress(user_id=user_id, room=room, started_at=datetime.utcnow(), attempts=1)
        db.session.add(row)
    else:
        if row.started_at is None:
            row.started_at = datetime.utcnow()
        row.attempts = (row.attempts or 0) + 1
    db.session.commit()
    return row

def mark_success(user_id: int, room: str) -> Progress:
    """Mark the first successful completion timestamp for a room."""
    row = Progress.query.filter_by(user_id=user_id, room=room).first()
    if not row:
        row = Progress(user_id=user_id, room=room, started_at=datetime.utcnow())
        db.session.add(row)
    if row.succeeded_at is None:
        row.succeeded_at = datetime.utcnow()
        db.session.commit()
    return row

def last_success_room(user_id: int):
    """Return the most recently completed room name, or None if none."""
    row = Progress.query.filter(
        Progress.user_id == user_id,
        Progress.succeeded_at.isnot(None)
    ).order_by(Progress.succeeded_at.desc()).first()
    return row.room if row else None
