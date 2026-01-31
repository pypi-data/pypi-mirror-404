from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class N8nInstances(Resource):
    def create_n8n_instance(
        self,
        request: models.N8nInstanceCreateRequest,
    ) -> DtoResponse[models.N8nInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/n8n-instances",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.N8nInstanceResource)

    def list_n8n_instances(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.N8nInstancesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.N8nInstanceResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/n8n-instances",
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

        return DtoResponse.from_response(local_response, models.N8nInstanceResource)

    def read_n8n_instance(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.N8nInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/n8n-instances/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.N8nInstanceResource)

    def update_n8n_instance(
        self,
        request: models.N8nInstanceUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.N8nInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/n8n-instances/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.N8nInstanceResource)

    def delete_n8n_instance(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/n8n-instances/{id_}",
            data=None,
            query_parameters={
                "delete_on_cluster": delete_on_cluster,
            },
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
