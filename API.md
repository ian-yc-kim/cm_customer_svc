# Session Management API Documentation

This document describes the session management endpoints for the cm_customer_svc service.

Base path prefix: /api
Cookie name: access_token

Overview

Authentication uses JWT access tokens stored in an HttpOnly cookie named "access_token". The server issues a signed JWT with iat and exp claims. The cookie attributes (HttpOnly, Secure, SameSite, Max-Age) are configurable via environment variables and enforced by the server.

Cookie Security Flags and Behavior

- HttpOnly: When enabled the cookie has the HttpOnly flag and is inaccessible to JavaScript. Controlled by HTTP_ONLY_COOKIE.
- Secure: When enabled the cookie has the Secure flag and is only sent over HTTPS. Controlled by SECURE_COOKIE.
- SameSite: Controls the SameSite attribute (e.g., Lax, Strict, None). Configured via SAMESITE_COOKIE (default: Lax).
- Max-Age: The cookie Max-Age equals ACCESS_TOKEN_EXPIRE_MINUTES * 60 seconds.
- Expiration semantics: JWT exp claim is validated server-side. Expired tokens cause 401 Unauthorized responses even if the cookie remains present.

Endpoints

POST /api/auth/login

- Description: Authenticate a user and establish a secure session by setting a JWT in an HttpOnly cookie.
- Request Body: JSON object
  {
    "username": "string",
    "password": "string"
  }
- Responses:
  - 200 OK
    - JSON body: { "message": "login successful" }
    - Response header: Set-Cookie: access_token=<JWT>; HttpOnly; SameSite=<SAMESITE_COOKIE>; Max-Age=<seconds>; Secure (if enabled)
  - 401 Unauthorized
    - JSON body: { "detail": "Invalid credentials" }
- Security: The cookie is set with HttpOnly and Secure flags (as configured). When using TestClient (HTTP) a test-only middleware may append a duplicate non-secure Set-Cookie header for testing convenience.
- Curl examples:
  Successful login (example):
  curl -i -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"password"}'

  Expected successful response includes a Set-Cookie header containing access_token, HttpOnly, SameSite and Max-Age.

POST /api/auth/logout

- Description: Invalidate the current user session and clear the session cookie.
- Request Body: None
- Responses:
  - 200 OK
    - JSON body: { "message": "logout successful" }
    - Response header: Set-Cookie: access_token=; Max-Age=0; HttpOnly; SameSite=<SAMESITE_COOKIE>; Secure (if enabled)
- Curl example:
  curl -i -X POST http://localhost:8000/api/auth/logout

GET /api/users/me

- Description: Retrieve details of the currently authenticated user.
- Authentication: Requires a valid access_token cookie on the request.
- Headers: No Authorization header required when cookie is used. Ensure the cookie is included in the request.
- Responses:
  - 200 OK
    - JSON body: { "current_user_id": "EMP00001" } (example)
  - 401 Unauthorized
    - JSON body: { "detail": "Not authenticated" } when cookie is missing
    - JSON body: { "detail": "Invalid or expired token" } when token is invalid or expired
- Curl example (using cookie):
  curl -i -X GET http://localhost:8000/api/users/me \
    --cookie "access_token=<JWT>"

Configuration Reference

Relevant environment variables and their effects:
- SECURE_COOKIE (bool): When true, cookies include the Secure flag and are only sent over HTTPS.
- HTTP_ONLY_COOKIE (bool): When true, cookies include the HttpOnly flag to prevent JavaScript access.
- SAMESITE_COOKIE (string): Controls SameSite value (Lax/Strict/None). Default: Lax.
- ACCESS_TOKEN_EXPIRE_MINUTES (int): Controls token lifetime. Max-Age on cookie equals minutes * 60.

Error Handling

- 401 Unauthorized is returned for invalid credentials, missing cookie, invalid token, or expired token.
- The server logs token decoding errors and returns a generic 401 response for invalid/expired tokens to avoid leaking implementation details.

Notes

- The service issues JWTs with iat and exp claims. The server strictly enforces exp.
- For local testing (TestClient over HTTP) the application may append a duplicate non-secure Set-Cookie header to allow cookie round-trip during tests while preserving the secure header for production semantics.


---

# User Registration

POST /api/register

- Description: Register a new user account.
- Authentication: Not required.
- Request model: UserCreate
  - Fields:
    - employee_id: string, exactly 8 digits; validated server-side.
    - employee_name: string, 1-100 characters; sanitized (trim, remove control chars, HTML-escape, collapse whitespace).
    - password: string; validated for strength.
- Validation rules applied:
  - Password strength: minimum 8 characters, at least one digit and one letter.
  - Employee ID: exactly 8 numeric digits.
  - employee_name sanitized to reduce XSS/whitespace issues.
- Responses:
  - 201 Created
    - Body: { "message": "user created", "employee_id": "12345678" }
  - 409 Conflict
    - Body: { "detail": "employee_id already exists" }
  - 422 Unprocessable Entity
    - Pydantic validation errors (e.g., missing fields or format failures)
  - 500 Internal Server Error
    - Body: { "detail": "internal server error" }
- Example request:
  {
    "employee_id": "12345678",
    "employee_name": "Alice Smith",
    "password": "passw0rd1"
  }
- Example curl:
  curl -i -X POST http://localhost:8000/api/register \
    -H "Content-Type: application/json" \
    -d '{"employee_id":"12345678","employee_name":"Alice Smith","password":"passw0rd1"}'


---

# Customers

