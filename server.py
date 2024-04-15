from flask import Flask, render_template
import os
from database import db
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.sql import text


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


def create_app():
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

    db.init_app(app)

    migrate = Migrate(app, db)

    server_port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=server_port)

    return app


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

    # return "some data2"


if __name__ == "__main__":
    create_app()
