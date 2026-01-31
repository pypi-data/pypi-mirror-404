from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class RedisInstances(Resource):
    def create_redis_instance(
        self,
        request: models.RedisInstanceCreateRequest,
    ) -> DtoResponse[models.RedisInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/redis-instances",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.RedisInstanceResource)

    def list_redis_instances(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.RedisInstancesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.RedisInstanceResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/redis-instances",
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

        return DtoResponse.from_response(local_response, models.RedisInstanceResource)

    def read_redis_instance(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.RedisInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/redis-instances/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.RedisInstanceResource)

    def update_redis_instance(
        self,
        request: models.RedisInstanceUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.RedisInstanceResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/redis-instances/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.RedisInstanceResource)

    def delete_redis_instance(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/redis-instances/{id_}",
            data=None,
            query_parameters={
                "delete_on_cluster": delete_on_cluster,
            },
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
