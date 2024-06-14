import string
import secrets
import hashlib

ALPHABET = string.ascii_letters + string.digits
ALPHABET_WITH_PUNC = ALPHABET + string.punctuation


def create_salt(length=16):
    return "".join(secrets.choice(ALPHABET_WITH_PUNC) for _ in range(length))


def hash_password(pw, salt):
    salted_pass = salt + pw
    return hashlib.sha256(salted_pass.encode()).hexdigest()


def create_session_tok():
    return "sess_" + "".join(secrets.choice(ALPHABET) for _ in range(15))


def time_pattern_to_seconds(time_pattern):
    """Convert the time pattern of hh:mm:ss into seconds for storing in DB"""
    time_pattern = time_pattern.split(":")
    return (
        int(time_pattern[0]) * 3600 + int(time_pattern[1]) * 60 + int(time_pattern[2])
    )
