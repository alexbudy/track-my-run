from functools import wraps
import logging
from flask import Flask, jsonify, session, redirect, render_template, request, url_for
import os
from database import db
from flask_migrate import Migrate

# from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Credentials, Users
from utils.utils import (
    create_salt,
    create_session_tok,
    hash_password,
)
import redis

hostname = "db"  # or '127.0.0.1'
port = 5432
database = "db"
username = "postgres"
password = "postgres"

LOGIN_EXPIRY_S = 3600

app = Flask(__name__)
# Session(app)

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{username}:{password}@{hostname}:{port}/{database}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

redis_cache = redis.Redis(host="cache", port=6379)


def create_app():
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.secret_key = "bad key"

    db.init_app(app)

    Migrate(app, db)

    server_port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=server_port)


def get_token_and_user_id_from_cookies():
    token = request.cookies.get("accessToken", "")
    if not token or not redis_cache.exists(token):
        return None, None

    return token, int(redis_cache.get(token))


def redirect_if_logged_in(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("accessToken", "")

        if token and redis_cache.exists(token):
            return redirect(url_for("landing_page"))

        return func(*args, **kwargs)

    return decorated_function


def auth_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("accessToken", "")

        if not token:
            return "Please login to view", 400

        if not redis_cache.exists(token):
            return "Session expired, please login", 440

        if app.logger.level <= logging.INFO:
            user_id = int(redis_cache.get(token))
            ttl_s = redis_cache.ttl(token)

            app.logger.info(
                f"User {user_id} accessing protected page, {round(ttl_s / 60, 2)} minutes left in session"
            )

        return func(*args, **kwargs)

    return decorated_function


@app.route("/login")
@redirect_if_logged_in
def login_page():
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@auth_required
def logout():
    tok, user_id = get_token_and_user_id_from_cookies()
    app.logger.info(f"Logout called for user {user_id}")

    redis_cache.delete(tok)
    redis_cache.delete(f"user_id:{user_id}")
    app.logger.info(f"Tokens deleted")

    return jsonify({"logged_out": True}), 200


@app.route("/login", methods=["POST"])
def login():
    app.logger.info("Login method")

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

    app.logger.info(f"User {user_id} logged in")
    tok = create_session_tok()

    redis_cache.set(tok, user_id, ex=LOGIN_EXPIRY_S)
    redis_cache.set(f"user_id:{user_id}", tok, ex=LOGIN_EXPIRY_S)

    return jsonify({"access_token": tok}), 200


@app.route("/register", methods=["GET", "POST"])
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


@app.route("/landing_page")
@auth_required
def landing_page():
    # protected page
    return render_template("landing_page.html")


@app.route("/")
def home():
    app.logger.info(session)
    return render_template("index.html")


@app.route("/api/data")
@auth_required
def data():
    return "Super secret info"


@app.route("/redis-health-check")
def redis_health_check():
    return str(redis_cache.ping())


if __name__ == "__main__":
    create_app()
