from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class FPMPools(Resource):
    def create_fpm_pool(
        self,
        request: models.FPMPoolCreateRequest,
    ) -> DtoResponse[models.FPMPoolResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/fpm-pools",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FPMPoolResource)

    def list_fpm_pools(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.FpmPoolsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.FPMPoolResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/fpm-pools",
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

        return DtoResponse.from_response(local_response, models.FPMPoolResource)

    def read_fpm_pool(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.FPMPoolResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/fpm-pools/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.FPMPoolResource)

    def update_fpm_pool(
        self,
        request: models.FPMPoolUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.FPMPoolResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/fpm-pools/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FPMPoolResource)

    def delete_fpm_pool(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/fpm-pools/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def restart_fpm_pool(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/fpm-pools/{id_}/restart",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def reload_fpm_pool(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/fpm-pools/{id_}/reload",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def get_fpm_pool_status(
        self,
        *,
        id_: int,
    ) -> DtoResponse[list[models.FPMPoolNodeStatus]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/fpm-pools/{id_}/status",
            data=None,
        )

        return DtoResponse.from_response(local_response, models.FPMPoolNodeStatus)

    def update_fpm_pool_version(
        self,
        *,
        id_: int,
        version: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/fpm-pools/{id_}/update-version",
            data=None,
            query_parameters={
                "version": version,
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
