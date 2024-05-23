from typing import Dict, List

from flask import current_app, jsonify

from app.utils.utils import create_session_tok
from app.cache import redis_cache

# util functions here

LOGIN_EXPIRY_S = 3600  # session expiry


def create_and_store_access_token_in_cache(user_id: int) -> str:
    current_app.logger.info(f"User {user_id} logged in")
    tok: str = create_session_tok()

    redis_cache.set(tok, user_id, ex=LOGIN_EXPIRY_S)
    redis_cache.set(f"user_id:{user_id}", tok, ex=LOGIN_EXPIRY_S)

    return tok


def flatten_validation_errors(err: Dict[str, List[str]]):
    return {key: "\n".join(value) for key, value in err.items()}


def stringify_validation_errors(err: Dict[str, List[str]] | str):
    if type(err) == dict:
        err_msg = [key.capitalize() + " " + val[0].lower() for key, val in err.items()]
    else:
        err_msg = [err]
    return "\n".join(err_msg)


def abort(err: Dict[str, List[str]] | str, page: str):
    """Handle errors from marshmallow as well as regular strings"""
    if type(err) == dict:
        err_msg = [key.capitalize() + " " + val[0].lower() for key, val in err.items()]
    else:
        err_msg = [err]
    current_app.logger.info(err_msg)

    return jsonify({"error": err_msg})  # TODO key should be 'error'?
