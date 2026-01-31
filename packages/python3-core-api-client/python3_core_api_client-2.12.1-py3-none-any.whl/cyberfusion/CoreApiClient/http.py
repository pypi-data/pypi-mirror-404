import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, TypeVar, Generic

from requests.structures import CaseInsensitiveDict

from cyberfusion.CoreApiClient.models import CoreApiModel

from requests.models import Response as RequestsResponse


ModelType = TypeVar("ModelType", bound=CoreApiModel)

DtoType = TypeVar("DtoType", CoreApiModel, list[CoreApiModel])


@dataclass
class Response:
    status_code: int
    body: str
    headers: CaseInsensitiveDict
    requests_response: RequestsResponse

    @property
    def failed(self) -> bool:
        return self.status_code >= HTTPStatus.BAD_REQUEST

    @property
    def json(self) -> Any:
        return json.loads(self.body)


@dataclass
class DtoResponse(Generic[DtoType], Response):
    dto: DtoType

    @classmethod
    def from_response(cls, response: Response, model: type[ModelType]) -> "DtoResponse":
        if isinstance(response.json, list):
            dto = [model.model_validate(object_) for object_ in response.json]
        else:
            dto = model.model_validate(response.json)

        return cls(
            status_code=response.status_code,
            body=response.body,
            headers=response.headers,
            requests_response=response.requests_response,
            dto=dto,
        )
