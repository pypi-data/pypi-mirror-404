from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class CustomConfigs(Resource):
    def create_custom_config(
        self,
        request: models.CustomConfigCreateRequest,
    ) -> DtoResponse[models.CustomConfigResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/custom-configs",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CustomConfigResource)

    def list_custom_configs(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.CustomConfigsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.CustomConfigResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/custom-configs",
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

        return DtoResponse.from_response(local_response, models.CustomConfigResource)

    def read_custom_config(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.CustomConfigResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/custom-configs/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.CustomConfigResource)

    def update_custom_config(
        self,
        request: models.CustomConfigUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.CustomConfigResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/custom-configs/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CustomConfigResource)

    def delete_custom_config(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/custom-configs/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
