import pytest
from cm_customer_svc.utils import validation_utils as v


# password strength
def test_validate_password_strength_valid():
    assert v.validate_password_strength("Abcdef1g") == "Abcdef1g"


def test_validate_password_strength_too_short():
    with pytest.raises(ValueError):
        v.validate_password_strength("Ab1c")


def test_validate_password_strength_no_digit():
    with pytest.raises(ValueError):
        v.validate_password_strength("Abcdefgh")


def test_validate_password_strength_no_alpha():
    with pytest.raises(ValueError):
        v.validate_password_strength("12345678")


# employee id
def test_validate_employee_id_format_valid():
    assert v.validate_employee_id_format("00001234") == "00001234"


def test_validate_employee_id_format_invalid_length():
    with pytest.raises(ValueError):
        v.validate_employee_id_format("123")


def test_validate_employee_id_format_non_numeric():
    with pytest.raises(ValueError):
        v.validate_employee_id_format("12AB1234")


# phone numbers
def test_validate_phone_number_format_valid_plus_and_dashes():
    assert v.validate_phone_number_format("+1 555-123-4567") == "+1 555-123-4567"


def test_validate_phone_number_format_valid_parentheses():
    assert v.validate_phone_number_format("(555)123-4567") == "(555)123-4567"


def test_validate_phone_number_format_too_short():
    with pytest.raises(ValueError):
        v.validate_phone_number_format("12345")


def test_validate_phone_number_format_with_letters():
    with pytest.raises(ValueError):
        v.validate_phone_number_format("555-ABC-1234")


# sanitize
def test_sanitize_input_html_and_whitespace():
    raw = "  <script>alert(1)</script>   DROP TABLE users;\n"
    cleaned = v.sanitize_input(raw)
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in cleaned
    assert "DROP TABLE users;" in cleaned
    assert cleaned.startswith("&lt;script")
