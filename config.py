import os

username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

prod_username = os.getenv("DB_USERNAME_PROD")
prod_password = os.getenv("DB_PASSWORD_PROD")

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
    SQLALCHEMY_DATABASE_URI = f"postgresql://{prod_username}:{prod_password}@{hostname['prod']}:{port['prod']}/{database}"
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['test']}:{port['test']}/{database}"
