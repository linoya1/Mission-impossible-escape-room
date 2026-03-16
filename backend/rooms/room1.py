"""Room 1 blueprint: image selection puzzle validation."""
from flask import Blueprint, render_template, request, jsonify

room1 = Blueprint('room1', __name__)

# Image choices for Room 1 (Tom Cruise appearances are the correct picks)
images_room1 = [
    {"filename": "image2.jpg"},
    {"filename": "image3.jpg"},
    {"filename": "image4.jpg"},  # Not a correct image
    {"filename": "image5.jpg"},
    {"filename": "image6.jpg"}
]
correct_images = {"image2.jpg", "image3.jpg", "image5.jpg", "image6.jpg"}  # Correct images

@room1.route("/room/1")
def show_room1():
    """Render the Room 1 puzzle page."""
    return render_template("room1.html", images=images_room1)

@room1.route("/check_room1_answer", methods=["POST"])
def check_room1_answer():
    """Validate selected images against the correct set."""
    data = request.get_json()
    selected_images = set(data.get("selected_images", []))

    if selected_images == correct_images:
        return jsonify({"status": "success", "message": "Correct! You erased the evidence!"})
    else:
        return jsonify({"status": "fail", "message": "Wrong selection. Try again!"})
