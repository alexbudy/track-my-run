import os

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

hostname = {
    "dev": os.getenv("DEV_HOSTNAME"),
    "test": os.getenv("TEST_HOSTNAME"),
    "prod": os.getenv("PROD_HOSTNAME"),
}
database = os.getenv("DB_NAME")  # as defined in docker compose
port = {
    "dev": os.getenv("DEV_PORT"),
    "test": os.getenv("TEST_PORT"),
    "prod": os.getenv("PROD_PORT"),
}


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{username}:{password}@{hostname['dev']}:{port['dev']}/{database}"
    )


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['prod']}:{port['prod']}/{database}"
    DEBUG = False
    ENV = "prod"


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "dev"


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    ENV = "test"

    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['test']}:{port['test']}/{database}"
