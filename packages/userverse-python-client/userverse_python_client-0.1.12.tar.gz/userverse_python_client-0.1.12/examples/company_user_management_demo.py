"""Demo script for managing company users through the userverse Python client."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

# Allow running the example without installing the package first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from userverse_models.user.user import UserLoginModel, UserQueryParams  # noqa: E402
from userverse_models.company.user import CompanyUserAddModel  # noqa: E402
from userverse_python_client import UverseUserClient  # noqa: E402
from userverse_python_client.clients.company_user_management import (  # noqa: E402
    UverseCompanyUserManagementClient,
)
from userverse_python_client.error_model import ClientErrorModel  # noqa: E402

BASE_URL = "https://apps.oxillium-api.co.za/userverse"


ClientProvider = Callable[[], Any]
ActionFunction = Callable[[Any], Any]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def require_int_env(name: str) -> int:
    raw_value = require_env(name)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got '{raw_value}'") from exc


def optional_int_env(name: str) -> Optional[int]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return None
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got '{raw_value}'") from exc


def build_user_client() -> UverseUserClient:
    return UverseUserClient(base_url=BASE_URL)


def build_company_user_client(token: str) -> UverseCompanyUserManagementClient:
    return UverseCompanyUserManagementClient(base_url=BASE_URL, access_token=token)


def log_response(label: str, response: Any) -> None:
    print(f"{label} Response:", response)
    dump_method = getattr(response, "model_dump", None)
    if callable(dump_method):
        print(f"{label} Response (dict):")
        print(json.dumps(dump_method(), indent=2, default=str))


def login_user(client: UverseUserClient) -> str:
    login_model = UserLoginModel(
        email=require_env("USER_EMAIL"),
        password=require_env("USER_PASSWORD"),
    )
    response = client.user_login(login_model)
    client.set_access_token(response.data.access_token)
    log_response("Login", response)
    return response.data.access_token


def build_user_query_params() -> UserQueryParams:
    params: dict[str, object] = {}

    limit = optional_int_env("COMPANY_USER_QUERY_LIMIT")
    if limit is not None:
        params["limit"] = limit

    page = optional_int_env("COMPANY_USER_QUERY_PAGE")
    if page is not None:
        params["page"] = page

    for field, env_name in [
        ("role_name", "COMPANY_USER_QUERY_ROLE_NAME"),
        ("email", "COMPANY_USER_QUERY_EMAIL"),
    ]:
        value = os.getenv(env_name)
        if value:
            params[field] = value

    return UserQueryParams(**params)


def require_company_id() -> int:
    return require_int_env("COMPANY_USER_COMPANY_ID")


def list_company_users(client: UverseCompanyUserManagementClient) -> None:
    company_id = require_company_id()
    params = build_user_query_params()
    response = client.list_company_users(company_id=company_id, query_params=params)
    log_response("List Company Users", response)


def add_company_user(client: UverseCompanyUserManagementClient) -> None:
    company_id = require_company_id()
    user_id = require_int_env("COMPANY_USER_ADD_USER_ID")
    role_name = os.getenv("COMPANY_USER_ADD_ROLE_NAME")
    add_model = CompanyUserAddModel(user_id=user_id, role_name=role_name)
    response = client.add_user_to_company(company_id=company_id, user_data=add_model)
    log_response("Add Company User", response)


def delete_company_user(client: UverseCompanyUserManagementClient) -> None:
    company_id = require_company_id()
    user_id = require_int_env("COMPANY_USER_DELETE_USER_ID")
    response = client.delete_user_from_company(company_id=company_id, user_id=user_id)
    log_response("Delete Company User", response)


def run_action(
    action_name: str,
    fn: ActionFunction,
    client_provider: ClientProvider,
) -> Tuple[bool, Any]:
    try:
        client = client_provider()
        result = fn(client)
        return True, result
    except ClientErrorModel as exc:
        detail = exc.payload.detail
        print(f"{action_name} failed ({exc.status_code}): {detail.message}")
        print(f"Error details: {detail.error}")
    except ValueError as exc:
        print(f"{action_name} skipped: {exc}")
    return False, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Company user management demo client")
    parser.add_argument("--login", action="store_true", help="Login user to get token")
    parser.add_argument(
        "--list-users",
        action="store_true",
        help="List users linked to COMPANY_USER_COMPANY_ID",
    )
    parser.add_argument(
        "--add-user",
        action="store_true",
        help="Add a user to COMPANY_USER_COMPANY_ID",
    )
    parser.add_argument(
        "--delete-user",
        action="store_true",
        help="Delete a user from COMPANY_USER_COMPANY_ID",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run login + list users flow",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user_client = build_user_client()

    if args.all:
        args.login = True
        args.list_users = True

    access_token: Optional[str] = None
    company_user_client: Optional[UverseCompanyUserManagementClient] = None
    logged_in = False

    def get_company_user_client() -> UverseCompanyUserManagementClient:
        nonlocal company_user_client, access_token, logged_in
        if not logged_in or not access_token:
            raise ValueError("Login is required before making company user calls.")
        if company_user_client is None:
            company_user_client = build_company_user_client(access_token)
        return company_user_client

    actions = [
        ("Login", args.login, login_user, lambda: user_client, False),
        (
            "List Company Users",
            args.list_users,
            list_company_users,
            get_company_user_client,
            True,
        ),
        (
            "Add Company User",
            args.add_user,
            add_company_user,
            get_company_user_client,
            True,
        ),
        (
            "Delete Company User",
            args.delete_user,
            delete_company_user,
            get_company_user_client,
            True,
        ),
    ]

    if not any(flag for _, flag, _, _, _ in actions):
        print("No actions selected. Try --help for available options.")
        return

    for name, enabled, fn, client_provider, needs_token in actions:
        if not enabled:
            continue
        if needs_token and not logged_in:
            if args.login:
                success, token = run_action("Login", login_user, lambda: user_client)
                if not success:
                    continue
                logged_in = True
                access_token = token
                company_user_client = None
            else:
                print(f"{name} skipped: missing --login for JWT-protected call")
                continue

        success, result = run_action(name, fn, client_provider)
        if name == "Login" and success:
            logged_in = True
            access_token = result
            company_user_client = None


if __name__ == "__main__":  # pragma: no cover
    # run with uv: uv run -m examples.company_user_management_demo --login --list-users
    main()
