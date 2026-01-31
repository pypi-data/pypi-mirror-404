from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Crons(Resource):
    def create_cron(
        self,
        request: models.CronCreateRequest,
    ) -> DtoResponse[models.CronResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/crons",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CronResource)

    def list_crons(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.CronsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.CronResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/crons",
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

        return DtoResponse.from_response(local_response, models.CronResource)

    def read_cron(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.CronResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/crons/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.CronResource)

    def update_cron(
        self,
        request: models.CronUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.CronResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/crons/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CronResource)

    def delete_cron(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/crons/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
