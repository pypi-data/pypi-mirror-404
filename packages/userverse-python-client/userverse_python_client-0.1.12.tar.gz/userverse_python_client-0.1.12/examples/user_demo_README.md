Examples

This folder contains runnable demos for the client library. The main script is
`user_demo.py`, which shows how to call the user endpoints with the
`UverseUserClient`.

Running the demo

The script is designed to turn features on/off using flags. Each action pulls
credentials or tokens from environment variables. If a required variable is
missing, that action is skipped with a message.

Run from the repo root:

```
uv run -m examples.user_demo --help
```

Common usage

Login and get the current user:

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
uv run -m examples.user_demo --login --get-user
```

Create a user (uses Basic Auth for the new user):

```
NEW_USER_EMAIL="new@example.com" NEW_USER_PASSWORD="secret" \
NEW_USER_FIRST_NAME="New" NEW_USER_LAST_NAME="User" \
uv run -m examples.user_demo --create-user
```

Update current user (requires login):

```
USER_EMAIL="you@example.com" USER_PASSWORD="secret" \
UPDATE_FIRST_NAME="Updated" UPDATE_LAST_NAME="Name" \
uv run -m examples.user_demo --login --update-user
```

Available flags

- --login
- --create-user
- --get-user
- --update-user
- --resend-verification
- --verify-user
- --request-password-reset
- --reset-password
- --all

Client methods covered

The demo exercises every public method on `UverseUserClient`:

- user_login (login, sets JWT)
- create_user (create user with Basic Auth)
- get_user (JWT required)
- update_user (JWT required)
- resend_verification_email (JWT required)
- verify_user (email verification token)
- request_password_reset (send reset email)
- reset_password_validate_otp (confirm reset with OTP + new password)

Environment variables

Login:
- USER_EMAIL
- USER_PASSWORD

Create user:
- NEW_USER_EMAIL
- NEW_USER_PASSWORD
- NEW_USER_FIRST_NAME (optional)
- NEW_USER_LAST_NAME (optional)
- NEW_USER_PHONE_NUMBER (optional)

Update user:
- UPDATE_FIRST_NAME (optional)
- UPDATE_LAST_NAME (optional)
- UPDATE_PHONE_NUMBER (optional)
- UPDATE_PASSWORD (optional)

Verify email:
- VERIFY_TOKEN

Password reset request:
- RESET_EMAIL

Password reset confirm:
- RESET_EMAIL
- RESET_NEW_PASSWORD
- RESET_OTP

Notes

- Actions marked "JWT required" need `--login` so the client has a token.
- `--verify-user` uses the `VERIFY_TOKEN` from the verification email.
- `--reset-password` calls `reset_password_validate_otp` with the email and new
  password (Basic Auth) plus the OTP code.
