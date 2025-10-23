import re
import html
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def validate_password_strength(password: str) -> str:
    """Ensure password has minimum length and contains at least one digit and one letter.

    Returns the original password on success. Raises ValueError on failure.
    """
    try:
        if not isinstance(password, str):
            raise ValueError("password must be a string")
        if len(password) < 8:
            raise ValueError("password must be at least 8 characters long")
        if not re.search(r"\d", password):
            raise ValueError("password must contain at least one digit")
        if not re.search(r"[A-Za-z]", password):
            raise ValueError("password must contain at least one alphabet character")
        return password
    except Exception as e:
        logger.error(e, exc_info=True)
        raise


def validate_employee_id_format(employee_id: str) -> str:
    """Require exactly 8 numeric digits for employee_id.

    Returns the employee_id on success. Raises ValueError on failure.
    """
    try:
        if not isinstance(employee_id, str):
            raise ValueError("employee_id must be a string of 8 digits")
        eid = employee_id.strip()
        if len(eid) != 8 or not eid.isdigit():
            raise ValueError("employee_id must be exactly 8 numeric digits")
        return eid
    except Exception as e:
        logger.error(e, exc_info=True)
        raise


_PHONE_DIGIT_MIN = 7
_PHONE_DIGIT_MAX = 15


def validate_phone_number_format(phone_number: Optional[str]) -> Optional[str]:
    """Basic phone number validation.

    Accepts common characters (+, digits, spaces, dashes, parentheses).
    Ensures total digit count between 7 and 15. Returns normalized original string on success.
    Raises ValueError on failure.
    If phone_number is None, returns None.
    """
    try:
        if phone_number is None:
            return None
        if not isinstance(phone_number, str):
            raise ValueError("phone_number must be a string")
        s = phone_number.strip()
        # allow characters + digits spaces - () .
        if re.search(r"[A-Za-z]", s):
            raise ValueError("phone_number contains alphabetic characters")
        digits = re.sub(r"\D", "", s)
        if len(digits) < _PHONE_DIGIT_MIN or len(digits) > _PHONE_DIGIT_MAX:
            raise ValueError("phone_number must contain between 7 and 15 digits")
        # Normalize by collapsing spaces
        normalized = re.sub(r"\s+", " ", s)
        return normalized
    except Exception as e:
        logger.error(e, exc_info=True)
        raise


def sanitize_input(input_string: Optional[str]) -> Optional[str]:
    """Basic sanitization to reduce risk of XSS/SQL injection in user-provided strings.

    - Returns None for None input
    - Strips leading/trailing whitespace
    - Removes control characters
    - Escapes HTML special characters
    - Collapses multiple whitespace to a single space
    """
    try:
        if input_string is None:
            return None
        s = str(input_string).strip()
        # remove control characters
        s = re.sub(r"[\x00-\x1f\x7f]", "", s)
        # escape HTML
        s = html.escape(s)
        # collapse whitespace
        s = re.sub(r"\s+", " ", s)
        return s
    except Exception as e:
        logger.error(e, exc_info=True)
        raise
