import pytest
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models.models import Base
from sqlalchemy import text
from sqlalchemy.orm.session import Session


@pytest.fixture(scope="session")
def app():
    app = create_app("test")
    yield app


@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as client:
        yield client


STATIC_TABLES = {
    "cooper_points"
}  # tables not to clear before each test - possibly move out of tests folder


def _reset_schema(session: Session):

    # clear all tables after each test
    for table in Base.metadata.sorted_tables:
        if table.name in STATIC_TABLES:
            continue

        db.session.execute(text(f"TRUNCATE {table.name} RESTART IDENTITY CASCADE;"))
        db.session.commit()


@pytest.fixture(scope="function")
def db_session(app):
    with app.app_context():
        _reset_schema(db.session)

        db.session.begin_nested()
        yield db.session
        db.session.rollback()

        # clear all tables after each test
        _reset_schema(db.session)
