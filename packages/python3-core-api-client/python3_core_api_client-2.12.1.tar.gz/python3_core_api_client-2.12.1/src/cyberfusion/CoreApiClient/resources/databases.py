from cyberfusion.CoreApiClient import models
from typing import Optional, List

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class Databases(Resource):
    def create_database(
        self,
        request: models.DatabaseCreateRequest,
    ) -> DtoResponse[models.DatabaseResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/databases",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DatabaseResource)

    def list_databases(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.DatabasesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.DatabaseResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/databases",
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

        return DtoResponse.from_response(local_response, models.DatabaseResource)

    def read_database(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.DatabaseResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/databases/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.DatabaseResource)

    def update_database(
        self,
        request: models.DatabaseUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.DatabaseResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/databases/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DatabaseResource)

    def delete_database(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/databases/{id_}",
            data=None,
            query_parameters={
                "delete_on_cluster": delete_on_cluster,
            },
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def compare_databases(
        self,
        *,
        left_database_id: int,
        right_database_id: int,
    ) -> DtoResponse[models.DatabaseComparison]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/databases/{left_database_id}/comparison",
            data=None,
            query_parameters={
                "right_database_id": right_database_id,
            },
        )

        return DtoResponse.from_response(local_response, models.DatabaseComparison)

    def sync_databases(
        self,
        *,
        left_database_id: int,
        right_database_id: int,
        callback_url: Optional[str] = None,
        exclude_tables_names: Optional[List[str]] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/databases/{left_database_id}/sync",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "right_database_id": right_database_id,
                "exclude_tables_names": exclude_tables_names,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_database_usages(
        self,
        *,
        id_: int,
        timestamp: str,
        time_unit: Optional[models.DatabaseUsageResource] = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.DatabaseUsageResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/databases/{id_}/usages",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "time_unit": time_unit,
            }
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.DatabaseUsageResource)
