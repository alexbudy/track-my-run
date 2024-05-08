from redis import Redis
import os

redis_cache: Redis = Redis(host=os.getenv("REDIS_CACHE"), port=os.getenv("REDIS_PORT"))
