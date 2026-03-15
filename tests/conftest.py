import importlib
import pytest


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    db_uri = f"sqlite:///{db_file.as_posix()}"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("DATABASE_URL", db_uri)
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    import backend.server as server
    importlib.reload(server)

    app = server.app
    app.config.update(TESTING=True)

    from backend.db import db
    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

    monkeypatch.undo()


@pytest.fixture(autouse=True)
def clean_db(app):
    from backend.db import db
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()
    yield


@pytest.fixture()
def client(app):
    return app.test_client()
