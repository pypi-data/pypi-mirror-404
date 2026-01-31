from cyberfusion.CoreApiClient import models
from typing import Optional

from cyberfusion.CoreApiClient._helpers import construct_includes_query_parameter
from cyberfusion.CoreApiClient.http import DtoResponse
from cyberfusion.CoreApiClient.interfaces import Resource


class Clusters(Resource):
    def get_common_properties(
        self,
    ) -> DtoResponse[models.ClustersCommonProperties]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/common-properties",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClustersCommonProperties
        )

    def create_cluster(
        self,
        request: models.ClusterCreateRequest,
        *,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            "/api/v1/clusters",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def list_clusters(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters",
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

        return DtoResponse.from_response(local_response, models.ClusterResource)

    def read_cluster(
        self,
        *,
        id_: int,
        includes: list[str] | None = None,
    ) -> DtoResponse[models.ClusterResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(local_response, models.ClusterResource)

    def update_cluster(
        self,
        request: models.ClusterUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.ClusterResource)

    def list_ip_addresses_for_cluster(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterIPAddresses]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/ip-addresses",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.ClusterIPAddresses)

    def create_ip_address_for_cluster(
        self,
        request: models.ClusterIPAddressCreateRequest,
        *,
        id_: int,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/ip-addresses",
            data=request.model_dump(exclude_unset=True),
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def delete_ip_address_for_cluster(
        self,
        *,
        id_: int,
        ip_address: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/clusters/{id_}/ip-addresses/{ip_address}",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def enable_l3_ddos_protection_for_ip_address(
        self,
        *,
        id_: int,
        ip_address: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/ip-addresses/{ip_address}/l3-ddos-protection",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def disable_l3_ddos_protection_for_ip_address(
        self,
        *,
        id_: int,
        ip_address: str,
        callback_url: Optional[str] = None,
    ) -> DtoResponse[models.TaskCollectionResource]:
        local_response = self.api_connector.send_or_fail(
            "DELETE",
            f"/api/v1/clusters/{id_}/ip-addresses/{ip_address}/l3-ddos-protection",
            data=None,
            query_parameters={
                "callback_url": callback_url,
            },
        )

        return DtoResponse.from_response(local_response, models.TaskCollectionResource)

    def get_ip_addresses_products_for_clusters(
        self,
    ) -> DtoResponse[list[models.IPAddressProduct]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/ip-addresses/products",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.IPAddressProduct)

    def list_cluster_deployments_results(
        self,
        *,
        id_: int,
        get_non_running: Optional[bool] = None,
    ) -> DtoResponse[models.ClusterDeploymentResults]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/deployments-results",
            data=None,
            query_parameters={
                "get_non_running": get_non_running,
            },
        )

        return DtoResponse.from_response(
            local_response, models.ClusterDeploymentResults
        )

    def list_unix_users_home_directory_usages(
        self,
        *,
        id_: int,
        timestamp: str,
        time_unit: Optional[models.UNIXUsersHomeDirectoryUsageResource] = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.UNIXUsersHomeDirectoryUsageResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/usages/unix-users-home-directory",
            data=None,
            query_parameters={
                "timestamp": timestamp,
                "time_unit": time_unit,
            }
            | construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.UNIXUsersHomeDirectoryUsageResource
        )

    def list_nodes_dependencies(
        self, *, id_: int
    ) -> DtoResponse[list[models.NodeDependenciesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/nodes-dependencies",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.NodeDependenciesResource
        )

    def get_nodes_specifications(
        self, *, id_: int
    ) -> DtoResponse[list[models.NodeDependenciesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/nodes-specifications",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.NodeDependenciesResource
        )

    def list_simple_specifications(
        self, *, id_: int
    ) -> DtoResponse[list[models.SimpleSpecificationsResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/specifications/simple",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.SimpleSpecificationsResource
        )

    def list_advanced_specifications(
        self, *, id_: int
    ) -> DtoResponse[list[models.CompositeSpecificationSatisfyResultResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/specifications/advanced",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.CompositeSpecificationSatisfyResultResource
        )

    def read_borg_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterBorgPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/borg",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterBorgPropertiesResource
        )

    def read_elasticsearch_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterElasticsearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/elasticsearch",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterElasticsearchPropertiesResource
        )

    def read_firewall_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterFirewallPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/firewall",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterFirewallPropertiesResource
        )

    def read_grafana_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterGrafanaPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/grafana",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterGrafanaPropertiesResource
        )

    def read_kernelcare_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterKernelcarePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/kernelcare",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterKernelcarePropertiesResource
        )

    def read_load_balancing_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterLoadBalancingPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/load-balancing",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterLoadBalancingPropertiesResource
        )

    def read_mariadb_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterMariadbPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/mariadb",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMariadbPropertiesResource
        )

    def read_meilisearch_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterMeilisearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/meilisearch",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMeilisearchPropertiesResource
        )

    def read_metabase_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterMetabasePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/metabase",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMetabasePropertiesResource
        )

    def read_new_relic_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterNewRelicPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/new-relic",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNewRelicPropertiesResource
        )

    def read_nodejs_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterNodejsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/nodejs",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNodejsPropertiesResource
        )

    def read_os_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterOsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/os",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterOsPropertiesResource
        )

    def read_php_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterPhpPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/php",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPhpPropertiesResource
        )

    def read_postgresql_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterPostgresqlPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/postgresql",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPostgresqlPropertiesResource
        )

    def read_rabbitmq_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterRabbitmqPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/rabbitmq",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRabbitmqPropertiesResource
        )

    def read_redis_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterRedisPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/redis",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRedisPropertiesResource
        )

    def read_singlestore_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterSinglestorePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/singlestore",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterSinglestorePropertiesResource
        )

    def read_unix_users_properties(
        self, *, id_: int, includes: list[str] | None = None
    ) -> DtoResponse[models.ClusterUnixUsersPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            f"/api/v1/clusters/{id_}/properties/unix-users",
            data=None,
            query_parameters=construct_includes_query_parameter(includes),
        )

        return DtoResponse.from_response(
            local_response, models.ClusterUnixUsersPropertiesResource
        )

    def create_borg_properties(
        self,
        request: models.ClusterBorgPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterBorgPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/borg",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterBorgPropertiesResource
        )

    def create_elasticsearch_properties(
        self,
        request: models.ClusterElasticsearchPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterElasticsearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/elasticsearch",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterElasticsearchPropertiesResource
        )

    def create_firewall_properties(
        self,
        request: models.ClusterFirewallPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterFirewallPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/firewall",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterFirewallPropertiesResource
        )

    def create_grafana_properties(
        self,
        request: models.ClusterGrafanaPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterGrafanaPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/grafana",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterGrafanaPropertiesResource
        )

    def create_kernelcare_properties(
        self,
        request: models.ClusterKernelcarePropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterKernelcarePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/kernelcare",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterKernelcarePropertiesResource
        )

    def create_mariadb_properties(
        self,
        request: models.ClusterMariadbPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMariadbPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/mariadb",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMariadbPropertiesResource
        )

    def create_meilisearch_properties(
        self,
        request: models.ClusterMeilisearchPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMeilisearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/meilisearch",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMeilisearchPropertiesResource
        )

    def create_metabase_properties(
        self,
        request: models.ClusterMetabasePropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMetabasePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/metabase",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMetabasePropertiesResource
        )

    def create_new_relic_properties(
        self,
        request: models.ClusterNewRelicPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterNewRelicPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/new-relic",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNewRelicPropertiesResource
        )

    def create_nodejs_properties(
        self,
        request: models.ClusterNodejsPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterNodejsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/nodejs",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNodejsPropertiesResource
        )

    def create_os_properties(
        self,
        request: models.ClusterOsPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterOsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/os",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterOsPropertiesResource
        )

    def create_php_properties(
        self,
        request: models.ClusterPhpPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterPhpPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/php",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPhpPropertiesResource
        )

    def create_postgresql_properties(
        self,
        request: models.ClusterPostgresqlPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterPostgresqlPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/postgresql",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPostgresqlPropertiesResource
        )

    def create_rabbitmq_properties(
        self,
        request: models.ClusterRabbitmqPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterRabbitmqPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/rabbitmq",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRabbitmqPropertiesResource
        )

    def create_redis_properties(
        self,
        request: models.ClusterRedisPropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterRedisPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/redis",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRedisPropertiesResource
        )

    def create_singlestore_properties(
        self,
        request: models.ClusterSinglestorePropertiesCreateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterSinglestorePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/properties/singlestore",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterSinglestorePropertiesResource
        )

    def list_borg_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersBorgPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterBorgPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/borg",
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

        return DtoResponse.from_response(
            local_response, models.ClusterBorgPropertiesResource
        )

    def list_redis_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersRedisPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterRedisPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/redis",
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

        return DtoResponse.from_response(
            local_response, models.ClusterRedisPropertiesResource
        )

    def list_elasticsearch_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersElasticsearchPropertiesSearchRequest
        | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterElasticsearchPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/elasticsearch",
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

        return DtoResponse.from_response(
            local_response, models.ClusterElasticsearchPropertiesResource
        )

    def list_firewall_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersFirewallPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterFirewallPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/firewall",
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

        return DtoResponse.from_response(
            local_response, models.ClusterFirewallPropertiesResource
        )

    def list_grafana_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersGrafanaPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterGrafanaPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/grafana",
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

        return DtoResponse.from_response(
            local_response, models.ClusterGrafanaPropertiesResource
        )

    def list_kernelcare_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersKernelcarePropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterKernelcarePropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/kernelcare",
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

        return DtoResponse.from_response(
            local_response, models.ClusterKernelcarePropertiesResource
        )

    def list_load_balancing_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersLoadBalancingPropertiesSearchRequest
        | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterLoadBalancingPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/load-balancing",
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

        return DtoResponse.from_response(
            local_response, models.ClusterLoadBalancingPropertiesResource
        )

    def list_mariadb_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersMariadbPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterMariadbPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/mariadb",
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

        return DtoResponse.from_response(
            local_response, models.ClusterMariadbPropertiesResource
        )

    def list_meilisearch_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersMeilisearchPropertiesSearchRequest
        | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterMeilisearchPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/meilisearch",
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

        return DtoResponse.from_response(
            local_response, models.ClusterMeilisearchPropertiesResource
        )

    def list_metabase_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersMetabasePropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterMetabasePropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/metabase",
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

        return DtoResponse.from_response(
            local_response, models.ClusterMetabasePropertiesResource
        )

    def list_new_relic_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersNewRelicPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterNewRelicPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/new-relic",
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

        return DtoResponse.from_response(
            local_response, models.ClusterNewRelicPropertiesResource
        )

    def list_nodejs_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersNodejsPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterNodejsPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/nodejs",
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

        return DtoResponse.from_response(
            local_response, models.ClusterNodejsPropertiesResource
        )

    def list_os_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersOsPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterOsPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/os",
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

        return DtoResponse.from_response(
            local_response, models.ClusterOsPropertiesResource
        )

    def list_php_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersPhpPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterPhpPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/php",
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

        return DtoResponse.from_response(
            local_response, models.ClusterPhpPropertiesResource
        )

    def list_postgresql_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersPostgresqlPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterPostgresqlPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/postgresql",
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

        return DtoResponse.from_response(
            local_response, models.ClusterPostgresqlPropertiesResource
        )

    def list_rabbitmq_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersRabbitmqPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterRabbitmqPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/rabbitmq",
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

        return DtoResponse.from_response(
            local_response, models.ClusterRabbitmqPropertiesResource
        )

    def list_singlestore_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersSinglestorePropertiesSearchRequest
        | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterSinglestorePropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/singlestore",
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

        return DtoResponse.from_response(
            local_response, models.ClusterSinglestorePropertiesResource
        )

    def list_unix_users_properties(
        self,
        *,
        page: int = 1,
        per_page: int = 50,
        include_filters: models.ClustersUnixUsersPropertiesSearchRequest | None = None,
        includes: list[str] | None = None,
    ) -> DtoResponse[list[models.ClusterUnixUsersPropertiesResource]]:
        local_response = self.api_connector.send_or_fail(
            "GET",
            "/api/v1/clusters/properties/unix-users",
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

        return DtoResponse.from_response(
            local_response, models.ClusterUnixUsersPropertiesResource
        )

    def update_borg_properties(
        self,
        request: models.ClusterBorgPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterBorgPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/borg",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterBorgPropertiesResource
        )

    def update_singlestore_properties(
        self,
        request: models.ClusterSinglestorePropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterSinglestorePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/singlestore",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterSinglestorePropertiesResource
        )

    def update_redis_properties(
        self,
        request: models.ClusterRedisPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterRedisPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/redis",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRedisPropertiesResource
        )

    def update_elasticsearch_properties(
        self,
        request: models.ClusterElasticsearchPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterElasticsearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/elasticsearch",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterElasticsearchPropertiesResource
        )

    def update_firewall_properties(
        self,
        request: models.ClusterFirewallPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterFirewallPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/firewall",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterFirewallPropertiesResource
        )

    def update_grafana_properties(
        self,
        request: models.ClusterGrafanaPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterGrafanaPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/grafana",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterGrafanaPropertiesResource
        )

    def update_kernelcare_properties(
        self,
        request: models.ClusterKernelcarePropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterKernelcarePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/kernelcare",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterKernelcarePropertiesResource
        )

    def update_load_balancing_properties(
        self,
        request: models.ClusterLoadBalancingPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterLoadBalancingPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/load-balancing",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterLoadBalancingPropertiesResource
        )

    def update_mariadb_properties(
        self,
        request: models.ClusterMariadbPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMariadbPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/mariadb",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMariadbPropertiesResource
        )

    def update_meilisearch_properties(
        self,
        request: models.ClusterMeilisearchPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMeilisearchPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/meilisearch",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMeilisearchPropertiesResource
        )

    def update_metabase_properties(
        self,
        request: models.ClusterMetabasePropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterMetabasePropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/metabase",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterMetabasePropertiesResource
        )

    def update_new_relic_properties(
        self,
        request: models.ClusterNewRelicPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterNewRelicPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/new-relic",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNewRelicPropertiesResource
        )

    def update_nodejs_properties(
        self,
        request: models.ClusterNodejsPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterNodejsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/nodejs",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterNodejsPropertiesResource
        )

    def update_os_properties(
        self,
        request: models.ClusterOsPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterOsPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/os",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterOsPropertiesResource
        )

    def update_php_properties(
        self,
        request: models.ClusterPhpPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterPhpPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/php",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPhpPropertiesResource
        )

    def update_postgresql_properties(
        self,
        request: models.ClusterPostgresqlPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterPostgresqlPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/postgresql",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterPostgresqlPropertiesResource
        )

    def update_rabbitmq_properties(
        self,
        request: models.ClusterRabbitmqPropertiesUpdateRequest,
        *,
        id_: int,
    ) -> DtoResponse[models.ClusterRabbitmqPropertiesResource]:
        local_response = self.api_connector.send_or_fail(
            "PATCH",
            f"/api/v1/clusters/{id_}/properties/rabbitmq",
            data=request.model_dump(exclude_unset=True),
            query_parameters={},
        )

        return DtoResponse.from_response(
            local_response, models.ClusterRabbitmqPropertiesResource
        )

    def generate_innodb_report(
        self,
        *,
        id_: int,
    ) -> DtoResponse[models.DatabaseInnodbReport]:
        local_response = self.api_connector.send_or_fail(
            "POST",
            f"/api/v1/clusters/{id_}/reports/innodb-data",
            data=None,
            query_parameters={},
        )

        return DtoResponse.from_response(local_response, models.DatabaseInnodbReport)
