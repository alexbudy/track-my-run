from itertools import product

import pytest

from app.utils.utils import (
    ALPHABET_WITH_PUNC,
    create_salt,
    create_session_tok,
    hash_password,
)


def test_create_salt():
    # default case
    assert len(create_salt()) == 16


def test_create_salt_custom_length():
    assert len(create_salt(length=32)) == 32


def test_create_salt_unique():
    salts = {create_salt() for _ in range(100)}
    assert len(salts) == 100


def test_create_salt_in_char_set():
    for _ in range(10):
        assert set(create_salt()).issubset(ALPHABET_WITH_PUNC)


@pytest.mark.parametrize(
    "pw, salt, expected_hash",
    [
        (
            "somepass",
            "somesalt",
            "ac5173928040074fa72fbbd907cd5c0317680fb7fdf96bd62eea16675125fdca",
        ),
        (
            "",
            "",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
    ],
)
def test_hash_password(pw, salt, expected_hash):
    assert hash_password(pw, salt) == expected_hash


def test_hash_password_different_combos():
    hashes = set()
    for pw, salt in product(["pass1", "pass2"], ["salt1", "salt2"]):
        hashes.add(hash_password(pw, salt))

    assert len(hashes) == 4


def test_create_session_tok():
    tok = create_session_tok()
    assert tok.startswith("sess_")
    assert len(tok[5:]) == 15
