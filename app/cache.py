from redis import StrictRedis
import os

redis_cache: StrictRedis = StrictRedis(
    host=os.getenv("REDIS_CACHE"), port=os.getenv("REDIS_PORT")
)
