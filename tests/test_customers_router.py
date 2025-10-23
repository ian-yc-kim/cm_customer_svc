from jose import jwt
from datetime import datetime, timedelta, timezone

from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME
from cm_customer_svc.config import SECRET_KEY, ALGORITHM


def _login_via_registration(client, employee_id: str, password: str):
    # Use registration flow so password hashing and stored user exist
    reg_payload = {"employee_id": employee_id, "employee_name": "Manager", "password": password}
    r = client.post("/api/register", json=reg_payload)
    assert r.status_code == 201

    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": password})
    assert resp.status_code == 200


def test_post_customer_success_and_persist(client, db_session):
    # register and login the manager, then create a customer
    # Use a valid 8-digit numeric employee_id to satisfy validation
    manager_emp = "00020001"
    pw = "Password123"

    _login_via_registration(client, manager_emp, pw)

    payload = {
        "customer_name": "Acme Corp",
        "customer_contact": "1234567890",
        "customer_address": "1 Main St",
        "managed_by": manager_emp,
    }

    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 201

    # verify persisted via DB session
    from sqlalchemy import select
    from cm_customer_svc.models import Customer

    stmt = select(Customer).filter_by(customer_name="Acme Corp")
    retrieved = db_session.execute(stmt).scalar_one()
    assert retrieved.managed_by == manager_emp
    assert retrieved.customer_contact == "1234567890"
