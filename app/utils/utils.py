from datetime import datetime
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
    """Convert the time pattern of (hh:)mm:ss into seconds for storing in DB"""
    time_pattern = time_pattern.split(":")
    if len(time_pattern) == 2:
        time_pattern = [0] + time_pattern

    return (
        int(time_pattern[0]) * 3600 + int(time_pattern[1]) * 60 + int(time_pattern[2])
    )


def seconds_to_time(seconds: int):
    """Convert seconds into hh:mm:ss (where hh is 0-23)"""
    hr = seconds // 3600
    mn = (seconds % 3600) // 60
    sec = seconds % 60

    if hr:
        return f"{hr}:{mn:02}:{sec:02}"

    t: str = f"{mn:02}:{sec:02}"
    if t[0] == "0":
        t = t[1:]

    return t


def time_to_display(time):
    """Convert hh:mm:ss (where hh is 0-23) into hh:mm AM/PM"""
    if not time:
        return ""

    # remove zero-padding the hour, platform specific
    return datetime.strptime(time, "%H:%M:%S").strftime("%-I:%M %p")


def calculate_pace(
    duration_s: int, distance_mi: float | None, distance_yard: int | None
):
    """For now, just do min/mi"""

    if distance_mi:
        return (duration_s / 60) / distance_mi

    if distance_yard:
        return (duration_s / 60) / (distance_yard / 1760)
