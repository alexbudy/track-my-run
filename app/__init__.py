from flask import Flask
from flask_migrate import Migrate
from app.routes.auth_routes import auth_blueprint
from app.routes.nav_routes import nav_blueprint
from app.routes.run_routes import runs_blueprint
from app.database import db
from config import TestConfig, DevelopmentConfig, ProdConfig
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


app = Flask(__name__)

app.register_blueprint(auth_blueprint)
app.register_blueprint(nav_blueprint)
app.register_blueprint(runs_blueprint)


def create_app(config_key="dev"):
    if config_key == "test":
        config = TestConfig
    elif config_key == "prod":
        config = ProdConfig
    else:
        config = DevelopmentConfig

    app.config.from_object(config)

    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

    app.Session = sessionmaker(bind=engine)

    db.init_app(app)

    Migrate(app, db)

    return app
