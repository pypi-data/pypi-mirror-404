from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class MailAccounts(Resource):
    def create_mail_account(
        self,
        request: models.MailAccountCreateRequest,
    ) -> DtoResponse[models.MailAccountResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/mail-accounts",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailAccountResource)

    def list_mail_accounts(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.MailAccountsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.MailAccountResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/mail-accounts",
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

        return DtoResponse.from_response(local_response, models.MailAccountResource)

    def read_mail_account(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.MailAccountResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/mail-accounts/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.MailAccountResource)

    def update_mail_account(
        self,
        request: models.MailAccountUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.MailAccountResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/mail-accounts/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.MailAccountResource)

    def delete_mail_account(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/mail-accounts/{id_}",
            data=None,
            query_parameters={
                "delete_on_cluster": delete_on_cluster,
            },
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def list_mail_account_usages(
        self,
        *,
        id_: int,
        timestamp: str,
        time_unit: Optional[models.MailAccountUsageResource] = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.MailAccountUsageResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/mail-accounts/{id_}/usages",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "time_unit": time_unit,
            }
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.MailAccountUsageResource
        )
