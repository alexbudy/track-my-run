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
