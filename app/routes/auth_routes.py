from flask import (
    Response,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    Blueprint,
    session,
    url_for,
)
from marshmallow import Schema, fields
from marshmallow.validate import Length

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
    redirect_if_logged_in,
)
from app.models.models import Credentials, Users
from app.cache import redis_cache
from app.routes import create_and_store_access_token_in_cache, flatten_validation_errors
from app.utils.utils import create_salt, hash_password

auth_blueprint = Blueprint("auth_blueprint", __name__)


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
    nick = fields.String(
        required=False,
        validate=Length(min=3, max=20),
    )


@auth_blueprint.route("/login", methods=["GET"])
@redirect_if_logged_in
def render_login():
    return render_template("login.html")


login_user_schema = LoginUserSchema()
register_user_schema = RegisterUserSchema()


@auth_blueprint.route("/login", methods=["POST"])
@redirect_if_logged_in
def login():
    current_app.logger.info("Login method")
    errs = login_user_schema.validate(request.form)

    if errs:
        return render_template(
            "login.html", logged_in=False, errors=flatten_validation_errors(errs)
        )

    login_fields: LoginUserSchema = login_user_schema.load(request.form)

    with current_app.Session() as sess:
        creds = (
            sess.query(Credentials)
            .filter(Credentials.login == login_fields["login"])
            .all()
        )

        if len(creds) == 0:
            flash("Login not found, please register and try again")
            return render_template(
                "login.html",
            )

        cred: Credentials = creds[0]
        hashed_pass = hash_password(login_fields["password"], cred.salt)
        if hashed_pass != cred.hashed_pass:
            flash("Invalid password, please try again")
            return render_template("login.html")

        user_id = cred.user_id
        user: Users = sess.query(Users).filter(Users.id == user_id).all()[0]

    flash(f"Welcome, {user.nick or cred.login}. Ready to track a run?", "message")
    accessToken: str = create_and_store_access_token_in_cache(user_id)

    res: Response = make_response(
        redirect(url_for("runs_blueprint.get_runs"), code=303)
    )
    res.set_cookie("accessToken", accessToken)

    return res


@auth_blueprint.route("/logout", methods=["POST"])
@auth_required
def logout():
    tok, user_id = get_token_and_user_id_from_cookies()
    current_app.logger.info(f"Logout called for user {user_id}")

    redis_cache.delete(tok)
    redis_cache.delete(f"user_id:{user_id}")

    flash("You have succesfully logged out :)", "message")
    return render_template("index.html")


# TODO - be logged out to register
@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    errs = register_user_schema.validate(request.form)

    if errs:
        return render_template("register.html", errors=flatten_validation_errors(errs))

    data = register_user_schema.load(request.form)

    if data.get("password") != data.get("password_repeat"):
        return render_template(
            "register.html",
            errors={"password_repeat": "Passwords do not match, please try again"},
        )

    login = data.get("login")
    password = data.get("password")
    nick = data.get("nick")

    salt = create_salt()
    hashed_pass = hash_password(password, salt)

    with current_app.Session() as sess:
        try:
            creds = sess.query(Credentials).filter(Credentials.login == login).all()
            if creds:
                flash("Login already exists, please try again")
                return render_template("register.html")

            user = Users(nick=nick)

            sess.add(user)
            sess.flush()

            sess.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            sess.commit()
            return render_template("index.html", logged_in=True)

        except Exception as e:
            sess.rollback()

            current_app.logger.error("Unknown error when registering: " + str(e))
            flash("Unknown error, please try again")
            return render_template("register.html")
