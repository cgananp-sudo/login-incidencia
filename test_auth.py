import pytest
import app as auth_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_app, "DB", str(tmp_path / "test.db"))
    auth_app.failed_attempts = 0
    auth_app.init_db()
    return auth_app.app.test_client()


def test_login_correcto(client):
    r = client.post("/login", json={"username": "jgarcia", "password": "Clave123"})
    assert r.status_code == 200


def test_clave_incorrecta(client):
    r = client.post("/login", json={"username": "jgarcia", "password": "mala"})
    assert r.status_code == 401


def test_falla_de_bd_devuelve_503(client, monkeypatch):
    def falla(_):
        raise TimeoutError("DB timeout")
    monkeypatch.setattr(auth_app, "find_user", falla)
    r = client.post("/login", json={"username": "jgarcia", "password": "Clave123"})
    assert r.status_code == 503