from datetime import datetime
from enum import StrEnum, IntEnum
from ipaddress import IPv4Address, IPv6Address
from typing import Dict, List, Optional, Union, Any
from pydantic import RootModel
from pydantic import UUID4, AnyUrl, EmailStr, Field, confloat, conint, constr, BaseModel
from typing import Iterator


class CoreApiModel:
    pass


class BaseCoreApiModel(CoreApiModel, BaseModel):
    pass


class RootCoreApiModel(CoreApiModel, RootModel):
    pass


class RootModelCollectionMixin:
    """Mixin supporting iterating over and accessing items in a root model, without explicitly accessing root.

    Inspired by https://docs.pydantic.dev/2.0/usage/models/#rootmodel-and-custom-root-types
    """

    root: dict | list | None

    def __iter__(self) -> Iterator:
        if not isinstance(self.root, (list, dict)):
            raise TypeError("Type does not support iter")

        return iter(self.root)

    def __getitem__(self, item: Any) -> Any:
        if not isinstance(self.root, (list, dict)):
            raise TypeError("Type does not support getitem")

        return self.root[item]

    def items(self) -> Any:
        if not isinstance(self.root, (dict)):
            raise TypeError("Type does not support items")

        return self.root.items()


class SpecificationMode(StrEnum):
    SINGLE = "Single"
    OR = "Or"
    AND = "And"


class ObjectLogTypeEnum(StrEnum):
    Create = "Create"
    Update = "Update"
    Delete = "Delete"


class CauserTypeEnum(StrEnum):
    API_User = "API User"


class HTTPMethod(StrEnum):
    CONNECT = "CONNECT"
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"
    TRACE = "TRACE"


class APIUserAuthenticationMethodEnum(StrEnum):
    API_KEY = "API Key"
    JWT_TOKEN = "JWT Token"


class APIUserInfo(BaseCoreApiModel):
    id: int
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    is_active: bool
    is_superuser: bool
    clusters: List[int]
    customers: List[int]
    service_accounts: List[int]
    authentication_method: APIUserAuthenticationMethodEnum


class AllowOverrideDirectiveEnum(StrEnum):
    ALL = "All"
    AUTHCONFIG = "AuthConfig"
    FILEINFO = "FileInfo"
    INDEXES = "Indexes"
    LIMIT = "Limit"
    NONE = "None"


class AllowOverrideOptionDirectiveEnum(StrEnum):
    ALL = "All"
    FOLLOWSYMLINKS = "FollowSymLinks"
    INDEXES = "Indexes"
    MULTIVIEWS = "MultiViews"
    SYMLINKSIFOWNERMATCH = "SymLinksIfOwnerMatch"
    NONE = "None"


class BasicAuthenticationRealmCreateRequest(BaseCoreApiModel):
    directory_path: Optional[str]
    uri_path: Optional[str]
    virtual_host_id: int
    name: constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=64)
    htpasswd_file_id: int


class BasicAuthenticationRealmUpdateRequest(BaseCoreApiModel):
    name: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=64)
    ] = None
    htpasswd_file_id: Optional[int] = None


class BodyLoginAccessToken(BaseCoreApiModel):
    grant_type: Optional[constr(pattern=r"^password$")] = None
    username: str
    password: str
    scope: Optional[str] = ""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class BorgArchiveContentObjectTypeEnum(StrEnum):
    REGULAR_FILE = "regular_file"
    DIRECTORY = "directory"
    SYMBOLIC_LINK = "symbolic_link"


class BorgArchiveCreateRequest(BaseCoreApiModel):
    borg_repository_id: int
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)


class BorgArchiveMetadata(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    borg_archive_id: int
    exists_on_server: bool
    contents_path: Optional[str]


class BorgRepositoryCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    unix_user_id: Optional[int]
    keep_hourly: Optional[int]
    keep_daily: Optional[int]
    keep_weekly: Optional[int]
    keep_monthly: Optional[int]
    keep_yearly: Optional[int]
    database_id: Optional[int]


class BorgRepositoryUpdateRequest(BaseCoreApiModel):
    keep_hourly: Optional[int] = None
    keep_daily: Optional[int] = None
    keep_weekly: Optional[int] = None
    keep_monthly: Optional[int] = None
    keep_yearly: Optional[int] = None


class CMSConfigurationConstant(BaseCoreApiModel):
    value: Union[str, int, float, bool]
    index: Optional[conint(ge=0)] = None
    name: constr(pattern=r"^[a-zA-Z0-9_]+$", min_length=1)


class CMSConfigurationConstantUpdateRequest(BaseCoreApiModel):
    value: Union[str, int, float, bool]
    index: Optional[conint(ge=0)] = None


class CMSInstallNextCloudRequest(BaseCoreApiModel):
    database_name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=63)
    database_user_name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=63)
    database_user_password: constr(pattern=r"^[ -~]+$", min_length=1, max_length=255)
    database_host: str
    admin_username: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=60)
    admin_password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)


class CMSInstallWordPressRequest(BaseCoreApiModel):
    database_name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=63)
    database_user_name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=63)
    database_user_password: constr(pattern=r"^[ -~]+$", min_length=1, max_length=255)
    database_host: str
    admin_username: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=60)
    admin_password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)
    site_title: constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=253)
    site_url: AnyUrl
    locale: constr(pattern=r"^[a-zA-Z_]+$", min_length=1, max_length=15)
    version: constr(pattern=r"^[0-9.]+$", min_length=1, max_length=6)
    admin_email_address: EmailStr


class CMSOneTimeLogin(BaseCoreApiModel):
    url: AnyUrl


class CMSOptionNameEnum(StrEnum):
    BLOG_PUBLIC = "blog_public"


class CMSOptionUpdateRequest(BaseCoreApiModel):
    value: conint(ge=0, le=1)


class CMSPlugin(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9_]+$", min_length=1)
    current_version: constr(pattern=r"^[a-z0-9.-]+$", min_length=1)
    available_version: Optional[constr(pattern=r"^[a-z0-9.-]+$", min_length=1)]
    is_enabled: bool


class CMSSoftwareNameEnum(StrEnum):
    WORDPRESS = "WordPress"
    NEXTCLOUD = "Nextcloud"


class CMSThemeInstallFromRepositoryRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=60)
    version: Optional[constr(pattern=r"^[0-9.]+$", min_length=1, max_length=6)]


class CMSThemeInstallFromURLRequest(BaseCoreApiModel):
    url: AnyUrl


class CMSUserCredentialsUpdateRequest(BaseCoreApiModel):
    password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)


class CertificateCreateRequest(BaseCoreApiModel):
    certificate: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n ]+$", min_length=1, max_length=65535
    )
    ca_chain: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n ]+$", min_length=1, max_length=65535
    )
    private_key: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n ]+$", min_length=1, max_length=65535
    )
    cluster_id: int


class CertificateManagerUpdateRequest(BaseCoreApiModel):
    request_callback_url: Optional[AnyUrl] = None


class CertificateProviderNameEnum(StrEnum):
    LETS_ENCRYPT = "lets_encrypt"


class NodejsVersion(RootCoreApiModel):
    __hash__ = object.__hash__

    root: constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")


class ClusterIPAddress(BaseCoreApiModel):
    ip_address: Union[IPv6Address, IPv4Address]
    dns_name: Optional[str]
    l3_ddos_protection_enabled: bool


class ClusterIPAddresses(RootModelCollectionMixin, RootCoreApiModel):  # type: ignore[misc]
    root: Optional[Dict[str, Dict[str, List[ClusterIPAddress]]]] = None


class CronCreateRequest(BaseCoreApiModel):
    node_id: Optional[int]
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    unix_user_id: int
    command: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    email_address: Optional[EmailStr]
    schedule: str
    error_count: int = 1
    random_delay_max_seconds: int = 10
    timeout_seconds: Optional[int] = 600
    locking_enabled: bool = True
    is_active: bool = True
    memory_limit: Optional[conint(ge=256)] = None
    cpu_limit: Optional[int] = None


class CronUpdateRequest(BaseCoreApiModel):
    command: Optional[constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)] = (
        None
    )
    email_address: Optional[EmailStr] = None
    schedule: Optional[str] = None
    error_count: Optional[int] = None
    random_delay_max_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    locking_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    memory_limit: Optional[conint(ge=256)] = None
    cpu_limit: Optional[int] = None
    node_id: Optional[int] = None


class CustomConfigServerSoftwareNameEnum(StrEnum):
    NGINX = "nginx"


class CustomConfigSnippetTemplateNameEnum(StrEnum):
    LARAVEL = "Laravel"
    COMPRESSION = "Compression"


class CustomConfigSnippetUpdateRequest(BaseCoreApiModel):
    contents: Optional[
        constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    ] = None
    is_default: Optional[bool] = None


class CustomConfigUpdateRequest(BaseCoreApiModel):
    contents: Optional[
        constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    ] = None


class CustomerIPAddressDatabase(BaseCoreApiModel):
    ip_address: Union[IPv6Address, IPv4Address]
    dns_name: Optional[str]


class CustomerIPAddresses(RootModelCollectionMixin, RootCoreApiModel):  # type: ignore[misc]
    root: Optional[Dict[str, Dict[str, List[CustomerIPAddressDatabase]]]] = None


class CustomerIncludes(BaseCoreApiModel):
    pass


class CustomerResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    identifier: constr(pattern=r"^[a-z0-9]+$", min_length=2, max_length=4)
    dns_subdomain: str
    is_internal: bool
    team_code: constr(pattern=r"^[A-Z0-9]+$", min_length=4, max_length=6)
    includes: CustomerIncludes


class DaemonCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    unix_user_id: int
    command: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    nodes_ids: List[int]
    memory_limit: Optional[conint(ge=256)] = None
    cpu_limit: Optional[int] = None


class DaemonUpdateRequest(BaseCoreApiModel):
    command: Optional[constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)] = (
        None
    )
    nodes_ids: Optional[List[int]] = None
    memory_limit: Optional[conint(ge=256)] = None
    cpu_limit: Optional[int] = None


class IdenticalTablesName(CoreApiModel, RootModel):
    root: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)


class NotIdenticalTablesName(RootCoreApiModel):
    root: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)


class OnlyLeftTablesName(RootCoreApiModel):
    root: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)


class OnlyRightTablesName(RootCoreApiModel):
    root: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)


class DatabaseComparison(BaseCoreApiModel):
    identical_tables_names: List[IdenticalTablesName]
    not_identical_tables_names: List[NotIdenticalTablesName]
    only_left_tables_names: List[OnlyLeftTablesName]
    only_right_tables_names: List[OnlyRightTablesName]


class DatabaseServerSoftwareNameEnum(StrEnum):
    MARIADB = "MariaDB"
    POSTGRESQL = "PostgreSQL"


class DatabaseUpdateRequest(BaseCoreApiModel):
    optimizing_enabled: Optional[bool] = None
    backups_enabled: Optional[bool] = None


class DatabaseUsageIncludes(BaseCoreApiModel):
    pass


class DatabaseUsageResource(BaseCoreApiModel):
    database_id: int
    usage: confloat(ge=0.0)
    timestamp: datetime
    includes: DatabaseUsageIncludes


class DatabaseUserUpdateRequest(BaseCoreApiModel):
    phpmyadmin_firewall_groups_ids: Optional[List[int]] = None
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)] = (
        None
    )


class DetailMessage(BaseCoreApiModel):
    detail: constr(pattern=r"^[ -~]+$", min_length=1, max_length=255)


class DocumentRootFileSuffixEnum(StrEnum):
    PHP = "php"


class DomainRouterCategoryEnum(StrEnum):
    GRAFANA = "Grafana"
    SINGLESTORE_STUDIO = "SingleStore Studio"
    SINGLESTORE_API = "SingleStore API"
    METABASE = "Metabase"
    KIBANA = "Kibana"
    RABBITMQ_MANAGEMENT = "RabbitMQ Management"
    VIRTUAL_HOST = "Virtual Host"
    URL_REDIRECT = "URL Redirect"
    N8N = "n8n"


