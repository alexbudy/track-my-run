from redis import StrictRedis
import os
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

redis_cache: StrictRedis = StrictRedis(
    host=os.getenv("REDIS_CACHE"), port=os.getenv("REDIS_PORT")
)
