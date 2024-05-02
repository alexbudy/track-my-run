from typing import Dict, List
from flask import current_app, jsonify, render_template, request, Blueprint
from marshmallow import Schema, fields
from marshmallow.validate import Length

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
    redirect_if_logged_in,
)
from app.models.models import Credentials, Users
from app.cache import redis_cache
from app.utils.utils import create_salt, create_session_tok, hash_password

auth_blueprint = Blueprint("auth_blueprint", __name__)


LOGIN_EXPIRY_S = 3600  # session expiry

MIN_LOGIN_LEN = 3
MAX_LOGIN_LEN = 20
MIN_PASS_LEN = 7
MAX_PASS_LEN = 20


class LoginUserSchema(Schema):
    login = fields.String(
        required=True,
        validate=Length(min=MIN_LOGIN_LEN, max=MAX_LOGIN_LEN),
    )
    password = fields.String(
        required=True,
        validate=Length(min=MIN_PASS_LEN, max=MAX_PASS_LEN),
    )


class RegisterUserSchema(Schema):
    login = fields.String(
        required=True,
        validate=Length(min=MIN_LOGIN_LEN, max=MAX_LOGIN_LEN),
    )
    password = fields.String(
        required=True,
        validate=Length(min=MIN_PASS_LEN, max=MAX_PASS_LEN),
    )
    password_repeat = fields.String(
        required=True,
        validate=Length(min=MIN_PASS_LEN, max=MAX_PASS_LEN),
    )
    firstname = fields.String(
        required=True,
        validate=Length(min=3, max=20),
    )
    lastname = fields.String(
        required=True,
        validate=Length(max=30),
    )
    email = fields.Email(required=True)


@auth_blueprint.route("/login", methods=["GET"])
@redirect_if_logged_in
def render_login():
    return render_template("login.html")


login_user_schema = LoginUserSchema()
register_user_schema = RegisterUserSchema()


def abort(err: Dict[str, List[str]] | str, err_code=400):
    """Handle errors from marshmallow as well as regular strings"""
    if type(err) == dict:
        err_msg = [key.capitalize() + " " + val[0].lower() for key, val in err.items()]
    else:
        err_msg = [err]
    current_app.logger.info(err_msg)
    return jsonify({"error": err_msg}), err_code  # TODO key should be 'error'?


@auth_blueprint.route("/login", methods=["POST"])
@redirect_if_logged_in
def login():
    current_app.logger.info("Login method")
    errs = login_user_schema.validate(request.json)

    if errs:
        return abort(errs)

    login = request.json.get("login")
    password = request.json.get("password")

    with current_app.Session() as sess:
        creds = sess.query(Credentials).filter(Credentials.login == login).all()

        if len(creds) == 0:
            return abort("Login not found, please register or try again")
        hashed_pass = hash_password(password, creds[0].salt)
        if hashed_pass != creds[0].hashed_pass:
            return abort("Invalid password, please try again")

    user_id = creds[0].user_id

    current_app.logger.info(f"User {user_id} logged in")
    tok = create_session_tok()

    redis_cache.set(tok, user_id, ex=LOGIN_EXPIRY_S)
    redis_cache.set(f"user_id:{user_id}", tok, ex=LOGIN_EXPIRY_S)

    return jsonify({"access_token": tok}), 200


@auth_blueprint.route("/logout", methods=["POST"])
@auth_required
def logout():
    tok, user_id = get_token_and_user_id_from_cookies()
    current_app.logger.info(f"Logout called for user {user_id}")

    redis_cache.delete(tok)
    redis_cache.delete(f"user_id:{user_id}")

    return jsonify({"logged_out": True}), 200


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    data = request.json

    errs = register_user_schema.validate(data)

    if errs:
        current_app.logger.info(errs)
        return abort(errs)

    if data.get("password") != data.get("password_repeat"):
        return abort("Passwords do not match, please try again")

    login = data.get("login")
    password = data.get("password")
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    email = data.get("email")

    salt = create_salt()
    hashed_pass = hash_password(password, salt)

    with current_app.Session() as sess:
        try:
            creds = sess.query(Credentials).filter(Credentials.login == login).all()
            if creds:
                raise Exception("unique constraint failed for login")

            user = Users(firstname=firstname, lastname=lastname, email=email)
            sess.add(user)
            sess.flush()

            sess.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            sess.commit()
            return jsonify({"success": True}), 200
        except Exception as e:
            sess.rollback()
            err = str(e)
            current_app.logger.error(err)

            if "unique constraint" in err:  # TODO better err checking
                if "users_email_key" in err:
                    return abort("Provided email has already been registered")
                elif "login" in err:
                    return abort("Login already exists, please pick a different one")
                else:
                    current_app.logger.error(
                        "Unknown unique constraint error when registering: " + err
                    )
                    return abort("Unknown error")
            else:
                current_app.logger.error("Unknown error when registering: " + err)
                return abort("Unknown error")
