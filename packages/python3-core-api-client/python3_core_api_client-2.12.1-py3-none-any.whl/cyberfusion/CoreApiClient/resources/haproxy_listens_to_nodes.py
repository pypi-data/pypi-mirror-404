from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class HAProxyListensToNodes(Resource):
    def create_haproxy_listen_to_node(
        self,
        request: models.HAProxyListenToNodeCreateRequest,
    ) -> DtoResponse[models.HAProxyListenToNodeResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/haproxy-listens-to-nodes",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.HAProxyListenToNodeResource
        )

    def list_haproxy_listens_to_nodes(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.HaproxyListensToNodesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.HAProxyListenToNodeResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/haproxy-listens-to-nodes",
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
            local_response, models.HAProxyListenToNodeResource
        )

    def read_haproxy_listen_to_node(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.HAProxyListenToNodeResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/haproxy-listens-to-nodes/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.HAProxyListenToNodeResource
        )

    def delete_haproxy_listen_to_node(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/haproxy-listens-to-nodes/{id_}",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
