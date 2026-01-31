from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class RootSSHKeys(Resource):
    def create_public_root_ssh_key(
        self,
        request: models.RootSSHKeyCreatePublicRequest,
    ) -> DtoResponse[models.RootSSHKeyResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/root-ssh-keys/public",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.RootSSHKeyResource)

    def create_private_root_ssh_key(
        self,
        request: models.RootSSHKeyCreatePrivateRequest,
    ) -> DtoResponse[models.RootSSHKeyResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/root-ssh-keys/private",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.RootSSHKeyResource)

    def list_root_ssh_keys(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.RootSshKeysSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.RootSSHKeyResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/root-ssh-keys",
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

        return DtoResponse.from_response(local_response, models.RootSSHKeyResource)

    def read_root_ssh_key(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.RootSSHKeyResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/root-ssh-keys/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.RootSSHKeyResource)

    def delete_root_ssh_key(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/root-ssh-keys/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
