import os
from typing import Optional
from flask import (
    Response,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    Blueprint,
    url_for,
)
from marshmallow import Schema, ValidationError, fields, post_load, pre_load, validate
from marshmallow.validate import Length

from app.auth import (
    auth_required,
    get_token_and_user_id_from_cookies,
    redirect_if_logged_in,
)
from app.models.models import Credentials, Users
from app.extensions import redis_cache
from app.routes import (
    create_and_store_access_token_in_cache,
    flatten_validation_errors,
)
from app.services.password_recovery_service import PasswordRecoveryService
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


def validate_email(value: Optional[str]):
    if value in (None, ""):
        return True
    try:
        validate.Email(error="Invalid email address")(value)
    except ValidationError:
        raise ValidationError("Invalid email address")


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
    email = fields.String(
        required=False,
        allow_none=True,
        validate=validate_email,
    )
    nick = fields.String(
        required=False,
        allow_none=True,
        validate=Length(min=3, max=20),
    )

    @pre_load
    def normalize_empty_string(self, data, **kwargs):
        print(data, "pre load", type(data))
        data = dict(data)
        if data["nick"] == "":
            data["nick"] = None
        return data


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
    return render_template("auth/login.html", latest_tag=os.getenv("LATEST_TAG"))


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

    res: Response = make_response(render_template("index.html"))
    res.set_cookie("accessToken", "", expires=0)
    return res


@auth_blueprint.route("/logout", methods=["GET"])
def logout_page():
    return redirect(url_for("auth_blueprint.render_login"))


@auth_blueprint.route("/password_recovery", methods=["POST"])
def password_recovery():
    login = request.form.get("login")

    current_app.logger.info(f"Password recovery called for {login}")

    cred = Credentials.find_cred_on_login(login)
    if cred and cred.user.email:
        current_app.logger.info(f"Sending recovery link to {cred.user.email}")
        PasswordRecoveryService.send_recovery_link(cred.user.email, login)
        return "ok"

    return "user email not found"


@auth_blueprint.route("/reset_password/<token>", methods=["GET"])
def reset_password(token: str):
    email = PasswordRecoveryService.verify_token(token)

    current_app.logger.info(f"Reset password called for {email}")

    if not email:
        return redirect(url_for("auth_blueprint.render_login"))

    login = Users.find_user_on_email(email).credentials.login

    return render_template("auth/reset_password.html", login=login, token=token)


@auth_blueprint.route("/reset_password", methods=["POST"])
def reset_password_post():
    login = request.form.get("login")
    token = request.form.get("token")

    if not PasswordRecoveryService.verify_token(token):
        # flash error message will come from verify_token call
        return redirect(url_for("auth_blueprint.render_login"))

    password = request.form.get("password")
    repeat_password = request.form.get("password_repeat")
    current_app.logger.info(f"Reset password called for {login}")

    # to reduce code dupe
    template_data = {
        "template_name_or_list": "auth/reset_password.html",
        "login": login,
        "token": token,
    }
    err: Optional[str] = None

    if password != repeat_password:
        err = "Passwords do not match, please try again"
    elif len(password) < MIN_PASS_LEN:
        err = f"Password must be at least {MIN_PASS_LEN} characters long, please try again"
    elif len(password) > MAX_PASS_LEN:
        err = (
            f"Password must be at most {MAX_PASS_LEN} characters long, please try again"
        )

    if err:
        flash(err, "error")
        return render_template(**template_data)

    try:
        Credentials.update_password(login, password)
    except ValueError:
        err = "New password cannot be the same as the old one, please try again"
    except Exception as e:
        current_app.logger.exception(
            f"Failed to reset password for {login} with error {str(e)}"
        )
        err = "An error occurred while resetting your password, please try again"

    if err:
        flash(err, "error")
        return render_template(**template_data)

    # add the token to redis so they cannot be used again
    redis_cache.setex(
        token, int(os.getenv("TOKEN_EXPIRATION_TIME_S")), "password_reset"
    )

    flash("Your password has been reset! Please login", "message")

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
    email = request.form.get("email")
    nick = request.form.get("nick")

    if errs:
        errors = flatten_validation_errors(errs)
        return render_template(
            "auth/register.html",
            errors=errors,
            login=login if "login" not in errors else "",
            nick=nick if "nick" not in errors else "",
            email=email if "email" not in errors else "",
            password=password if "password" not in errors else "",
            password_repeat=repeat_password if "password_repeat" not in errors else "",
        )

    if password != repeat_password:
        return render_template(
            "auth/register.html",
            errors={"password_repeat": "Passwords do not match, please try again"},
            login=login,
            nick=nick,
            email=email,
        )

    salt = create_salt()
    hashed_pass = hash_password(password, salt)

    with current_app.Session() as sess:
        try:
            creds = sess.query(Credentials).filter(Credentials.login == login).all()
            if creds:
                flash("Login already exists, please try again")
                return render_template("auth/register.html", nick=nick)

            user = Users(nick=nick, email=email, is_admin=0, is_readonly=0)

            if email and Users.find_user_on_email(email):
                flash("Email already exists, please try again")
                return render_template(
                    "auth/register.html",
                    nick=nick,
                    login=login,
                    password=password,
                    password_repeat=repeat_password,
                )

            sess.add(user)
            sess.flush()

            sess.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            sess.commit()

            flash("Registration successful!")
            return redirect(url_for("runs_blueprint.get_runs"), code=303)

        except Exception as e:
            sess.rollback()

            current_app.logger.error("Unknown error when registering: " + str(e))
            flash("Unknown error, please try again")
            return render_template("auth/register.html")
