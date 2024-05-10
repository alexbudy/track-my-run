import os
from dotenv import load_dotenv

load_dotenv()  # load env variables before importing from app

from app import create_app

flask_config = os.getenv("FLASK_CONFIG") or "dev"
app = create_app(flask_config)  # set to 'prod' for production

if __name__ == "__main__":
    app.run(
        debug=flask_config != "prod",
        host=os.getenv("LOCAL_HOST"),
        port=os.getenv("LOCAL_PORT"),
    )
