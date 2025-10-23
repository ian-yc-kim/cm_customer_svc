from jose import jwt
from datetime import datetime, timedelta, timezone
import uuid

from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME
from cm_customer_svc.config import SECRET_KEY, ALGORITHM


def _login_via_registration(client, employee_id: str, password: str):
    # Use registration flow so password hashing and stored user exist
    reg_payload = {"employee_id": employee_id, "employee_name": "Manager", "password": password}
    r = client.post("/api/register", json=reg_payload)
    assert r.status_code == 201

    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": password})
    assert resp.status_code == 200


def _create_customer(client, customer_name: str, customer_contact: str = None, customer_address: str = None, extra: dict = None):
    payload = {
        "customer_name": customer_name,
        "customer_contact": customer_contact,
        "customer_address": customer_address,
    }
    if extra:
        payload.update(extra)
    resp = client.post("/api/customers", json=payload)
    return resp


def test_post_customer_success_and_persist(client, db_session):
    manager_emp = "00020001"
    pw = "Password123"

    _login_via_registration(client, manager_emp, pw)

    payload = {
        "customer_name": "Acme Corp",
        "customer_contact": "1234567890",
        "customer_address": "1 Main St",
    }

    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["customer_name"] == "Acme Corp"
    assert body["managed_by"] == manager_emp

    # verify persisted via DB session
    from sqlalchemy import select
    from cm_customer_svc.models import Customer

    stmt = select(Customer).filter_by(customer_name="Acme Corp")
    retrieved = db_session.execute(stmt).scalar_one()
    assert retrieved.managed_by == manager_emp
    assert retrieved.customer_contact == "1234567890"


def test_post_customer_unauthenticated(client):
    payload = {"customer_name": "NoAuth", "customer_contact": "1234567"}
    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Not authenticated"


def test_post_customer_managed_by_ignored_and_set_from_current_user(client, db_session):
    manager_emp = "00020002"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    # try to supply managed_by in payload (should be ignored)
    resp = _create_customer(client, "IgnoreManager", "1234567", "Addr", extra={"managed_by": "99999999"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["managed_by"] == manager_emp

    # persisted value
    from sqlalchemy import select
    from cm_customer_svc.models import Customer
    stmt = select(Customer).filter_by(customer_name="IgnoreManager")
    retrieved = db_session.execute(stmt).scalar_one()
    assert retrieved.managed_by == manager_emp


def test_post_customer_invalid_contact_validation(client):
    manager_emp = "00020003"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    # invalid contact contains letters -> validation error
    resp = _create_customer(client, "BadContact", "abcde", "Addr")
    # Pydantic validation should return 422
    assert resp.status_code == 422


def test_get_customer_by_id_success(client):
    manager_emp = "00020004"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    post = _create_customer(client, "GetMe", "1234567", "Addr")
    assert post.status_code == 201
    created = post.json()
    cid = created["customer_id"]

    resp = client.get(f"/api/customers/{cid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == cid
    assert body["customer_name"] == "GetMe"


def test_get_customer_by_id_not_found(client):
    manager_emp = "00020005"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    fake = str(uuid.uuid4())
    resp = client.get(f"/api/customers/{fake}")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "customer not found"


def test_get_customer_by_id_invalid_uuid(client):
    manager_emp = "00020006"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    resp = client.get("/api/customers/not-a-uuid")
    assert resp.status_code == 404
    assert resp.json().get("detail") == "customer not found"


def test_get_customer_unauthenticated(client):
    # create a customer under an authenticated user, then clear cookies and attempt fetch
    manager_emp = "00020007"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)
    post = _create_customer(client, "ToFetchUnauth", "1234567", "Addr")
    cid = post.json()["customer_id"]

    # clear cookies to simulate unauthenticated request
    client.cookies.clear()
    resp = client.get(f"/api/customers/{cid}")
    assert resp.status_code == 401


def test_put_customer_full_and_partial_update(client, db_session):
    manager_emp = "00020008"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    post = _create_customer(client, "ToUpdate", "1234567", "OldAddr")
    assert post.status_code == 201
    created = post.json()
    cid = created["customer_id"]

    # full update
    payload = {"customer_name": "UpdatedName", "customer_contact": "7654321", "customer_address": "NewAddr"}
    resp = client.put(f"/api/customers/{cid}", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_name"] == "UpdatedName"
    assert body["customer_contact"] == "7654321"
    assert body["customer_address"] == "NewAddr"

    # partial update (only name)
    payload2 = {"customer_name": "PartiallyUpdated"}
    resp2 = client.put(f"/api/customers/{cid}", json=payload2)
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body2["customer_name"] == "PartiallyUpdated"
    assert body2["customer_contact"] == "7654321"

    # persisted check in DB
    from sqlalchemy import select
    from cm_customer_svc.models import Customer
    stmt = select(Customer).filter_by(customer_id=uuid.UUID(cid))
    retrieved = db_session.execute(stmt).scalar_one()
    assert retrieved.customer_name == "PartiallyUpdated"


def test_put_customer_non_existent_and_invalid_uuid(client):
    manager_emp = "00020009"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    # non-existent
    fake = str(uuid.uuid4())
    resp = client.put(f"/api/customers/{fake}", json={"customer_name": "X"})
    assert resp.status_code == 404

    # invalid uuid
    resp2 = client.put("/api/customers/invalid-uuid", json={"customer_name": "X"})
    assert resp2.status_code == 404


def test_put_customer_invalid_input(client):
    manager_emp = "00020010"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    post = _create_customer(client, "ToBadUpdate", "1234567", "Addr")
    cid = post.json()["customer_id"]

    # invalid phone number
    resp = client.put(f"/api/customers/{cid}", json={"customer_contact": "no-digits-here"})
    assert resp.status_code == 422


def test_put_customer_unauthenticated(client):
    manager_emp = "00020011"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)
    post = _create_customer(client, "AuthNeededForPut", "1234567", "Addr")
    cid = post.json()["customer_id"]

    client.cookies.clear()
    resp = client.put(f"/api/customers/{cid}", json={"customer_name": "ShouldFail"})
    assert resp.status_code == 401


def test_delete_customer_success_and_followup_get_404(client):
    manager_emp = "00020012"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)
    post = _create_customer(client, "ToDelete", "1234567", "Addr")
    cid = post.json()["customer_id"]

    resp = client.delete(f"/api/customers/{cid}")
    assert resp.status_code == 204

    # subsequent get should 404
    resp2 = client.get(f"/api/customers/{cid}")
    assert resp2.status_code == 404


def test_delete_customer_non_existent_and_invalid_uuid(client):
    manager_emp = "00020013"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    fake = str(uuid.uuid4())
    resp = client.delete(f"/api/customers/{fake}")
    assert resp.status_code == 404

    resp2 = client.delete("/api/customers/not-a-uuid")
    assert resp2.status_code == 404


def test_delete_customer_unauthenticated(client):
    manager_emp = "00020014"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)
    post = _create_customer(client, "AuthNeededForDelete", "1234567", "Addr")
    cid = post.json()["customer_id"]

    client.cookies.clear()
    resp = client.delete(f"/api/customers/{cid}")
    assert resp.status_code == 401
