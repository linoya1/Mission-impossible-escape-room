import numpy as np
from flask import Blueprint, render_template, request, jsonify, url_for, session

room2 = Blueprint('room2', __name__)

# ===== הגדרות נתונים בסיסיות כפי שהיו + הוספת 3 תמונות חדשות =====
all_images = [
    "image7.jpg", "image8.jpg", "image9.jpg",
    "image10.jpg", "image11.jpg", "image12.jpg",
    # חדשות:
    "sub_surface.jpg",      # <- לא צוללת (0)
    "sub_corridor.jpg",     # <- לא צוללת (0)
    "sub_close_up.jpg",     # <- לא צוללת (0)
]

# אילו תמונות נחשבות "זוהתה צוללת" (האמת הקרקעית)
correct_images = {
    "image7.jpg", "image8.jpg", "image9.jpg", "image12.jpg",
}

# אילו תמונות אינן צוללת
wrong_images = {
    "image10.jpg", "image11.jpg",
    "sub_corridor.jpg",     # החדשות שנחשבות 0
    "sub_close_up.jpg", "sub_surface.jpg",
}

# שיוך קטגוריה אחת לכל תמונה לצורך "כיסוי" (coverage)
# (המודל שלך מסתכל על קטגוריה אחת לתמונה, וזה בסדר.)
CATEGORIES = {
    "image7.jpg":  "open_sea",
    "image8.jpg":  "night_ops",
    "image9.jpg":  "harbor",
    "image10.jpg": "harbor",
    "image11.jpg": "river",
    "image12.jpg": "underwater",

    # חדשות:
    "sub_surface.jpg":  "open_sea",
    "sub_corridor.jpg": "night_ops",
    "sub_close_up.jpg": "harbor",
}

# דרוג קושי (1=קל, 2=בינוני, 3=קשה) — ערכי ברירת מחדל סבירים
DIFFICULTY = {
    "image7.jpg":  2,
    "image8.jpg":  3,
    "image9.jpg":  2,
    "image10.jpg": 1,
    "image11.jpg": 2,
    "image12.jpg": 1,

    # חדשות:
    "sub_surface.jpg":  2,
    "sub_corridor.jpg": 2,
    "sub_close_up.jpg": 2,
}

# ===== פרמטרים של המשימה =====
REQUIRED_MIN_SELECTIONS = 3   # מינימום בחירות "זיהיתי צוללת" לפני בחינת מעבר
REQUIRED_COVERAGE = 2         # לפחות N קטגוריות שונות מבין הבחירות
SUCCESS_THRESHOLD = 0.75      # סף הצלחה (posterior)
MAX_ATTEMPTS = 8              # מגבלה כללית לניסיונות (כל לחיצה = ניסיון)
STREAK_STEP = 2               # כל רצף של 2 פגיעות = בונוס קטן

# Prior לבטא (מאוזן־עדין)
ALPHA0 = 1.5
BETA0  = 1.5

# ===== עזר =====
def softmax(scores):
    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / exp_scores.sum()

def _init_state():
    """יוצר מצב סשן אם לא קיים."""
    s = session.get("room2_state")
    if s is None:
        s = {
            "selections": [],   # [{image, label, confidence, truth, diff, cat}]
            "attempts": 0,
            "streak": 0,
        }
        session["room2_state"] = s
    return s

def _truth_for(img: str) -> int:
    return 1 if img in correct_images else 0

def _diff_for(img: str) -> int:
    return int(DIFFICULTY.get(img, 2))

def _cat_for(img: str) -> str:
    return CATEGORIES.get(img, "misc")

def _update_state(image: str, label: int, confidence: float):
    s = _init_state()
    sel = {
        "image": image,
        "label": int(label),
        "confidence": float(confidence),
        "truth": _truth_for(image),
        "diff": _diff_for(image),
        "cat": _cat_for(image),
    }
    s["selections"].append(sel)
    s["attempts"] += 1

    # streak מתעדכן רק על פגיעה "חיובית נכונה"
    if sel["truth"] == 1 and sel["label"] == 1:
        s["streak"] += 1
    else:
        s["streak"] = 0

    session["room2_state"] = s
    return s

