import string
import secrets
import hashlib
import uuid
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
