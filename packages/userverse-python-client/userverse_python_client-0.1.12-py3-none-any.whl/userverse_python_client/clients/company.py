from typing import Optional
from pydantic import EmailStr

from sverse_generic_models.generic_response import GenericResponseModel
from sverse_generic_models.generic_pagination import PaginatedResponse
from userverse_models.company.company import (
    CompanyReadModel,
    CompanyUpdateModel,
    CompanyCreateModel,
    CompanyQueryParamsModel,
)
from ..http_client_base import BaseClient


class UverseCompanyClient(BaseClient):
    # This must have client.set_access_token() called after user login
    # so access token is required on __init__

    def __init__(self, base_url, access_token, timeout=30):
        super().__init__(base_url, access_token, timeout)

    def get_user_companies(
        self,
        query_params: CompanyQueryParamsModel = CompanyQueryParamsModel(),
    ) -> GenericResponseModel[PaginatedResponse[CompanyReadModel]]:
        """Fetches a list of companies associated with the logged-in user."""
        params = query_params.model_dump(exclude_none=True)

        response = self._request("GET", "/user/companies", params=params)

        if not response or "data" not in response:
            raise ValueError("Invalid response from get user companies endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected company pagination data to be a dict, got {type(data)}"
            )

        return GenericResponseModel[PaginatedResponse[CompanyReadModel]].model_validate(
            response
        )

    def get_company_by_id_or_email(
        self,
        company_id: Optional[int] = None,
        email: Optional[EmailStr] = None,
    ) -> GenericResponseModel[CompanyReadModel]:
        """Fetches a company by its ID or email."""
        params = None
        if company_id is not None:
            params = {"company_id": company_id}
        elif email is not None:
            params = {"email": email}
        else:
            raise ValueError("Either company_id or email must be provided")

        path = self._build_path_with_query("/company", params)
        response = self._request("GET", path)

        if not response or "data" not in response:
            raise ValueError("Invalid response from get company endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected company data to be a dict, got {type(data)}")

        return GenericResponseModel[CompanyReadModel].model_validate(response)

    def update_company(
        self,
        company_id: int,
        company_update: CompanyUpdateModel,
    ) -> GenericResponseModel[CompanyReadModel]:
        """Updates an existing company with the provided data, returns the updated company model."""
        response = self._request(
            "PATCH",
            f"/company/{company_id}",
            json=company_update.model_dump(exclude_none=True),
        )

        if not response or "data" not in response:
            raise ValueError("Invalid response from update company endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected company data to be a dict, got {type(data)}")

        return GenericResponseModel[CompanyReadModel].model_validate(response)

    def create_company(
        self,
        company_data: CompanyCreateModel,
    ) -> GenericResponseModel[CompanyReadModel]:
        """Creates a new company with the provided data, returns the company model."""
        response = self._request(
            "POST", "/company", json=company_data.model_dump(exclude_none=True)
        )

        if not response or "data" not in response:
            raise ValueError("Invalid response from create company endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected company data to be a dict, got {type(data)}")

        return GenericResponseModel[CompanyReadModel].model_validate(response)
