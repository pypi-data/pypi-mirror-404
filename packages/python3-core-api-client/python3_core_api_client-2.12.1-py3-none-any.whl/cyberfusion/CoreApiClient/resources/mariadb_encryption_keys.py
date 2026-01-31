from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class MariaDBEncryptionKeys(Resource):
    def create_mariadb_encryption_key(
        self,
        request: models.MariaDBEncryptionKeyCreateRequest,
    ) -> DtoResponse[models.MariaDBEncryptionKeyResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/mariadb-encryption-keys",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.MariaDBEncryptionKeyResource
        )

    def list_mariadb_encryption_keys(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.MariadbEncryptionKeysSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.MariaDBEncryptionKeyResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/mariadb-encryption-keys",
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
            local_response, models.MariaDBEncryptionKeyResource
        )

    def read_mariadb_encryption_key(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.MariaDBEncryptionKeyResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/mariadb-encryption-keys/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.MariaDBEncryptionKeyResource
        )
