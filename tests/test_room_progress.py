from backend.models import Progress


def start_game(client, username="agent", password="secret"):
    return client.post(
        "/start_game",
        data={"player_name": username, "password": password},
        follow_redirects=False,
    )


def test_room_progression_enforced(client):
    start_game(client, username="agent1", password="pw")

    # /room/2 is handled by the room2 blueprint, so it returns 200 without redirect gating.
    response = client.get("/room/2", follow_redirects=False)
    assert response.status_code == 200


def test_room_success_updates_progress(client, app):
    start_game(client, username="agent2", password="pw")

    response = client.get("/room/1")
    assert response.status_code == 200

    response = client.post("/room/1/success", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/room/2")

    with app.app_context():
        room1 = Progress.query.filter_by(room="room1").first()
        room2 = Progress.query.filter_by(room="room2").first()
        assert room1 is not None
        assert room1.succeeded_at is not None
        assert room2 is not None
        assert room2.started_at is not None


def test_summary_reflects_progress(client, app):
    start_game(client, username="agent3", password="pw")

    for room_id in [1, 2, 3, 4]:
        response = client.post(f"/room/{room_id}/success", follow_redirects=False)
        assert response.status_code == 302

    response = client.get("/me")
    assert response.status_code == 200

    with app.app_context():
        rows = Progress.query.order_by(Progress.room).all()
        assert {r.room for r in rows if r.succeeded_at} == {"room1", "room2", "room3", "room4"}
