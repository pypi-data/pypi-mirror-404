from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Daemons(Resource):
    def create_daemon(
        self,
        request: models.DaemonCreateRequest,
    ) -> DtoResponse[models.DaemonResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/daemons",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DaemonResource)

    def list_daemons(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.DaemonsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.DaemonResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/daemons",
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

        return DtoResponse.from_response(local_response, models.DaemonResource)

    def read_daemon(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.DaemonResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/daemons/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.DaemonResource)

    def update_daemon(
        self,
        request: models.DaemonUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.DaemonResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/daemons/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DaemonResource)

    def delete_daemon(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/daemons/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def restart_daemon(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/daemons/{id_}/restart",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_logs(
        self,
        *,
        daemon_id: int,
        timestamp: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
    ) -> DtoResponse[list[models.DaemonLogResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/daemons/{daemon_id}/logs",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "page": page,
            },
        )

        return DtoResponse.from_response(local_response, models.DaemonLogResource)
