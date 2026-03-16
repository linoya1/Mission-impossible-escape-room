"""Room 4 blueprint: RSA puzzle with optional C++ acceleration."""
# from flask import Blueprint, render_template

# room4 = Blueprint('room4', __name__)

# @room4.route("/room/4")
# def show_room4():
#     return render_template("room4.html")
from flask import Blueprint, render_template, request, jsonify, session, url_for
import math

room4 = Blueprint('room4', __name__)

# Try importing the C++ module; fall back to Python if unavailable
try:
    import rsa_cpp
except Exception:
    rsa_cpp = None

@room4.route("/room/4")
def show_room4():
    """Render the Room 4 puzzle page."""
    return render_template("room4.html")

# --- RSA toy params (p=61, q=53) ---
# n = 3233, e = 17, d = 2753 (classic example)
RSA_TRUE = {"id": "K3", "n": 3233, "e": 17, "d": 2753}
RSA_FAKE1 = {"id": "K1", "n": 3337, "e": 17, "d": 2753}
RSA_FAKE2 = {"id": "K2", "n": 3233, "e": 7,  "d": 1783}
KEY_OPTIONS = [RSA_FAKE1, RSA_FAKE2, RSA_TRUE]  # shuffled order in UI

# Secret symbol map used by the "IMF device"
SYMBOL_MAP = {
    '^':'A',
    '~':'N',
    '*':'O',
    '-':'M',
    '.':'L',
    '+':'Y',
    '=':' ',   # space
    '#':'D',
    '@':'E',
    '!':'T',
    '%':'H',
    '?':'S',
    '$':'P',
    '&':'I',
    '<':'C',
    '>':'R',
}


def _encode_plain_to_symbols(text):
    """Map plain text into the symbol alphabet used for the puzzle."""
    rev = {v:k for k,v in SYMBOL_MAP.items()}
    return ''.join(rev.get(ch.upper(), '?') for ch in text)

def _symbols_to_text(s):
    """Convert a string of symbols back to plain text."""
    return ''.join(SYMBOL_MAP.get(ch, '?') for ch in s)

def _rsa_encrypt_bytes(plain_bytes, e, n):
    """Encrypt a list of byte values with the provided RSA public key."""
    return [ pow(b, e, n) for b in plain_bytes ]


def _rsa_decrypt_bytes(cipher_bytes, d, n):
    """Decrypt a list of byte values using C++ if available, else Python."""
    if rsa_cpp:
        return rsa_cpp.rsa_decrypt_bytes(cipher_bytes, int(d), int(n))
    else:
        return [ pow(c, d, n) for c in cipher_bytes ]

@room4.route("/api/room4/lidar_scan", methods=["POST"])
def lidar_scan():
    """Build and return an encrypted payload plus candidate RSA keys."""
    data = request.get_json(silent=True) or {}
    objects = data.get("objects") or []

    # True message before symbol encoding
    clear_text = "STOP THE ENTITY AT CORE NODE"

    # Convert to symbols, then to byte values
    symbol_msg = _encode_plain_to_symbols(clear_text)
    plain_bytes = [ord(ch) for ch in symbol_msg]  # each char <256

    # Encrypt with the correct public key
    cipher = _rsa_encrypt_bytes(plain_bytes, RSA_TRUE["e"], RSA_TRUE["n"])

    # Store cipher for later decryption
    session["r4_cipher"] = cipher

    # Return candidate key options (without private exponent)
    options = [{"id": k["id"], "n": k["n"]} for k in KEY_OPTIONS]

    return jsonify({
        "status": "ok",
        "objects": objects,
        "cipher": cipher,
        "key_options": options
    })

@room4.route("/api/room4/rsa_try", methods=["POST"])
def rsa_try():
    """Try a key against the stored cipher and return decoded result."""
    data = request.get_json(silent=True) or {}
    key_id = data.get("key_id")

    cipher = session.get("r4_cipher")
    if not cipher:
        return jsonify({"status":"error","message":"No cipher yet. Run LIDAR scan first."}), 400

    # Find key by id
    key = next((k for k in KEY_OPTIONS if k["id"] == key_id), None)
    if not key:
        return jsonify({"status":"error","message":"Unknown key."}), 400

    # Decrypt and decode
    dec_bytes = _rsa_decrypt_bytes(cipher, key["d"], key["n"])
    try:
        symbol_str = ''.join(chr(b) for b in dec_bytes)
    except Exception:
        symbol_str = ""

    # Wrong key yields gibberish; right key decodes to readable text
    decoded = _symbols_to_text(symbol_str)

    success = ("STOP" in decoded) or ("ENTITY" in decoded)
    result = {
        "status": "ok",
        "key_id": key_id,
        "symbol_text": symbol_str,
        "decoded_text": decoded,
        "success": bool(success),
    }

    # On success, provide the next route for the UI
    if success:
        result["next"] = url_for("home")

    return jsonify(result)
