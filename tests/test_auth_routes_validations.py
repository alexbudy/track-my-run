from app.routes.auth_routes import (
    MAX_LOGIN_LEN,
    MAX_PASS_LEN,
    MIN_LOGIN_LEN,
    MIN_PASS_LEN,
    RegisterUserSchema,
)


schema = RegisterUserSchema()


def test_register_user_schema():

    data = {
        "login": "some_login",
        "password": "some_pass",
        "password_repeat": "some_pass",
        "nick": "some_nick",
    }
    assert schema.validate(data) == {}
    data["nick"] = ""
    assert schema.validate(data) == {}


def test_register_user_schema_errors():
    data = {
        "login": "l1",
        "password": "p1",
        "password_repeat": "p1",
        "nick": "n1",
    }
    assert schema.validate(data) == {
        "login": [f"Length must be between {MIN_LOGIN_LEN} and {MAX_LOGIN_LEN}."],
        "password": [f"Length must be between {MIN_PASS_LEN} and {MAX_PASS_LEN}."],
        "password_repeat": [
            f"Length must be between {MIN_PASS_LEN} and {MAX_PASS_LEN}."
        ],
        "nick": ["Length must be between 3 and 20."],
    }
