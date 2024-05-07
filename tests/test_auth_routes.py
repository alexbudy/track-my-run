from unittest import mock
from unittest.mock import patch
from flask.testing import FlaskClient

from app.models.models import Credentials, Users
from app.routes.auth_routes import LOGIN_EXPIRY_S
from app.utils.utils import create_salt, hash_password
from tests import client, app, db_session


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


@patch("app.routes.auth_routes.redis_cache")
@patch("app.routes.auth_routes.create_session_tok")
def test_login_post(create_session_tok, redis_cache, client: FlaskClient, db_session):
    dummy_tok: str = "some_session_token"

    redis_cache.set.return_value = True
    create_session_tok.return_value = dummy_tok

    new_user = Users(firstname="Alex", lastname="Budi", email="a@gmail.com")
    db_session.add(new_user)
    db_session.commit()

    salt = create_salt()
    hashed_pass = hash_password("some_pass", salt)
    db_session.add(
        Credentials(
            login="some_user",
            hashed_pass=hashed_pass,
            salt=salt,
            user_id=new_user.id,
        )
    )
    db_session.commit()

    resp = client.post("/login", json={"login": "some_user", "password": "some_pass"})

    # assert that redis stores the created token
    assert redis_cache.set.call_count == 2
    expected_calls = [
        mock.call(dummy_tok, new_user.id, ex=LOGIN_EXPIRY_S),
        mock.call(f"user_id:{new_user.id}", dummy_tok, ex=LOGIN_EXPIRY_S),
    ]
    redis_cache.set.assert_has_calls(expected_calls)

    assert resp.json == {"access_token": dummy_tok}
    assert resp.status_code == 200
