from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class BorgArchives(Resource):
    def create_borg_archive(
        self,
        request: models.BorgArchiveCreateRequest,
        *,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/borg-archives",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_borg_archives(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.BorgArchivesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.BorgArchiveResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/borg-archives",
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

        return DtoResponse.from_response(local_response, models.BorgArchiveResource)

    def read_borg_archive(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.BorgArchiveResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/borg-archives/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.BorgArchiveResource)

    def get_borg_archive_metadata(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.BorgArchiveMetadata]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/borg-archives/{id_}/metadata",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.BorgArchiveMetadata)

    def restore_borg_archive(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
        path: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/borg-archives/{id_}/restore",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "path": path,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_borg_archive_contents(
        self,
        *,
        id_: int,
        path: Optional[str] = None,
    ) -> DtoResponse[list[models.BorgArchiveContent]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/borg-archives/{id_}/contents",
            data=None,
            query_parameters={
                "path": path,
            },
        )

        return DtoResponse.from_response(local_response, models.BorgArchiveContent)

    def download_borg_archive(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
        path: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/borg-archives/{id_}/download",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "path": path,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
