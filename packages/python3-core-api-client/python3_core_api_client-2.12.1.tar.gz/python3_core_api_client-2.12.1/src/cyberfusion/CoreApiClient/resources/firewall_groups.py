from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class FirewallGroups(Resource):
    def create_firewall_group(
        self,
        request: models.FirewallGroupCreateRequest,
    ) -> DtoResponse[models.FirewallGroupResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/firewall-groups",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FirewallGroupResource)

    def list_firewall_groups(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.FirewallGroupsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.FirewallGroupResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/firewall-groups",
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

        return DtoResponse.from_response(local_response, models.FirewallGroupResource)

    def read_firewall_group(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.FirewallGroupResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/firewall-groups/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.FirewallGroupResource)

    def update_firewall_group(
        self,
        request: models.FirewallGroupUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.FirewallGroupResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/firewall-groups/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FirewallGroupResource)

    def delete_firewall_group(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/firewall-groups/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
