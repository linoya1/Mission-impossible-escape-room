import pytest

from backend.models import User
from backend.db import db


def start_game(client, username="agent", password="secret"):
    return client.post(
        "/start_game",
        data={"player_name": username, "password": password},
        follow_redirects=False,
    )


def test_start_game_missing_fields(client):
    response = client.post("/start_game", data={"player_name": "", "password": ""})
    assert response.status_code == 200
    assert b"Please enter a codename and passphrase." in response.data


def test_new_user_created_and_logged_in(client, app):
    response = start_game(client, username="neo", password="matrix")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/prelude")

    with app.app_context():
        user = User.query.filter_by(username="neo").first()
        assert user is not None
        assert user.check_password("matrix")


def test_existing_user_login_ok(client, app):
    with app.app_context():
        user = User(username="ethan")
        user.set_password("imf")
        db.session.add(user)
        db.session.commit()

    response = start_game(client, username="ethan", password="imf")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/prelude")


def test_wrong_password_rejected(client, app):
    with app.app_context():
        user = User(username="benji")
        user.set_password("correct")
        db.session.add(user)
        db.session.commit()

    response = start_game(client, username="benji", password="wrong")
    assert response.status_code == 200
    assert b"Invalid passphrase. Try again." in response.data