Note: All endpoints below require a valid session cookie named access_token. The cookie must be sent with requests (TestClient helpers or browser will manage sending the cookie).

Customer object (API representation)
- customer_id: UUID string
- customer_name: string
- customer_contact: string|null (validated phone format)
- customer_address: string|null (sanitized)
- managed_by: string (employee id; see rules)
- created_at: ISO-8601 timestamp
- updated_at: ISO-8601 timestamp


## Create Customer

POST /api/customers

- Description: Create a new customer record and assign a manager.
- Authentication: Required (access_token cookie).
- Request model: CustomerCreate
  - customer_name: required, 1-100 chars, sanitized
  - customer_contact: optional, phone format validated (7-15 digits total; allowed characters + digits spaces - () . )
  - customer_address: optional, sanitized
  - managed_by: required employee id; validated
    - Primary accepted form: exactly 8 digits
    - Compatibility: accepts EMP + 5 digits (e.g., EMP00001) for backward compatibility
- Responses:
  - 201 Created
    - Body: { "message": "customer created", "customer": { ...Customer... } }
  - 400 Bad Request
    - Occurs when managed_by does not reference an existing user
  - 401 Unauthorized
    - Missing/invalid/expired auth cookie
  - 422 Unprocessable Entity
    - Validation errors from Pydantic
  - 500 Internal Server Error
- Example request:
  {
    "customer_name": "Acme Co",
    "customer_contact": "+1 (555) 123-4567",
    "customer_address": "123 Main St, Suite 200",
    "managed_by": "12345678"
  }
- Example curl:
  curl -i -X POST http://localhost:8000/api/customers \
    -H "Content-Type: application/json" \
    --cookie "access_token=<JWT>" \
    -d '{"customer_name":"Acme Co","customer_contact":"+1 (555) 123-4567","customer_address":"123 Main St","managed_by":"12345678"}'


## Get Customer

GET /api/customers/{customer_id}

- Description: Retrieve a customer by UUID.
- Path parameter: customer_id (UUID string)
- Authentication: Required (access_token cookie)
- Responses:
  - 200 OK
    - Body: { "customer": { ...Customer... } }
  - 401 Unauthorized
    - Missing/invalid/expired auth cookie
  - 404 Not Found
    - When the customer does not exist or customer_id is invalid
  - 500 Internal Server Error
- Example curl:
  curl -i -X GET http://localhost:8000/api/customers/550e8400-e29b-41d4-a716-446655440000 \
    --cookie "access_token=<JWT>"


## Update Customer

PUT /api/customers/{customer_id}

- Description: Update customer fields. All fields optional in request.
- Path parameter: customer_id (UUID string)
- Authentication: Required (access_token cookie)
- Request model: CustomerUpdate (all fields optional)
  - Validations and sanitization same as create
  - If managed_by is present it must reference an existing user
- Responses:
  - 200 OK
    - Body: { "customer": { ...Customer... } }
  - 400 Bad Request
    - Invalid managed_by that does not match an existing user
  - 401 Unauthorized
  - 404 Not Found
    - Customer not found
  - 422 Unprocessable Entity
    - Validation errors
  - 500 Internal Server Error
- Example request:
  {
    "customer_contact": "(555) 999-0000",
    "managed_by": "EMP00001"
  }
- Example curl:
  curl -i -X PUT http://localhost:8000/api/customers/550e8400-e29b-41d4-a716-446655440000 \
    -H "Content-Type: application/json" \
    --cookie "access_token=<JWT>" \
    -d '{"customer_contact":"(555) 999-0000","managed_by":"EMP00001"}'


## Delete Customer

DELETE /api/customers/{customer_id}

- Description: Delete a customer by UUID.
- Path parameter: customer_id (UUID string)
- Authentication: Required (access_token cookie)
- Responses:
  - 204 No Content
  - 401 Unauthorized
  - 404 Not Found
  - 500 Internal Server Error
- Example curl:
  curl -i -X DELETE http://localhost:8000/api/customers/550e8400-e29b-41d4-a716-446655440000 \
    --cookie "access_token=<JWT>"


---

# Validation Rules Summary

- Password strength
  - Minimum 8 characters
  - At least one digit
  - At least one alphabetic character

- Employee ID
  - Registration requires exactly 8 numeric digits (e.g., "12345678")
  - For managed_by fields: primary rule is 8 digits; compatibility also accepts "EMP" + 5 digits (e.g., "EMP00001")

- Phone number
  - Allowed characters: digits, +, spaces, dashes, parentheses, dot
  - No alphabetic characters allowed
  - Total digit count must be between 7 and 15

- Sanitization
  - Strings (names, addresses) are trimmed, control characters removed, HTML-escaped, and whitespace collapsed


# Authentication Reference

- Session cookie name: access_token
- Cookie attributes: HttpOnly, Secure (if enabled), SameSite, Max-Age
- Requests to customer endpoints must include the cookie. Missing/invalid/expired cookie yields 401.
- Current implementation: no role-based 403 enforcement on customer endpoints (403 reserved for future use).


# Examples and Notes

- Timestamps returned by APIs use ISO-8601 (UTC) format, e.g. 2023-01-01T12:00:00Z or with offset.
- Validation failures are surfaced as 422 responses from Pydantic validators when field-level validation fails.
- Where business checks fail (e.g., managed_by not found), handler returns 400 with explanatory message.


# Change Log

- Added User Registration and full Customer CRUD documentation (create, get, update, delete).
- Documented request/response models, authentication requirements, and validation rules.
