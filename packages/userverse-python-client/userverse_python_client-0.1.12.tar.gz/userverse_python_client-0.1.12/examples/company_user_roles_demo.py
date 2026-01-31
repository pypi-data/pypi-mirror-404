"""Demo script for managing company roles via userverse_python_client."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

# Allow running the example without installing the package first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from userverse_models.user.user import UserLoginModel  # noqa: E402
from userverse_models.company.roles import (  # noqa: E402
    RoleCreateModel,
    RoleUpdateModel,
    RoleDeleteModel,
    RoleQueryParamsModel,
)
from userverse_python_client import UverseUserClient  # noqa: E402
from userverse_python_client.clients.company_user_roles_management import (  # noqa: E402
    UverseCompanyUserRolesManagement,
)
from userverse_python_client.error_model import ClientErrorModel  # noqa: E402

BASE_URL = "https://apps.oxillium-api.co.za/userverse"
USE_ENV_VALUE = object()


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


def build_role_client(token: str) -> UverseCompanyUserRolesManagement:
    return UverseCompanyUserRolesManagement(base_url=BASE_URL, access_token=token)


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


def require_company_id() -> int:
    return require_int_env("COMPANY_ROLE_COMPANY_ID")


def build_role_query_params() -> RoleQueryParamsModel:
    params: dict[str, object] = {}

    limit = optional_int_env("COMPANY_ROLE_QUERY_LIMIT")
    if limit is not None:
        params["limit"] = limit

    page = optional_int_env("COMPANY_ROLE_QUERY_PAGE")
    if page is not None:
        params["page"] = page

    for field, env_name in [
        ("name", "COMPANY_ROLE_QUERY_NAME"),
        ("description", "COMPANY_ROLE_QUERY_DESCRIPTION"),
    ]:
        value = os.getenv(env_name)
        if value:
            params[field] = value

    return RoleQueryParamsModel(**params)


def list_roles(client: UverseCompanyUserRolesManagement) -> None:
    company_id = require_company_id()
    params = build_role_query_params()
    response = client.get_company_roles(company_id=company_id, query_params=params)
    log_response("List Roles", response)


def create_role(client: UverseCompanyUserRolesManagement) -> None:
    company_id = require_company_id()
    role = RoleCreateModel(
        name=require_env("COMPANY_ROLE_CREATE_NAME"),
        description=os.getenv("COMPANY_ROLE_CREATE_DESCRIPTION"),
    )
    response = client.create_company_role(company_id=company_id, role_data=role)
    log_response("Create Role", response)


def update_role(client: UverseCompanyUserRolesManagement) -> None:
    company_id = require_company_id()
    role_name = require_env("COMPANY_ROLE_UPDATE_ROLE_NAME")
    role_update = RoleUpdateModel(
        name=os.getenv("COMPANY_ROLE_UPDATE_NAME"),
        description=os.getenv("COMPANY_ROLE_UPDATE_DESCRIPTION"),
    )
    if not role_update.model_dump(exclude_none=True):
        raise ValueError("Provide at least one COMPANY_ROLE_UPDATE_* value to update.")
    response = client.update_company_role(
        company_id=company_id,
        role_name=role_name,
        role_data=role_update,
    )
    log_response("Update Role", response)


def delete_role(client: UverseCompanyUserRolesManagement) -> None:
    company_id = require_company_id()
    delete_model = RoleDeleteModel(
        role_name_to_delete=require_env("COMPANY_ROLE_DELETE_NAME"),
        replacement_role_name=require_env("COMPANY_ROLE_DELETE_REPLACEMENT"),
    )
    response = client.delete_company_role(
        company_id=company_id,
        role_delete_data=delete_model,
    )
    log_response("Delete Role", response)


def show_default_roles(_: UverseCompanyUserRolesManagement) -> None:
    roles = UverseCompanyUserRolesManagement.list_default_roles()
    print("Default Roles:", ", ".join(roles))


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
    parser = argparse.ArgumentParser(description="Company role management demo")
    parser.add_argument("--login", action="store_true", help="Login user to get token")
    parser.add_argument(
        "--list-roles",
        action="store_true",
        help="List roles linked to COMPANY_ROLE_COMPANY_ID",
    )
    parser.add_argument(
        "--create-role",
        action="store_true",
        help="Create a new role for COMPANY_ROLE_COMPANY_ID",
    )
    parser.add_argument(
        "--update-role",
        action="store_true",
        help="Update a role for COMPANY_ROLE_COMPANY_ID",
    )
    parser.add_argument(
        "--delete-role",
        action="store_true",
        help="Delete a role from COMPANY_ROLE_COMPANY_ID",
    )
    parser.add_argument(
        "--default-roles",
        action="store_true",
        help="Print the built-in default role names",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run login + list roles (requires env vars)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user_client = build_user_client()

    if args.all:
        args.login = True
        args.list_roles = True

    access_token: Optional[str] = None
    role_client: Optional[UverseCompanyUserRolesManagement] = None
    logged_in = False

    def get_role_client() -> UverseCompanyUserRolesManagement:
        nonlocal role_client, access_token, logged_in
        if not logged_in or not access_token:
            raise ValueError("Login is required before making company role calls.")
        if role_client is None:
            role_client = build_role_client(access_token)
        return role_client

    actions = [
        ("Login", args.login, login_user, lambda: user_client, False),
        ("List Roles", args.list_roles, list_roles, get_role_client, True),
        ("Create Role", args.create_role, create_role, get_role_client, True),
        ("Update Role", args.update_role, update_role, get_role_client, True),
        ("Delete Role", args.delete_role, delete_role, get_role_client, True),
        (
            "Default Roles",
            args.default_roles,
            show_default_roles,
            get_role_client,
            False,
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
                role_client = None
            else:
                print(f"{name} skipped: missing --login for JWT-protected call")
                continue

        success, result = run_action(name, fn, client_provider)
        if name == "Login" and success:
            logged_in = True
            access_token = result
            role_client = None


if __name__ == "__main__":  # pragma: no cover
    # run with uv: uv run -m examples.company_user_roles_demo --login --list-roles
    main()
