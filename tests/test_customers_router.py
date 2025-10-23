import uuid
import pytest
from fastapi import status

from cm_customer_svc.models.user import User
from cm_customer_svc.models.customer import Customer


def _login(client):
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "password"})
    assert resp.status_code == 200


def test_auth_required_for_customers_endpoints(client):
    # ensure no cookie
    client.cookies.clear()
    resp = client.post("/api/customers", json={
        "customer_name": "X",
        "managed_by": "EMP00001"
    })
    assert resp.status_code == 401


def test_post_customer_success_and_persist(client, db_session):
    # create manager user
    manager = User(employee_id="EMP20001", employee_name="Manager", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    _login(client)

    payload = {
        "customer_name": "Acme Test",
        "customer_contact": "1234567890",
        "customer_address": "1 Test St",
        "managed_by": manager.employee_id,
    }
    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data.get("message") == "customer created"
    cust = data.get("customer")
    assert cust["customer_name"] == "Acme Test"
    assert cust["managed_by"] == manager.employee_id

    # verify persisted
    db_session.expire_all()
    c = db_session.query(Customer).filter_by(customer_name="Acme Test").one_or_none()
    assert c is not None
    assert c.managed_by == manager.employee_id


def test_post_customer_invalid_managed_by_returns_400(client):
    _login(client)
    payload = {"customer_name": "No Manager", "managed_by": "EMP99999"}
    resp = client.post("/api/customers", json=payload)
    assert resp.status_code == 400
    assert "does not exist" in resp.json().get("detail")


def test_get_customer_existing_and_not_found(client, db_session):
    manager = User(employee_id="EMP20002", employee_name="Mgr2", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(customer_name="GetMe", managed_by=manager.employee_id)
    db_session.add(customer)
    db_session.commit()

    _login(client)

    resp = client.get(f"/api/customers/{customer.customer_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer"]["customer_name"] == "GetMe"

    # not found
    resp2 = client.get(f"/api/customers/{uuid.uuid4()}")
    assert resp2.status_code == 404


def test_put_customer_update_success_and_invalid_managed_by(client, db_session):
    manager1 = User(employee_id="EMP20003", employee_name="M1", password_hash="pw")
    manager2 = User(employee_id="EMP20004", employee_name="M2", password_hash="pw")
    db_session.add_all([manager1, manager2])
    db_session.commit()

    customer = Customer(customer_name="Updatable", managed_by=manager1.employee_id)
    db_session.add(customer)
    db_session.commit()

    _login(client)

    update_payload = {"customer_name": "Updated Name", "managed_by": manager2.employee_id}
    resp = client.put(f"/api/customers/{customer.customer_id}", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer"]["customer_name"] == "Updated Name"
    assert data["customer"]["managed_by"] == manager2.employee_id

    # invalid managed_by
    resp2 = client.put(f"/api/customers/{customer.customer_id}", json={"managed_by": "EMP99998"})
    assert resp2.status_code == 400


def test_put_customer_not_found_returns_404(client):
    _login(client)
    resp = client.put(f"/api/customers/{uuid.uuid4()}", json={"customer_name": "NoOne"})
    assert resp.status_code == 404


def test_delete_customer_success_and_not_found(client, db_session):
    manager = User(employee_id="EMP20005", employee_name="Mdel", password_hash="pw")
    db_session.add(manager)
    db_session.commit()

    customer = Customer(customer_name="DeleteMe", managed_by=manager.employee_id)
    db_session.add(customer)
    db_session.commit()

    _login(client)

    resp = client.delete(f"/api/customers/{customer.customer_id}")
    assert resp.status_code == 204

    # subsequent get should 404
    resp2 = client.get(f"/api/customers/{customer.customer_id}")
    assert resp2.status_code == 404

    # delete non-existing
    resp3 = client.delete(f"/api/customers/{uuid.uuid4()}")
    assert resp3.status_code == 404
