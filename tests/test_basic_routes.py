def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_prelude_page_loads(client):
    response = client.get("/prelude")
    assert response.status_code == 200


def test_me_redirects_when_not_logged_in(client):
    response = client.get("/me", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_invalid_room_redirects_home(client):
    response = client.get("/room/99", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_invalid_room_success_redirects_home(client):
    response = client.post("/room/99/success", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def _start_game(client, username="agent", password="secret"):
    return client.post(
        "/start_game",
        data={"player_name": username, "password": password},
        follow_redirects=False,
    )


def test_me_loads_when_logged_in_no_progress(client):
    _start_game(client, username="no_progress", password="pw")

    response = client.get("/me")
    assert response.status_code == 200


def test_room_success_redirects_when_not_logged_in(client):
    response = client.post("/room/1/success", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
