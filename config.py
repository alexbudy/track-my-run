import os

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

hostname = {
    "dev": os.getenv("DEV_HOSTNAME"),
    "prod": os.getenv("PROD_HOSTNAME"),
    "stage": os.getenv("STAGE_HOSTNAME"),
    "test": os.getenv("TEST_HOSTNAME"),
}
database = os.getenv("DB_NAME")  # as defined in docker compose
port = {
    "dev": os.getenv("DEV_PORT"),
    "prod": os.getenv("PROD_PORT"),
    "stage": os.getenv("STAGE_PORT"),
    "test": os.getenv("TEST_PORT"),
}


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{username}:{password}@{hostname['dev']}:{port['dev']}/{database}"
    )
    DEBUG = True


class ProdConfig(Config):
    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['prod']}:{port['prod']}/{database}"
    DEBUG = False
    ENV = "prod"


class StageConfig(Config):
    ENV = "stage"
    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['stage']}:{port['stage']}/{database}"


class DevelopmentConfig(Config):
    ENV = "dev"


class TestConfig(Config):
    TESTING = True
    ENV = "test"

    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['test']}:{port['test']}/{database}"
