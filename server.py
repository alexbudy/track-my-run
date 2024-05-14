import os
import logging
from flask import current_app
from dotenv import load_dotenv

load_dotenv()  # load env variables before importing from app

from app import create_app

flask_config = os.getenv("FLASK_CONFIG") or "dev"
app = create_app(flask_config)  # set to 'prod' for production

with app.app_context():
    current_app.logger.setLevel(logging.INFO)


if __name__ == "__main__":
    app.run(
        debug=flask_config != "prod",
        host=os.getenv("SERVER_HOST"),
        port=os.getenv("SERVER_PORT"),
    )
