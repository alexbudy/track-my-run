from typing import Dict, List

from flask import current_app

from app.extensions import redis_cache
from app.utils.utils import create_session_tok

# util functions here

LOGIN_EXPIRY_S = 3600  # session expiry

DEFAULT_ORDERING = {
    "date": "desc",
    "activity_start_time": "asc",
    "distance_mi": "desc",
    "distance_yard": "desc",
    "duration_s": "desc",
    "pace": "desc",
    "activity_type": "desc",
    "cooper_points": "desc",
}


def create_and_store_access_token_in_cache(user_id: int) -> str:
    current_app.logger.info(f"User {user_id} logged in")
    tok: str = create_session_tok()

    redis_cache.set(tok, user_id, ex=LOGIN_EXPIRY_S)

    redis_cache.rpush(
        f"user_id:{user_id}", tok
    )  # maintain a list of tokens for a logged in user (multi-device) - useful for admin session management
    redis_cache.expire(f"user_id:{user_id}", LOGIN_EXPIRY_S)

    return tok


def flatten_validation_errors(err: Dict[str, List[str]]):
    return {key: "\n".join(value) for key, value in err.items()}


def stringify_validation_errors(err: Dict[str, List[str]] | str):
    if type(err) == dict:
        err_msg = [key.capitalize() + " " + val[0].lower() for key, val in err.items()]
    else:
        err_msg = [err]
    return "\n".join(err_msg)
