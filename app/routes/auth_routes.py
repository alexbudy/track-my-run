import os
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
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Length

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
    redirect_if_logged_in,
)
from app.models.models import Credentials, Users
from app.cache import redis_cache
from app.routes import (
    DEFAULT_ORDERING,
    create_and_store_access_token_in_cache,
    flatten_validation_errors,
)
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

    @post_load
    def cleanup(self, data, **kwargs):
        data["login"] = data.get("login").lower().strip()

        return data


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
    flash_msg = []

    user_agent = request.user_agent.string
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        flash_msg.append(
            "Please note that for the best experience, a desktop browser is preferred."
        )

    if os.getenv("SHOW_READONLY_MSG") == "true":
        msg: str = (
            "If you would like to see a readonly version with demo data without creating an "
            f"account, please use login: <i>readonly</i>, password: <i>{os.getenv('R_O_PASS')}</i> as credentials"
        )

        flash_msg.append(msg)

    if flash_msg:
        flash("\n".join(flash_msg))

    return render_template("auth/login.html")


login_user_schema = LoginUserSchema()
register_user_schema = RegisterUserSchema()


@auth_blueprint.route("/login", methods=["POST"])
@redirect_if_logged_in
def login():
    current_app.logger.info("Login method")
    errs = login_user_schema.validate(request.form)

    if errs:
        return render_template(
            "auth/login.html",
            logged_in=False,
            errors=flatten_validation_errors(errs),
            login=request.form.get("login") if "login" not in errs else "",
        )

    login_fields: LoginUserSchema = login_user_schema.load(request.form)

    cred = Credentials.find_cred_on_login(login_fields["login"])

    if not cred:
        flash("Login not found, please register and try again")
        return render_template(
            "auth/login.html",
        )

    hashed_pass = hash_password(login_fields["password"], cred.salt)
    if hashed_pass != cred.hashed_pass:
        flash("Invalid password, please try again")
        return render_template("auth/login.html", login=login_fields["login"])

    user_id = cred.user_id

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

    flash("You have succesfully logged out 🎉", "message")
    return render_template("index.html")


@auth_blueprint.route("/logout", methods=["GET"])
def logout_page():
    return redirect(url_for("auth_blueprint.render_login"))


# TODO - be logged out to register
@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")

    errs = register_user_schema.validate(request.form)

    login = request.form.get("login")
    password = request.form.get("password")
    repeat_password = request.form.get("password_repeat")
    nick = request.form.get("nick")

    if errs:
        errors = flatten_validation_errors(errs)
        return render_template(
            "auth/register.html",
            errors=errors,
            login=login if "login" not in errors else "",
            nick=nick if "nick" not in errors else "",
        )

    if password != repeat_password:
        return render_template(
            "auth/register.html",
            errors={"password_repeat": "Passwords do not match, please try again"},
            login=login,
            nick=nick,
        )

    salt = create_salt()
    hashed_pass = hash_password(password, salt)

    with current_app.Session() as sess:
        try:
            creds = sess.query(Credentials).filter(Credentials.login == login).all()
            if creds:
                flash("Login already exists, please try again")
                return render_template("auth/register.html", nick=nick)

            user = Users(nick=nick)

            sess.add(user)
            sess.flush()

            sess.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            sess.commit()

            return redirect(url_for("runs_blueprint.get_runs"), code=303)

        except Exception as e:
            sess.rollback()

            current_app.logger.error("Unknown error when registering: " + str(e))
            flash("Unknown error, please try again")
            return render_template("auth/register.html")
