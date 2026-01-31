from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class DatabaseUserGrants(Resource):
    def create_database_user_grant(
        self,
        request: models.DatabaseUserGrantCreateRequest,
    ) -> DtoResponse[models.DatabaseUserGrantResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/database-user-grants",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.DatabaseUserGrantResource
        )

    def list_database_user_grants(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.DatabaseUserGrantsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.DatabaseUserGrantResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/database-user-grants",
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

        return DtoResponse.from_response(
            local_response, models.DatabaseUserGrantResource
        )

    def delete_database_user_grant(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/database-user-grants/{id_}",
            data=None,
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
