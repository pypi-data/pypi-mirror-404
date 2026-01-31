from cyberfusion.CoreApiClient import models
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class URLRedirects(Resource):
    def create_url_redirect(
        self,
        request: models.URLRedirectCreateRequest,
    ) -> DtoResponse[models.URLRedirectResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/url-redirects",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.URLRedirectResource)

    def list_url_redirects(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.UrlRedirectsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.URLRedirectResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/url-redirects",
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

        return DtoResponse.from_response(local_response, models.URLRedirectResource)

    def read_url_redirect(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.URLRedirectResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/url-redirects/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.URLRedirectResource)

    def update_url_redirect(
        self,
        request: models.URLRedirectUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.URLRedirectResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/url-redirects/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.URLRedirectResource)

    def delete_url_redirect(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/url-redirects/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
