from flask import Flask, render_template, request
import os
from database import db
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker
from models import Credentials
from utils.utils import create_salt, hash_password


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


def create_app():
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    db.init_app(app)

    Migrate(app, db)

    server_port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=server_port)


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    login = data.get("login", "")
    pw = data.get("pw", "")

    if not login:
        return "Missing login field", 400
    if not pw:
        return "Missing password field", 400

    salt = create_salt()
    hashed_pass = hash_password(pw, salt)

    session = Session()
    try:
        session.add(Credentials(login=login, hashed_pass=hashed_pass, salt=salt))
        session.commit()

        return hashed_pass
    except Exception as e:
        session.rollback()
        err = str(e)

        if "unique constraint" in err:
            return "Login already exists", 400
        else:
            return "Unknown error", 400

    finally:
        session.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/data")
def data():
    try:
        with engine.connect() as conn:
            stmt = text("select * from users;")
            x = conn.execute(stmt).fetchall()
        return str(x)
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    create_app()
