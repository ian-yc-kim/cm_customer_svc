import io


def test_api_md_contains_customer_management_section():
    with open("API.md", "r", encoding="utf-8") as f:
        content = f.read()

    assert "Customer Management API" in content
    # key endpoints
    assert "POST /api/customers" in content
    assert "GET /api/customers" in content
    assert "GET /api/customers/{customer_id}" in content
    assert "PUT /api/customers/{customer_id}" in content
    assert "DELETE /api/customers/{customer_id}" in content


def test_api_md_documents_pagination_and_response_fields():
    with open("API.md", "r", encoding="utf-8") as f:
        content = f.read()

    # pagination params documented
    assert "page: integer" in content or "page (integer" in content
    assert "page_size" in content

    # paginated response fields
    assert "PaginatedCustomerResponse" in content or "total_count" in content
    assert "items" in content
    assert "page_size" in content
