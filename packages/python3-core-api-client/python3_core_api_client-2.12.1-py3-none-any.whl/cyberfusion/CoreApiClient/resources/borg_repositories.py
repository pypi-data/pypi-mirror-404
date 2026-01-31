from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class BorgRepositories(Resource):
    def create_borg_repository(
        self,
        request: models.BorgRepositoryCreateRequest,
    ) -> DtoResponse[models.BorgRepositoryResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/borg-repositories",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.BorgRepositoryResource)

    def list_borg_repositories(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.BorgRepositoriesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.BorgRepositoryResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/borg-repositories",
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

        return DtoResponse.from_response(local_response, models.BorgRepositoryResource)

    def read_borg_repository(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.BorgRepositoryResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/borg-repositories/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.BorgRepositoryResource)

    def update_borg_repository(
        self,
        request: models.BorgRepositoryUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.BorgRepositoryResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/borg-repositories/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.BorgRepositoryResource)

    def delete_borg_repository(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/borg-repositories/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def prune_borg_repository(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/borg-repositories/{id_}/prune",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def check_borg_repository(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/borg-repositories/{id_}/check",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def get_borg_archives_metadata(
        self,
        *,
        id_: int,
    ) -> DtoResponse[list[models.BorgArchiveMetadata]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/borg-repositories/{id_}/archives-metadata",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.BorgArchiveMetadata)
