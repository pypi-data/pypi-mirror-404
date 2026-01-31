from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Customers(Resource):
    def list_customers(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.CustomersSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.CustomerResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/customers",
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

        return DtoResponse.from_response(local_response, models.CustomerResource)

    def read_customer(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.CustomerResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/customers/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.CustomerResource)

    def list_ip_addresses_for_customer(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.CustomerIPAddresses]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/customers/{id_}/ip-addresses",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CustomerIPAddresses)

    def create_ip_address_for_customer(
        self,
        request: models.CustomerIPAddressCreateRequest,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/customers/{id_}/ip-addresses",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def delete_ip_address_for_customer(
        self,
        *,
        id_: int,
        ip_address: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/customers/{id_}/ip-addresses/{ip_address}",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def get_ip_addresses_products_for_customers(
        self,
    ) -> DtoResponse[list[models.IPAddressProduct]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/customers/ip-addresses/products",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.IPAddressProduct)
