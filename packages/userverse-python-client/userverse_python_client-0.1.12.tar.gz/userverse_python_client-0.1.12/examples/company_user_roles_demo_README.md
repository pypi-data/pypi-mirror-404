Company user roles demo

`examples/company_user_roles_demo.py` showcases how to manage custom company
roles via `UverseCompanyUserRolesManagement`. The script logs in a user first
and reuses that token for every role action.

Running the demo

Each action uses CLI flags and reads data from environment variables. If a
required env var is missing the script skips that action with a message, so you
can run only the flows you need.

From the repo root:

```
uv run -m examples.company_user_roles_demo --help
```

Common usage

Login and list roles:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_ROLE_COMPANY_ID=123 \
uv run -m examples.company_user_roles_demo --login --list-roles
```

Create a role:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_ROLE_COMPANY_ID=123 \
COMPANY_ROLE_CREATE_NAME="Supervisor" \
COMPANY_ROLE_CREATE_DESCRIPTION="Can approve requests" \
uv run -m examples.company_user_roles_demo --login --create-role
```

Update a role:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_ROLE_COMPANY_ID=123 \
COMPANY_ROLE_UPDATE_ROLE_NAME="Supervisor" \
COMPANY_ROLE_UPDATE_DESCRIPTION="Approves and audits" \
uv run -m examples.company_user_roles_demo --login --update-role
```

Delete a role (requires a replacement role):

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_ROLE_COMPANY_ID=123 \
COMPANY_ROLE_DELETE_NAME="Seasonal Contractor" \
COMPANY_ROLE_DELETE_REPLACEMENT="Viewer" \
uv run -m examples.company_user_roles_demo --login --delete-role
```

Show default role names (no API call needed):

```
uv run -m examples.company_user_roles_demo --default-roles
```

Available flags

- --login
- --list-roles
- --create-role
- --update-role
- --delete-role
- --default-roles
- --all (runs `--login --list-roles`)

Client methods covered

- user_login (fetches the JWT used by the role client)
- get_company_roles
- create_company_role
- update_company_role
- delete_company_role
- list_default_roles (local helper for built-in roles)

Environment variables

Login:
- USER_EMAIL
- USER_PASSWORD

Shared:
- COMPANY_ROLE_COMPANY_ID (required for API actions)

List roles (optional filters):
- COMPANY_ROLE_QUERY_LIMIT
- COMPANY_ROLE_QUERY_PAGE
- COMPANY_ROLE_QUERY_NAME
- COMPANY_ROLE_QUERY_DESCRIPTION

Create role:
- COMPANY_ROLE_CREATE_NAME
- COMPANY_ROLE_CREATE_DESCRIPTION (optional)

Update role:
- COMPANY_ROLE_UPDATE_ROLE_NAME
- COMPANY_ROLE_UPDATE_NAME (optional)
- COMPANY_ROLE_UPDATE_DESCRIPTION (optional)

Delete role:
- COMPANY_ROLE_DELETE_NAME
- COMPANY_ROLE_DELETE_REPLACEMENT

Notes

- All role operations except `--default-roles` require logging in first.
- The role client is instantiated only after login so the Authorization header
  always carries the fresh token.
- Server-side validation may reject special-use domains (e.g., `.test`,
  `.example`); use realistic data for company roles to avoid failures.
