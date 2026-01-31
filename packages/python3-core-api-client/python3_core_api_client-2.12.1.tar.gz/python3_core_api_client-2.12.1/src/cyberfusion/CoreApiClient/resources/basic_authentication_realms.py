from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class BasicAuthenticationRealms(Resource):
    def create_basic_authentication_realm(
        self,
        request: models.BasicAuthenticationRealmCreateRequest,
    ) -> DtoResponse[models.BasicAuthenticationRealmResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/basic-authentication-realms",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.BasicAuthenticationRealmResource
        )

    def list_basic_authentication_realms(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.BasicAuthenticationRealmsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.BasicAuthenticationRealmResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/basic-authentication-realms",
            data=None,
            query_parameters={
                "page": page,
                "per_page": per_page,
            }
            | (
                include_filters.model_dump(exclude_unset=True)
                if include_filters
                else {}
            )
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.BasicAuthenticationRealmResource
        )

    def read_basic_authentication_realm(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.BasicAuthenticationRealmResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/basic-authentication-realms/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response,
            models.BasicAuthenticationRealmResource,
        )

    def update_basic_authentication_realm(
        self,
        request: models.BasicAuthenticationRealmUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.BasicAuthenticationRealmResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/basic-authentication-realms/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.BasicAuthenticationRealmResource
        )

    def delete_basic_authentication_realm(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/basic-authentication-realms/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
