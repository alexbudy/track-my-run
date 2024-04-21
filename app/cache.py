from redis import Redis


redis_cache: Redis = Redis(host="cache", port=6379)
