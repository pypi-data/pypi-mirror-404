from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse


class TaskCollections(Resource):
    def list_task_collection_results(
        self,
        *,
        uuid: str,
    ) -> DtoResponse[list[models.TaskResult]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/task-collections/{uuid}/results",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.TaskResult)

    def retry_task_collection(
        self,
        *,
        uuid: str,
        callback_url: Optional[str] = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/task-collections/{uuid}/retry",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            }
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)
