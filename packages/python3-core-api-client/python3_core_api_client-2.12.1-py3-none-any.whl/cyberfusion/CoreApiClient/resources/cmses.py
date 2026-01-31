from cyberfusion.CoreApiClient import models
from typing import Optional, Union

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class CMSes(Resource):
    def create_cms(
        self,
        request: models.CMSCreateRequest,
    ) -> DtoResponse[models.CMSResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/cmses",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CMSResource)

    def list_cmses(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.CmsesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.CMSResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/cmses",
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

        return DtoResponse.from_response(local_response, models.CMSResource)

    def read_cms(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.CMSResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/cmses/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.CMSResource)

    def delete_cms(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "DELETE", f"/api/v1/cmses/{id_}", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def install_wordpress(
        self,
        request: models.CMSInstallWordPressRequest,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/install/wordpress",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def install_nextcloud(
        self,
        request: models.CMSInstallNextCloudRequest,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/install/nextcloud",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def get_cms_one_time_login(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.CMSOneTimeLogin]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/cmses/{id_}/one-time-login",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CMSOneTimeLogin)

    def get_cms_plugins(
        self,
        *,
        id_: int,
    ) -> DtoResponse[list[models.CMSPlugin]]:
        local_response = self.api_connector.send_or_fail(
            "GET", f"/api/v1/cmses/{id_}/plugins", data=None, query_parameters={}
        )

        return DtoResponse.from_response(local_response, models.CMSPlugin)

    def update_cms_option(
        self,
        request: models.CMSOptionUpdateRequest,
        *,
        id_: int,
        name: models.CMSOptionNameEnum,
    ) -> DtoResponse[models.CMSOption]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/cmses/{id_}/options/{name}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.CMSOption)

    def update_cms_configuration_constant(
        self,
        request: models.CMSConfigurationConstantUpdateRequest,
        *,
        id_: int,
        name: str,
    ) -> DtoResponse[models.CMSConfigurationConstant]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/cmses/{id_}/configuration-constants/{name}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.CMSConfigurationConstant
        )

    def update_cms_user_credentials(
        self,
        request: models.CMSUserCredentialsUpdateRequest,
        *,
        id_: int,
        user_id: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/cmses/{id_}/users/{user_id}/credentials",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def update_cms_core(
        self,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/core/update",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def update_cms_plugin(
        self,
        *,
        id_: int,
        name: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/plugins/{name}/update",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def search_replace_in_cms_database(
        self,
        *,
        id_: int,
        search_string: str,
        replace_string: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/search-replace",
            data=None,
            query_parameters={
                "callback_url": callback_url,
                "search_string": search_string,
                "replace_string": replace_string,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def enable_cms_plugin(
        self,
        *,
        id_: int,
        name: str,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/plugins/{name}/enable",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def disable_cms_plugin(
        self,
        *,
        id_: int,
        name: str,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/plugins/{name}/disable",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def regenerate_cms_salts(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/regenerate-salts",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)

    def install_cms_theme(
        self,
        request: Union[
            models.CMSThemeInstallFromRepositoryRequest,
            models.CMSThemeInstallFromURLRequest,
        ],
        *,
        id_: int,
    ) -> DtoResponse[models.DetailMessage]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/cmses/{id_}/themes",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DetailMessage)
