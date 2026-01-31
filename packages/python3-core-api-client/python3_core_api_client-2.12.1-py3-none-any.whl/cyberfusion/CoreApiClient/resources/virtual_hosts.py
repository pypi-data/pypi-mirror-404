from cyberfusion.CoreApiClient import models
from typing import Optional, List

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class VirtualHosts(Resource):
    def create_virtual_host(
        self,
        request: models.VirtualHostCreateRequest,
    ) -> DtoResponse[models.VirtualHostResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/virtual-hosts",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.VirtualHostResource)

    def list_virtual_hosts(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.VirtualHostsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.VirtualHostResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/virtual-hosts",
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

        return DtoResponse.from_response(local_response, models.VirtualHostResource)

    def read_virtual_host(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.VirtualHostResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/virtual-hosts/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.VirtualHostResource)

    def update_virtual_host(
        self,
        request: models.VirtualHostUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.VirtualHostResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/virtual-hosts/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.VirtualHostResource)

    def delete_virtual_host(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/virtual-hosts/{id_}",
            data=None,
            query_parameters={
                "delete_on_cluster": delete_on_cluster,
            },
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def get_virtual_host_document_root(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.VirtualHostDocumentRoot]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/virtual-hosts/{id_}/document-root",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.VirtualHostDocumentRoot)

    def sync_document_roots_of_virtual_hosts(
        self,
        *,
        left_virtual_host_id: int,
        right_virtual_host_id: int,
        callback_url: Optional[str] = None,
        exclude_paths: Optional[List[str]] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/virtual-hosts/{left_virtual_host_id}/document-root/sync",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "right_virtual_host_id": right_virtual_host_id,
                "exclude_paths": exclude_paths,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_virtual_host_access_logs(
        self,
        *,
        id_: int,
        timestamp: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
    ) -> DtoResponse[list[models.VirtualHostAccessLogResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/virtual-hosts/{id_}/logs/access",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "page": page,
            },
        )

        return DtoResponse.from_response(
            local_response, models.VirtualHostAccessLogResource
        )

    def list_virtual_host_error_logs(
        self,
        *,
        id_: int,
        timestamp: Optional[str] = None,
        sort: Optional[str] = None,
        page: int = 1,
    ) -> DtoResponse[list[models.VirtualHostErrorLogResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/virtual-hosts/{id_}/logs/error",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "page": page,
            },
        )

        return DtoResponse.from_response(
            local_response, models.VirtualHostErrorLogResource
        )
