import string
import secrets
import hashlib
import uuid
import jwt
import datetime

ALPHABET = string.ascii_letters + string.digits
ALPHABET_WITH_PUNC = ALPHABET + string.punctuation


def create_salt(length=16):
    return "".join(secrets.choice(ALPHABET_WITH_PUNC) for _ in range(length))


def hash_password(pw, salt):
    salted_pass = salt + pw
    return hashlib.sha256(salted_pass.encode()).hexdigest()


def create_uuid():
    return str(uuid.uuid4())


def create_session_tok():
    return "sess_" + "".join(secrets.choice(ALPHABET) for _ in range(15))


def current_utc_ts():
    return round(datetime.datetime.now(datetime.UTC).timestamp())


def create_jwt_token(user_id):
    payload = {"user_id": user_id}
    secret = "SUPERSECRET"  # TODO - change
    tok = jwt.encode(payload=payload, key=secret, algorithm="HS256")
    return tok


def user_id_from_token(tok):
    # TODO better decoding?
    try:
        dec = jwt.decode(tok, key="SUPERSECRET", algorithms="HS256")
        return dec["user_id"]
    except Exception as e:
        return None
