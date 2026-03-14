from flask import Blueprint, render_template, request, jsonify

room1 = Blueprint('room1', __name__)

# רשימת התמונות לחדר 1 (התמונות שבהן טום קרוז מופיע הן התשובה הנכונה)
images_room1 = [
    {"filename": "image2.jpg"},
    {"filename": "image3.jpg"},
    {"filename": "image4.jpg"},  # טום קרוז לא נמצא כאן - לא לבחור
    {"filename": "image5.jpg"},
    {"filename": "image6.jpg"}
]
correct_images = {"image2.jpg", "image3.jpg", "image5.jpg", "image6.jpg"}  # התמונות הנכונות

@room1.route("/room/1")
def show_room1():
    return render_template("room1.html", images=images_room1)

@room1.route("/check_room1_answer", methods=["POST"])
def check_room1_answer():
    data = request.get_json()
    selected_images = set(data.get("selected_images", []))

    if selected_images == correct_images:
        return jsonify({"status": "success", "message": "Correct! You erased the evidence!"})
    else:
        return jsonify({"status": "fail", "message": "Wrong selection. Try again!"})