def _posterior_success(selections):
    """
    Beta-Bernoulli posterior עם משקלי קושי (diff) ו-confidence.
    - diff: 1->1.0, 2->1.2, 3->1.5
    - confidence: 0..1 משפיע 0.6..1.0
    - טעות חיובית (סימן 1 על תמונה שגויה) מחמירה מעט את beta
    - streak bonus קטן בתום הלולאה
    """
    alpha = ALPHA0
    beta = BETA0

    for sel in selections:
        w_diff = {1: 1.0, 2: 1.2, 3: 1.5}.get(sel["diff"], 1.0)
        conf = max(0.0, min(1.0, float(sel.get("confidence", 0.7))))
        w = w_diff * (0.6 + 0.4 * conf)  # 0.6..1.0 כפול משקל קושי

        is_hit  = 1 if (sel["truth"] == 1 and sel["label"] == 1) else 0
        is_miss = 1 if (sel["truth"] == 0 and sel["label"] == 1) else 0

        if is_hit:
            alpha += 1.0 * w
        if is_miss:
            beta  += 1.2 * w   # מעט מחמיר ל-FP

    # bonus על רצף פגיעות בקצה
    streak_hits = 0
    for sel in reversed(selections):
        if sel["truth"] == 1 and sel["label"] == 1:
            streak_hits += 1
        else:
            break
    if streak_hits >= STREAK_STEP:
        alpha += 0.4 * (streak_hits // STREAK_STEP)

    return float(alpha / (alpha + beta))

def _coverage_ok(selections):
    cats = {sel["cat"] for sel in selections if sel["label"] == 1 and sel["truth"] == 1}
    return (len(cats) >= REQUIRED_COVERAGE, cats)

# ===== ראוטים =====
@room2.route("/room/2")
def show_room2():
    session.pop("room2_state", None)  # ← איפוס מצב החדר בכניסה חדשה
    _init_state()
    return render_template("room2.html", images=all_images)

@room2.route("/room2/submit", methods=["POST"])
def submit_label():
    data = request.get_json() or {}
    image = data.get("image")
    label = int(data.get("label", 0))      # 1 = זוהתה צוללת, 0 = לא
    confidence = float(data.get("confidence", 0.7))

    if image not in all_images:
        return jsonify({"status": "error", "message": "Invalid image selection."})

    state = _update_state(image, label, confidence)

    # חישובי התקדמות
    p_succ = _posterior_success(state["selections"])
    coverage_ok, cats = _coverage_ok(state["selections"])

    # בחירות שסומנו 1 (לאו דווקא נכונות)
    chosen_count = len([s for s in state["selections"] if s["label"] == 1])
    correct_chosen = len([s for s in state["selections"] if s["label"] == 1 and s["truth"] == 1])

    enough = correct_chosen >= REQUIRED_MIN_SELECTIONS
    attempts_left = max(0, MAX_ATTEMPTS - state["attempts"])
    can_pass = (p_succ >= SUCCESS_THRESHOLD) and enough and coverage_ok

    resp = {
        "status": "warning",
        "message": (
            f"IMF says: keep working. "
            f"p={p_succ:.2f} | coverage={len(cats)}/{REQUIRED_COVERAGE} | "
            f"chosen={chosen_count} (correct {correct_chosen}) | attempts_left={attempts_left}"
        ),
        "progress": {
            "posterior_success": round(p_succ, 3),
            "coverage": sorted(list(cats)),
            "coverage_required": REQUIRED_COVERAGE,
            "chosen_total": chosen_count,
            "correct_chosen": correct_chosen,
            "attempts_left": attempts_left,
            "streak": state["streak"],
        }
    }

    if can_pass:
        resp.update({
            "status": "success",
            "message": (
                f"IMF says: You located the submarine pattern.Go Down! "
                f"(p={p_succ:.2f}, coverage={len(cats)})"
            ),
            "next": url_for('static', filename='images/image13.jpg'),
            "next_room_url": url_for("enter_room", room_id=3),
        })
        return jsonify(resp)

    if attempts_left == 0:
        resp.update({
            "status": "error",
            "message": (
                f"IMF says: attempts exhausted. "
                f"p={p_succ:.2f}, coverage={len(cats)}/{REQUIRED_COVERAGE}. "
                f"Try a more diverse set of scenes."
            )
        })
        return jsonify(resp)

    return jsonify(resp)

@room2.route("/room2/reset", methods=["POST"])
def reset_room2():
    """מאפס מצב החדר (לסשן הנוכחי)."""
    session.pop("room2_state", None)
    return jsonify({"status": "ok", "message": "Room 2 state cleared."})
