import os
from flask import Flask
from app.routes.auth_routes import auth_blueprint
from app.routes.nav_routes import nav_blueprint
from app.routes.run_routes import runs_blueprint
from app.extensions import db, mail
from config import TestConfig, DevelopmentConfig, ProdConfig
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


app = Flask(__name__)

app.register_blueprint(auth_blueprint)
app.register_blueprint(nav_blueprint)
app.register_blueprint(runs_blueprint)


def create_app(config_key="dev"):
    # probably better way to do this
    if "sqlalchemy" in app.extensions:
        print("SQLAlchemy already initialized")
        return app

    if config_key == "test":
        config = TestConfig
    elif config_key == "prod":
        config = ProdConfig
    else:
        config = DevelopmentConfig

    app.config.from_object(config)

    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

    app.config["MAIL_SERVER"] = "live.smtp.mailtrap.io"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USERNAME"] = "api"
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False

    app.Session = sessionmaker(bind=engine)

    db.init_app(app)
    mail.init_app(app)

    return app
