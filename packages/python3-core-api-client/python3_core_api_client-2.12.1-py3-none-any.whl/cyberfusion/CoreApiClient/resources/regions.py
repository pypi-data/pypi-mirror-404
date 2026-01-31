from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Regions(Resource):
    def list_regions(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.RegionsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.RegionResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/regions",
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

        return DtoResponse.from_response(local_response, models.RegionResource)
