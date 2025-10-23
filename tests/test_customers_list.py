from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME


def _login_via_registration(client, employee_id: str, password: str):
    reg_payload = {"employee_id": employee_id, "employee_name": "Manager", "password": password}
    r = client.post("/api/register", json=reg_payload)
    assert r.status_code == 201

    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": password})
    assert resp.status_code == 200


def _create_customers(client, count: int):
    for i in range(count):
        payload = {
            "customer_name": f"Customer {i}",
            "customer_contact": f"100000000{i}",
            "customer_address": f"Address {i}",
        }
        resp = client.post("/api/customers", json=payload)
        assert resp.status_code == 201


def test_get_customers_default_pagination(client):
    manager_emp = "00030001"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    _create_customers(client, 12)

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert body["total_count"] == 12
    assert len(body["items"]) == 10


def test_get_customers_custom_pagination(client):
    manager_emp = "00030002"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    _create_customers(client, 12)

    resp = client.get("/api/customers?page=2&page_size=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["page_size"] == 5
    assert body["total_count"] == 12
    assert len(body["items"]) == 5


def test_get_customers_empty_db(client):
    manager_emp = "00030003"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    resp = client.get("/api/customers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 0
    assert body["items"] == []


def test_get_customers_page_out_of_bounds(client):
    manager_emp = "00030004"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    _create_customers(client, 12)

    resp = client.get("/api/customers?page=5&page_size=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 12
    assert body["items"] == []


def test_get_customers_last_page_empty(client):
    manager_emp = "00030005"
    pw = "Password123"
    _login_via_registration(client, manager_emp, pw)

    _create_customers(client, 12)

    resp = client.get("/api/customers?page=4&page_size=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] == 12
    assert body["items"] == []


def test_get_customers_unauthenticated(client):
    resp = client.get("/api/customers")
    assert resp.status_code == 401
