import multiprocessing as mp
import os
from dotenv import load_dotenv

load_dotenv()
LOG_DIR = os.getenv("LOG_DIR")
FLASK_CONFIG = os.getenv("FLASK_CONFIG")

port = 8000  # prod port
if FLASK_CONFIG == "stage":
    port = 8001

bind = f"0.0.0.0:{port}"
workers = mp.cpu_count() * 2 + 1

# Logging values
capture_output = True
accesslog = f"{LOG_DIR}/access.log"
errorlog = f"{LOG_DIR}/error.log"
loglevel = "debug"
