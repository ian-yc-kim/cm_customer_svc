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