class DomainRouterUpdateRequest(BaseCoreApiModel):
    node_id: Optional[int] = None
    certificate_id: Optional[int] = None
    security_txt_policy_id: Optional[int] = None
    firewall_groups_ids: Optional[List[int]] = None
    force_ssl: Optional[bool] = None


class EncryptionTypeEnum(StrEnum):
    TLS = "TLS"
    SSL = "SSL"
    STARTTLS = "STARTTLS"


class FPMPoolCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    version: str
    unix_user_id: int
    max_children: int = 25
    max_requests: int = 20
    process_idle_timeout: int = 10
    cpu_limit: Optional[int] = None
    log_slow_requests_threshold: Optional[int] = None
    is_namespaced: bool = True
    memory_limit: Optional[conint(ge=256)] = None


class FPMPoolUpdateRequest(BaseCoreApiModel):
    max_children: Optional[int] = None
    max_requests: Optional[int] = None
    process_idle_timeout: Optional[int] = None
    cpu_limit: Optional[int] = None
    log_slow_requests_threshold: Optional[int] = None
    is_namespaced: Optional[bool] = None
    memory_limit: Optional[conint(ge=256)] = None


class FTPUserCreateRequest(BaseCoreApiModel):
    username: constr(pattern=r"^[a-z0-9-_.@]+$", min_length=1, max_length=32)
    unix_user_id: int
    password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)
    directory_path: Optional[str] = None


class FTPUserUpdateRequest(BaseCoreApiModel):
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)] = (
        None
    )
    directory_path: Optional[str] = None


class FirewallGroupCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9_]+$", min_length=1, max_length=32)
    cluster_id: int
    ip_networks: List[str] = Field(
        ...,
        min_length=1,
    )


class FirewallGroupUpdateRequest(BaseCoreApiModel):
    ip_networks: Optional[List[str]] = None


class FirewallRuleExternalProviderNameEnum(StrEnum):
    ATLASSIAN = "Atlassian"
    AWS = "AWS"
    BUDDY = "Buddy"
    GOOGLE_CLOUD = "Google Cloud"


class FirewallRuleServiceNameEnum(StrEnum):
    SSH = "SSH"
    PROFTPD = "ProFTPD"
    NGINX = "nginx"
    APACHE = "Apache"


class HAProxyListenToNodeCreateRequest(BaseCoreApiModel):
    haproxy_listen_id: int
    node_id: int


class HTTPRetryConditionEnum(StrEnum):
    CONNECTION_FAILURE = "Connection failure"
    EMPTY_RESPONSE = "Empty response"
    JUNK_RESPONSE = "Junk response"
    RESPONSE_TIMEOUT = "Response timeout"
    ZERO_RTT_REJECTED = "0-RTT rejected"
    HTTP_STATUS_401 = "HTTP status 401"
    HTTP_STATUS_403 = "HTTP status 403"
    HTTP_STATUS_404 = "HTTP status 404"
    HTTP_STATUS_408 = "HTTP status 408"
    HTTP_STATUS_425 = "HTTP status 425"
    HTTP_STATUS_500 = "HTTP status 500"
    HTTP_STATUS_501 = "HTTP status 501"
    HTTP_STATUS_502 = "HTTP status 502"
    HTTP_STATUS_503 = "HTTP status 503"
    HTTP_STATUS_504 = "HTTP status 504"


class HTTPRetryProperties(BaseCoreApiModel):
    tries_amount: Optional[conint(ge=1, le=3)]
    tries_failover_amount: Optional[conint(ge=1, le=3)]
    conditions: List[HTTPRetryConditionEnum]


class HealthStatusEnum(StrEnum):
    UP = "up"
    MAINTENANCE = "maintenance"


class HostsEntryCreateRequest(BaseCoreApiModel):
    node_id: int
    host_name: str
    cluster_id: int


class HtpasswdFileCreateRequest(BaseCoreApiModel):
    unix_user_id: int


class HtpasswdUserCreateRequest(BaseCoreApiModel):
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=255)
    htpasswd_file_id: int
    password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)


class HtpasswdUserUpdateRequest(BaseCoreApiModel):
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)] = (
        None
    )


class IPAddressFamilyEnum(StrEnum):
    IPV6 = "IPv6"
    IPV4 = "IPv4"


class IPAddressProductTypeEnum(StrEnum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"


class LanguageCodeEnum(StrEnum):
    NL = "nl"
    EN = "en"


class LoadBalancingMethodEnum(StrEnum):
    ROUND_ROBIN = "Round Robin"
    SOURCE_IP_ADDRESS = "Source IP Address"


class LogMethodEnum(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    DELETE = "DELETE"
    HEAD = "HEAD"


class LogSortOrderEnum(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


class MailAccountCreateRequest(BaseCoreApiModel):
    local_part: constr(pattern=r"^[a-z0-9-.]+$", min_length=1, max_length=64)
    mail_domain_id: int
    password: constr(pattern=r"^[ -~]+$", min_length=6, max_length=255)
    quota: Optional[int] = None


class MailAccountUpdateRequest(BaseCoreApiModel):
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=6, max_length=255)] = None
    quota: Optional[int] = None


class MailAccountUsageIncludes(BaseCoreApiModel):
    pass


class MailAccountUsageResource(BaseCoreApiModel):
    mail_account_id: int
    usage: confloat(ge=0.0)
    timestamp: datetime
    includes: MailAccountUsageIncludes


class MailAliasCreateRequest(BaseCoreApiModel):
    local_part: constr(pattern=r"^[a-z0-9-.]+$", min_length=1, max_length=64)
    mail_domain_id: int
    forward_email_addresses: List[EmailStr] = Field(
        ...,
        min_length=1,
    )


class MailAliasUpdateRequest(BaseCoreApiModel):
    forward_email_addresses: Optional[List[EmailStr]] = None


class MailDomainCreateRequest(BaseCoreApiModel):
    domain: str
    unix_user_id: int
    catch_all_forward_email_addresses: List[EmailStr] = Field(
        [],
    )
    is_local: bool = True


class MailDomainUpdateRequest(BaseCoreApiModel):
    catch_all_forward_email_addresses: Optional[List[EmailStr]] = None
    is_local: Optional[bool] = None


class MailHostnameCreateRequest(BaseCoreApiModel):
    domain: str
    cluster_id: int
    certificate_id: int


class MailHostnameUpdateRequest(BaseCoreApiModel):
    certificate_id: Optional[int] = None


class MariaDBEncryptionKeyCreateRequest(BaseCoreApiModel):
    cluster_id: int


class MariaDBPrivilegeEnum(StrEnum):
    ALL = "ALL"
    SELECT = "SELECT"


class MeilisearchEnvironmentEnum(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"


class NestedPathsDict(RootModelCollectionMixin, RootCoreApiModel):  # type: ignore[misc]
    root: Optional[Dict[str, Optional["NestedPathsDict"]]] = None


class NodeAddOnCreateRequest(BaseCoreApiModel):
    node_id: int
    product: constr(pattern=r"^[a-zA-Z0-9 ]+$", min_length=1, max_length=64)
    quantity: int


class NodeAddOnProduct(BaseCoreApiModel):
    uuid: UUID4
    name: constr(pattern=r"^[a-zA-Z0-9 ]+$", min_length=1, max_length=64)
    memory_mib: Optional[int]
    cpu_cores: Optional[int]
    disk_gib: Optional[int]
    price: confloat(ge=0.0)
    period: constr(pattern=r"^[A-Z0-9]+$", min_length=2, max_length=2)
    currency: constr(pattern=r"^[A-Z]+$", min_length=3, max_length=3)


class NodeGroupEnum(StrEnum):
    ADMIN = "Admin"
    APACHE = "Apache"
    PROFTPD = "ProFTPD"
    NGINX = "nginx"
    DOVECOT = "Dovecot"
    MARIADB = "MariaDB"
    POSTGRESQL = "PostgreSQL"
    PHP = "PHP"
    PASSENGER = "Passenger"
    FAST_REDIRECT = "Fast Redirect"
    HAPROXY = "HAProxy"
    REDIS = "Redis"
    COMPOSER = "Composer"
    WP_CLI = "WP-CLI"
    KERNELCARE = "KernelCare"
    IMAGEMAGICK = "ImageMagick"
    WKHTMLTOPDF = "wkhtmltopdf"
    GNU_MAILUTILS = "GNU Mailutils"
    CLAMAV = "ClamAV"
    PUPPETEER = "Puppeteer"
    N8N = "n8n"
    LIBREOFFICE = "LibreOffice"
    GHOSTSCRIPT = "Ghostscript"
    FFMPEG = "FFmpeg"
    DOCKER = "Docker"
    MEILISEARCH = "Meilisearch"
    NEW_RELIC = "New Relic"
    MALDET = "maldet"
    NODEJS = "NodeJS"
    GRAFANA = "Grafana"
    SINGLESTORE = "SingleStore"
    METABASE = "Metabase"
    ELASTICSEARCH = "Elasticsearch"
    RABBITMQ = "RabbitMQ"


class NodeMariaDBGroupProperties(BaseCoreApiModel):
    is_master: bool


class NodeProduct(BaseCoreApiModel):
    uuid: UUID4
    name: constr(pattern=r"^[A-Z]+$", min_length=1, max_length=2)
    memory_mib: int
    cpu_cores: int
    disk_gib: int
    allow_upgrade_to: List[constr(pattern=r"^[A-Z]+$", min_length=1, max_length=2)]
    allow_downgrade_to: List[constr(pattern=r"^[A-Z]+$", min_length=1, max_length=2)]
    price: confloat(ge=0.0)
    period: constr(pattern=r"^[A-Z0-9]+$", min_length=2, max_length=2)
    currency: constr(pattern=r"^[A-Z]+$", min_length=3, max_length=3)


class NodeRabbitMQGroupProperties(BaseCoreApiModel):
    is_master: bool


class NodeRedisGroupProperties(BaseCoreApiModel):
    is_master: bool


class ObjectModelNameEnum(StrEnum):
    BORG_ARCHIVE = "BorgArchive"
    BORG_REPOSITORY = "BorgRepository"
    SERVICE_ACCOUNT_TO_CLUSTER = "ServiceAccountToCluster"
    REGION = "Region"
    SERVICE_ACCOUNT_TO_CUSTOMER = "ServiceAccountToCustomer"
    CLUSTER = "Cluster"
    CUSTOMER = "Customer"
    CMS = "Cms"
    FPM_POOL = "FpmPool"
    VIRTUAL_HOST = "VirtualHost"
    PASSENGER_APP = "PassengerApp"
    DATABASE = "Database"
    CERTIFICATE_MANAGER = "CertificateManager"
    BASIC_AUTHENTICATION_REALM = "BasicAuthenticationRealm"
    CRON = "Cron"
    DAEMON = "Daemon"
    MARIADB_ENCRYPTION_KEYS = "MariadbEncryptionKey"
    FIREWALL_RULE = "FirewallRule"
    HOSTS_ENTRY = "HostsEntry"
    NODE_ADD_ON = "NodeAddOn"
    IP_ADDRESS = "IpAddress"
    SECURITY_TXT_POLICY = "SecurityTxtPolicy"
    DATABASE_USER = "DatabaseUser"
    DATABASE_USER_GRANT = "DatabaseUserGrant"
    HTPASSWD_FILE = "HtpasswdFile"
    HTPASSWD_USER = "HtpasswdUser"
    MAIL_ACCOUNT = "MailAccount"
    MAIL_ALIASES = "MailAlias"
    MAIL_DOMAIN = "MailDomain"
    NODE = "Node"
    REDIS_INSTANCE = "RedisInstance"
    DOMAIN_ROUTER = "DomainRouter"
    MAIL_HOSTNAME = "MailHostname"
    CERTIFICATE = "Certificate"
    ROOT_SSH_KEY = "RootSshKey"
    SSH_KEY = "SshKey"
    BORG_REPOSITORY_SSH_KEY = "BorgRepositorySshKey"
    UNIX_USER = "UnixUser"
    UNIX_USER_RABBITMQ_CREDENTIALS = "UnixUserRabbitmqCredentials"
    HAPROXY_LISTEN = "HaproxyListen"
    HAPROXY_LISTEN_TO_NODE = "HaproxyListenToNode"
    URL_REDIRECT = "UrlRedirect"
    REGION_TO_CUSTOMER = "RegionToCustomer"
    SERVICE_ACCOUNT = "ServiceAccount"
    SERVICE_ACCOUNT_SERVER = "ServiceAccountServer"
    CUSTOM_CONFIG = "CustomConfig"
    N8N_INSTANCE = "N8nInstance"
    CLUSTERS_PHP_PROPERTIES = "ClustersPhpProperties"
    CLUSTERS_NODEJS_PROPERTIES = "ClustersNodejsProperties"
    CLUSTERS_BORG_PROPERTIES = "ClustersBorgProperties"
    CLUSTERS_KERNELCARE_PROPERTIES = "ClustersKernelcareProperties"
    CLUSTERS_NEW_RELIC_PROPERTIES = "ClustersNewRelicProperties"
    CLUSTERS_REDIS_PROPERTIES = "ClustersRedisProperties"
    CLUSTERS_POSTGRESQL_PROPERTIES = "ClustersPostgresqlProperties"
    CLUSTERS_MARIADB_PROPERTIES = "ClustersMariadbProperties"
    CLUSTERS_MEILISEARCH_PROPERTIES = "ClustersMeilisearchProperties"
    CLUSTERS_GRAFANA_PROPERTIES = "ClustersGrafanaProperties"
    CLUSTERS_SINGLESTORE_PROPERTIES = "ClustersSinglestoreProperties"
    CLUSTERS_ELASTICSEARCH_PROPERTIES = "ClustersElasticsearchProperties"
    CLUSTERS_RABBITMQ_PROPERTIES = "ClustersRabbitmqProperties"
    CLUSTERS_METABASE_PROPERTIES = "ClustersMetabaseProperties"
    CLUSTERS_UNIX_USERS_PROPERTIES = "ClustersUnixUsersProperties"
    CLUSTERS_LOAD_BALANCING_PROPERTIES = "ClustersLoadBalancingProperties"
    CLUSTERS_FIREWALL_PROPERTIES = "ClustersFirewallProperties"
    CLUSTERS_OS_PROPERTIES = "ClustersOsProperties"


class PHPExtensionEnum(StrEnum):
    REDIS = "redis"
    IMAGICK = "imagick"
    SQLITE3 = "sqlite3"
    INTL = "intl"
    BCMATH = "bcmath"
    XDEBUG = "xdebug"
    PGSQL = "pgsql"
    SSH2 = "ssh2"
    LDAP = "ldap"
    MCRYPT = "mcrypt"
    XMLRPC = "xmlrpc"
    APCU = "apcu"
    TIDEWAYS = "tideways"
    SQLSRV = "sqlsrv"
    GMP = "gmp"
    VIPS = "vips"
    EXCIMER = "excimer"
    MAILPARSE = "mailparse"
    UV = "uv"
    AMQP = "amqp"
    MONGODB = "mongodb"


class PHPSettings(BaseCoreApiModel):
    apc_enable_cli: bool = False
    opcache_file_cache: bool = False
    opcache_validate_timestamps: bool = True
    short_open_tag: bool = False
    session_gc_maxlifetime: conint(ge=1440, le=14400) = 1440
    error_reporting: constr(pattern=r"^[A-Z&~_ ]+$", min_length=1, max_length=255) = (
        Field(
            "E_ALL & ~E_DEPRECATED & ~E_STRICT",
        )
    )
    opcache_memory_consumption: conint(ge=192, le=1024) = 192
    max_execution_time: conint(ge=30, le=120) = 120
    max_file_uploads: conint(ge=100, le=1000) = 100
    memory_limit: conint(ge=256, le=4096) = 256
    post_max_size: conint(ge=32, le=256) = 32
    upload_max_filesize: conint(ge=32, le=256) = 32
    tideways_api_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9_]+$", min_length=16, max_length=32)
    ] = None
    tideways_sample_rate: Optional[conint(ge=1, le=100)] = None
    newrelic_browser_monitoring_auto_instrument: bool = True


