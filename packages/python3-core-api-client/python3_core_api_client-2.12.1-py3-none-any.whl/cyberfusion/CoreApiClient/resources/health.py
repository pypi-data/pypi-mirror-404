from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient.http import DtoResponse


class Health(Resource):
    def read_health(
        self,
    ) -> DtoResponse[models.HealthResource]:
        local_response = self.api_connector.send_or_fail(
            "GET", "/api/v1/health", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.HealthResource)
