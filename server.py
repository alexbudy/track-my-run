import os
from dotenv import load_dotenv

load_dotenv()  # load env variables before importing from app

from app import create_app

app = create_app(os.getenv("FLASK_CONFIG") or "dev")  # set to 'prod' for production

if __name__ == "__main__":
    app.run(debug=True, host=os.getenv("LOCAL_HOST"), port=os.getenv("LOCAL_PORT"))