class PassengerAppTypeEnum(StrEnum):
    NODEJS = "NodeJS"


class PassengerEnvironmentEnum(StrEnum):
    PRODUCTION = "Production"
    DEVELOPMENT = "Development"


class RedisEvictionPolicyEnum(StrEnum):
    VOLATILE_TTL = "volatile-ttl"
    VOLATILE_RANDOM = "volatile-random"
    ALLKEYS_RANDOM = "allkeys-random"
    VOLATILE_LFU = "volatile-lfu"
    VOLATILE_LRU = "volatile-lru"
    ALLKEYS_LFU = "allkeys-lfu"
    ALLKEYS_LRU = "allkeys-lru"
    NOEVICTION = "noeviction"


class N8nInstanceCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    domain: str
    cluster_id: int


class N8nInstanceUpdateRequest(BaseCoreApiModel):
    domain: str | None = None


class N8nInstancesSearchRequest(BaseCoreApiModel):
    name: str | None = None
    domain: str | None = None
    cluster_id: int | None = None


class RedisInstanceCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    password: constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    memory_limit: conint(ge=8)
    max_databases: int = 16
    eviction_policy: RedisEvictionPolicyEnum = RedisEvictionPolicyEnum.VOLATILE_LRU


class RedisInstanceUpdateRequest(BaseCoreApiModel):
    password: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    ] = None
    memory_limit: Optional[conint(ge=8)] = None
    max_databases: Optional[int] = None
    eviction_policy: Optional[RedisEvictionPolicyEnum] = None


class RootSSHKeyCreatePrivateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    private_key: str


class RootSSHKeyCreatePublicRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    public_key: str


class SSHKeyCreatePrivateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=128)
    unix_user_id: int
    private_key: str


class SSHKeyCreatePublicRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=128)
    unix_user_id: int
    public_key: str


class SecurityTXTPolicyCreateRequest(BaseCoreApiModel):
    cluster_id: int
    expires_timestamp: datetime
    email_contacts: List[EmailStr]
    url_contacts: List[AnyUrl]
    encryption_key_urls: List[AnyUrl] = Field(
        [],
    )
    acknowledgment_urls: List[AnyUrl] = Field(
        [],
    )
    policy_urls: List[AnyUrl] = Field(
        [],
    )
    opening_urls: List[AnyUrl] = Field(
        [],
    )
    preferred_languages: List[LanguageCodeEnum] = Field(
        [],
    )


class SecurityTXTPolicyUpdateRequest(BaseCoreApiModel):
    expires_timestamp: Optional[datetime] = None
    email_contacts: Optional[List[EmailStr]] = None
    url_contacts: Optional[List[AnyUrl]] = None
    encryption_key_urls: Optional[List[AnyUrl]] = None
    acknowledgment_urls: Optional[List[AnyUrl]] = None
    policy_urls: Optional[List[AnyUrl]] = None
    opening_urls: Optional[List[AnyUrl]] = None
    preferred_languages: Optional[List[LanguageCodeEnum]] = None


class ServiceAccountGroupEnum(StrEnum):
    SECURITY_TXT_POLICY_SERVER = "Security TXT Policy Server"
    LOAD_BALANCER = "Load Balancer"
    BORG = "Borg"
    MAIL_PROXY = "Mail Proxy"
    MAIL_GATEWAY = "Mail Gateway"
    INTERNET_ROUTER = "Internet Router"
    STORAGE_ROUTER = "Storage Router"
    PHPMYADMIN = "phpMyAdmin"


class ShellNameEnum(StrEnum):
    BASH = "Bash"
    NOLOGIN = "nologin"


class RegionIncludes(BaseCoreApiModel):
    pass


class RegionResource(BaseCoreApiModel):
    id: int
    name: constr(pattern=r"^[A-Z0-9-]+$", min_length=1, max_length=32)
    includes: RegionIncludes


class StatusCodeEnum(IntEnum):
    INTEGER_301 = 301
    INTEGER_302 = 302
    INTEGER_303 = 303
    INTEGER_307 = 307
    INTEGER_308 = 308


class TaskCollectionCallback(BaseCoreApiModel):
    task_collection_uuid: UUID4
    success: bool


class TaskCollectionTypeEnum(StrEnum):
    ASYNCHRONOUS = "asynchronous"


class TaskStateEnum(StrEnum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TemporaryFTPUserCreateRequest(BaseCoreApiModel):
    unix_user_id: int
    node_id: int


class TemporaryFTPUserResource(BaseCoreApiModel):
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=32)
    password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)
    file_manager_url: AnyUrl


class TimeUnitEnum(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TokenTypeEnum(StrEnum):
    BEARER = "bearer"


class UNIXUserComparison(BaseCoreApiModel):
    not_identical_paths: NestedPathsDict
    only_left_files_paths: NestedPathsDict
    only_right_files_paths: NestedPathsDict
    only_left_directories_paths: NestedPathsDict
    only_right_directories_paths: NestedPathsDict


class UNIXUserCreateRequest(BaseCoreApiModel):
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=32)
    virtual_hosts_directory: Optional[str] = None
    mail_domains_directory: Optional[str] = None
    cluster_id: int
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)]
    shell_name: ShellNameEnum = ShellNameEnum.BASH
    record_usage_files: bool = False
    default_php_version: Optional[str] = None
    default_nodejs_version: Optional[constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")] = None
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ] = None
    shell_is_namespaced: bool = True


class UNIXUserHomeDirectoryEnum(StrEnum):
    VAR_WWW_VHOSTS = "/var/www/vhosts"
    VAR_WWW = "/var/www"
    HOME = "/home"
    MNT_MAIL = "/mnt/mail"
    MNT_BACKUPS = "/mnt/backups"


class UNIXUserUpdateRequest(BaseCoreApiModel):
    password: Optional[constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)] = (
        None
    )
    shell_name: Optional[ShellNameEnum] = None
    record_usage_files: Optional[bool] = None
    default_php_version: Optional[str] = None
    default_nodejs_version: Optional[constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")] = None
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ] = None
    shell_is_namespaced: Optional[bool] = None


class UNIXUserUsageFile(BaseCoreApiModel):
    path: str
    size: confloat(ge=0.0)


class UNIXUserUsageIncludes(BaseCoreApiModel):
    pass


class UNIXUserUsageResource(BaseCoreApiModel):
    unix_user_id: int
    usage: confloat(ge=0.0)
    files: Optional[List[UNIXUserUsageFile]]
    timestamp: datetime
    includes: UNIXUserUsageIncludes


class UNIXUsersHomeDirectoryUsageIncludes(BaseCoreApiModel):
    pass


class UNIXUsersHomeDirectoryUsageResource(BaseCoreApiModel):
    cluster_id: int
    usage: confloat(ge=0.0)
    timestamp: datetime
    includes: UNIXUsersHomeDirectoryUsageIncludes


class URLRedirectCreateRequest(BaseCoreApiModel):
    domain: str
    cluster_id: int
    server_aliases: List[str]
    destination_url: AnyUrl
    status_code: StatusCodeEnum = StatusCodeEnum.INTEGER_301
    keep_query_parameters: bool = True
    keep_path: bool = True
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ]


class URLRedirectUpdateRequest(BaseCoreApiModel):
    server_aliases: Optional[List[str]] = None
    destination_url: Optional[AnyUrl] = None
    status_code: Optional[StatusCodeEnum] = None
    keep_query_parameters: Optional[bool] = None
    keep_path: Optional[bool] = None
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ] = None


class ValidationError(BaseCoreApiModel):
    loc: List[Union[str, int]]
    msg: str
    type: str


class VirtualHostDocumentRoot(BaseCoreApiModel):
    contains_files: Dict[str, bool]


class VirtualHostServerSoftwareNameEnum(StrEnum):
    APACHE = "Apache"
    NGINX = "nginx"


