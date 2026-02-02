import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Literal, TypeVar, Union
from pydantic import BaseModel, Field, NatsDsn, SecretStr, AnyUrl
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from prometheus_client import CollectorRegistry

class Tags:
    supporting_infra = "supporting_infra"


class ResourceTags(str, Enum):

    redis_dsn = "RedisDsn"
    redis_username = "redis_username"
    redis_password = "redis_password"
    redis_host = "redis_host"
    redis_port = "redis_port"

    mongo_dsn = "MongoDsn"

    psql_dsn = "PostgresDsn"

    psql_host = "psql_host"
    psql_name = "psql_name"
    psql_password = "psql_password"
    psql_username = "psql_username"
    psql_ssl = "psql_ssl"
    psql_port = "psql_port"

    sqs_endpoint = "sqs_endpoint"
    sqs_access_key = "sqs_access_key"
    sqs_secret_key = "sqs_secret_key"
    sqs_region_name = "sqs_region_name"

    s3_endpoint = "s3_endpoint"
    s3_access_key = "s3_access_key"
    s3_secret_key = "s3_secret_key"
    s3_region_name = "s3_region_name"
    s3_bucket_name = "s3_bucket_name"

    mlflow_tracking_uri = "mlflow_tracking_uri"
    mlflow_registry_uri = "mlflow_registry_uri"

    nats_dsn = "NatsDsn"
    nats_creds_file = "nats_creds_file"

    loki_push_endpoint = "loki_push_endpoint"
    loki_base_url = "loki_base_url"
    loki_user = "loki_user"
    loki_token = "loki_token"

    mimir_base_url = "mimir_base_url"
    mimir_token = "mimir_token"

    slack_webhook_url = "slack_webhook_url"
    discord_webhook_url = "discord_webhook_url"
    teams_webhook_url = "teams_webhook_url"

    database_host = "database_host"
    database_name = "database_name"
    database_password = "database_password"
    database_username = "database_username"
    database_ssl = "database_ssl"
    database_port = "database_port"

    environment = "environment"

    

Environments = Literal["dev", "test", "prod", "qa"]

SqsEndpoint = Annotated[AnyUrl, ResourceTags.sqs_endpoint]
SqsAccessKey = Annotated[str, ResourceTags.sqs_access_key]
SqsSecretKey = Annotated[SecretStr, ResourceTags.sqs_secret_key]
SqsRegionName = Annotated[str, ResourceTags.sqs_region_name]

S3Endpoint = Annotated[AnyUrl, ResourceTags.s3_endpoint]
S3AccessKey = Annotated[str, ResourceTags.s3_access_key]
S3SecretKey = Annotated[SecretStr, ResourceTags.s3_secret_key]
S3RegionName = Annotated[str, ResourceTags.s3_region_name]
S3BucketName = Annotated[str, ResourceTags.s3_bucket_name]

MlflowTrackingUri = Annotated[AnyUrl, ResourceTags.mlflow_tracking_uri]
MlflowRegistryUri = Annotated[AnyUrl, ResourceTags.mlflow_registry_uri]

NatsCredsFile = Annotated[str, ResourceTags.nats_creds_file]

LokiPushEndpoint = Annotated[str, ResourceTags.loki_push_endpoint]
LokiUser = Annotated[str | None, ResourceTags.loki_user]
LokiToken = Annotated[SecretStr | None, ResourceTags.loki_token]

MimirBaseUrl = Annotated[str, ResourceTags.mimir_base_url]
MimirToken = Annotated[SecretStr | None, ResourceTags.mimir_token]

SlackWebhookUrl = Annotated[str, ResourceTags.slack_webhook_url]
DiscordWebhookUrl = Annotated[str, ResourceTags.discord_webhook_url]
TeamsWebhookUrl = Annotated[str, ResourceTags.teams_webhook_url]

DatabaseHost = Annotated[str, ResourceTags.database_host]
DatabaseName = Annotated[str, ResourceTags.database_name]
DatabaseUsername = Annotated[str, ResourceTags.database_username]
DatabasePassword = Annotated[str, ResourceTags.database_password]
DatabaseSsl = Annotated[str, ResourceTags.database_ssl]


T = TypeVar("T", bound=BaseModel)


