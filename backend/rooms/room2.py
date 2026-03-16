"""Room 2 blueprint: submarine identification puzzle with Bayesian scoring."""
import numpy as np
from flask import Blueprint, render_template, request, jsonify, url_for, session

room2 = Blueprint('room2', __name__)

# ===== Base image set with additional distractors =====
all_images = [
    "image7.jpg", "image8.jpg", "image9.jpg",
    "image10.jpg", "image11.jpg", "image12.jpg",
    "sub_surface.jpg",      # not a submarine (0)
    "sub_corridor.jpg",     # not a submarine (0)
    "sub_close_up.jpg",     # not a submarine (0)
]

# Ground-truth submarine images
correct_images = {
    "image7.jpg", "image8.jpg", "image9.jpg", "image12.jpg",
}

# Non-submarine images
wrong_images = {
    "image10.jpg", "image11.jpg",
    "sub_corridor.jpg",
    "sub_close_up.jpg", "sub_surface.jpg",
}

# One category per image for coverage checks
CATEGORIES = {
    "image7.jpg":  "open_sea",
    "image8.jpg":  "night_ops",
    "image9.jpg":  "harbor",
    "image10.jpg": "harbor",
    "image11.jpg": "river",
    "image12.jpg": "underwater",

    "sub_surface.jpg":  "open_sea",
    "sub_corridor.jpg": "night_ops",
    "sub_close_up.jpg": "harbor",
}

# Difficulty ratings: 1=easy, 2=medium, 3=hard
DIFFICULTY = {
    "image7.jpg":  2,
    "image8.jpg":  3,
    "image9.jpg":  2,
    "image10.jpg": 1,
    "image11.jpg": 2,
    "image12.jpg": 1,

    "sub_surface.jpg":  2,
    "sub_corridor.jpg": 2,
    "sub_close_up.jpg": 2,
}

# ===== Mission parameters =====
REQUIRED_MIN_SELECTIONS = 3   # Minimum correct picks before checking pass
REQUIRED_COVERAGE = 2         # At least N distinct categories among correct picks
SUCCESS_THRESHOLD = 0.75      # Posterior success threshold
MAX_ATTEMPTS = 8              # Max attempts per session
STREAK_STEP = 2               # Every N correct hits adds a small bonus

# Beta prior (balanced)
ALPHA0 = 1.5
BETA0  = 1.5

# ===== Helpers =====
def softmax(scores):
    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / exp_scores.sum()

def _init_state():
    """Initialize room state in session for the current player."""
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
    """Append a labeled selection and update attempts/streak counters."""
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

    # Streak counts only correct positive hits
    if sel["truth"] == 1 and sel["label"] == 1:
        s["streak"] += 1
    else:
        s["streak"] = 0

    session["room2_state"] = s
    return s

def _posterior_success(selections):
    """Compute a weighted Beta-Bernoulli posterior success score."""
    alpha = ALPHA0
    beta = BETA0

    for sel in selections:
        w_diff = {1: 1.0, 2: 1.2, 3: 1.5}.get(sel["diff"], 1.0)
        conf = max(0.0, min(1.0, float(sel.get("confidence", 0.7))))
        w = w_diff * (0.6 + 0.4 * conf)  # 0.6..1.0 scaled by difficulty

        is_hit  = 1 if (sel["truth"] == 1 and sel["label"] == 1) else 0
        is_miss = 1 if (sel["truth"] == 0 and sel["label"] == 1) else 0

        if is_hit:
            alpha += 1.0 * w
        if is_miss:
            beta  += 1.2 * w   # Mild penalty for false positives

    # Small bonus for trailing streak of correct hits
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

# ===== Routes =====
@room2.route("/room/2")
def show_room2():
    """Render the Room 2 puzzle and reset per-session state."""
    session.pop("room2_state", None)  # reset state on fresh entry
    _init_state()
    return render_template("room2.html", images=all_images)

@room2.route("/room2/submit", methods=["POST"])
def submit_label():
    """Handle a labeled image selection and return progress feedback."""
    data = request.get_json() or {}
    image = data.get("image")
    label = int(data.get("label", 0))      # 1 = submarine, 0 = not
    confidence = float(data.get("confidence", 0.7))

    if image not in all_images:
        return jsonify({"status": "error", "message": "Invalid image selection."})

    state = _update_state(image, label, confidence)

    # Progress calculations
    p_succ = _posterior_success(state["selections"])
    coverage_ok, cats = _coverage_ok(state["selections"])

    # All picks labeled as positive (not necessarily correct)
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
    """Clear the current session's Room 2 state."""
    session.pop("room2_state", None)
    return jsonify({"status": "ok", "message": "Room 2 state cleared."})