class VirtualHostUpdateRequest(BaseCoreApiModel):
    server_aliases: Optional[List[str]] = None
    document_root: Optional[str] = None
    fpm_pool_id: Optional[int] = None
    passenger_app_id: Optional[int] = None
    custom_config: Optional[
        constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    ] = None
    allow_override_directives: Optional[List[AllowOverrideDirectiveEnum]] = None
    allow_override_option_directives: Optional[
        List[AllowOverrideOptionDirectiveEnum]
    ] = None
    server_software_name: Optional[VirtualHostServerSoftwareNameEnum] = None


class BorgArchiveContent(BaseCoreApiModel):
    object_type: BorgArchiveContentObjectTypeEnum
    symbolic_mode: constr(pattern=r"^[rwx\+\-dlsStT]+$", min_length=10, max_length=10)
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=32)
    group_name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=32)
    path: str
    link_target: Optional[str]
    modification_time: datetime
    size: Optional[conint(ge=0)]


class CMSCreateRequest(BaseCoreApiModel):
    software_name: CMSSoftwareNameEnum
    virtual_host_id: int


class CMSOption(BaseCoreApiModel):
    value: conint(ge=0, le=1)
    name: CMSOptionNameEnum


class CertificateManagerCreateRequest(BaseCoreApiModel):
    common_names: List[str] = Field(
        ...,
        min_length=1,
    )
    provider_name: CertificateProviderNameEnum = (
        CertificateProviderNameEnum.LETS_ENCRYPT
    )
    cluster_id: int
    request_callback_url: Optional[AnyUrl] = None


class ClusterCreateRequest(BaseCoreApiModel):
    customer_id: int
    region_id: int
    description: constr(pattern=r"^[a-zA-Z0-9-_. ]+$", min_length=1, max_length=255)
    cephfs_enabled: bool


class ClusterDeploymentTaskResult(BaseCoreApiModel):
    description: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    message: Optional[str]
    state: TaskStateEnum


class ClusterIPAddressCreateRequest(BaseCoreApiModel):
    service_account_name: str
    dns_name: str
    address_family: IPAddressFamilyEnum


class ClusterIncludes(BaseCoreApiModel):
    region: Optional[RegionResource]
    customer: Optional[CustomerResource]


class ClusterResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-.]+$", min_length=1, max_length=64)
    customer_id: int
    region_id: int
    description: constr(pattern=r"^[a-zA-Z0-9-_. ]+$", min_length=1, max_length=255)
    includes: ClusterIncludes


class ClusterUpdateRequest(BaseCoreApiModel):
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_. ]+$", min_length=1, max_length=255)
    ] = None


class ClustersCommonProperties(BaseCoreApiModel):
    imap_hostname: str
    imap_port: int
    imap_encryption: EncryptionTypeEnum
    smtp_hostname: str
    smtp_port: int
    smtp_encryption: EncryptionTypeEnum
    pop3_hostname: str
    pop3_port: int
    pop3_encryption: EncryptionTypeEnum
    phpmyadmin_url: AnyUrl


class CustomConfigCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=128)
    server_software_name: CustomConfigServerSoftwareNameEnum
    cluster_id: int
    contents: constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)


class CustomConfigIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class CustomConfigResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=128)
    cluster_id: int
    contents: constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    server_software_name: CustomConfigServerSoftwareNameEnum
    includes: CustomConfigIncludes


class CustomConfigSnippetCreateFromContentsRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=128)
    server_software_name: VirtualHostServerSoftwareNameEnum
    cluster_id: int
    is_default: bool = False
    contents: constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)


class CustomConfigSnippetCreateFromTemplateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=128)
    server_software_name: VirtualHostServerSoftwareNameEnum
    cluster_id: int
    is_default: bool = False
    template_name: CustomConfigSnippetTemplateNameEnum


class CustomConfigSnippetIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class CustomConfigSnippetResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=128)
    server_software_name: VirtualHostServerSoftwareNameEnum
    contents: constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    cluster_id: int
    is_default: bool
    includes: CustomConfigSnippetIncludes


class CustomerIPAddressCreateRequest(BaseCoreApiModel):
    service_account_name: str
    dns_name: str
    address_family: IPAddressFamilyEnum


class DatabaseCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=63)
    server_software_name: DatabaseServerSoftwareNameEnum
    cluster_id: int
    optimizing_enabled: bool = False
    backups_enabled: bool = True


class DatabaseIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class DatabaseResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=63)
    server_software_name: DatabaseServerSoftwareNameEnum
    cluster_id: int
    optimizing_enabled: bool
    backups_enabled: bool
    includes: DatabaseIncludes


class DatabaseUserCreateRequest(BaseCoreApiModel):
    password: constr(pattern=r"^[ -~]+$", min_length=24, max_length=255)
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=63)
    server_software_name: DatabaseServerSoftwareNameEnum
    cluster_id: int
    phpmyadmin_firewall_groups_ids: Optional[List[int]] = None


class DatabaseUserGrantCreateRequest(BaseCoreApiModel):
    database_id: int
    database_user_id: int
    table_name: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    ]
    privilege_name: MariaDBPrivilegeEnum


class DatabaseUserIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class DatabaseUserResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=63)
    server_software_name: DatabaseServerSoftwareNameEnum
    host: Optional[str]
    cluster_id: int
    phpmyadmin_firewall_groups_ids: Optional[List[int]]
    includes: DatabaseUserIncludes


class FirewallGroupIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class FirewallGroupResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9_]+$", min_length=1, max_length=32)
    cluster_id: int
    ip_networks: List[str] = Field(
        ...,
        min_length=1,
    )
    includes: FirewallGroupIncludes


class FirewallRuleCreateRequest(BaseCoreApiModel):
    node_id: int
    firewall_group_id: Optional[int]
    external_provider_name: Optional[FirewallRuleExternalProviderNameEnum]
    service_name: Optional[FirewallRuleServiceNameEnum]
    haproxy_listen_id: Optional[int]
    port: Optional[int]


class HAProxyListenCreateRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z_]+$", min_length=1, max_length=64)
    cluster_id: int
    nodes_group: NodeGroupEnum
    nodes_ids: Optional[List[int]] = None
    port: Optional[int]
    socket_path: Optional[str]
    load_balancing_method: LoadBalancingMethodEnum = Field(
        LoadBalancingMethodEnum.SOURCE_IP_ADDRESS,
    )
    destination_cluster_id: int


class HAProxyListenIncludes(BaseCoreApiModel):
    destination_cluster: Optional[ClusterResource]
    cluster: Optional[ClusterResource]


class HAProxyListenResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z_]+$", min_length=1, max_length=64)
    cluster_id: int
    nodes_group: NodeGroupEnum
    nodes_ids: Optional[List[int]]
    port: Optional[int]
    socket_path: Optional[str]
    load_balancing_method: Optional[LoadBalancingMethodEnum] = (
        LoadBalancingMethodEnum.SOURCE_IP_ADDRESS
    )
    destination_cluster_id: int
    includes: HAProxyListenIncludes


class HTTPValidationError(BaseCoreApiModel):
    detail: Optional[List[ValidationError]] = None


class HealthResource(BaseCoreApiModel):
    status: HealthStatusEnum


class IPAddressProduct(BaseCoreApiModel):
    uuid: UUID4
    name: constr(pattern=r"^[a-zA-Z0-9 ]+$", min_length=1, max_length=64)
    type: IPAddressProductTypeEnum
    price: confloat(ge=0.0)
    period: constr(pattern=r"^[A-Z0-9]+$", min_length=2, max_length=2)
    currency: constr(pattern=r"^[A-Z]+$", min_length=3, max_length=3)


class VirtualHostAccessLogResource(BaseCoreApiModel):
    remote_address: str
    raw_message: constr(min_length=1, max_length=65535)
    method: Optional[LogMethodEnum] = None
    uri: Optional[constr(min_length=1, max_length=65535)] = None
    timestamp: datetime
    status_code: int
    bytes_sent: conint(ge=0)


class VirtualHostErrorLogResource(BaseCoreApiModel):
    remote_address: str
    raw_message: constr(min_length=1, max_length=65535)
    method: Optional[LogMethodEnum] = None
    uri: Optional[constr(min_length=1, max_length=65535)] = None
    timestamp: datetime
    error_message: constr(min_length=1, max_length=65535)


class MariaDBEncryptionKeyIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class MariaDBEncryptionKeyResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    identifier: int
    key: constr(pattern=r"^[a-z0-9]+$", min_length=64, max_length=64)
    cluster_id: int
    includes: MariaDBEncryptionKeyIncludes


class NodeGroupDependency(BaseCoreApiModel):
    is_dependency: bool
    impact: Optional[str]
    reason: str
    group: NodeGroupEnum


class NodeGroupsProperties(BaseCoreApiModel):
    Redis: Optional[NodeRedisGroupProperties]
    MariaDB: Optional[NodeMariaDBGroupProperties]
    RabbitMQ: Optional[NodeRabbitMQGroupProperties]


class NodeIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class NodeResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    hostname: str
    product: constr(pattern=r"^[A-Z]+$", min_length=1, max_length=2)
    cluster_id: int
    groups: List[NodeGroupEnum]
    comment: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ]
    load_balancer_health_checks_groups_pairs: Dict[NodeGroupEnum, List[NodeGroupEnum]]
    groups_properties: NodeGroupsProperties
    is_ready: bool
    includes: NodeIncludes


class NodeUpdateRequest(BaseCoreApiModel):
    comment: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ] = None
    load_balancer_health_checks_groups_pairs: Optional[
        Dict[NodeGroupEnum, List[NodeGroupEnum]]
    ] = None


class PassengerAppCreateNodeJSRequest(BaseCoreApiModel):
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    app_root: str
    unix_user_id: int
    environment: PassengerEnvironmentEnum
    environment_variables: Dict[
        constr(pattern=r"^[A-Za-z_]+$"), constr(pattern=r"^[ -~]+$")
    ] = {}
    max_pool_size: int = 10
    max_requests: int = 2000
    pool_idle_time: int = 10
    is_namespaced: bool = True
    cpu_limit: Optional[int] = None
    nodejs_version: constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")
    startup_file: str


class PassengerAppUpdateRequest(BaseCoreApiModel):
    environment: Optional[PassengerEnvironmentEnum] = None
    environment_variables: Optional[
        Dict[constr(pattern=r"^[A-Za-z_]+$"), constr(pattern=r"^[ -~]+$")]
    ] = None
    max_pool_size: Optional[int] = None
    max_requests: Optional[int] = None
    pool_idle_time: Optional[int] = None
    is_namespaced: Optional[bool] = None
    cpu_limit: Optional[int] = None
    nodejs_version: Optional[constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")] = None
    startup_file: Optional[str] = None


class RedisInstanceIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class RedisInstanceResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    port: int
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    password: constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    memory_limit: conint(ge=8)
    max_databases: int
    eviction_policy: RedisEvictionPolicyEnum
    includes: RedisInstanceIncludes


class RootSSHKeyIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class RootSSHKeyResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    public_key: Optional[str]
    private_key: Optional[str]
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    includes: RootSSHKeyIncludes


class SecurityTXTPolicyIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class SecurityTXTPolicyResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    expires_timestamp: datetime
    email_contacts: List[EmailStr]
    url_contacts: List[AnyUrl]
    encryption_key_urls: List[AnyUrl]
    acknowledgment_urls: List[AnyUrl]
    policy_urls: List[AnyUrl]
    opening_urls: List[AnyUrl]
    preferred_languages: List[LanguageCodeEnum]
    includes: SecurityTXTPolicyIncludes


class TaskCollectionIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class TaskCollectionResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    objects_ids: List[int]
    object_model_name: ObjectModelNameEnum
    uuid: UUID4
    description: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    collection_type: TaskCollectionTypeEnum
    cluster_id: Optional[int]
    reference: constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    includes: TaskCollectionIncludes


class TaskResult(BaseCoreApiModel):
    description: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    uuid: UUID4
    message: Optional[str]
    state: TaskStateEnum
    retries: conint(ge=0)
    free_form_data: Dict[str, Any]


class TokenResource(BaseCoreApiModel):
    access_token: constr(pattern=r"^[ -~]+$", min_length=1)
    token_type: TokenTypeEnum
    expires_in: int


class UNIXUserIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource] = None


class UNIXUserResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=32)
    unix_id: int
    home_directory: str
    ssh_directory: str
    virtual_hosts_directory: Optional[str]
    mail_domains_directory: Optional[str]
    cluster_id: int
    shell_name: ShellNameEnum
    record_usage_files: bool
    default_php_version: Optional[str]
    default_nodejs_version: Optional[constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")]
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ]
    shell_is_namespaced: bool
    includes: UNIXUserIncludes


class URLRedirectIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class URLRedirectResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    domain: str
    cluster_id: int
    server_aliases: List[str]
    destination_url: AnyUrl
    status_code: StatusCodeEnum
    keep_query_parameters: bool
    keep_path: bool
    description: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ]
    includes: URLRedirectIncludes


class VirtualHostCreateRequest(BaseCoreApiModel):
    server_software_name: Optional[VirtualHostServerSoftwareNameEnum]
    allow_override_directives: Optional[List[AllowOverrideDirectiveEnum]] = None
    allow_override_option_directives: Optional[
        List[AllowOverrideOptionDirectiveEnum]
    ] = None
    domain: str
    unix_user_id: int
    server_aliases: List[str] = Field(
        [],
    )
    document_root: str | None = None
    fpm_pool_id: Optional[int] = None
    passenger_app_id: Optional[int] = None
    custom_config: Optional[
        constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    ] = None


class BorgRepositoryIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    database: Optional[DatabaseResource]
    cluster: Optional[ClusterResource]


class BorgRepositoryResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    keep_hourly: Optional[int]
    keep_daily: Optional[int]
    keep_weekly: Optional[int]
    keep_monthly: Optional[int]
    keep_yearly: Optional[int]
    unix_user_id: Optional[int]
    unix_id: int
    includes: BorgRepositoryIncludes


class CertificateIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]


class CertificateResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    main_common_name: str
    common_names: List[str] = Field(
        ...,
        min_length=1,
    )
    expires_at: datetime
    certificate: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n\\ ]+$", min_length=1, max_length=65535
    )
    ca_chain: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n\\ ]+$", min_length=1, max_length=65535
    )
    private_key: constr(
        pattern=r"^[a-zA-Z0-9-_\+\/=\n\\ ]+$", min_length=1, max_length=65535
    )
    cluster_id: int
    includes: CertificateIncludes


class ClusterDeploymentResults(BaseCoreApiModel):
    created_at: datetime
    tasks_results: List[ClusterDeploymentTaskResult]


class CronIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]
    unix_user: Optional[UNIXUserResource]
    node: Optional[NodeResource]


class CronResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    node_id: int
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    unix_user_id: int
    command: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    email_address: Optional[EmailStr]
    schedule: str
    error_count: int
    random_delay_max_seconds: int
    timeout_seconds: Optional[int]
    locking_enabled: bool
    is_active: bool
    memory_limit: Optional[conint(ge=256)]
    cpu_limit: Optional[int]
    includes: CronIncludes


class DaemonIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class DaemonResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    unix_user_id: int
    command: constr(pattern=r"^[ -~]+$", min_length=1, max_length=65535)
    nodes_ids: List[int]
    memory_limit: Optional[conint(ge=256)]
    cpu_limit: Optional[int]
    includes: DaemonIncludes


class DatabaseUserGrantIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]
    database: Optional[DatabaseResource]
    database_user: Optional[DatabaseUserResource]


class DatabaseUserGrantResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    database_id: int
    database_user_id: int
    table_name: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    ]
    privilege_name: MariaDBPrivilegeEnum
    includes: DatabaseUserGrantIncludes


class FPMPoolIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class FPMPoolResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    version: str
    unix_user_id: int
    max_children: int
    max_requests: int
    process_idle_timeout: int
    cpu_limit: Optional[int]
    log_slow_requests_threshold: Optional[int]
    is_namespaced: bool
    memory_limit: Optional[conint(ge=256)]
    includes: FPMPoolIncludes


class FTPUserIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class FTPUserResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    username: constr(pattern=r"^[a-z0-9-_.@]+$", min_length=1, max_length=32)
    unix_user_id: int
    directory_path: str
    includes: FTPUserIncludes


class FirewallRuleIncludes(BaseCoreApiModel):
    node: Optional[NodeResource]
    firewall_group: Optional[FirewallGroupResource]
    haproxy_listen: Optional[HAProxyListenResource]
    cluster: Optional[ClusterResource]


class FirewallRuleResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    node_id: int
    firewall_group_id: Optional[int]
    external_provider_name: Optional[FirewallRuleExternalProviderNameEnum]
    service_name: Optional[FirewallRuleServiceNameEnum]
    haproxy_listen_id: Optional[int]
    port: Optional[int]
    includes: FirewallRuleIncludes


class HAProxyListenToNodeIncludes(BaseCoreApiModel):
    haproxy_listen: Optional[HAProxyListenResource]
    node: Optional[NodeResource]
    cluster: Optional[ClusterResource]


class HAProxyListenToNodeResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    haproxy_listen_id: int
    node_id: int
    includes: HAProxyListenToNodeIncludes


class HostsEntryIncludes(BaseCoreApiModel):
    node: Optional[NodeResource]
    cluster: Optional[ClusterResource]


class HostsEntryResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    node_id: int
    host_name: str
    cluster_id: int
    includes: HostsEntryIncludes


class HtpasswdFileIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class HtpasswdFileResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    unix_user_id: int
    includes: HtpasswdFileIncludes


class HtpasswdUserIncludes(BaseCoreApiModel):
    htpasswd_file: Optional[HtpasswdFileResource]
    cluster: Optional[ClusterResource]


class HtpasswdUserResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    username: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=255)
    htpasswd_file_id: int
    includes: HtpasswdUserIncludes


class MailDomainIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class MailDomainResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    domain: str
    unix_user_id: int
    catch_all_forward_email_addresses: List[EmailStr]
    is_local: bool
    includes: MailDomainIncludes


class MailHostnameIncludes(BaseCoreApiModel):
    certificate: Optional[CertificateResource]
    cluster: Optional[ClusterResource]


class MailHostnameResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    domain: str
    cluster_id: int
    certificate_id: int
    includes: MailHostnameIncludes


class MalwareIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class MalwareResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    unix_user_id: int
    name: constr(pattern=r"^\{([A-Z]+)\}[a-zA-Z0-9-_.]+$", min_length=1, max_length=255)
    path: str
    last_seen_at: datetime
    includes: MalwareIncludes


class NodeAddOnIncludes(BaseCoreApiModel):
    node: Optional[NodeResource]
    cluster: Optional[ClusterResource]


class NodeAddOnResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    node_id: int
    product: constr(pattern=r"^[a-zA-Z0-9 ]+$", min_length=1, max_length=64)
    quantity: int
    includes: NodeAddOnIncludes


class NodeCreateRequest(BaseCoreApiModel):
    product: constr(pattern=r"^[A-Z]+$", min_length=1, max_length=2)
    cluster_id: int
    groups: List[NodeGroupEnum]
    comment: Optional[
        constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=255)
    ] = None
    load_balancer_health_checks_groups_pairs: Dict[NodeGroupEnum, List[NodeGroupEnum]]


class NodeCronDependency(BaseCoreApiModel):
    is_dependency: bool
    impact: Optional[str]
    reason: str
    cron: CronResource


class NodeDaemonDependency(BaseCoreApiModel):
    is_dependency: bool
    impact: Optional[str]
    reason: str
    daemon: DaemonResource


class NodeHostsEntryDependency(BaseCoreApiModel):
    is_dependency: bool
    impact: Optional[str]
    reason: str
    hosts_entry: HostsEntryResource


class PassengerAppIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class PassengerAppResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    port: int
    app_type: PassengerAppTypeEnum
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    app_root: str
    unix_user_id: int
    environment: PassengerEnvironmentEnum
    environment_variables: Dict[
        constr(pattern=r"^[A-Za-z_]+$"), constr(pattern=r"^[ -~]+$")
    ]
    max_pool_size: int
    max_requests: int
    pool_idle_time: int
    is_namespaced: bool
    cpu_limit: Optional[int]
    includes: PassengerAppIncludes
    nodejs_version: Optional[constr(pattern=r"^[0-9]{1,2}\.[0-9]{1,2}$")]
    startup_file: Optional[str]


class SSHKeyIncludes(BaseCoreApiModel):
    unix_user: Optional[UNIXUserResource]
    cluster: Optional[ClusterResource]


class SSHKeyResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    public_key: Optional[str]
    private_key: Optional[str]
    identity_file_path: Optional[str]
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=128)
    unix_user_id: int
    includes: SSHKeyIncludes


class VirtualHostIncludes(BaseCoreApiModel):
    cluster: Optional[ClusterResource]
    unix_user: Optional[UNIXUserResource]
    fpm_pool: Optional[FPMPoolResource]
    passenger_app: Optional[PassengerAppResource]


class VirtualHostResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    unix_user_id: int
    server_software_name: VirtualHostServerSoftwareNameEnum
    allow_override_directives: Optional[List[AllowOverrideDirectiveEnum]]
    allow_override_option_directives: Optional[List[AllowOverrideOptionDirectiveEnum]]
    cluster_id: int
    domain: str
    server_aliases: List[str]
    document_root: str
    fpm_pool_id: Optional[int]
    passenger_app_id: Optional[int]
    custom_config: Optional[
        constr(pattern=r"^[ -~\n]+$", min_length=1, max_length=65535)
    ]
    includes: VirtualHostIncludes


class BasicAuthenticationRealmIncludes(BaseCoreApiModel):
    htpasswd_file: Optional[HtpasswdFileResource]
    virtual_host: Optional[VirtualHostResource]
    cluster: Optional[ClusterResource]


class BasicAuthenticationRealmResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    directory_path: Optional[str]
    uri_path: Optional[str]
    virtual_host_id: int
    name: constr(pattern=r"^[a-zA-Z0-9-_ ]+$", min_length=1, max_length=64)
    htpasswd_file_id: int
    includes: BasicAuthenticationRealmIncludes


class BorgArchiveIncludes(BaseCoreApiModel):
    borg_repository: Optional[BorgRepositoryResource]
    cluster: Optional[ClusterResource]


class BorgArchiveResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    borg_repository_id: int
    name: constr(pattern=r"^[a-zA-Z0-9-_]+$", min_length=1, max_length=64)
    includes: BorgArchiveIncludes


class CMSIncludes(BaseCoreApiModel):
    virtual_host: Optional[VirtualHostResource]
    cluster: Optional[ClusterResource]


class CMSResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    software_name: CMSSoftwareNameEnum
    is_manually_created: bool
    virtual_host_id: int
    includes: CMSIncludes


class CertificateManagerIncludes(BaseCoreApiModel):
    certificate: Optional[CertificateResource]
    cluster: Optional[ClusterResource]


class CertificateManagerResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    main_common_name: str
    certificate_id: Optional[int]
    last_request_task_collection_uuid: Optional[UUID4]
    common_names: List[str] = Field(
        ...,
        min_length=1,
    )
    provider_name: CertificateProviderNameEnum
    cluster_id: int
    request_callback_url: Optional[AnyUrl]
    includes: CertificateManagerIncludes


class DomainRouterIncludes(BaseCoreApiModel):
    virtual_host: Optional[VirtualHostResource]
    url_redirect: Optional[URLRedirectResource]
    node: Optional[NodeResource]
    certificate: Optional[CertificateResource]
    security_txt_policy: Optional[SecurityTXTPolicyResource]
    cluster: Optional[ClusterResource]


class DomainRouterResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    domain: str
    virtual_host_id: Optional[int]
    url_redirect_id: Optional[int]
    category: DomainRouterCategoryEnum
    cluster_id: int
    node_id: Optional[int]
    certificate_id: Optional[int]
    security_txt_policy_id: Optional[int]
    firewall_groups_ids: Optional[List[int]]
    force_ssl: bool
    includes: DomainRouterIncludes


