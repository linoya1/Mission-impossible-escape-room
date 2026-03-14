from flask import Flask, render_template, redirect, url_for, request, session, jsonify, abort
import os

# === DB ===
from backend.db import db, init_db
from backend.models import User, Progress  # <-- הוספנו Progress

# === PROGRESS helpers ===
from backend.progress import start_progress, mark_success, last_success_room  # פונקציות עזר

# === Blueprints (קיים) ===
from backend.rooms.room1 import room1
from backend.rooms.room2 import room2
from backend.rooms.room3 import room3
from backend.rooms.room4 import room4

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")  # לשמירת מצב המשחק

# === חיבור מסד נתונים (קיים) ===
init_db(app)

# יצירת טבלאות (מתוקן לשם המודול המלא כדי לעבוד גם כשהקובץ מורץ מהשורש)
with app.app_context():
    from . import models  # חשוב: טוען את כל המודלים (User, Progress)
    db.create_all()

# ------------------ הגדרות חדרים/סדר (PROGRESS) ------------------
ORDER = ['room1', 'room2', 'room3', 'room4']   # עדכני לפי החדרים האמיתיים
ROOM_IDS = [1, 2, 3, 4]

def room_name_from_id(room_id: int) -> str:
    return f'room{room_id}'

def next_room_name(curr_room_name: str | None) -> str:
    """אם אין עדיין חדר שעברנו (None) → room1, אחרת הבא לפי ORDER."""
    if not curr_room_name:
        return ORDER[0]
    try:
        i = ORDER.index(curr_room_name)
    except ValueError:
        return ORDER[0]
    return ORDER[i + 1] if i < len(ORDER) - 1 else ORDER[-1]

def allowed_room_for(uid: int) -> str:
    """מהו החדר הבא שמותר למשתמש להיכנס אליו (למניעת קפיצות)?"""
    last = last_success_room(uid)        # 'roomX' או None
    return next_room_name(last)

# ------------------ תאימות ישנה (נשאר כמו שהיה) ------------------
players = {}

# ---------- דפי פתיחה / פרלוד (נשאר כמו שהיה) ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    # שם משתמש + סיסמה מהטופס
    player_name = (request.form.get("player_name") or "").strip()
    password    = request.form.get("password") or ""

    if not player_name or not password:
        return render_template("index.html", error="Please enter a codename and passphrase.")

    # מצא/צר משתמש במסד הנתונים
    user = User.query.filter_by(username=player_name).first()
    if user is None:
        # הרשמה אוטומטית (אם לא רוצים - החליפו לשגיאה "User not found")
        user = User(username=player_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    else:
        # אימות סיסמה
        if not user.check_password(password):
            return render_template("index.html", error="Invalid passphrase. Try again.")

    # שמירה ל-session (תאימות עם הקוד שהיה)
    session["player_name"] = player_name
    session["player_id"]   = player_name   # נשאר כפי שהיה אצלך
    session["user_id"]     = user.id       # === PROGRESS: נוסיף user_id אמיתי לסשן
    players[session["player_id"]] = {"room": 1}

    # חשוב: עוברים קודם ל־Prelude (חדר קדם עם זיהוי עין השומר)
    return redirect(url_for("prelude"))

@app.route("/prelude", methods=["GET"])
def prelude():
    # prelude.html משתמש ב-session.get('player_name') להצגת השם
    return render_template("prelude.html")

# אופציונלי: לוג/סטטיסטיקה מאירוע ההצלחה בפרלוד (נשאר כמו שהיה)
@app.route("/prelude/event", methods=["POST"])
def prelude_event():
    data = request.get_json() or {}
    print("Prelude event:", data)
    return jsonify(status="ok")

# ---------- מסך סיכום לשחקן (חדש) ----------
@app.route('/me')
def my_summary():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    uid = session['user_id']
    rows = Progress.query.filter_by(user_id=uid).order_by(Progress.room).all()
    # רשימת חדרים שעברו בהצלחה
    succeeded = {r.room for r in rows if r.succeeded_at}
    # השרת כבר מכיל ORDER = ['room1','room2','room3','room4']
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
# ---------- חדרים (GET) ----------
@app.route("/room/<int:room_id>")
def enter_room(room_id):
    if room_id not in ROOM_IDS:
        return redirect(url_for("home"))

    # === PROGRESS: בדיקת הוגנות + התחלת מדידה ===
    if 'user_id' in session:
        uid = session['user_id']
        requested = room_name_from_id(room_id)     # 'roomX'
        allowed  = allowed_room_for(uid)           # החדר הבא שהמשתמש רשאי להיכנס אליו

        # לא לאפשר קפיצה קדימה (כן לאפשר אחורה/אותו חדר אם תרצי)
        if ORDER.index(requested) > ORDER.index(allowed):
            return redirect(url_for("enter_room", room_id=int(allowed.replace('room', ''))))

        # מתחילים למדוד חדר זה (אם זה ניסיון ראשון, ייקבע started_at; אחרת attempts++)
        start_progress(uid, requested)

    return render_template(f"room{room_id}.html")

# ---------- סימון הצלחה לחדר (חדש, לזימון מה-Blueprints/JS) ----------
@app.route("/room/<int:room_id>/success", methods=["POST", "GET"])
def room_success(room_id):
    if room_id not in ROOM_IDS:
        return redirect(url_for("home"))
    if 'user_id' not in session:
        return redirect(url_for("home"))

    uid = session['user_id']
    current_room_name = room_name_from_id(room_id)

    # סוגרים מדידה של החדר הנוכחי
    mark_success(uid, current_room_name)

    # אם זה החדר האחרון ב-ORDER => דף סיכום
    if current_room_name == ORDER[-1]:
        return redirect(url_for('my_summary'))

    # אחרת: מתחילים למדוד את החדר הבא וממשיכים כרגיל
    next_name = next_room_name(current_room_name)
    next_id   = int(next_name.replace('room', ''))
    if next_id != room_id:
        start_progress(uid, next_name)

    return redirect(url_for("enter_room", room_id=next_id))

# ---------- רישום ה-Blueprint לכל החדרים (נשאר כמו שהיה) ----------
app.register_blueprint(room1)
app.register_blueprint(room2)
app.register_blueprint(room3)
app.register_blueprint(room4)

if __name__ == "__main__":
    app.run(debug=True)
