from flask import Flask, make_response, redirect, render_template, request
import os
from database import db
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
from models import Credentials, Users
from utils.utils import create_salt, hash_password, create_uuid
import redis

hostname = "db"  # or '127.0.0.1'
port = 5432
database = "db"
username = "postgres"
password = "postgres"

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{username}:{password}@{hostname}:{port}/{database}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

redis_cache = redis.Redis(host="cache", port=6379)


def create_app():
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    db.init_app(app)

    Migrate(app, db)

    server_port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=server_port)


@app.route("/login", methods=["POST"])
def login():
    app.logger.info("Login method")
    app.logger.info(request)

    data = request.form
    login = data.get("login", "")
    pw = data.get("pw", "")

    if not login:
        return "Missing login field", 400
    if not pw:
        return "Missing password field", 400

    with Session() as session:
        creds = session.query(Credentials).filter(Credentials.login == login).all()
        if len(creds) == 0:
            return "Login not found", 400
        hashed_pass = hash_password(pw, creds[0].salt)
        if hashed_pass != creds[0].hashed_pass:
            return "Invalid password, please try again", 400

        resp = make_response("Logged in")
        resp.headers["auth"] = create_uuid()
        return resp


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

    session = Session()
    with Session() as session:
        try:
            user = Users(firstname=firstname, lastname=lastname, email=email)
            session.add(user)
            session.flush()

            session.add(
                Credentials(
                    login=login, hashed_pass=hashed_pass, salt=salt, user_id=user.id
                )
            )
            return redirect("/")
        except Exception as e:
            session.rollback()
            err = str(e)

            if "unique constraint" in err:
                return "Login already exists", 400
            else:
                return "Unknown error", 400


@app.route("/login")
def login_page():
    return render_template("login.html")


# @app.route("/register")
# def register_page():
#     app.logger.info(request.method)
#     return render_template("register.html")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def data():
    try:
        with engine.connect() as conn:
            stmt = text("select * from credentials;")
            x = conn.execute(stmt).fetchall()
        return str(x)
    except Exception as e:
        return str(e)


@app.route("/redis-health-check")
def redis_health_check():
    return str(redis_cache.ping())


if __name__ == "__main__":
    create_app()
