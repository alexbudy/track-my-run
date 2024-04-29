from flask import Flask
from flask_migrate import Migrate
from app.routes.auth_routes import auth_blueprint
from app.routes.nav_routes import nav_blueprint
from app.session import SQLALCHEMY_DATABASE_URI
from app.database import db


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(nav_blueprint)

    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.secret_key = "bad key"  # TODO replace

    db.init_app(app)

    Migrate(app, db)

    return app
