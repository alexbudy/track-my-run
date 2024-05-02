from flask.testing import FlaskClient

from tests import client, app


def test_login_route(client: FlaskClient):
    resp = client.get("/login")
    html = resp.data.decode()

    assert resp.status_code == 200
    assert '<a href="/login">Login</a>' in html
    assert '<a href="/register">Register</a>' in html

    assert '<label for="login">Login:</label>' in html
    assert '<label for="password">Password:</label>' in html


def test_login_post_invalid_params(client: FlaskClient):
    resp = client.post("/login", json={"login": "ab", "password": "ab"})
    errors = resp.json["error"]

    assert resp.status_code == 400
    assert errors == [
        "Login length must be between 3 and 20.",
        "Password length must be between 7 and 20.",
    ]


def test_login_post(client: FlaskClient):
    resp = client.post("/login", json={"login": "some_user", "password": "some_pass"})
    print(resp)

    assert resp.status_code == 200
