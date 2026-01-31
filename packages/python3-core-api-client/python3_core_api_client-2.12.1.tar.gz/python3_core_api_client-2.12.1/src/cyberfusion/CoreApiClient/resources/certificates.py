from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Certificates(Resource):
    def create_certificate(
        self,
        request: models.CertificateCreateRequest,
    ) -> DtoResponse[models.CertificateResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/certificates",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CertificateResource)

    def list_certificates(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.CertificatesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.CertificateResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/certificates",
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

        return DtoResponse.from_response(local_response, models.CertificateResource)

    def read_certificate(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.CertificateResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/certificates/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.CertificateResource)

    def delete_certificate(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/certificates/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
