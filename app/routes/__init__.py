from typing import Dict, List

from flask import current_app, jsonify

# util functions here


def abort(err: Dict[str, List[str]] | str, err_code=400):
    """Handle errors from marshmallow as well as regular strings"""
    if type(err) == dict:
        err_msg = [key.capitalize() + " " + val[0].lower() for key, val in err.items()]
    else:
        err_msg = [err]
    current_app.logger.info(err_msg)
    return jsonify({"error": err_msg}), err_code  # TODO key should be 'error'?
