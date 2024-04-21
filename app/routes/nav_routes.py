from flask import Blueprint, current_app, render_template
from app.cache import redis_cache

from app.auth import auth_required


nav_blueprint = Blueprint("nav_blueprint", __name__)


@nav_blueprint.route("/landing_page")
@auth_required
def landing_page():
    # protected page
    return render_template("landing_page.html")


@nav_blueprint.route("/")
def home():
    current_app.logger.info("NAME " + __name__)
    return render_template("index.html")


@nav_blueprint.route("/api/data")
@auth_required
def data():
    return "Super secret info"


@nav_blueprint.route("/redis-health-check")
def redis_health_check():
    try:
        ping = redis_cache.ping()
        return "Redis ping returned with value: " + str(ping), 200
    except Exception as e:
        current_app.logger.info("Redis ping failed with " + str(e))
        return "Redis failed to ping", 200
