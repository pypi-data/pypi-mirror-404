Company user management demo

`examples/company_user_management_demo.py` demonstrates how to work with the
company user endpoints exposed by `UverseCompanyUserManagementClient`. The script
authenticates a user first (via `UverseUserClient`) and then uses the returned
token for every company user request.

Running the demo

Every action is toggled with a CLI flag and reads its data from environment
variables. Missing required env vars cause that action to be skipped with a
message so you can focus on a single flow at a time.

From the repo root:

```
uv run -m examples.company_user_management_demo --help
```

Common usage

Login and list company users:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_USER_COMPANY_ID=123 \
uv run -m examples.company_user_management_demo --login --list-users
```

Add a user to a company:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_USER_COMPANY_ID=123 COMPANY_USER_ADD_USER_ID=456 \
COMPANY_USER_ADD_ROLE_NAME="admin" \
uv run -m examples.company_user_management_demo --login --add-user
```

Delete a user from a company:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_USER_COMPANY_ID=123 COMPANY_USER_DELETE_USER_ID=456 \
uv run -m examples.company_user_management_demo --login --delete-user
```

Available flags

- --login
- --list-users
- --add-user
- --delete-user
- --all (runs `--login --list-users`)

Client methods covered

- user_login (fetches the JWT used by the company user client)
- list_company_users
- add_user_to_company
- delete_user_from_company

Environment variables

Login:
- USER_EMAIL
- USER_PASSWORD

Shared:
- COMPANY_USER_COMPANY_ID (required for every company user action)

List users (optional filters):
- COMPANY_USER_QUERY_LIMIT
- COMPANY_USER_QUERY_PAGE
- COMPANY_USER_QUERY_ROLE_NAME
- COMPANY_USER_QUERY_EMAIL

Add user:
- COMPANY_USER_ADD_USER_ID
- COMPANY_USER_ADD_ROLE_NAME (optional)

Delete user:
- COMPANY_USER_DELETE_USER_ID

Notes

- All company user actions require a logged-in user. Pass `--login` (or `--all`)
  and ensure the login env vars are set.
- The script builds the `UverseCompanyUserManagementClient` only after login
  succeeds so the Authorization header always uses the latest access token.
- Company user endpoints expect real domains/emails; avoid `.test`, `.example`,
  `.invalid`, or `.localhost` to prevent validation failures.
