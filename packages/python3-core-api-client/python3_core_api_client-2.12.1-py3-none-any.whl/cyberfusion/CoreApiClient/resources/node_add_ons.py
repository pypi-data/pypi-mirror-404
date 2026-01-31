from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class NodeAddOns(Resource):
    def create_node_add_on(
        self,
        request: models.NodeAddOnCreateRequest,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/node-add-ons",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_node_add_ons(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.NodeAddOnsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.NodeAddOnResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/node-add-ons",
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

        return DtoResponse.from_response(local_response, models.NodeAddOnResource)

    def get_node_add_on_products(
        self,
    ) -> DtoResponse[list[models.NodeAddOnProduct]]:
        local_response = self.api_connector.send_or_fail(
            "GET", "/api/v1/node-add-ons/products", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.NodeAddOnProduct)

    def read_node_add_on(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.NodeAddOnResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/node-add-ons/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.NodeAddOnResource)

    def delete_node_add_on(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/node-add-ons/{id_}",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
