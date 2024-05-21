from enum import Enum
from functools import wraps
import logging
from flask import flash, redirect, render_template, request, url_for, current_app
from app.cache import redis_cache
from app.models.models import Users

# TODO - could use cleanup


class LoggedInStatusEnum(Enum):
    LOGGED_IN = 1
    LOGGED_OUT = 2
    EXPIRED = 3


def logged_in_status() -> LoggedInStatusEnum:
    token = request.cookies.get("accessToken")
    if not token:
        return LoggedInStatusEnum.LOGGED_OUT
    if not redis_cache.get(token):
        return LoggedInStatusEnum.EXPIRED
    return LoggedInStatusEnum.LOGGED_IN


def is_logged_in() -> bool:
    return logged_in_status() == LoggedInStatusEnum.LOGGED_IN


def get_token_and_user_id_from_cookies() -> tuple[str, int]:
    token = request.cookies.get("accessToken", "")
    if not token or not redis_cache.exists(token):
        return None, None

    return token, int(redis_cache.get(token))


def redirect_if_logged_in(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("accessToken", "")
        current_app.logger.info("redirect if logged in for token " + token)
        if token and redis_cache.exists(token):
            current_app.logger.info("Token exists in cache ")

            return redirect(url_for("nav_blueprint.home"))

        return func(*args, **kwargs)

    return decorated_function


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        _, user_id = get_token_and_user_id_from_cookies()

        with current_app.Session() as sess:
            user = sess.query(Users).filter(Users.id == user_id).all()

            if not user or not user[0].is_admin == 1:
                return "Not admin", 400

        return func(*args, **kwargs)

    return decorated_function


def auth_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        logged_in_status_enum: LoggedInStatusEnum = logged_in_status()

        if logged_in_status_enum == LoggedInStatusEnum.LOGGED_OUT:
            flash("Please login to view")
            return render_template("index.html")

        if logged_in_status_enum == LoggedInStatusEnum.EXPIRED:
            flash("Session expired or token invalid, please login")
            return render_template("index.html")

        if current_app.logger.level <= logging.INFO:
            token = request.cookies.get("accessToken")
            user_id = int(redis_cache.get(token))
            ttl_s = redis_cache.ttl(token)

            current_app.logger.info(
                f"User {user_id} accessing protected page, {round(ttl_s / 60, 2)} minutes left in session"
            )

        return func(*args, **kwargs)

    return decorated_function


# TODO create admin_required wrapper
