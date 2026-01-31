# Developing Userverse Clients in Other Languages

This document summarizes the Python client architecture and provides a plan for
building equivalent clients in other languages (e.g., Dart, JavaScript, Go).

## Summary of the Python Client

### Core HTTP design
- **Base URL normalization**: The Python client trims trailing slashes from the
  base URL and requires all request paths to start with `/`.
- **Session headers**: Every request sets `Accept: application/json` and
  `Content-Type: application/json`.
- **Timeouts**: The `BaseClient` accepts a configurable timeout (default: 30
  seconds).
- **Authorization**:
  - **Bearer** token for authenticated endpoints via
    `Authorization: Bearer <token>`.
  - **Basic Auth** for user login and account creation with email/password
    encoded as `Basic <base64(email:password)>`.
- **Error handling**:
  - HTTP errors are parsed into a structured error payload if possible.
  - Network/timeouts are surfaced as client errors with a generic "invalid
    request" message.
  - Empty bodies (e.g., 204 responses) return `None`.
  - Successful responses that are not JSON fall back to text.

### Client surface area
The Python package exposes dedicated client classes that map to API domains and
reuse the shared `BaseClient`:
- `UverseUserClient` (login, create user, get/update user, verification, password
  reset).
- `UverseCompanyClient` (list companies, get company by ID/email, create/update
  company).
- `UverseCompanyUserManagementClient` (add/list/delete users in a company).
- `UverseCompanyUserRolesManagement` (list/create/update/delete company roles).

### Models and response shapes
- Responses are wrapped in a generic response shape (`GenericResponseModel`)
  with a `data` field that holds the typed payload.
- Request and response schemas are defined in the shared model packages
  (`userverse_models`, `sverse_generic_models`), which the client references
  directly.

### Usage patterns
Examples show a consistent flow:
1. Create a `UverseUserClient` with `base_url`.
2. Login with Basic Auth to obtain a JWT.
3. Set `Authorization: Bearer <token>` on other clients for protected endpoints.
4. Call methods that mirror API routes and validate responses.

## Plan to Build Clients in Other Languages

### 1. Establish a shared API contract
- Extract the request/response schemas (from `userverse_models` and
  `sverse_generic_models`) into an OpenAPI or JSON schema source of truth.
- Ensure the response wrapper and error formats match the server responses.

### 2. Implement a base HTTP client
- Mirror the Python `BaseClient` behavior:
  - Normalize `base_url` and enforce path formatting.
  - Default headers: `Accept` + `Content-Type` set to JSON.
  - Configurable timeout.
  - Helper for setting Bearer tokens.
  - Return `None` for empty bodies.
  - Prefer explicit query parameter handling instead of manual string building.
- Provide a centralized request method that every endpoint uses.

### 3. Port authentication flows
- Implement Basic Auth encoding for login and create-user endpoints.
- Implement bearer token injection after login for all protected endpoints.
- Preserve the same endpoints/methods:
  - `PATCH /user/login`
  - `POST /user`
  - `GET /user/get`
  - `PATCH /user/update`
  - `POST /user/resend-verification`
  - `GET /user/verify?token=<token>`
  - `PATCH /password-reset/request?email=<email>`
  - `PATCH /password-reset/validate-otp`
  - `GET /user/companies`
  - `GET /company?company_id=<id>` or `GET /company?email=<email>`
  - `PATCH /company/{id}`
  - `POST /company`
  - Company user/role management endpoints as in the Python client.

### 4. Generate or hand-write typed models
- If your language supports OpenAPI codegen (e.g., Dart `openapi-generator`,
  TypeScript `openapi-typescript`), generate data models and response wrappers.
- Otherwise, hand-write models matching the Python client types and ensure
  required/optional fields align with the API.

### 5. Error handling and response validation
- Match the Python client’s strategy:
  - On non-2xx responses, parse the error body into a structured error type.
  - If the server returns `detail.message` and `detail.error`, map them directly.
  - If parsing fails, fall back to a generic error message and raw body text.
- Provide a top-level error type (similar to `ClientErrorModel`) that includes
  HTTP status code and a detail payload.

### 6. Organize the client by domain
Mirror the Python structure for discoverability:
- `user` module/class for authentication + user profile.
- `company` module/class for company CRUD.
- `company_user_management` module/class for user membership in companies.
- `company_user_roles_management` module/class for role management.

### 7. Tests and example scripts
- Use the Python unit tests as reference for expected behaviors:
  - Enforce path requirements.
  - Validate error handling in HTTP failures.
  - Verify response shape parsing and Basic/Bearer auth handling.
- Provide runnable examples similar to the Python `examples/` to document flows
  for login, list companies, etc.

### 8. Packaging and documentation
- Provide a README that mirrors the Python client usage.
- Publish artifacts to the target ecosystem (npm, pub.dev, etc.).
- Version releases consistently with the API behavior.