class MailAccountIncludes(BaseCoreApiModel):
    mail_domain: Optional[MailDomainResource]
    cluster: Optional[ClusterResource]


class MailAccountResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    local_part: constr(pattern=r"^[a-z0-9-.]+$", min_length=1, max_length=64)
    mail_domain_id: int
    cluster_id: int
    quota: Optional[int]
    includes: MailAccountIncludes


class MailAliasIncludes(BaseCoreApiModel):
    mail_domain: Optional[MailDomainResource]
    cluster: Optional[ClusterResource]


class MailAliasResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    cluster_id: int
    local_part: constr(pattern=r"^[a-z0-9-.]+$", min_length=1, max_length=64)
    mail_domain_id: int
    forward_email_addresses: List[EmailStr] = Field(
        ...,
        min_length=1,
    )
    includes: MailAliasIncludes


class NodeDomainRouterDependency(BaseCoreApiModel):
    is_dependency: bool
    impact: Optional[str]
    reason: str
    domain_router: DomainRouterResource


class NodeDependenciesResource(BaseCoreApiModel):
    hostname: str
    groups: List[NodeGroupDependency]
    domain_routers: List[NodeDomainRouterDependency]
    daemons: List[NodeDaemonDependency]
    crons: List[NodeCronDependency]
    hosts_entries: List[NodeHostsEntryDependency]


class DaemonLogResource(BaseCoreApiModel):
    application_name: constr(min_length=1, max_length=65535)
    priority: int
    pid: int
    message: constr(min_length=1, max_length=65535)
    node_hostname: str
    timestamp: datetime


class NodeSpecificationsResource(BaseCoreApiModel):
    hostname: str
    memory_mib: int
    cpu_cores: int
    disk_gib: int
    usable_cpu_cores: int
    usable_memory_mib: int
    usable_disk_gib: int


class RequestLogIncludes(BaseCoreApiModel):
    pass


class RequestLogResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    ip_address: str
    path: str
    method: HTTPMethod
    query_parameters: Dict[str, str]
    body: Any
    api_user_id: int
    request_id: UUID4
    includes: RequestLogIncludes


class ObjectLogIncludes(BaseCoreApiModel):
    customer: Optional[CustomerResource]


class ObjectLogResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    object_id: int
    object_model_name: Optional[
        constr(pattern=r"^[a-zA-Z]+$", min_length=1, max_length=255)
    ]
    request_id: Optional[UUID4]
    type: ObjectLogTypeEnum
    causer_type: Optional[CauserTypeEnum]
    causer_id: Optional[int]
    customer_id: Optional[int]
    includes: ObjectLogIncludes


class SimpleSpecificationsResource(RootModelCollectionMixin, RootCoreApiModel):  # type: ignore[misc]
    root: List[str]


class ConcreteSpecificationSatisfyResult(BaseCoreApiModel):
    satisfied: bool
    requirement: str


class ConcreteSpecificationSatisfyResultResource(BaseCoreApiModel):
    satisfied: bool
    requirement: str


class CompositeSpecificationSatisfyResult(BaseCoreApiModel):
    name: str
    results: List[
        Union[ConcreteSpecificationSatisfyResult, "CompositeSpecificationSatisfyResult"]
    ]
    mode: SpecificationMode


class CompositeSpecificationSatisfyResultResource(BaseCoreApiModel):
    name: str
    satisfied: bool
    results: List[
        Union[
            ConcreteSpecificationSatisfyResultResource,
            "CompositeSpecificationSatisfyResultResource",
        ]
    ]
    mode: SpecificationMode


class ClusterBorgPropertiesCreateRequest(BaseCoreApiModel):
    automatic_borg_repositories_prune_enabled: bool = True


class ClusterBorgPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterBorgPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    automatic_borg_repositories_prune_enabled: bool
    cluster_id: int
    includes: ClusterBorgPropertiesIncludes


class ClusterBorgPropertiesUpdateRequest(BaseCoreApiModel):
    automatic_borg_repositories_prune_enabled: Optional[bool] = None


class ClusterElasticsearchPropertiesCreateRequest(BaseCoreApiModel):
    elasticsearch_default_users_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )
    kibana_domain: str


class ClusterElasticsearchPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterElasticsearchPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    elasticsearch_default_users_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )
    kibana_domain: str
    cluster_id: int
    includes: ClusterElasticsearchPropertiesIncludes


class ClusterElasticsearchPropertiesUpdateRequest(BaseCoreApiModel):
    elasticsearch_default_users_password: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    ] = None
    kibana_domain: Optional[str] = None


class ClusterFirewallPropertiesCreateRequest(BaseCoreApiModel):
    firewall_rules_external_providers_enabled: bool = False


class ClusterFirewallPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterFirewallPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    firewall_rules_external_providers_enabled: bool
    cluster_id: int
    includes: ClusterFirewallPropertiesIncludes


class ClusterFirewallPropertiesUpdateRequest(BaseCoreApiModel):
    firewall_rules_external_providers_enabled: Optional[bool] = None


class ClusterGrafanaPropertiesCreateRequest(BaseCoreApiModel):
    grafana_domain: str


class ClusterGrafanaPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterGrafanaPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    grafana_domain: str
    cluster_id: int
    includes: ClusterGrafanaPropertiesIncludes


class ClusterGrafanaPropertiesUpdateRequest(BaseCoreApiModel):
    grafana_domain: Optional[str] = None


class ClusterKernelcarePropertiesCreateRequest(BaseCoreApiModel):
    kernelcare_license_key: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=16
    )


class ClusterKernelcarePropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterKernelcarePropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    kernelcare_license_key: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=16
    )
    cluster_id: int
    includes: ClusterKernelcarePropertiesIncludes


class ClusterKernelcarePropertiesUpdateRequest(BaseCoreApiModel):
    kernelcare_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=16)
    ] = None


class ClusterLoadBalancingPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterMariadbPropertiesCreateRequest(BaseCoreApiModel):
    mariadb_version: str = "11.4"
    mariadb_backup_interval: conint(ge=1, le=24) = 24
    mariadb_backup_local_retention: conint(ge=1, le=24) = 3


class ClusterMariadbPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterMariadbPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    mariadb_version: str
    mariadb_backup_interval: conint(ge=1, le=24)
    mariadb_backup_local_retention: conint(ge=1, le=24)
    cluster_id: int
    includes: ClusterMariadbPropertiesIncludes


class ClusterMariadbPropertiesUpdateRequest(BaseCoreApiModel):
    mariadb_backup_interval: Optional[conint(ge=1, le=24)] = None
    mariadb_backup_local_retention: Optional[conint(ge=1, le=24)] = None


class ClusterMeilisearchPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterMetabasePropertiesCreateRequest(BaseCoreApiModel):
    metabase_domain: str


class ClusterMetabasePropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterMetabasePropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    metabase_domain: str
    cluster_id: int
    includes: ClusterMetabasePropertiesIncludes


class ClusterMetabasePropertiesUpdateRequest(BaseCoreApiModel):
    metabase_domain: Optional[str] = None


class ClusterNewRelicPropertiesCreateRequest(BaseCoreApiModel):
    new_relic_apm_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ] = None
    new_relic_infrastructure_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ] = None


class ClusterNewRelicPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterNewRelicPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    new_relic_apm_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ]
    new_relic_infrastructure_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ]
    cluster_id: int
    includes: ClusterNewRelicPropertiesIncludes


class ClusterNewRelicPropertiesUpdateRequest(BaseCoreApiModel):
    new_relic_apm_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ] = None
    new_relic_infrastructure_license_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=40, max_length=40)
    ] = None


class ClusterNodejsPropertiesCreateRequest(BaseCoreApiModel):
    nodejs_versions: List[str]


class ClusterNodejsPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterNodejsPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    nodejs_versions: List[NodejsVersion]
    cluster_id: int
    includes: ClusterNodejsPropertiesIncludes


class ClusterNodejsPropertiesUpdateRequest(BaseCoreApiModel):
    nodejs_versions: Optional[List[str]] = None


class ClusterOsPropertiesCreateRequest(BaseCoreApiModel):
    automatic_upgrades_enabled: bool = False


class ClusterOsPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterOsPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    automatic_upgrades_enabled: bool
    cluster_id: int
    includes: ClusterOsPropertiesIncludes


class ClusterOsPropertiesUpdateRequest(BaseCoreApiModel):
    automatic_upgrades_enabled: Optional[bool] = None


class ClusterPhpPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterPostgresqlPropertiesCreateRequest(BaseCoreApiModel):
    postgresql_version: int = 15
    postgresql_backup_local_retention: conint(ge=1, le=24) = 3
    postgresql_backup_interval: conint(ge=1, le=24) = 24


class ClusterPostgresqlPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterPostgresqlPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    postgresql_version: int
    postgresql_backup_local_retention: conint(ge=1, le=24)
    postgresql_backup_interval: conint(ge=1, le=24)
    cluster_id: int
    includes: ClusterPostgresqlPropertiesIncludes


class ClusterPostgresqlPropertiesUpdateRequest(BaseCoreApiModel):
    postgresql_backup_local_retention: Optional[conint(ge=1, le=24)] = None
    postgresql_backup_interval: Optional[conint(ge=1, le=24)] = None


class ClusterRabbitmqPropertiesCreateRequest(BaseCoreApiModel):
    rabbitmq_admin_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )
    rabbitmq_management_domain: str


class ClusterRabbitmqPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterRabbitmqPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    rabbitmq_admin_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )
    rabbitmq_management_domain: str
    cluster_id: int
    includes: ClusterRabbitmqPropertiesIncludes


class ClusterRabbitmqPropertiesUpdateRequest(BaseCoreApiModel):
    rabbitmq_admin_password: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    ] = None
    rabbitmq_management_domain: Optional[str] = None


class ClusterRedisPropertiesCreateRequest(BaseCoreApiModel):
    redis_password: constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    redis_memory_limit: int


class ClusterRedisPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterRedisPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    redis_password: constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    redis_memory_limit: int
    cluster_id: int
    includes: ClusterRedisPropertiesIncludes


class ClusterRedisPropertiesUpdateRequest(BaseCoreApiModel):
    redis_password: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    ] = None
    redis_memory_limit: Optional[int] = None


class ClusterSinglestorePropertiesCreateRequest(BaseCoreApiModel):
    singlestore_studio_domain: str
    singlestore_api_domain: str
    singlestore_license_key: constr(pattern=r"^[ -~]+$", min_length=144, max_length=144)
    singlestore_root_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )


class ClusterSinglestorePropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterSinglestorePropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    singlestore_studio_domain: str
    singlestore_api_domain: str
    singlestore_license_key: constr(
        pattern=r"^[ -~]+$", min_length=144, max_length=6144
    )
    singlestore_root_password: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255
    )
    cluster_id: int
    includes: ClusterSinglestorePropertiesIncludes


class ClusterSinglestorePropertiesUpdateRequest(BaseCoreApiModel):
    singlestore_studio_domain: Optional[str] = None
    singlestore_api_domain: Optional[str] = None
    singlestore_license_key: Optional[
        constr(pattern=r"^[ -~]+$", min_length=144, max_length=144)
    ] = None
    singlestore_root_password: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=24, max_length=255)
    ] = None


class ClusterUnixUsersPropertiesIncludes(BaseCoreApiModel):
    pass


class ClusterLoadBalancingPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    http_retry_properties: HTTPRetryProperties
    load_balancing_method: LoadBalancingMethodEnum
    cluster_id: int
    includes: ClusterLoadBalancingPropertiesIncludes


class ClusterLoadBalancingPropertiesUpdateRequest(BaseCoreApiModel):
    http_retry_properties: Optional[HTTPRetryProperties] = None
    load_balancing_method: Optional[LoadBalancingMethodEnum] = None


