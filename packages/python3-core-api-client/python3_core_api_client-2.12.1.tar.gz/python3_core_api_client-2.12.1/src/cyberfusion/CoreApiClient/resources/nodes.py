from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.models import NodeGroupEnum


class Nodes(Resource):
    def create_nodes(
        self,
        request: models.NodeCreateRequest,
        *,
        callback_url: Optional[str] = None,
        amount: int = 1,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/nodes",
            data=request.model_dump(exclude_unset=True),
            query_parameters={"callback_url": callback_url, "amount": amount},
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_nodes(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.NodesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.NodeResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/nodes",
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

        return DtoResponse.from_response(local_response, models.NodeResource)

    def get_node_products(
        self,
    ) -> DtoResponse[list[models.NodeProduct]]:
        local_response = self.api_connector.send_or_fail(
            "GET", "/api/v1/nodes/products", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.NodeProduct)

    def read_node(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.NodeResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/nodes/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.NodeResource)

    def update_node(
        self,
        request: models.NodeUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.NodeResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/nodes/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.NodeResource)

    def delete_node(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/nodes/{id_}",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def upgrade_downgrade_node(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
        product: str,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/nodes/{id_}/xgrade",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "product": product,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def add_node_groups(
        self,
        *,
        id_: int,
        groups: list[NodeGroupEnum],
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/nodes/{id_}/groups",
            data=groups,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
