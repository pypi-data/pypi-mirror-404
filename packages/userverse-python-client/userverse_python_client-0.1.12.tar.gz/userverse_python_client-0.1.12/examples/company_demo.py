"""Demo script showing how to use the company client in userverse_python_client."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

# Allow running the example without installing the package first.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from userverse_models.user.user import UserLoginModel  # noqa: E402
from userverse_models.company.company import (  # noqa: E402
    CompanyCreateModel,
    CompanyUpdateModel,
    CompanyQueryParamsModel,
)
from userverse_python_client import UverseUserClient, UverseCompanyClient  # noqa: E402
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


def build_company_client(token: str) -> UverseCompanyClient:
    return UverseCompanyClient(base_url=BASE_URL, access_token=token)


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


def build_query_params() -> CompanyQueryParamsModel:
    params: dict[str, object] = {}

    limit = optional_int_env("COMPANY_QUERY_LIMIT")
    if limit is not None:
        params["limit"] = limit

    page = optional_int_env("COMPANY_QUERY_PAGE")
    if page is not None:
        params["page"] = page

    for field, env_name in [
        ("role_name", "COMPANY_QUERY_ROLE_NAME"),
        ("name", "COMPANY_QUERY_NAME"),
        ("description", "COMPANY_QUERY_DESCRIPTION"),
        ("industry", "COMPANY_QUERY_INDUSTRY"),
        ("email", "COMPANY_QUERY_EMAIL"),
    ]:
        value = os.getenv(env_name)
        if value:
            params[field] = value

    return CompanyQueryParamsModel(**params)


def list_user_companies(client: UverseCompanyClient) -> None:
    params = build_query_params()
    response = client.get_user_companies(params)
    log_response("List Companies", response)


def get_company_by_id(
    client: UverseCompanyClient, company_id_value: object = USE_ENV_VALUE
) -> None:
    if company_id_value is USE_ENV_VALUE:
        company_id = require_int_env("COMPANY_LOOKUP_ID")
    else:
        company_id = int(company_id_value)
    response = client.get_company_by_id_or_email(company_id=company_id)
    log_response("Company Lookup (ID)", response)


def get_company_by_email(
    client: UverseCompanyClient, email_value: object = USE_ENV_VALUE
) -> None:
    if email_value is USE_ENV_VALUE:
        email = require_env("COMPANY_LOOKUP_EMAIL")
    else:
        email = str(email_value)
    response = client.get_company_by_id_or_email(email=email)
    log_response("Company Lookup (Email)", response)


def create_company(client: UverseCompanyClient) -> None:
    company = CompanyCreateModel(
        name=require_env("COMPANY_CREATE_NAME"),
        email=require_env("COMPANY_CREATE_EMAIL"),
        description=os.getenv("COMPANY_CREATE_DESCRIPTION"),
        industry=os.getenv("COMPANY_CREATE_INDUSTRY"),
        phone_number=os.getenv("COMPANY_CREATE_PHONE_NUMBER"),
        address=os.getenv("COMPANY_CREATE_ADDRESS"),
    )
    response = client.create_company(company)
    log_response("Create Company", response)


def update_company(client: UverseCompanyClient) -> None:
    company_id = require_int_env("COMPANY_UPDATE_ID")
    company_update = CompanyUpdateModel(
        name=os.getenv("COMPANY_UPDATE_NAME"),
        description=os.getenv("COMPANY_UPDATE_DESCRIPTION"),
        industry=os.getenv("COMPANY_UPDATE_INDUSTRY"),
        phone_number=os.getenv("COMPANY_UPDATE_PHONE_NUMBER"),
        address=os.getenv("COMPANY_UPDATE_ADDRESS"),
    )
    if not company_update.model_dump(exclude_none=True):
        raise ValueError("Provide at least one COMPANY_UPDATE_* env var to update.")
    response = client.update_company(company_id, company_update)
    log_response("Update Company", response)


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
    parser = argparse.ArgumentParser(description="Userverse company demo")
    parser.add_argument("--login", action="store_true", help="Login user to get token")
    parser.add_argument(
        "--list-companies",
        action="store_true",
        help="List companies linked to the authenticated user",
    )
    parser.add_argument(
        "--get-company-by-id",
        metavar="COMPANY_ID",
        type=int,
        nargs="?",
        const=USE_ENV_VALUE,
        help=(
            "Fetch a company by ID. Provide the ID inline (e.g. --get-company-by-id 3) "
            "or omit the value to use COMPANY_LOOKUP_ID."
        ),
    )
    parser.add_argument(
        "--get-company-by-email",
        metavar="COMPANY_EMAIL",
        nargs="?",
        const=USE_ENV_VALUE,
        help=(
            "Fetch a company by email. Provide the email inline or omit the value to use "
            "COMPANY_LOOKUP_EMAIL."
        ),
    )
    parser.add_argument(
        "--create-company",
        action="store_true",
        help="Create a new company using COMPANY_CREATE_* env vars",
    )
    parser.add_argument(
        "--update-company",
        action="store_true",
        help="Update an existing company using COMPANY_UPDATE_* env vars",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run login + list companies (requires env vars)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user_client = build_user_client()

    if args.all:
        args.login = True
        args.list_companies = True

    access_token: Optional[str] = None
    company_client: Optional[UverseCompanyClient] = None
    logged_in = False

    def get_company_client() -> UverseCompanyClient:
        nonlocal company_client, access_token, logged_in
        if not logged_in or not access_token:
            raise ValueError("Login is required before making company API calls.")
        if company_client is None:
            company_client = build_company_client(access_token)
        return company_client

    actions = [
        ("Login", args.login, login_user, lambda: user_client, False),
        (
            "List Companies",
            args.list_companies,
            list_user_companies,
            get_company_client,
            True,
        ),
        (
            "Get Company (ID)",
            args.get_company_by_id is not None,
            lambda client, value=args.get_company_by_id: get_company_by_id(
                client, value
            ),
            get_company_client,
            True,
        ),
        (
            "Get Company (Email)",
            args.get_company_by_email is not None,
            lambda client, value=args.get_company_by_email: get_company_by_email(
                client, value
            ),
            get_company_client,
            True,
        ),
        (
            "Create Company",
            args.create_company,
            create_company,
            get_company_client,
            True,
        ),
        (
            "Update Company",
            args.update_company,
            update_company,
            get_company_client,
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
                company_client = None
            else:
                print(f"{name} skipped: missing --login for JWT-protected call")
                continue

        success, result = run_action(name, fn, client_provider)
        if name == "Login" and success:
            logged_in = True
            access_token = result
            company_client = None


if __name__ == "__main__":  # pragma: no cover
    # run with uv: uv run -m examples.company_demo --login --list-companies
    main()
