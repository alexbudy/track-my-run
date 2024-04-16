import string
import secrets
import hashlib


def create_salt(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_password(pw, salt):
    salted_pass = salt + pw
    return hashlib.sha256(salted_pass.encode()).hexdigest()
