from cyberfusion.CoreApiClient import models

from cyberfusion.CoreApiClient.interfaces import Resource
from cyberfusion.CoreApiClient.http import DtoResponse


class Login(Resource):
    def request_access_token(
        self,
        request: models.BodyLoginAccessToken,
    ) -> DtoResponse[models.TokenResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/login/access-token",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
            content_type="application/x-www-form-urlencoded",
        )

        return DtoResponse.from_response(local_response, models.TokenResource)

    def test_access_token(
        self,
    ) -> DtoResponse[models.APIUserInfo]:
        local_response = self.api_connector.send_or_fail(
            "POST", "/api/v1/login/test-token", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.APIUserInfo)
