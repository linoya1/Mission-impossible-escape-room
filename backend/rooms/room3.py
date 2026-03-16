"""Room 3 blueprint: trajectory anomaly scoring and classification."""
from flask import Blueprint, render_template, request, jsonify
import math

room3 = Blueprint('room3', __name__)

@room3.route("/room/3")
def show_room3():
    """Render the Room 3 puzzle page."""
    return render_template("room3.html")


# ====== API for anomaly scoring ======

def _curvature2d(x1, y1, x2, y2, x3, y3):
    """Compute the turning angle between three 2D points."""
    a1 = math.atan2(y2 - y1, x2 - x1)
    a2 = math.atan2(y3 - y2, x3 - x2)
    d = abs(a2 - a1)
    if d > math.pi:
        d = 2 * math.pi - d
    return d  # 0..pi

def _score_trajectory(points):
    """Compute the anomaly score for a trajectory based on curvature and jerk."""
    if len(points) < 3:
        return 0.0
    sum_curv, max_jerk = 0.0, 0.0
    for i in range(2, len(points)):
        x1, y1, t1 = points[i-2]
        x2, y2, t2 = points[i-1]
        x3, y3, t3 = points[i]
        sum_curv += _curvature2d(x1, y1, x2, y2, x3, y3)

        dt1 = max(1e-6, t2 - t1)
        dt2 = max(1e-6, t3 - t2)
        vx1, vy1 = (x2 - x1) / dt1, (y2 - y1) / dt1
        vx2, vy2 = (x3 - x2) / dt2, (y3 - y2) / dt2
        ax, ay = (vx2 - vx1) / dt2, (vy2 - vy1) / dt2  # jerk proxy
        max_jerk = max(max_jerk, math.hypot(ax, ay))

    curv_norm = min(1.0, sum_curv / (math.pi * (len(points) - 2)))
    jerk_norm = min(1.0, max_jerk / 10.0)
    s = 0.6 * curv_norm + 0.4 * jerk_norm
    return max(0.0, min(1.0, s))

@room3.route("/api/anomaly/score", methods=["POST"])
def api_anomaly_score():
    """Return a scalar anomaly score for a trajectory."""
    data = request.get_json(silent=True) or {}
    traj = data.get("trajectory") or []
    clean = [p for p in traj if isinstance(p, list) and len(p) == 3]
    return jsonify({"score": _score_trajectory(clean)})

# === Add below in backend/rooms/room3.py ===
from flask import session

def _features(points):
    """Extract a tiny feature vector to compare trajectories later."""
    if len(points) < 3:
        return [0.0, 0.0, 0.0]
    # total curvature + max jerk from our existing scorer, plus avg speed
    sum_curv, max_jerk = 0.0, 0.0
    total_dist, total_dt = 0.0, 0.0
    for i in range(2, len(points)):
        x1, y1, t1 = points[i-2]
        x2, y2, t2 = points[i-1]
        x3, y3, t3 = points[i]
        sum_curv += _curvature2d(x1, y1, x2, y2, x3, y3)

        dt1 = max(1e-6, t2 - t1)
        dt2 = max(1e-6, t3 - t2)
        vx1, vy1 = (x2 - x1) / dt1, (y2 - y1) / dt1
        vx2, vy2 = (x3 - x2) / dt2, (y3 - y2) / dt2
        ax, ay = (vx2 - vx1) / dt2, (vy2 - vy1) / dt2
        max_jerk = max(max_jerk, math.hypot(ax, ay))

        total_dist += math.hypot(x3 - x2, y3 - y2)
        total_dt   += (t3 - t2)

    curv_norm = min(1.0, sum_curv / (math.pi * (len(points) - 2)))
    jerk_norm = min(1.0, max_jerk / 10.0)
    avg_speed = (total_dist / max(1e-6, total_dt)) if total_dt > 0 else 0.0
    # rescale avg_speed to ~[0,1] heuristically
    sp_norm = min(1.0, avg_speed / 10.0)
    return [curv_norm, jerk_norm, sp_norm]

def _euclid(a, b):
    """Compute the Euclidean distance between two points in feature space."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

@room3.route("/api/anomaly/save", methods=["POST"])
def api_anomaly_save():
    """Save current trajectory as a hostile prototype in session."""
    data = request.get_json(silent=True) or {}
    traj = data.get("trajectory") or []
    clean = [p for p in traj if isinstance(p, list) and len(p) == 3]
    vec = _features(clean)

    bank = session.setdefault("hostile_prototypes", [])
    bank.append(vec)
    session["hostile_prototypes"] = bank
    return jsonify({"status": "ok", "saved_count": len(bank), "vector": vec})

@room3.route("/api/anomaly/classify", methods=["POST"])
def api_anomaly_classify():
    """Classify trajectory using anomaly score + nearest saved prototype."""
    data = request.get_json(silent=True) or {}
    traj = data.get("trajectory") or []
    clean = [p for p in traj if isinstance(p, list) and len(p) == 3]

    score = _score_trajectory(clean)
    vec = _features(clean)
    bank = session.get("hostile_prototypes", [])

    # Hostile if anomaly high or close to a saved hostile prototype
    is_hostile_by_score = score >= 0.70
    nearest = None
    dist = None
    if bank:
        dists = [_euclid(vec, v) for v in bank]
        dist = min(dists)
        nearest = bank[dists.index(dist)]
    # Threshold ~0.35 works for our 3D feature vector (heuristic)
    is_hostile_by_similarity = (dist is not None and dist <= 0.35)

    hostile = bool(is_hostile_by_score or is_hostile_by_similarity)
    reason = "score" if is_hostile_by_score else ("similarity" if is_hostile_by_similarity else "none")

    return jsonify({
        "label": "hostile" if hostile else "ally",
        "score": score,
        "nearest_dist": dist,
        "reason": reason,
        "bank_size": len(bank)
    })
