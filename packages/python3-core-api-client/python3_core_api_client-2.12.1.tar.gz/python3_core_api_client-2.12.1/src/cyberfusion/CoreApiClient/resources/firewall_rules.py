from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class FirewallRules(Resource):
    def create_firewall_rule(
        self,
        request: models.FirewallRuleCreateRequest,
    ) -> DtoResponse[models.FirewallRuleResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/firewall-rules",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.FirewallRuleResource)

    def list_firewall_rules(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.FirewallRulesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.FirewallRuleResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/firewall-rules",
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

        return DtoResponse.from_response(local_response, models.FirewallRuleResource)

    def read_firewall_rule(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.FirewallRuleResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/firewall-rules/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.FirewallRuleResource)

    def delete_firewall_rule(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/firewall-rules/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
