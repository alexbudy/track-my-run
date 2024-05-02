import pytest
from app import create_app, db


@pytest.fixture(scope="session")
def app():
    app = create_app("test")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as client:
        yield client


# @pytest.fixture(scope="function")
# def db_session(app):
#     with app.app_context():
#         db.session.begin_nested()
#         yield db.session
#         db.session.rollback()
