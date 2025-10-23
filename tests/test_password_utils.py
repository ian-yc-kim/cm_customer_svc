import pytest
from cm_customer_svc.utils.password_utils import hash_password, verify_password


def test_hash_password_and_verify():
    plain = "Password123"
    hashed = hash_password(plain)
    assert isinstance(hashed, str)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_verify_password_wrong_returns_false():
    plain = "Password123"
    hashed = hash_password(plain)
    assert not verify_password("WrongPass", hashed)


def test_verify_password_malformed_hash_returns_false():
    assert not verify_password("anything", "not-a-valid-hash")


def test_hash_password_invalid_input_raises():
    with pytest.raises(ValueError):
        hash_password("")
