from sverse_generic_models.generic_response import GenericResponseModel
from sverse_generic_models.generic_pagination import PaginatedResponse
from userverse_models.company.roles import (
    CompanyDefaultRoles,
    RoleCreateModel,
    RoleUpdateModel,
    RoleDeleteModel,
    RoleReadModel,
    RoleQueryParamsModel,
)

from ..http_client_base import BaseClient


class UverseCompanyUserRolesManagement(BaseClient):
    def __init__(self, base_url, access_token, timeout=30):
        super().__init__(base_url, access_token, timeout)

    @staticmethod
    def list_default_roles() -> list[str]:
        """Return the list of built-in company role names."""
        return [role.name_value for role in CompanyDefaultRoles]

    def get_company_roles(
        self,
        company_id: int,
        query_params: RoleQueryParamsModel = RoleQueryParamsModel(),
    ) -> GenericResponseModel[PaginatedResponse[RoleReadModel]]:
        """Fetches a list of roles associated with the company."""
        params = query_params.model_dump(exclude_none=True)

        response = self._request("GET", f"/company/{company_id}/roles", params=params)

        if not response or "data" not in response:
            raise ValueError("Invalid response from get company roles endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected role pagination data to be a dict, got {type(data)}"
            )

        return GenericResponseModel[PaginatedResponse[RoleReadModel]].model_validate(
            response
        )

    def create_company_role(
        self,
        company_id: int,
        role_data: RoleCreateModel,
    ) -> GenericResponseModel[RoleReadModel]:
        """Creates a new role for the specified company."""
        payload = role_data.model_dump(exclude_none=True)
        response = self._request(
            "POST",
            f"/company/{company_id}/roles",
            json=payload,
        )

        if not response or "data" not in response:
            raise ValueError("Invalid response from create company role endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected role data to be a dict, got {type(data)}")

        return GenericResponseModel[RoleReadModel].model_validate(response)

    def update_company_role(
        self,
        company_id: int,
        role_name: str,
        role_data: RoleUpdateModel,
    ) -> GenericResponseModel[RoleReadModel]:
        """Updates an existing role for the specified company."""
        payload = role_data.model_dump(exclude_none=True)
        response = self._request(
            "PUT",
            f"/company/{company_id}/roles/{role_name}",
            json=payload,
        )

        if not response or "data" not in response:
            raise ValueError("Invalid response from update company role endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected role data to be a dict, got {type(data)}")

        return GenericResponseModel[RoleReadModel].model_validate(response)

    def delete_company_role(
        self,
        company_id: int,
        role_delete_data: RoleDeleteModel,
    ) -> GenericResponseModel[None]:
        """Deletes a role from the specified company, replacing it with another role."""
        payload = role_delete_data.model_dump(exclude_none=True)
        response = self._request(
            "DELETE",
            f"/company/{company_id}/roles",
            json=payload,
        )

        if not response or "data" not in response:
            raise ValueError("Invalid response from delete company role endpoint")

        data = response.get("data", {})
        if not isinstance(data, dict):
            raise ValueError(f"Expected response data to be a dict, got {type(data)}")

        return GenericResponseModel[None].model_validate(response)
