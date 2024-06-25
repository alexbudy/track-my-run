import os

from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

db = SQLAlchemy()
mail = Mail()

redis_cache: StrictRedis = StrictRedis(
    host=os.getenv("REDIS_CACHE"), port=os.getenv("REDIS_PORT")
)
