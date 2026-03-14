#from flask import Blueprint, render_template

#room4 = Blueprint('room4', __name__)

#@room4.route("/room/4")
#def show_room4():
#    return render_template("room4.html")
from flask import Blueprint, render_template, request, jsonify, session, url_for
import math

room4 = Blueprint('room4', __name__)

# ננסה לייבא את ++C; אם לא קיים - fallback לפייתון
try:
    import rsa_cpp
except Exception:
    rsa_cpp = None

@room4.route("/room/4")
def show_room4():
    return render_template("room4.html")

# --- RSA toy params (p=61, q=53) ---
# n = 3233, e = 17, d = 2753 (הדוגמה הקלאסית)
RSA_TRUE = {"id": "K3", "n": 3233, "e": 17, "d": 2753}
RSA_FAKE1 = {"id": "K1", "n": 3337, "e": 17, "d": 2753}
RSA_FAKE2 = {"id": "K2", "n": 3233, "e": 7,  "d": 1783}
KEY_OPTIONS = [RSA_FAKE1, RSA_FAKE2, RSA_TRUE]  # סדר אקראי

# מפה סודית (סמלים -> אותיות) של "מכשיר ה-IMF"
# מפה סודית (סמלים -> אותיות) של "מכשיר ה-IMF"
SYMBOL_MAP = {
    '^':'A',
    '~':'N',
    '*':'O',
    '-':'M',
    '.':'L',
    '+':'Y',
    '=':' ',   # רווח
    '#':'D',
    '@':'E',
    '!':'T',
    '%':'H',
    '?':'S',   # נוספו
    '$':'P',
    '&':'I',
    '<':'C',
    '>':'R',
}


def _encode_plain_to_symbols(text):
    # הופך טקסט לאוסף סמלים (למשחק). פשוט ומגוחך בכוונה :)
    rev = {v:k for k,v in SYMBOL_MAP.items()}
    return ''.join(rev.get(ch.upper(), '?') for ch in text)

def _symbols_to_text(s):
    return ''.join(SYMBOL_MAP.get(ch, '?') for ch in s)

def _rsa_encrypt_bytes(plain_bytes, e, n):
    return [ pow(b, e, n) for b in plain_bytes ]

def _rsa_decrypt_bytes(cipher_bytes, d, n):
    if rsa_cpp:
        return rsa_cpp.rsa_decrypt_bytes(cipher_bytes, int(d), int(n))
    else:
        return [ pow(c, d, n) for c in cipher_bytes ]

@room4.route("/api/room4/lidar_scan", methods=["POST"])
def lidar_scan():
    """
    מקבל 'objects' (רשימת שמות מה-UI), ובונה מטען מוצפן לפי הנתונים.
    בפועל כאן תמיד ניצור הודעת-סמלים קבועה ונצפין.
    """
    data = request.get_json(silent=True) or {}
    objects = data.get("objects") or []

    # המסר האמיתי (לפני הסמלים): STOP THE ENTITY AT CORE NODE
    clear_text = "STOP THE ENTITY AT CORE NODE"

    # ממירים לסמלים (כמו מכשיר IMF) – זה מה שייצא אחרי RSA
    symbol_msg = _encode_plain_to_symbols(clear_text)
    plain_bytes = [ord(ch) for ch in symbol_msg]  # כל תו (<256)

    # מצפינים במפתח הציבורי (של המפתח הנכון)
    cipher = _rsa_encrypt_bytes(plain_bytes, RSA_TRUE["e"], RSA_TRUE["n"])

    # שומרים ב-session כדי שנוכל לפענח אח"כ
    session["r4_cipher"] = cipher

    # מחזירים גם רשימת מפתחות מועמדים (בלי הד)
    options = [{"id": k["id"], "n": k["n"]} for k in KEY_OPTIONS]

    return jsonify({
        "status": "ok",
        "objects": objects,
        "cipher": cipher,
        "key_options": options
    })

@room4.route("/api/room4/rsa_try", methods=["POST"])
def rsa_try():
    data = request.get_json(silent=True) or {}
    key_id = data.get("key_id")

    cipher = session.get("r4_cipher")
    if not cipher:
        return jsonify({"status":"error","message":"No cipher yet. Run LIDAR scan first."}), 400

    # מאתרים את המפתח לפי id
    key = next((k for k in KEY_OPTIONS if k["id"] == key_id), None)
    if not key:
        return jsonify({"status":"error","message":"Unknown key."}), 400

    # מפענחים
    dec_bytes = _rsa_decrypt_bytes(cipher, key["d"], key["n"])
    try:
        symbol_str = ''.join(chr(b) for b in dec_bytes)
    except Exception:
        symbol_str = ""

    # אם המפתח שגוי – יהיה ג'יבריש; אם נכון – מפה סודית תחזיר טקסט קריא
    decoded = _symbols_to_text(symbol_str)

    success = ("STOP" in decoded) or ("ENTITY" in decoded)
    result = {
        "status": "ok",
        "key_id": key_id,
        "symbol_text": symbol_str,
        "decoded_text": decoded,
        "success": bool(success),
    }

    # אם הצליח – החדר נפתח
    if success:
        result["next"] = url_for("home")  # או room5 אם תרצי בעתיד

    return jsonify(result)
