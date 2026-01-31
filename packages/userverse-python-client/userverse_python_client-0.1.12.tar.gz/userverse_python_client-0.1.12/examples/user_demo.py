"""Small demo script showing how to use the userverse_python_client package."""

import argparse
import os
import sys
from pathlib import Path

# Allow running the example without installing the package first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from userverse_models.user.user import (  # noqa: E402
    UserLoginModel,
    UserUpdateModel,
    UserCreateModel,
)
from userverse_python_client import UverseUserClient  # noqa: E402
from userverse_python_client.error_model import ClientErrorModel  # noqa: E402

BASE_URL = "https://apps.oxillium-api.co.za/userverse"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def build_client() -> UverseUserClient:
    return UverseUserClient(base_url=BASE_URL)


def login_user(client: UverseUserClient) -> str:
    login_model = UserLoginModel(
        email=require_env("USER_EMAIL"),
        password=require_env("USER_PASSWORD"),
    )
    response = client.user_login(login_model)
    client.set_access_token(response.data.access_token)
    print("Login Response:", response)
    return response.data.access_token


def create_user(client: UverseUserClient) -> None:
    user_data = UserCreateModel(
        first_name=os.getenv("NEW_USER_FIRST_NAME"),
        last_name=os.getenv("NEW_USER_LAST_NAME"),
        phone_number=os.getenv("NEW_USER_PHONE_NUMBER"),
    )
    user_credentials = UserLoginModel(
        email=require_env("NEW_USER_EMAIL"),
        password=require_env("NEW_USER_PASSWORD"),
    )
    response = client.create_user(user_data, user_credentials)
    print("Create User Response:", response)


def get_user(client: UverseUserClient) -> None:
    response = client.get_user()
    print("Get User Response:", response)


def update_user(client: UverseUserClient) -> None:
    user_update = UserUpdateModel(
        first_name=os.getenv("UPDATE_FIRST_NAME"),
        last_name=os.getenv("UPDATE_LAST_NAME"),
        phone_number=os.getenv("UPDATE_PHONE_NUMBER"),
        password=os.getenv("UPDATE_PASSWORD"),
    )
    response = client.update_user(user_update)
    print("Update User Response:", response)


def resend_verification_email(client: UverseUserClient) -> None:
    response = client.resend_verification_email()
    print("Resend Verification Response:", response)


def verify_user(client: UverseUserClient) -> None:
    token = require_env("VERIFY_TOKEN")
    response = client.verify_user(token)
    print("Verify User Response:", response)


def request_password_reset(client: UverseUserClient) -> None:
    email = require_env("RESET_EMAIL")
    response = client.request_password_reset(email)
    print("Password Reset Request Response:", response)


def reset_password(client: UverseUserClient) -> None:
    user_credentials = UserLoginModel(
        email=require_env("RESET_EMAIL"),
        password=require_env("RESET_NEW_PASSWORD"),
    )
    one_time_pin = require_env("RESET_OTP")
    response = client.reset_password(user_credentials, one_time_pin)
    print("Password Reset Confirm Response:", response)


def run_action(action_name: str, fn, client: UverseUserClient) -> bool:
    try:
        fn(client)
        return True
    except ClientErrorModel as exc:
        detail = exc.payload.detail
        print(f"{action_name} failed ({exc.status_code}): {detail.message}")
        print(f"Error details: {detail.error}")
    except ValueError as exc:
        print(f"{action_name} skipped: {exc}")
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Userverse user demo")
    parser.add_argument(
        "--login", action="store_true", help="Login and set access token"
    )
    parser.add_argument("--create-user", action="store_true", help="Create a new user")
    parser.add_argument("--get-user", action="store_true", help="Fetch current user")
    parser.add_argument(
        "--update-user", action="store_true", help="Update current user"
    )
    parser.add_argument(
        "--resend-verification",
        action="store_true",
        help="Resend verification email",
    )
    parser.add_argument("--verify-user", action="store_true", help="Verify user email")
    parser.add_argument(
        "--request-password-reset",
        action="store_true",
        help="Request password reset email",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Confirm password reset with OTP",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run login + get-user + update-user (requires env vars)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()

    if args.all:
        args.login = True
        args.get_user = True
        args.update_user = True

    actions = [
        ("Login", args.login, login_user, False),
        ("Create User", args.create_user, create_user, False),
        ("Get User", args.get_user, get_user, True),
        ("Update User", args.update_user, update_user, True),
        (
            "Resend Verification",
            args.resend_verification,
            resend_verification_email,
            True,
        ),
        ("Verify User", args.verify_user, verify_user, False),
        (
            "Request Password Reset",
            args.request_password_reset,
            request_password_reset,
            False,
        ),
        ("Reset Password", args.reset_password, reset_password, False),
    ]

    if not any(flag for _, flag, _, _ in actions):
        print("No actions selected. Try --help for available options.")
        return

    logged_in = False
    for name, enabled, fn, needs_token in actions:
        if not enabled:
            continue
        if needs_token and not logged_in:
            if args.login:
                logged_in = run_action("Login", login_user, client)
            else:
                print(f"{name} skipped: missing --login for JWT-protected call")
                continue
        action_ok = run_action(name, fn, client)
        if name == "Login":
            logged_in = action_ok


if __name__ == "__main__":  # pragma: no cover
    # run with uv: uv run -m examples.user_demo --login --get-user
    main()
