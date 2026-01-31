from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class MailDomains(Resource):
    def create_mail_domain(
        self,
        request: models.MailDomainCreateRequest,
    ) -> DtoResponse[models.MailDomainResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/mail-domains",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailDomainResource)

    def list_mail_domains(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.MailDomainsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.MailDomainResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/mail-domains",
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

        return DtoResponse.from_response(local_response, models.MailDomainResource)

    def read_mail_domain(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.MailDomainResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/mail-domains/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.MailDomainResource)

    def update_mail_domain(
        self,
        request: models.MailDomainUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.MailDomainResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/mail-domains/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailDomainResource)

    def delete_mail_domain(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/mail-domains/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
