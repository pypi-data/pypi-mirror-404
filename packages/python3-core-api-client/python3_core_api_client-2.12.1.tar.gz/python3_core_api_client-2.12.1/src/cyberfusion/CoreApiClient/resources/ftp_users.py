from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class FTPUsers(Resource):
    def create_ftp_user(
        self,
        request: models.FTPUserCreateRequest,
    ) -> DtoResponse[models.FTPUserResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/ftp-users",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FTPUserResource)

    def list_ftp_users(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.FtpUsersSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.FTPUserResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/ftp-users",
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

        return DtoResponse.from_response(local_response, models.FTPUserResource)

    def read_ftp_user(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.FTPUserResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/ftp-users/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.FTPUserResource)

    def update_ftp_user(
        self,
        request: models.FTPUserUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.FTPUserResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/ftp-users/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FTPUserResource)

    def delete_ftp_user(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/ftp-users/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def create_temporary_ftp_user(
        self,
        request: models.TemporaryFTPUserCreateRequest,
    ) -> DtoResponse[models.TemporaryFTPUserResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/ftp-users/temporary",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.TemporaryFTPUserResource
        )
