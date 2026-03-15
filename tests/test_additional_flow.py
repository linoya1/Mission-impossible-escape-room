from contextlib import contextmanager

from flask import template_rendered


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def _start_game(client, username="agent", password="secret"):
    return client.post(
        "/start_game",
        data={"player_name": username, "password": password},
        follow_redirects=False,
    )


def _complete_all_rooms(client):
    for room_id in [1, 2, 3, 4]:
        client.post(f"/room/{room_id}/success", follow_redirects=False)


def test_final_room_success_redirects_to_summary(client):
    _start_game(client, username="finisher", password="pw")

    response = client.post("/room/4/success", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/me")


def test_summary_finished_state_after_all_rooms(client, app):
    _start_game(client, username="summary", password="pw")
    _complete_all_rooms(client)

    with captured_templates(app) as templates:
        response = client.get("/me")
        assert response.status_code == 200

    assert templates, "Expected summary template to render."
    _, context = templates[-1]
    assert context.get("finished") is True


def test_room3_access_is_not_redirected(client):
    _start_game(client, username="skip_check", password="pw")

    response = client.get("/room/3", follow_redirects=False)
    assert response.status_code == 200
