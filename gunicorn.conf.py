import multiprocessing as mp
import os

from dotenv import load_dotenv

load_dotenv()
LOG_DIR = os.getenv("LOG_DIR")

bind = "0.0.0.0:8000"
workers = mp.cpu_count() * 2 + 1

# Logging values
capture_output = True
accesslog = f"{LOG_DIR}/access.log"
errorlog = f"{LOG_DIR}/error.log"
loglevel = "debug"