class ClusterMeilisearchPropertiesCreateRequest(BaseCoreApiModel):
    meilisearch_backup_local_retention: conint(ge=1, le=24) = 3
    meilisearch_master_key: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=24
    )
    meilisearch_environment: MeilisearchEnvironmentEnum
    meilisearch_backup_interval: conint(ge=1, le=24) = 24


class ClusterMeilisearchPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    meilisearch_backup_local_retention: conint(ge=1, le=24)
    meilisearch_master_key: constr(
        pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=24
    )
    meilisearch_environment: MeilisearchEnvironmentEnum
    meilisearch_backup_interval: conint(ge=1, le=24)
    cluster_id: int
    includes: ClusterMeilisearchPropertiesIncludes


class ClusterMeilisearchPropertiesUpdateRequest(BaseCoreApiModel):
    meilisearch_backup_local_retention: Optional[conint(ge=1, le=24)] = None
    meilisearch_master_key: Optional[
        constr(pattern=r"^[a-zA-Z0-9]+$", min_length=16, max_length=24)
    ] = None
    meilisearch_environment: Optional[MeilisearchEnvironmentEnum] = None
    meilisearch_backup_interval: Optional[conint(ge=1, le=24)] = None


class ClusterPhpPropertiesCreateRequest(BaseCoreApiModel):
    php_versions: List[str]
    custom_php_modules_names: List[PHPExtensionEnum] = Field(
        [],
    )
    php_settings: PHPSettings
    php_ioncube_enabled: bool = False
    php_sessions_spread_enabled: bool = True


class ClusterPhpPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    php_versions: List[str]
    custom_php_modules_names: List[PHPExtensionEnum]
    php_settings: PHPSettings
    php_ioncube_enabled: bool
    php_sessions_spread_enabled: bool
    cluster_id: int
    includes: ClusterPhpPropertiesIncludes


class ClusterPhpPropertiesUpdateRequest(BaseCoreApiModel):
    php_versions: Optional[List[str]] = None
    custom_php_modules_names: Optional[List[PHPExtensionEnum]] = None
    php_settings: Optional[PHPSettings] = None
    php_ioncube_enabled: Optional[bool] = None
    php_sessions_spread_enabled: Optional[bool] = None


class ClusterUnixUsersPropertiesResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    unix_users_home_directory: UNIXUserHomeDirectoryEnum
    cluster_id: int
    includes: ClusterUnixUsersPropertiesIncludes


class SpecificationModeEnum(StrEnum):
    SINGLE = "Single"
    OR = "Or"
    AND = "And"


class SpecificationNameEnum(StrEnum):
    CLUSTER_SUPPORTS_VIRTUAL_HOSTS = "Cluster supports virtual hosts"
    CLUSTER_SUPPORTS_MARIADB_ENCRYPTION_KEYS = (
        "Cluster supports MariaDB encryption keys"
    )
    CLUSTER_SUPPORTS_MARIADB_DATABASES = "Cluster supports MariaDB databases"
    CLUSTER_SUPPORTS_MARIADB_DATABASE_USERS = "Cluster supports MariaDB database users"
    CLUSTER_SUPPORTS_POSTGRESQL_DATABASES = "Cluster supports PostgreSQL databases"
    CLUSTER_SUPPORTS_POSTGRESQL_DATABASE_USERS = (
        "Cluster supports PostgreSQL database users"
    )
    CLUSTER_SUPPORTS_NGINX_VIRTUAL_HOSTS = "Cluster supports nginx virtual hosts"
    CLUSTER_SUPPORTS_APACHE_VIRTUAL_HOSTS = "Cluster supports Apache virtual hosts"
    CLUSTER_SUPPORTS_NGINX_CUSTOM_CONFIGS = "Cluster supports nginx custom configs"
    CLUSTER_SUPPORTS_NGINX_CUSTOM_CONFIG_SNIPPETS = (
        "Cluster supports nginx custom config snippets"
    )
    CLUSTER_SUPPORTS_APACHE_CUSTOM_CONFIG_SNIPPETS = (
        "Cluster supports Apache custom config snippets"
    )
    CLUSTER_SUPPORTS_URL_REDIRECTS = "Cluster supports URL redirects"
    CLUSTER_SUPPORTS_HTPASSWD_FILES = "Cluster supports htpasswd files"
    CLUSTER_SUPPORTS_MAIL_DOMAINS = "Cluster supports mail domains"
    CLUSTER_SUPPORTS_MAIL_HOSTNAMES = "Cluster supports mail hostnames"
    CLUSTER_SUPPORTS_BORG_REPOSITORIES = "Cluster supports Borg repositories"
    CLUSTER_SUPPORTS_FTP_USERS = "Cluster supports FTP users"
    CLUSTER_SUPPORTS_FPM_POOLS = "Cluster supports FPM pools"
    CLUSTER_SUPPORTS_PASSENGER_APPS = "Cluster supports Passenger apps"
    CLUSTER_SUPPORTS_REDIS_INSTANCES = "Cluster supports Redis instances"
    CLUSTER_SUPPORTS_N8N_INSTANCES = "Cluster supports n8n instances"
    CLUSTER_SUPPORTS_UNIX_USERS = "Cluster supports UNIX users"
    CLUSTER_SUPPORTS_FIREWALL_RULES = "Cluster supports firewall rules"
    CLUSTER_SUPPORTS_FIREWALL_GROUPS = "Cluster supports firewall groups"
    CLUSTER_SUPPORTS_MALDET_NODES = "Cluster supports maldet nodes"
    CLUSTER_SUPPORTS_DOCKER_NODES = "Cluster supports Docker nodes"
    CLUSTER_SUPPORTS_FFMPEG_NODES = "Cluster supports FFmpeg nodes"
    CLUSTER_SUPPORTS_GHOSTSCRIPT_NODES = "Cluster supports Ghostscript nodes"
    CLUSTER_SUPPORTS_LIBREOFFICE_NODES = "Cluster supports LibreOffice nodes"
    CLUSTER_SUPPORTS_PUPPETEER_NODES = "Cluster supports Puppeteer nodes"
    CLUSTER_SUPPORTS_N8N_NODES = "Cluster supports n8n nodes"
    CLUSTER_SUPPORTS_CLAMAV_NODES = "Cluster supports ClamAV nodes"
    CLUSTER_SUPPORTS_GNU_MAILUTILS_NODES = "Cluster supports GNU Mailutils nodes"
    CLUSTER_SUPPORTS_WKHTMLTOPDF_NODES = "Cluster supports wkhtmltopdf nodes"
    CLUSTER_SUPPORTS_IMAGEMAGICK_NODES = "Cluster supports ImageMagick nodes"
    CLUSTER_SUPPORTS_HAPROXY_NODES = "Cluster supports HAProxy nodes"
    CLUSTER_SUPPORTS_PROFTPD_NODES = "Cluster supports ProFTPD nodes"
    CLUSTER_SUPPORTS_DOVECOT_NODES = "Cluster supports Dovecot nodes"
    CLUSTER_SUPPORTS_ADMIN_NODES = "Cluster supports admin nodes"
    CLUSTER_SUPPORTS_APACHE_NODES = "Cluster supports Apache nodes"
    CLUSTER_SUPPORTS_NGINX_NODES = "Cluster supports nginx nodes"
    CLUSTER_SUPPORTS_FAST_REDIRECT_NODES = "Cluster supports Fast Redirect nodes"
    CLUSTER_SUPPORTS_MARIADB_NODES = "Cluster supports MariaDB nodes"
    CLUSTER_SUPPORTS_POSTGRESQL_NODES = "Cluster supports PostgreSQL nodes"
    CLUSTER_SUPPORTS_PHP_NODES = "Cluster supports PHP nodes"
    CLUSTER_SUPPORTS_COMPOSER_NODES = "Cluster supports Composer nodes"
    CLUSTER_SUPPORTS_WP_CLI_NODES = "Cluster supports WP-CLI nodes"
    CLUSTER_SUPPORTS_NODEJS_NODES = "Cluster supports NodeJS nodes"
    CLUSTER_SUPPORTS_PASSENGER_NODES = "Cluster supports Passenger nodes"
    CLUSTER_SUPPORTS_KERNELCARE_NODES = "Cluster supports KernelCare nodes"
    CLUSTER_SUPPORTS_NEW_RELIC_NODES = "Cluster supports New Relic nodes"
    CLUSTER_SUPPORTS_REDIS_NODES = "Cluster supports Redis nodes"
    CLUSTER_SUPPORTS_MEILISEARCH_NODES = "Cluster supports Meilisearch nodes"
    CLUSTER_SUPPORTS_GRAFANA_NODES = "Cluster supports Grafana nodes"
    CLUSTER_SUPPORTS_SINGLESTORE_NODES = "Cluster supports SingleStore nodes"
    CLUSTER_SUPPORTS_ELASTICSEARCH_NODES = "Cluster supports Elasticsearch nodes"
    CLUSTER_SUPPORTS_RABBITMQ_NODES = "Cluster supports RabbitMQ nodes"
    CLUSTER_SUPPORTS_METABASE_NODES = "Cluster supports Metabase nodes"
    UNIX_USER_SUPPORTS_VIRTUAL_HOSTS = "UNIX user supports virtual hosts"
    UNIX_USER_SUPPORTS_MAIL_DOMAINS = "UNIX user supports mail domains"
    CLUSTER_SUPPORTS_LOAD_BALANCER_SERVICE_ACCOUNT_SERVICE_ACCOUNT_TO_CLUSTER = (
        "Cluster supports Load Balancer service account service account to cluster"
    )
    CLUSTER_SUPPORTS_DOMAIN_ROUTERS = "Cluster supports domain routers"
    CLUSTER_SUPPORTS_MARIADB_DATABASE_BORG_REPOSITORIES = (
        "Cluster supports MariaDB database Borg repositories"
    )
    CLUSTER_SUPPORTS_UNIX_USER_BORG_REPOSITORIES = (
        "Cluster supports UNIX user Borg repositories"
    )


class TableInnodbDataLengths(BaseCoreApiModel):
    name: str
    data_length_bytes: int
    index_length_bytes: int
    total_length_bytes: int


class DatabaseInnodbDataLengths(BaseCoreApiModel):
    name: str
    total_length_bytes: int
    tables_data_lengths: List[TableInnodbDataLengths]


class DatabaseInnodbReport(BaseCoreApiModel):
    innodb_buffer_pool_size_bytes: int
    total_innodb_data_length_bytes: int
    databases_innodb_data_lengths: List[DatabaseInnodbDataLengths]


class FPMPoolChildStatus(BaseCoreApiModel):
    current_request_duration: int
    http_method: HTTPMethod
    http_uri: str
    basic_authentication_user: Optional[str]
    script: str


class FPMPoolNodeStatus(BaseCoreApiModel):
    node_id: int
    child_statuses: List[FPMPoolChildStatus]
    current_amount_children: conint(ge=0)


class BasicAuthenticationRealmsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    virtual_host_id: Optional[int] = None
    name: Optional[str] = None
    htpasswd_file_id: Optional[int] = None


class BorgArchivesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    borg_repository_id: Optional[int] = None
    name: Optional[str] = None


class BorgRepositoriesSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    unix_id: Optional[int] = None
    cluster_id: Optional[int] = None
    unix_user_id: Optional[int] = None
    database_id: Optional[int] = None


class CertificatesSearchRequest(BaseCoreApiModel):
    main_common_name: Optional[str] = None
    common_names: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersBorgPropertiesSearchRequest(BaseCoreApiModel):
    automatic_borg_repositories_prune_enabled: Optional[bool] = None
    cluster_id: Optional[int] = None


class ClustersElasticsearchPropertiesSearchRequest(BaseCoreApiModel):
    kibana_domain: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersFirewallPropertiesSearchRequest(BaseCoreApiModel):
    firewall_rules_external_providers_enabled: Optional[bool] = None
    cluster_id: Optional[int] = None


