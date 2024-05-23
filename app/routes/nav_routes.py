import os
from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from func_timeout import FunctionTimedOut, func_timeout
from sqlalchemy import text
from app.auth import admin_required, is_logged_in
from app.cache import redis_cache


nav_blueprint = Blueprint("nav_blueprint", __name__)


@nav_blueprint.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@nav_blueprint.route("/")
def home():
    if is_logged_in():
        return redirect(url_for("runs_blueprint.get_runs"))
    return render_template("login.html")


@nav_blueprint.route("/redis-health-check")
@admin_required
def redis_health_check():
    timeout: int = 5  # s
    try:
        ping = func_timeout(timeout, redis_cache.ping)
        return f"Redis ping returned with value: {str(ping)}", 200
    except FunctionTimedOut as fto:
        current_app.logger.error("Redis ping timed out " + str(fto))
        return f"Redis ping timed out after {timeout} seconds", 500
    except Exception as e:
        current_app.logger.error("Redis ping failed with " + str(e))
        return "Redis failed to ping", 500


@nav_blueprint.route("/rds-health-check")
@admin_required
def rds_health_check():
    try:
        with current_app.Session() as sess:
            res = sess.execute(text("SELECT 1"))
            if res.scalar() == 1:
                return "DB connection is healthy!", 200
            else:
                return "Query executed but incorrect result - should not happen", 500
    except Exception as e:
        current_app.logger.error("DB health check failed with " + str(e))
        return "DB connection failed with " + str(e), 500


@nav_blueprint.route("/log-check")
@admin_required
def log_check():
    current_app.logger.debug("this is a DEBUG message")
    current_app.logger.info("this is an INFO message")
    current_app.logger.warning("this is a WARNING message")
    current_app.logger.error("this is an ERROR message")
    current_app.logger.critical("this is a CRITICAL message")
    return "Logs written to logger", 200
