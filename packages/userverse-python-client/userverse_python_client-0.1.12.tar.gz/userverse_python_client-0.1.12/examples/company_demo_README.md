Company demo

`examples/company_demo.py` shows how to work with the company endpoints in
`UverseCompanyClient`. The script handles user authentication first (via
`UverseUserClient`) and then reuses that token for every company call.

Running the demo

Every action is toggled with a CLI flag and reads data from environment
variables. Missing required env vars cause that action to be skipped with a
message so you can run only the flow you need.

From the repo root:

```
uv run -m examples.company_demo --help
```

Common usage

Login and list user companies (most calls require a token):

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
uv run -m examples.company_demo --login --list-companies
```

Lookup a company by id (pass inline or rely on env fallback):

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
uv run -m examples.company_demo --login --get-company-by-id 123
```

Lookup a company by email:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
uv run -m examples.company_demo --login --get-company-by-email info@acmecorp.com
```

Create a company:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
COMPANY_CREATE_NAME="Acme Corp" COMPANY_CREATE_EMAIL="info@acmecorp.com" \
uv run -m examples.company_demo --login --create-company
```

Available flags

- --login
- --list-companies
- --get-company-by-id
- --get-company-by-email
- --create-company
- --update-company
- --all (runs `--login --list-companies`)

Client methods covered

- user_login (fetches the JWT used by the company client)
- get_user_companies
- get_company_by_id_or_email (ID)
- get_company_by_id_or_email (email)
- create_company
- update_company

Environment variables

Login:
- USER_EMAIL
- USER_PASSWORD

List companies (all optional filters):
- COMPANY_QUERY_LIMIT
- COMPANY_QUERY_PAGE
- COMPANY_QUERY_ROLE_NAME
- COMPANY_QUERY_NAME
- COMPANY_QUERY_DESCRIPTION
- COMPANY_QUERY_INDUSTRY
- COMPANY_QUERY_EMAIL

Get company by id (env fallback when CLI value omitted):
- COMPANY_LOOKUP_ID

Get company by email (env fallback when CLI value omitted):
- COMPANY_LOOKUP_EMAIL

Create company:
- COMPANY_CREATE_NAME
- COMPANY_CREATE_EMAIL
- COMPANY_CREATE_DESCRIPTION (optional)
- COMPANY_CREATE_INDUSTRY (optional)
- COMPANY_CREATE_PHONE_NUMBER (optional)
- COMPANY_CREATE_ADDRESS (optional)

Update company:
- COMPANY_UPDATE_ID
- COMPANY_UPDATE_NAME (optional)
- COMPANY_UPDATE_DESCRIPTION (optional)
- COMPANY_UPDATE_INDUSTRY (optional)
- COMPANY_UPDATE_PHONE_NUMBER (optional)
- COMPANY_UPDATE_ADDRESS (optional)

Notes

- All company actions require a logged-in user. Pass `--login` (or `--all`) and
  ensure `USER_EMAIL`/`USER_PASSWORD` are set.
- The script builds the `UverseCompanyClient` only after login succeeds so the
  Authorization header always carries the fresh token.
- Company-related endpoints validate email domains and reject [RFC 2606](https://datatracker.ietf.org/doc/html/rfc2606) special-use TLDs such as `.test`, `.example`, `.invalid`, or `.localhost`. Use a realistic domain like `info@acmecorp.com` in the examples above (or your own email) to avoid validation failures.
