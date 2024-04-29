from flask.testing import FlaskClient
from tests import client


def test_login_route(client: FlaskClient):
    resp = client.get("/login")
    html = resp.data.decode()

    assert resp.status_code == 200
    assert '<a href="/login">Login</a>' in html
    assert '<a href="/register">Register</a>' in html

    assert '<label for="login">Login:</label>' in html
    assert '<label for="password">Password:</label>' in html
