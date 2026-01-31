from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class PassengerApps(Resource):
    def create_nodejs_passenger_app(
        self,
        request: models.PassengerAppCreateNodeJSRequest,
    ) -> DtoResponse[models.PassengerAppResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/passenger-apps/nodejs",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.PassengerAppResource)

    def list_passenger_apps(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.PassengerAppsSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.PassengerAppResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/passenger-apps",
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

        return DtoResponse.from_response(local_response, models.PassengerAppResource)

    def read_passenger_app(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.PassengerAppResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/passenger-apps/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.PassengerAppResource)

    def update_passenger_app(
        self,
        request: models.PassengerAppUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.PassengerAppResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/passenger-apps/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.PassengerAppResource)

    def delete_passenger_app(
        self,
        *,
        id_: int,
        delete_on_cluster: Optional[bool] = None,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/passenger-apps/{id_}",
            data=None,
            query_parameters={"delete_on_cluster": delete_on_cluster},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def restart_passenger_app(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/passenger-apps/{id_}/restart",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
