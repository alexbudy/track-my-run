username = "postgres"
password = "postgres"

hostname = {"dev": "db", "test": "localhost"}
database = {"dev": "db", "test": "db"}  # as defined in docker compose
port = {"dev": 5432, "test": 5433}


class Config:
    SECRET_KEY = "bad_key"
    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['dev']}:{port['dev']}/{database['dev']}"


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = f"postgresql://{username}:{password}@{hostname['test']}:{port['test']}/{database['test']}"
