from cyberfusion.CoreApiClient import models
from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class DomainRouters(Resource):
    def list_domain_routers(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.DomainRoutersSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.DomainRouterResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/domain-routers",
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

        return DtoResponse.from_response(local_response, models.DomainRouterResource)

    def update_domain_router(
        self,
        request: models.DomainRouterUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.DomainRouterResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/domain-routers/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DomainRouterResource)