@dataclass
class ResourceRef:
    tag: ResourceTags
    name: str = field(default="default")

    def __hash__(self) -> int:
        return hash(self.to_string())

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return f"{self.tag.value}:{self.name}"

    @staticmethod
    def from_string(val: str) -> "ResourceRef":
        tag, name = val.split(":") 
        return ResourceRef(ResourceTags(tag), name) # type: ignore

@dataclass
class ServiceUrl:

    value: str
    url_type: Literal["internal", "external"]

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        return f"service:{self.value}:{self.url_type}"

    @staticmethod
    def from_string(val: str) -> Union["ServiceUrl", None]:
        if not val.startswith("service:"):
            return None
        val, url_type = val.removeprefix("service:").split(":")
        return ServiceUrl(val, url_type) # type: ignore


def settings_for_resources(resources: dict[str, str], settings_type: type[T]) -> T:
    from takk.models import settings_for_secrets, secrets_for

    vals = {
        key.lower(): val
        for key, val in settings_for_secrets(
            secrets_for(settings_type),
            resources
        ).items()
    }
    return settings_type.model_validate(vals)


class NatsConfig(BaseSettings):
    nats_url: NatsDsn
    nats_credentials: NatsCredsFile | None = Field(default=None)


class SqsConfig(BaseSettings):
    sqs_endpoint: SqsEndpoint
    sqs_access_key: SqsAccessKey
    sqs_secret_key: SqsSecretKey
    sqs_region_name: SqsRegionName


class SqsQueueSettings(BaseModel):

    wait_time_seconds: int = Field(default=10)
    max_message_size_kbs: int = Field(default=258)
    max_number_of_messages: int = Field(default=1)
    visibility_timeout_seconds: int = Field(default=30)
    message_retention_period_seconds: int = Field(default=60)


    def attributes(self) -> dict[str, str]:
        return {
            "VisibilityTimeout": str(self.visibility_timeout_seconds),
            "MessageRetentionPeriod": str(self.message_retention_period_seconds),
            "MaximumMessageSize": str(self.max_message_size_kbs * (2 ^ 10)),
            "ReceiveMessageWaitTimeSeconds": str(self.wait_time_seconds)
        }


class UnleashConfig(BaseSettings):
    database_host: DatabaseHost
    database_name: DatabaseName
    database_password: DatabasePassword
    database_username: DatabaseUsername
    database_ssl: DatabaseSsl


class ObjectStorageConfig(BaseSettings):
    object_storage_access_key: S3AccessKey
    object_storage_secret_key: S3SecretKey
    object_storage_region: S3RegionName


class S3StorageConfig(BaseSettings):
    s3_access_key: S3AccessKey
    s3_secret_key: S3SecretKey
    s3_region: S3RegionName
    s3_endpoint: Annotated[AnyUrl | None, ResourceTags.s3_endpoint] = None
    s3_bucket: Annotated[str | None, ResourceTags.s3_bucket_name] = None


class MlflowConfig(BaseSettings):
    mlflow_tracking_uri: MlflowTrackingUri
    mlflow_registry_uri: MlflowRegistryUri


class LokiLoggerConfig(BaseSettings):
    loki_push_endpoint: LokiPushEndpoint
    loki_user: LokiUser = Field(default=None)
    loki_token: LokiToken = Field(default=None)
    loki_logger_version: int = Field(default=1)

    def setup_logger(self, *, logger: logging.Logger | None = None, tags: dict | None = None) -> None:
        from logging_loki import LokiHandler

        auth = None
        if self.loki_user and self.loki_token:
            auth = (self.loki_user, self.loki_token.get_secret_value())

        handler = LokiHandler(
            url=self.loki_push_endpoint,
            auth=auth,
            tags=tags,
            version=f"{self.loki_logger_version}"
        )
        (logger or logging.getLogger("")).addHandler(handler)


class MimirConfiguration(BaseSettings):
    mimir_base_url: MimirBaseUrl
    mimir_token: MimirToken = Field(default=None)

    def push_metrics(self, registry: "CollectorRegistry", job: str):
        from prometheus_client import push_to_gateway

        push_to_gateway(self.mimir_base_url, job=job, registry=registry)


class SlackWebhook(BaseSettings):
    slack_webhook_url: SlackWebhookUrl

class TeamsWebhook(BaseSettings):
    teams_webhook_url: TeamsWebhookUrl

class DiscordWebhook(BaseSettings):
    discord_webhook_url: DiscordWebhookUrl