class ClustersGrafanaPropertiesSearchRequest(BaseCoreApiModel):
    grafana_domain: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersKernelcarePropertiesSearchRequest(BaseCoreApiModel):
    kernelcare_license_key: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersMariadbPropertiesSearchRequest(BaseCoreApiModel):
    mariadb_version: Optional[str] = None
    mariadb_backup_interval: Optional[int] = None
    mariadb_backup_local_retention: Optional[int] = None
    cluster_id: Optional[int] = None


class ClustersMetabasePropertiesSearchRequest(BaseCoreApiModel):
    metabase_domain: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersNewRelicPropertiesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None


class ClustersNodejsPropertiesSearchRequest(BaseCoreApiModel):
    nodejs_versions: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersOsPropertiesSearchRequest(BaseCoreApiModel):
    automatic_upgrades_enabled: Optional[bool] = None
    cluster_id: Optional[int] = None


class ClustersPostgresqlPropertiesSearchRequest(BaseCoreApiModel):
    postgresql_version: Optional[int] = None
    postgresql_backup_local_retention: Optional[int] = None
    postgresql_backup_interval: Optional[int] = None
    cluster_id: Optional[int] = None


class ClustersRabbitmqPropertiesSearchRequest(BaseCoreApiModel):
    rabbitmq_management_domain: Optional[str] = None
    cluster_id: Optional[int] = None


class ClustersRedisPropertiesSearchRequest(BaseCoreApiModel):
    redis_memory_limit: Optional[int] = None
    cluster_id: Optional[int] = None


class ClustersSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    region_id: Optional[int] = None
    description: Optional[str] = None
    customer_id: Optional[int] = None
    cephfs_enabled: bool | None = None


class ClustersSinglestorePropertiesSearchRequest(BaseCoreApiModel):
    singlestore_studio_domain: Optional[str] = None
    singlestore_api_domain: Optional[str] = None
    cluster_id: Optional[int] = None


class CmsesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    software_name: Optional[CMSSoftwareNameEnum] = None
    is_manually_created: Optional[bool] = None
    virtual_host_id: Optional[int] = None


class CronsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    node_id: Optional[int] = None
    name: Optional[str] = None
    unix_user_id: Optional[int] = None
    email_address: Optional[EmailStr] = None
    locking_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class CustomConfigsSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    cluster_id: Optional[int] = None
    server_software_name: Optional[CustomConfigServerSoftwareNameEnum] = None


class CustomersSearchRequest(BaseCoreApiModel):
    identifier: Optional[str] = None
    dns_subdomain: Optional[str] = None
    is_internal: Optional[bool] = None
    team_code: Optional[str] = None


class DaemonsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    name: Optional[str] = None
    unix_user_id: Optional[int] = None
    nodes_ids: Optional[int] = None


class DatabaseUsersSearchRequest(BaseCoreApiModel):
    phpmyadmin_firewall_group_id: Optional[int] = None


class DatabasesSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    server_software_name: Optional[DatabaseServerSoftwareNameEnum] = None
    cluster_id: Optional[int] = None
    optimizing_enabled: Optional[bool] = None
    backups_enabled: Optional[bool] = None


class DomainRoutersSearchRequest(BaseCoreApiModel):
    domain: Optional[str] = None
    virtual_host_id: Optional[int] = None
    url_redirect_id: Optional[int] = None
    category: Optional[DomainRouterCategoryEnum] = None
    cluster_id: Optional[int] = None
    node_id: Optional[int] = None
    certificate_id: Optional[int] = None
    security_txt_policy_id: Optional[int] = None
    firewall_group_id: Optional[int] = None
    force_ssl: Optional[bool] = None


class FirewallGroupsSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    cluster_id: Optional[int] = None
    ip_networks: Optional[str] = None


class FirewallRulesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    node_id: Optional[int] = None
    firewall_group_id: Optional[int] = None
    external_provider_name: Optional[FirewallRuleExternalProviderNameEnum] = None
    service_name: Optional[FirewallRuleServiceNameEnum] = None
    haproxy_listen_id: Optional[int] = None
    port: Optional[int] = None


class FpmPoolsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    name: Optional[str] = None
    version: Optional[str] = None
    unix_user_id: Optional[int] = None
    max_children: Optional[int] = None
    is_namespaced: Optional[bool] = None


class FtpUsersSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    username: Optional[str] = None
    unix_user_id: Optional[int] = None


class HaproxyListensToNodesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    haproxy_listen_id: Optional[int] = None
    node_id: Optional[int] = None


class HostsEntriesSearchRequest(BaseCoreApiModel):
    node_id: Optional[int] = None
    host_name: Optional[str] = None
    cluster_id: Optional[int] = None


class HtpasswdFilesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    unix_user_id: Optional[int] = None


class HtpasswdUsersSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    username: Optional[str] = None
    htpasswd_file_id: Optional[int] = None


class MailAccountsSearchRequest(BaseCoreApiModel):
    local_part: Optional[str] = None
    mail_domain_id: Optional[int] = None
    cluster_id: Optional[int] = None
    quota: Optional[int] = None


class MailAliasesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    local_part: Optional[str] = None
    mail_domain_id: Optional[int] = None
    forward_email_address: Optional[EmailStr] = None


class MailDomainsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    domain: Optional[str] = None
    unix_user_id: Optional[int] = None
    catch_all_forward_email_addresses: Optional[EmailStr] = None
    is_local: Optional[bool] = None


class MailHostnamesSearchRequest(BaseCoreApiModel):
    domain: Optional[str] = None
    cluster_id: Optional[int] = None
    certificate_id: Optional[int] = None


class MalwaresSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    unix_user_id: Optional[int] = None
    name: Optional[str] = None


class MariadbEncryptionKeysSearchRequest(BaseCoreApiModel):
    identifier: Optional[int] = None
    cluster_id: Optional[int] = None


class NodeAddOnsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    node_id: Optional[int] = None
    product: Optional[str] = None
    quantity: Optional[int] = None


class NodesSearchRequest(BaseCoreApiModel):
    hostname: Optional[str] = None
    product: Optional[str] = None
    cluster_id: Optional[int] = None
    groups: Optional[NodeGroupEnum] = None
    comment: Optional[str] = None
    is_ready: Optional[bool] = None


class ObjectLogsSearchRequest(BaseCoreApiModel):
    object_id: Optional[int] = None
    object_model_name: Optional[str] = None
    request_id: Optional[UUID4] = None
    type: Optional[ObjectLogTypeEnum] = None
    causer_type: Optional[CauserTypeEnum] = None
    causer_id: Optional[int] = None
    customer_id: Optional[int] = None


class N8nInstanceIncludes(BaseCoreApiModel):
    cluster: ClusterResource | None


class N8nInstanceResource(BaseCoreApiModel):
    id: int
    created_at: datetime
    updated_at: datetime
    domain: str
    name: constr(pattern=r"^[a-z0-9-_]+$", min_length=1, max_length=64)
    cluster_id: int
    includes: N8nInstanceIncludes


class RedisInstancesSearchRequest(BaseCoreApiModel):
    port: Optional[int] = None
    name: Optional[str] = None
    cluster_id: Optional[int] = None
    eviction_policy: Optional[RedisEvictionPolicyEnum] = None


class RegionsSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None


class RequestLogsSearchRequest(BaseCoreApiModel):
    ip_address: Optional[str] = None
    path: Optional[str] = None
    method: Optional[HTTPMethod] = None
    api_user_id: Optional[int] = None
    request_id: Optional[UUID4] = None


class RootSshKeysSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    name: Optional[str] = None


class SecurityTxtPoliciesSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    email_contacts: Optional[EmailStr] = None
    url_contacts: Optional[AnyUrl] = None
    encryption_key_urls: Optional[AnyUrl] = None
    acknowledgment_urls: Optional[AnyUrl] = None
    policy_urls: Optional[AnyUrl] = None
    opening_urls: Optional[AnyUrl] = None
    preferred_languages: Optional[LanguageCodeEnum] = None


class SshKeysSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    name: Optional[str] = None
    unix_user_id: Optional[int] = None


class UnixUsersSearchRequest(BaseCoreApiModel):
    username: Optional[str] = None
    unix_id: Optional[int] = None
    cluster_id: Optional[int] = None
    shell_name: Optional[ShellNameEnum] = None
    record_usage_files: Optional[bool] = None
    default_php_version: Optional[str] = None
    default_nodejs_version: Optional[str] = None
    description: Optional[str] = None


class UrlRedirectsSearchRequest(BaseCoreApiModel):
    domain: Optional[str] = None
    cluster_id: Optional[int] = None
    server_aliases: Optional[str] = None
    destination_url: Optional[AnyUrl] = None
    status_code: Optional[StatusCodeEnum] = None
    keep_query_parameters: Optional[bool] = None
    keep_path: Optional[bool] = None
    description: Optional[str] = None


class VirtualHostsSearchRequest(BaseCoreApiModel):
    unix_user_id: Optional[int] = None
    server_software_name: Optional[VirtualHostServerSoftwareNameEnum] = None
    cluster_id: Optional[int] = None
    domain: Optional[str] = None
    server_aliases: Optional[str] = None
    document_root: Optional[str] = None
    fpm_pool_id: Optional[int] = None
    passenger_app_id: Optional[int] = None


class CertificateManagersSearchRequest(BaseCoreApiModel):
    main_common_name: Optional[str] = None
    certificate_id: Optional[int] = None
    common_names: Optional[str] = None
    provider_name: Optional[CertificateProviderNameEnum] = None
    cluster_id: Optional[int] = None
    request_callback_url: Optional[AnyUrl] = None


class ClustersLoadBalancingPropertiesSearchRequest(BaseCoreApiModel):
    http_retry_properties: Optional[HTTPRetryProperties] = None
    load_balancing_method: Optional[LoadBalancingMethodEnum] = None
    cluster_id: Optional[int] = None


class ClustersMeilisearchPropertiesSearchRequest(BaseCoreApiModel):
    meilisearch_backup_local_retention: Optional[int] = None
    meilisearch_environment: Optional[MeilisearchEnvironmentEnum] = None
    meilisearch_backup_interval: Optional[int] = None
    cluster_id: Optional[int] = None


class ClustersPhpPropertiesSearchRequest(BaseCoreApiModel):
    php_versions: Optional[str] = None
    custom_php_modules_names: Optional[PHPExtensionEnum] = None
    php_ioncube_enabled: Optional[bool] = None
    php_sessions_spread_enabled: Optional[bool] = None
    cluster_id: Optional[int] = None


class ClustersUnixUsersPropertiesSearchRequest(BaseCoreApiModel):
    unix_users_home_directory: Optional[UNIXUserHomeDirectoryEnum] = None
    cluster_id: Optional[int] = None


class CustomConfigSnippetsSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    server_software_name: Optional[VirtualHostServerSoftwareNameEnum] = None
    cluster_id: Optional[int] = None
    is_default: Optional[bool] = None


class DatabaseUserGrantsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    database_id: Optional[int] = None
    database_user_id: Optional[int] = None
    table_name: Optional[str] = None
    privilege_name: Optional[MariaDBPrivilegeEnum] = None


class HaproxyListensSearchRequest(BaseCoreApiModel):
    name: Optional[str] = None
    cluster_id: Optional[int] = None
    nodes_group: Optional[NodeGroupEnum] = None
    nodes_ids: Optional[int] = None
    port: Optional[int] = None
    socket_path: Optional[str] = None
    load_balancing_method: Optional[LoadBalancingMethodEnum] = None
    destination_cluster_id: Optional[int] = None


class PassengerAppsSearchRequest(BaseCoreApiModel):
    cluster_id: Optional[int] = None
    port: Optional[int] = None
    app_type: Optional[PassengerAppTypeEnum] = None
    name: Optional[str] = None
    unix_user_id: Optional[int] = None
    environment: Optional[PassengerEnvironmentEnum] = None
    max_pool_size: Optional[int] = None
    is_namespaced: Optional[bool] = None
    cpu_limit: Optional[int] = None
    nodejs_version: Optional[str] = None


NestedPathsDict.model_rebuild()
CompositeSpecificationSatisfyResult.model_rebuild()
CompositeSpecificationSatisfyResultResource.model_rebuild()
