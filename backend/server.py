"""Flask app entrypoint, routes, and room progression enforcement."""

from flask import Flask, render_template, redirect, url_for, request, session, jsonify, abort
import os
from backend.config import DevelopmentConfig

# === DB ===
from backend.db import db, init_db
from backend.models import User, Progress  # Progress model for per-room tracking

# === PROGRESS helpers ===
from backend.progress import start_progress, mark_success, last_success_room

# === Blueprints ===
from backend.rooms.room1 import room1
from backend.rooms.room2 import room2
from backend.rooms.room3 import room3
from backend.rooms.room4 import room4

# app = Flask(__name__, static_folder="static")
# app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")  # Session signing key
app = Flask(__name__, static_folder="static")
app.config.from_object(DevelopmentConfig)
app.secret_key = app.config["SECRET_KEY"]  # Session signing key
# === Database wiring ===
init_db(app)

# Create tables at startup (imports all models into metadata)
with app.app_context():
    from . import models
    db.create_all()

# ------------------ Room order for progression ------------------
ORDER = ['room1', 'room2', 'room3', 'room4']   # Canonical progression order
ROOM_IDS = [1, 2, 3, 4]

def room_name_from_id(room_id: int) -> str:
    """Map numeric room id to room name used in progress tracking."""
    return f'room{room_id}'

def next_room_name(curr_room_name: str | None) -> str:
    """Compute the next allowed room name given the last successful room."""
    if not curr_room_name:
        return ORDER[0]
    try:
        i = ORDER.index(curr_room_name)
    except ValueError:
        return ORDER[0]
    return ORDER[i + 1] if i < len(ORDER) - 1 else ORDER[-1]


def allowed_room_for(uid: int) -> str:
    """Return the next room a user may enter, preventing forward skips."""
    last = last_success_room(uid)        # 'roomX' or None
    return next_room_name(last)

# ------------------ Legacy in-memory state (kept for compatibility) ------------------
players = {}

# ---------- Landing and prelude ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    """Authenticate or create a user, then start the mission at the prelude."""
    # Username + password from the form
    player_name = (request.form.get("player_name") or "").strip()
    password    = request.form.get("password") or ""

    if not player_name or not password:
        return render_template("index.html", error="Please enter a codename and passphrase.")

    # Find or create user in the database
    user = User.query.filter_by(username=player_name).first()
    if user is None:
        # Auto-register if not found
        user = User(username=player_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    else:
        # Verify password
        if not user.check_password(password):
            return render_template("index.html", error="Invalid passphrase. Try again.")

    # Store session data (kept for compatibility)
    session["player_name"] = player_name
    session["player_id"]   = player_name
    session["user_id"]     = user.id
    players[session["player_id"]] = {"room": 1}

    # Start at the prelude room
    return redirect(url_for("prelude"))

@app.route("/prelude", methods=["GET"])
def prelude():
    # prelude.html uses session.get('player_name') to render the codename
    return render_template("prelude.html")

# Optional: log prelude success events
@app.route("/prelude/event", methods=["POST"])
def prelude_event():
    data = request.get_json() or {}
    print("Prelude event:", data)
    return jsonify(status="ok")

# ---------- Player summary ----------
@app.route('/me')
def my_summary():
    """Render a per-user mission summary using tracked progress rows."""
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    rows = Progress.query.filter_by(user_id=uid).order_by(Progress.room).all()
    # Rooms completed successfully
    succeeded = {r.room for r in rows if r.succeeded_at}
    finished = all(room in succeeded for room in ORDER)
    items = []
    for r in rows:
        secs = (r.succeeded_at - r.started_at).total_seconds() if (r.started_at and r.succeeded_at) else None
        items.append({
            'room': r.room,
            'status': 'Passed' if r.succeeded_at else 'In progress',
            'attempts': r.attempts or 0,
            'seconds': secs
        })

    return render_template('game/summery.html', items=items, finished=finished)
# ---------- Rooms (GET) ----------
@app.route("/room/<int:room_id>")
def enter_room(room_id):
    """Gate room entry based on progress and start timing for the room."""
    if room_id not in ROOM_IDS:
        return redirect(url_for("home"))

    # === Progress: enforce order and start timing ===
    if 'user_id' in session:
        uid = session['user_id']
        requested = room_name_from_id(room_id)     # 'roomX'
        allowed  = allowed_room_for(uid)           # Next allowed room

        # Prevent forward skips; allow back/redo
        if ORDER.index(requested) > ORDER.index(allowed):
            return redirect(url_for("enter_room", room_id=int(allowed.replace('room', ''))))

        # Start timing for this room (first attempt sets started_at)
        start_progress(uid, requested)

    return render_template(f"room{room_id}.html")

# ---------- Room success (called by blueprints/JS) ----------
@app.route("/room/<int:room_id>/success", methods=["POST", "GET"])
def room_success(room_id):
    """Mark room success, then route to next room or summary when finished."""
    if room_id not in ROOM_IDS:
        return redirect(url_for("home"))
    if 'user_id' not in session:
        return redirect(url_for("home"))

    uid = session['user_id']
    current_room_name = room_name_from_id(room_id)

    # Close timing for the current room
    mark_success(uid, current_room_name)

    # If last room, go to summary
    if current_room_name == ORDER[-1]:
        return redirect(url_for('my_summary'))

    # Otherwise, start timing the next room and continue
    next_name = next_room_name(current_room_name)
    next_id   = int(next_name.replace('room', ''))
    if next_id != room_id:
        start_progress(uid, next_name)

    return redirect(url_for("enter_room", room_id=next_id))

# ---------- Register room blueprints ----------
app.register_blueprint(room1)
app.register_blueprint(room2)
app.register_blueprint(room3)
app.register_blueprint(room4)

# if __name__ == "__main__":
#    app.run(debug=True)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

