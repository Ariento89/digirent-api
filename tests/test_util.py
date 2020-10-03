from sqlalchemy import util
import digirent.util as util


def test_hash_password():
    password = "testpass"
    hashed_password = util.hash_password(password)
    assert password != hashed_password


def test_password_is_match():
    password = "testpass"
    hashed_password = util.hash_password(password)
    assert not util.password_is_match("wrong", hashed_password)
    assert util.password_is_match(password, hashed_password)
