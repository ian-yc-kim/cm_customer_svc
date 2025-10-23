import pytest
from pydantic import ValidationError
from cm_customer_svc.schemas.user import UserCreate, UserLogin
from cm_customer_svc.schemas.customer import CustomerCreate, CustomerUpdate


def test_usercreate_valid_and_sanitizes():
    u = UserCreate(employee_id="00001234", employee_name=" Alice <b>Bob</b> ", password="Pass1234")
    assert u.employee_id == "00001234"
    assert "&lt;b&gt;" in u.employee_name


def test_usercreate_invalid_password_raises():
    with pytest.raises(ValidationError):
        UserCreate(employee_id="00001234", employee_name="Bob", password="short1")


def test_userlogin_invalid_employee_id_raises():
    with pytest.raises(ValidationError):
        UserLogin(employee_id="123", password="whatever")


def test_customercreate_valid_and_optional_none():
    c = CustomerCreate(customer_name="Acme Corp", customer_contact=None, customer_address=None, managed_by="00001234")
    assert c.customer_name == "Acme Corp"
    assert c.customer_contact is None


def test_customercreate_invalid_phone_raises():
    with pytest.raises(ValidationError):
        CustomerCreate(customer_name="X", customer_contact="bad-phone", customer_address=None, managed_by="00001234")


def test_customercreate_invalid_managed_by_raises():
    with pytest.raises(ValidationError):
        CustomerCreate(customer_name="X", customer_contact=None, customer_address=None, managed_by="ABC")


def test_customerupdate_sanitization_and_optional():
    cu = CustomerUpdate(customer_name="  Name <i>Inc</i>", customer_contact="+15551234567", customer_address=None, managed_by=None)
    assert cu.customer_name is not None and "&lt;i&gt;" in cu.customer_name
    assert cu.customer_contact == "+15551234567"
