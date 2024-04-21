from flask import current_app, jsonify, redirect, render_template, request, Blueprint
from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
    redirect_if_logged_in,
)
from app.session import Session
from app.models.models import Credentials, Users
from app.cache import redis_cache
from app.utils.utils import create_salt, create_session_tok, hash_password


auth_blueprint = Blueprint("auth_blueprint", __name__)


LOGIN_EXPIRY_S = 3600


@auth_blueprint.route("/login", methods=["GET", "POST"])
@redirect_if_logged_in
def login():
    if request.method == "GET":
        return render_template("login.html")

    current_app.logger.info("Login method")

    data = request.json
    login = data.get("login", "")
    pw = data.get("pw", "")
    if not login:
        return "Missing login field", 400
    if not pw:
        return "Missing password field", 400

    with Session() as sess:
        creds = sess.query(Credentials).filter(Credentials.login == login).all()
        if len(creds) == 0:
            return "Login not found", 400
        hashed_pass = hash_password(pw, creds[0].salt)
        if hashed_pass != creds[0].hashed_pass:
            return "Invalid password, please try again", 400

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

    data = request.form
    login = data.get("login", "")
    pw = data.get("pw", "")
    pw2 = data.get("pw2", "")
    firstname = data.get("name", "")
    lastname = data.get("last", "")
    email = data.get("email", "")

    if not login:
        return "Missing login field", 400
    if not pw:
        return "Missing password field", 400
    if pw != pw2:
        return "Mismatched passwords", 400
    if not firstname or not email:
        return "Missing first name/email fields", 400

    salt = create_salt()
    hashed_pass = hash_password(pw, salt)

    with Session() as sess:
        try:
            user = Users(firstname=firstname, lastname=lastname, email=email)
            sess.add(user)
            sess.flush()

            sess.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            sess.commit()
            return redirect("/")
        except Exception as e:
            sess.rollback()
            err = str(e)

            if "unique constraint" in err:
                return "Login already exists", 400
            else:
                return "Unknown error", 400
