from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class MailHostnames(Resource):
    def create_mail_hostname(
        self,
        request: models.MailHostnameCreateRequest,
    ) -> DtoResponse[models.MailHostnameResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/mail-hostnames",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailHostnameResource)

    def list_mail_hostnames(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.MailHostnamesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.MailHostnameResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/mail-hostnames",
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

        return DtoResponse.from_response(local_response, models.MailHostnameResource)

    def read_mail_hostname(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.MailHostnameResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/mail-hostnames/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.MailHostnameResource)

    def update_mail_hostname(
        self,
        request: models.MailHostnameUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.MailHostnameResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/mail-hostnames/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailHostnameResource)

    def delete_mail_hostname(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/mail-hostnames/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
