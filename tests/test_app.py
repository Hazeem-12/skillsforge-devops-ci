import pytest

from app.main import add, create_app


@pytest.fixture()
def client():
    return create_app().test_client()


def test_add_function():
    assert add(2, 3) == 5


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_add_endpoint(client):
    r = client.get("/add?a=1.5&b=2")
    assert r.status_code == 200
    assert r.get_json()["result"] == 3.5


def test_add_missing_params(client):
    assert client.get("/add?a=1").status_code == 400


def test_add_bad_input(client):
    assert client.get("/add?a=x&b=2").status_code == 400


def test_greet(client):
    assert client.get("/greet/Hazeem").get_json()["message"] == "Hello, Hazeem!"


def test_unknown_route_404(client):
    assert client.get("/nope").status_code == 404
