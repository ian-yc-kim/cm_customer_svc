from sqlalchemy import select

from cm_customer_svc.models import User
from cm_customer_svc.utils.password_utils import verify_password


def test_register_success(client, db_session):
    payload = {"employee_id": "00001234", "employee_name": "Alice", "password": "Password123"}
    resp = client.post("/api/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["employee_id"] == "00001234"
    assert "message" in data

    stmt = select(User).filter_by(employee_id="00001234")
    user = db_session.execute(stmt).scalar_one()
    assert user is not None
    # Ensure stored password is hashed and verification succeeds
    assert user.password_hash != payload["password"]
    assert verify_password(payload["password"], user.password_hash)


def test_register_invalid_password(client):
    # password too short / weak per validation
    payload = {"employee_id": "00001235", "employee_name": "Bob", "password": "short1"}
    resp = client.post("/api/register", json=payload)
    assert resp.status_code == 422


def test_register_duplicate_employee_id(client, db_session):
    # pre-insert a user to cause duplicate
    existing = User(employee_id="00001236", employee_name="Existing", password_hash="pw")
    db_session.add(existing)
    db_session.commit()

    payload = {"employee_id": "00001236", "employee_name": "New", "password": "Password123"}
    resp = client.post("/api/register", json=payload)
    assert resp.status_code == 409
    assert resp.json().get("detail") == "employee_id already exists"
