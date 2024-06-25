from unittest import mock
from unittest.mock import patch

from flask.testing import FlaskClient

from app.models.models import Credentials, Users
from app.routes import LOGIN_EXPIRY_S
from app.utils.utils import create_salt, hash_password
from tests import app, client, db_session


def test_login_route(client: FlaskClient):
    resp = client.get("/login")
    html = resp.data.decode()

    assert resp.status_code == 200
    assert '<a hx-get="/login"' in html
    assert '<a hx-get="/register"' in html

    assert '<input type="text" id="login"' in html
    assert '<input type="password"' in html


def test_login_post_invalid_params(client: FlaskClient):
    resp = client.post("/login", data={"login": "ab", "password": "ab"})
    html = resp.data.decode()

    assert resp.status_code == 200
    assert '<span class="error">Length must be between 3 and 20.</span>' in html
    assert '<span class="error">Length must be between 7 and 20.</span>' in html


@patch("app.routes.redis_cache")
@patch("app.routes.create_session_tok")
def test_login_post(create_session_tok, redis_cache, client: FlaskClient, db_session):
    dummy_tok: str = "some_session_token"

    redis_cache.set.return_value = True
    create_session_tok.return_value = dummy_tok

    new_user = Users(nick="Alex")
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

    resp = client.post("/login", data={"login": "some_user", "password": "some_pass"})

    # assert that redis stores the created token
    assert redis_cache.set.call_count == 1
    expected_calls = [mock.call(dummy_tok, new_user.id, ex=LOGIN_EXPIRY_S)]
    redis_cache.set.assert_has_calls(expected_calls)

    assert redis_cache.rpush.call_count == 1
    expected_calls = [mock.call(f"user_id:{new_user.id}", dummy_tok)]
    redis_cache.rpush.assert_has_calls(expected_calls)

    assert (
        'You should be redirected automatically to the target URL: <a href="/my_runs">/my_runs</a>'
        in resp.data.decode()
    )
    assert (
        resp.headers.get("Location") == "/my_runs"
    )  # ensure redirection will go to new path
    assert (
        resp.headers.get("Set-Cookie") == f"accessToken={dummy_tok}; Path=/"
    )  # ensure token is set
    assert resp.status_code == 303
