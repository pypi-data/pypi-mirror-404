from __future__ import annotations
from contextlib import suppress
from datetime import timedelta
import inspect
import json
import types
import typing
from uuid import UUID
from httpx import AsyncClient
from dataclasses import dataclass, field
import logging
from pathlib import Path
from types import ModuleType, NoneType
from typing import Any, Awaitable, Callable, Generic, Iterable, Literal, Protocol, Sequence, TypeVar
from pydantic import BaseModel, Field, SecretStr, ValidationError
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings

from takk.alembic import Revision, revisions_for_alembic_config
from takk.resources import CompiledResource, MongoDBInstance, PostgresInstance, RedisInstance, Resource, ServerlessPostgresInstance
from takk.secrets import ResourceRef, ResourceTags, NatsConfig, ObjectStorageConfig, ServiceUrl, SqsConfig, SqsQueueSettings, UnleashConfig, Environments
from rich.console import Console

logger = logging.getLogger(__name__)

console = Console()

T = TypeVar("T", bound=BaseModel)

class NobsEnvironment(BaseSettings):
    nobs_env: Environments = Field(default="dev")

def current_env() -> Environments:

    return NobsEnvironment().nobs_env


class Contact(BaseModel):
    name: str
    email: str | None = None
    discord_member_id: str | None = None
    slack_member_id: str | None = None


class SecretValue(BaseModel):
    name: str
    data_type: str
    description: str | None = Field(default=None)
    default_value: str | None = Field(default=None)
    is_optional: bool = Field(default=False)
    tags: list[str] = Field(default_factory=list)

    def __hash__(self):
        return hash(self.name + self.data_type)


class Compute(BaseModel):
    mvcpu_limit: int = 1000
    mb_memory_limit: int = 1024
    mb_local_storage_limit: int = 1000

def tags_for(attrs: Iterable) -> list[str]:
    tags = []
    for attr in attrs:
        if isinstance(attr, str):
            tags.append(attr)
        elif isinstance(attr, ResourceTags):
            tags.append(attr.value)
        elif isinstance(attr, ResourceRef):
            tags.append(attr.to_string())
        elif isinstance(attr, ServiceUrl):
            tags.append(str(attr))
    return tags


def tags_for_annotation(annotation: Any) -> tuple[str, list[str], bool]:
    data_type = "str"
    is_optional = False

    if typing.get_origin(annotation) is typing.Annotated:
        args = typing.get_args(annotation)
        tags = tags_for(args)
        arg_type = args[0]

        dtype, sub_tags, is_optional = tags_for_annotation(arg_type)

        return (dtype, [*tags, *sub_tags], is_optional)


    if typing.get_origin(annotation) is typing.Union:
        args = typing.get_args(annotation)
        is_optional = NoneType in args
        data_type = annotation.__name__

        all_dtypes: set[str] = set()
        all_tags = []

        for arg in args:
            dtype, sub_tags, sub_is_optional = tags_for_annotation(arg)
            all_tags.extend(sub_tags)

            if dtype != "NoneType":
                all_dtypes.add(dtype)

            is_optional = is_optional or sub_is_optional

        if len(all_dtypes) == 1:
            return (next(iter(all_dtypes)), all_tags, is_optional)

        return (" | ".join(all_dtypes), all_tags, is_optional)

    elif annotation == SecretStr:
        data_type = "str"
    elif annotation:
        is_optional = NoneType == annotation
        if hasattr(annotation, "__name__"):
            data_type = annotation.__name__
        else:
            data_type = str(annotation)

    return (data_type, [], is_optional)

def secrets_for(settings_type: type[BaseModel] | list[type[BaseModel]]) -> list[SecretValue]:

    values: list[SecretValue] = []

    if isinstance(settings_type, list):
        for stype in settings_type:
            values.extend(
                secrets_for(stype)
            )
    else:
        for name, field in settings_type.__pydantic_fields__.items():

            data_type, tags, is_optional = tags_for_annotation(field.annotation)
            values.append(
                SecretValue(
                    name=name.upper(), 
                    data_type=data_type,
                    description=field.description, 
                    default_value=str(field.default) if field.default != PydanticUndefined else None,
                    is_optional=is_optional,
                    tags=[
                        *tags,
                        *tags_for(field.metadata)
                    ]
                )
            )
    return values


def settings_for_secrets(secrets: list[SecretValue], resources: dict[str, str]) -> dict[str, str]:
    vals = {}
    for secret in secrets:
        for resource, value in resources.items():
            if resource == secret.data_type or resource in secret.tags:
                vals[secret.name] = value
    return vals


class NetworkHealthCheck(BaseModel):
    url: str
    interval: int = 10
    timeout: int = 5
    retries: int = 5



class CompiledNetworkApp(BaseModel):
    name: str
    command: list[str] | None
    port: int

    description: str | None = None
    environments: dict[str, str] | None = None
    secrets: list[SecretValue] | None = None
    contacts: list[Contact] | None = None

    health_check: NetworkHealthCheck | None = None

    compute: Compute = field(default_factory=Compute)
    min_scale: int = 0
    max_scale: int = 1

    https_only: bool = True
    tags: list[str] | None = None

    domain_names: list[str] | None = None

    resource_id: str | None = None
    docker_image: str | None = None

    def id(self) -> str:
        from hashlib import sha1
        return sha1(self.name.encode()).hexdigest()


@dataclass
class ComputeRequest:
    min_mvcpus: int = field(default=1000)
    min_mb_ram: int = field(default=1024)
    min_mb_local_storage: int = field(default=1000)
    min_gpus: int = field(default=0)


@dataclass
class ServerlessCompute:
    compute: Compute
    min_scale: int = 0
    max_scale: int = 1


@dataclass
class NetworkApp:
    port: int

    command: list[str] | None = None
    description: str | None = None
    environments: dict[str, str] | None = None
    secrets: list[type[BaseModel]] | None = None
    contacts: list[Contact] | Contact | None = None

    compute: Compute = field(default_factory=Compute)
    min_scale: int = 0
    max_scale: int = 1

    https_only: bool = True
    domain_names: list[str] | str | None = None
    tags: list[str] | None = None

    health_check: str | NetworkHealthCheck | None = None

    docker_image: str | None = None

    def compile(self, name: str) -> CompiledNetworkApp:

        return CompiledNetworkApp(
            name=name,
            command=self.command,
            port=self.port,
            description=self.description,
            environments=self.environments,
            secrets=secrets_for(self.secrets or []),
            contacts=[self.contacts] if isinstance(self.contacts, Contact) else self.contacts,
            health_check=NetworkHealthCheck(url=self.health_check) if isinstance(self.health_check, str) else self.health_check,  
            compute=self.compute,
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            tags=self.tags,
            https_only=self.https_only,
            domain_names=[self.domain_names] if isinstance(self.domain_names, str) else self.domain_names,
            docker_image=self.docker_image
        )

def startup_command(scripts: Sequence[str | Callable], root_path: Path) -> list[str]:
    commands = []

    for script in scripts:
        if isinstance(script, str):
            commands.append(script)
        else:
            source_file = Path(inspect.getfile(script))
            relative_file = source_file.relative_to(root_path).as_posix().replace("/", ".").removesuffix(".py")
            commands.append(f"python -m {relative_file}")

    return commands


@dataclass
class FastAPIApp:
    app: ModuleType | str | None = None
    secrets: list[type[BaseSettings]] | None = None
    environments: dict[str, str] | None = None
    contacts: list[Contact] | Contact | None = None
    
    port: int = 8000
    compute: Compute = field(default_factory=Compute)
    min_scale: int = 0
    max_scale: int = 1

    https_only: bool = True
    domain_names: list[str] | str | None = None
    health_check: str | NetworkHealthCheck | None = None

    def network_app(self, root_path: Path) -> NetworkApp:
        import inspect

        bash_commands = []
        if self.app is None:
            relative_file = "Unknown"
            bash_commands.append(f"fastapi run --host 0.0.0.0 --port {self.port}")
        else:
            if isinstance(self.app, str):
                relative_file = self.app
            else:
                source_file = Path(inspect.getfile(self.app))
                relative_file = source_file.relative_to(root_path).as_posix().replace("/", ".").removesuffix(".py")

            bash_commands.append(f"uvicorn {relative_file}:app --host 0.0.0.0 --port {self.port}")

        command = ["/bin/bash", "-c", " && ".join(bash_commands)]

        return NetworkApp(
            command=command,
            port=self.port,
            secrets=self.secrets,
            environments=self.environments,
            description=f"FastAPI application at {relative_file}",
            contacts=self.contacts,
            compute=self.compute,
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            https_only=self.https_only,
            domain_names=self.domain_names,
            health_check=self.health_check
        )



@dataclass
class StreamlitApp:
    main_function: Callable[[], None] | Callable[[], Awaitable[None]]
    secrets: list[type[BaseSettings]] | None = None
    environments: dict[str, str] | None = None
    contacts: list[Contact] | Contact | None = None

    compute: Compute = field(default_factory=Compute)
    min_scale: int = 0
    max_scale: int = 1

    tags: list[str] | None = None

    https_only: bool = True
    domain_names: list[str] | str | None = None

    def network_app(self, root_path: Path) -> NetworkApp:
        import inspect

        function_file = Path(inspect.getfile(self.main_function))
        relative_function = function_file.relative_to(root_path)
        app_path = relative_function.as_posix()

        command = ["bash", "-c", f"python -m streamlit run {app_path}"]

        return NetworkApp(
            command=command,
            port=8501,
            environments=self.environments,
            secrets=self.secrets,
            contacts=self.contacts,
            health_check="/healthz",
            compute=self.compute,
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            tags=[*(self.tags or []), "streamlit"],
            description=self.main_function.__doc__,
            https_only=self.https_only,
            domain_names=self.domain_names
        )

class CompiledJob(BaseModel):
    name: str
    function_ref: str
    arguments: dict
    description: str
    cron_schedule: str | None = None
    contacts: list[Contact] | None = None
    secrets: list[SecretValue] | None = None
    environments: dict[str, str] = field(default_factory=dict)
    compute: Compute = field(default_factory=Compute)
    custom_command: str | None = None

    definition_id: str | None = None


    def command(self, project_name: str) -> str:
        if self.custom_command:
            return self.custom_command

        function_ref = self.function_ref
        encoded_args = json.dumps(self.arguments, separators=(',', ':'))
        return f"python -m takk.cli run-job --project-name={project_name} --job-id={self.id()} --file-ref {function_ref} --args '{encoded_args}'"


    def id(self) -> str:
        from hashlib import sha1
        return sha1(self.name.encode(), usedforsecurity=False).hexdigest()


@dataclass
class Job(Generic[T]):
    main_function: Callable[[T], None] | Callable[[T], Awaitable[None]]

    arguments: T

    cron_schedule: str | None = None
    description: str | None = None
    contacts: list[Contact] | Contact | None = None
    secrets: list[type[BaseSettings]] | None = None
    environments: dict[str, str] = field(default_factory=dict)

    compute: Compute = field(default_factory=Compute)

    async def run(self, arguments: T | None = None) -> None:
        if inspect.iscoroutinefunction(self.main_function):
            await self.main_function(arguments or self.arguments)
        else:
            self.main_function(arguments or self.arguments)

    def used_description(self) -> str:
        if self.description:
            return self.description
        if self.main_function.__doc__:
            return self.main_function.__doc__
        return f"A cron job with schedule '{self.cron_schedule}' that runs {self.main_function.__name__}" 


    def function_ref(self, root_path: Path) -> str:
        function_file = Path(inspect.getfile(self.main_function))
        relative_function = function_file.relative_to(root_path)
        module_path = relative_function.as_posix().replace("/", ".").removesuffix(".py")

        return f"{module_path}:{self.main_function.__name__}"


    def command(self, root_path: Path) -> str:
        function_ref = self.function_ref(root_path)
        encoded_args = self.arguments.model_dump_json()
        return f"bash -c python -m src.apps --file-ref {function_ref} --args '{encoded_args}'"


    def compile(self, name: str) -> CompiledJob:
        return CompiledJob(
            name=name,
            function_ref=self.function_ref(Path.cwd()),
            arguments=self.arguments.model_dump(),
            cron_schedule=self.cron_schedule,
            description=self.used_description(),
            contacts=[self.contacts] if isinstance(self.contacts, Contact) else self.contacts,
            secrets=secrets_for(self.secrets or []),
            environments=self.environments,
            compute=self.compute
        )


@dataclass
class Subscriber(Generic[T]):
    method: Callable[[T], None] | Callable[[T], Awaitable[None]]
    subject: str
    broker_type: Literal["nats"] = field(default="nats")
    contacts: list[Contact] = field(default_factory=list)
    secret_type: list[type[BaseSettings]] = field(default_factory=list)
    compute: Compute = field(default_factory=Compute)


    def function_ref(self, root_path: Path) -> str:
        import inspect

        function_file = Path(inspect.getfile(self.method))
        relative_function = function_file.relative_to(root_path)
        module_path = relative_function.as_posix().replace("/", ".").removesuffix(".py")

        return f"{module_path}:{self.method.__name__}"


    def compile(self, name: str, root_path: Path | None = None) -> CompiledSubscriber:

        return CompiledSubscriber(
            name=name,
            function_ref=self.function_ref(root_path or Path.cwd()),
            subject=self.subject,
            broker_type=self.broker_type,
            contacts=self.contacts,
            secrets=secrets_for(self.secret_type or []),
            compute=self.compute
        )


@dataclass
class PubSub(Generic[T]):
    content_type: type[T]
    subject: str

    broker_type: Literal["nats"] = "nats"
    nats_secret: type[BaseSettings] = NatsConfig

    def subscriber(
        self, 
        method: Callable[[T], None] | Callable[[T], Awaitable[None]], 
        compute: Compute | None = None,
        secrets: list[type[BaseSettings]] | None = None
    ) -> Subscriber[T]:
        return Subscriber(
            method=method,
            subject=self.subject,
            broker_type=self.broker_type,
            secret_type=[self.nats_secret, *(secrets or [])],
            compute=compute or Compute()
        )

    async def publish(self, content: T) -> None:
        from takk.secrets import ResourceTags
        from pydantic import NatsDsn
        import nats

        settings = self.nats_secret() # type: ignore

        servers = [
            val.encoded_string() for val in
            settings.model_dump().values()
            if isinstance(val, NatsDsn)
        ]

        user_credentials = None

        for key, model_field in settings.model_fields.items():
            if ResourceTags.nats_creds_file in model_field.metadata:
                user_credentials = getattr(settings, key)

        if not servers:
            raise ValueError("Unable to find any nats connections. Remember to tag the secret with the NatsDsn type.")

        nc = await nats.connect(servers=servers, user_credentials=user_credentials)
        await nc.publish(self.subject, content.model_dump_json().encode())


@dataclass
class LokiServer:
    docker_image: str = field(default="grafana/loki")
    compute: Compute = field(default_factory=Compute)

    min_scale: int = 0
    max_scale: int = 1
    tags: list[str] | None = None

    contacts: list[Contact] | Contact | None = None
    domain_names: list[str] | str | None = None

    def network_app(self, root_path: Path) -> NetworkApp:
        return NetworkApp(
            command=None,
            port=3100,
            description="A logging service",
            docker_image=self.docker_image,
            contacts=self.contacts,
            compute=self.compute,
            tags=[*(self.tags or []), "loki"],
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            domain_names=self.domain_names
        )


@dataclass
class UnleashServer:
    """
    project = Project(
        ...,
        unleash_server=UnleashServer()
    )
    """
    secrets: list[type[BaseSettings]] = field(default_factory=lambda: [UnleashConfig])
    docker_image: str = field(default="unleashorg/unleash-server:latest")
    compute: Compute = field(default_factory=Compute)

    min_scale: int = 0
    max_scale: int = 1
    tags: list[str] | None = None

    contacts: list[Contact] | Contact | None = None

    domain_names: list[str] | str | None = None


    def network_app(self, root_path: Path) -> NetworkApp:
        return NetworkApp(
            command=None,
            port=4242,
            description="A feature toggle service",
            secrets=self.secrets,
            docker_image=self.docker_image,
            contacts=self.contacts,
            compute=self.compute,
            tags=[*(self.tags or []), "unleash"],
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            domain_names=self.domain_names
        )


@dataclass
class MlflowServer:
    """
    project = Project(
        ...,
        mlflow_server=MlflowServer(
            domain_names=[
                "mlflow.my-cool-project.com",
                "www.mlflow.my-cool-project.com",
            ]
        )
    )
    """
    mlflow_version: str | None = None
    secrets: list[type[BaseSettings]] = field(default_factory=lambda: [ObjectStorageConfig])
    docker_image: str = field(default="ghcr.io/mlflow/mlflow")
    compute: Compute = field(default_factory=Compute)

    min_scale: int = 0
    max_scale: int = 1
    tags: list[str] | None = None

    contacts: list[Contact] | Contact | None = None

    domain_names: list[str] | str | None = None


    def network_app(self, root_path: Path) -> NetworkApp:
        mlflow_version = "3.5.0"
        with suppress(ImportError):
            import mlflow
            mlflow_version = mlflow.__version__

        if self.mlflow_version:
            mlflow_version = self.mlflow_version

        port = 8000

        if ":" in self.docker_image:
            docker_image = self.docker_image
        else:
            docker_image = f"{self.docker_image}:v{mlflow_version}"

        command = f"mlflow server --host 0.0.0.0 --port {port}"
        if mlflow_version.startswith("3"):
            command = command + " --allowed-hosts=*"

        return NetworkApp(
            command=["bash", "-c", command],
            port=port,
            description=f"An MLFlow Server used for tracking experiments and managing model versions. Using version: {mlflow_version}.",
            secrets=self.secrets,
            docker_image=docker_image,
            contacts=self.contacts,
            compute=self.compute,
            tags=[*(self.tags or []), "mlflow-server"],
            min_scale=self.min_scale,
            max_scale=self.max_scale,
            domain_names=self.domain_names
        )



@dataclass
class Worker:
    name: str

    broker_type: Literal["sqs"] = "sqs"

    queue_settings: SqsQueueSettings = field(default_factory=SqsQueueSettings)

    compute: Compute = field(default_factory=Compute)
    secrets: list[type[BaseModel]] | type[BaseModel] = field(default_factory=lambda: [SqsConfig])


    async def queue(self, method: Callable[[T], None] | Callable[[T], Awaitable[None]], payload: T) -> None:
        import inspect 
        from takk.queue import QueueBroker, SqsQueueBroker
        from takk.secrets import SqsConfig

        function_file = Path(inspect.getfile(method))
        relative_function = function_file.relative_to(Path.cwd())
        module_path = relative_function.as_posix().replace("/", ".").removesuffix(".py")

        logger.info(f"Queueing function {function_file}")
        assert self.broker_type == "sqs", f"Expected SQS worker, got {self.broker_type}"

        broker: QueueBroker = SqsQueueBroker(
            config=SqsConfig(), # type: ignore
            queue_settings=self.queue_settings 
        )
        queue = broker.with_name(self.name)

        sign = inspect.signature(method)
        
        assert len(sign.parameters) == 1
        key = list(sign.parameters.keys())[0]

        await queue.send(
            QueueMessage(
                function_ref=f"{module_path}:{method.__name__}",
                arguments={key: payload.model_dump()}
            )
        )

    def compile(self) -> CompiledWorker:
        return CompiledWorker(
            name=self.name,
            broker_type=self.broker_type,
            compute=self.compute,
            secrets=secrets_for(self.secrets) if isinstance(self.secrets, list) else secrets_for([self.secrets])
        )


class NetworkAppable(Protocol):

    def network_app(self, root_path: Path) -> NetworkApp:
        ...


class Project:
    name: str
    additional_dirs: list[Path] | None
    testing_dirs: list[Path] | None
    docker_image: str | None
    shared_secrets: list[type[BaseModel]] | None

    workers: list[Worker] | None

    components: dict[str, NetworkApp | Job | Subscriber | NetworkAppable | Resource]
    project_file: str = "unknown"


    def __init__(
        self, 
        name: str, 
        additional_dirs: Sequence[str | Path] | None = None,
        testing_dirs: Sequence[str | Path] | None = None,
        docker_image: str | None = None, 
        shared_secrets: list[type[BaseModel]] | None = None, 
        workers: list[Worker] | None = None, 
        **kwargs: NetworkApp | NetworkAppable | Job | Subscriber | Resource
    ):
        self.name = name
        self.additional_dirs = [
            path if isinstance(path, Path) else Path(path)
            for path in additional_dirs
        ] if additional_dirs else None
        self.testing_dirs = [
            path if isinstance(path, Path) else Path(path)
            for path in testing_dirs or ["tests", "conftest.py"]
        ]
        self.workers = workers
        self.docker_image = docker_image
        self.shared_secrets = shared_secrets
        self.components = kwargs


class CompiledWorker(BaseModel):
    name: str

    broker_type: Literal["sqs"]
    compute: Compute = field(default_factory=Compute)
    secrets: list[SecretValue] | None = None

    max_scale: int = 1

    resource_id: str | None = None


class CompiledSubscriber(BaseModel):
    name: str
    function_ref: str
    subject: str
    broker_type: Literal["nats"]

    contacts: list[Contact] | None = None
    secrets: list[SecretValue] | None = None
    environments: dict[str, str] = field(default_factory=dict)
    compute: Compute = field(default_factory=Compute)




class CompiledProject(BaseModel):
    name: str
    docker_image: str | None
    shared_secrets: list[SecretValue]

    network_apps: list[CompiledNetworkApp]
    jobs: list[CompiledJob]

    workers: list[CompiledWorker]
    subscribers: list[CompiledSubscriber]

    resources: list[CompiledResource]

    packages: list[str]
    project_file: str

    revisions: list[Revision]

    @staticmethod
    def from_project(project: Project, packages: list[str]) -> "CompiledProject":

        current_dir = Path.cwd()

        network_apps = []
        jobs = []
        subs = []
        resources = []

        for name, component in project.components.items():
            if isinstance(component, NetworkApp):
                network_apps.append(component.compile(name))
            elif isinstance(component, Job):
                jobs.append(component.compile(name))
            elif isinstance(component, Subscriber):
                subs.append(component.compile(name, current_dir))
            elif isinstance(component, Resource):
                resources.append(component.resource(name))
            else:
                network_apps.append(component.network_app(current_dir).compile(name))


        alembic_file = current_dir / "alembic.ini"

        revisions = []
        if alembic_file.is_file():
            revisions = revisions_for_alembic_config(alembic_file)

        return CompiledProject(
            name=project.name,
            docker_image=project.docker_image,
            shared_secrets=secrets_for(project.shared_secrets or []),
            network_apps=network_apps,
            jobs=jobs,
            workers=[queue.compile() for queue in project.workers or []],
            resources=resources,
            subscribers=subs,
            packages=packages,
            project_file=project.project_file,
            revisions=revisions
        )


default_nobs_file = Path().home() / ".config/nobs"

class NobsServer(BaseSettings):
    nobs_api: str = "http://localhost:8000/api/v1" # "https://cloud.aligned.codes/api/v1" # 
    nobs_token: SecretStr

    @staticmethod
    def read() -> "NobsServer":
        try:
            return NobsServer() # type: ignore
        except ValidationError:
            if not default_nobs_file.is_file():
                raise ValueError("Found no env vars or config file. Try to run `takk login`.")
            content = default_nobs_file.read_bytes()
            return NobsServer.model_validate_json(content)
            

class DockerCreds(BaseModel):
    registry: str
    password: str
    project_id: str


class UpdateProjectResponse(BaseModel):
    project_id: UUID
    project_env_id: UUID


class ServerSideEvent(BaseModel):
    data: str | None = None
    event: str | None = None

    def decode_data(self, content_type: type[T]) -> T:
        if not self.data:
            raise ValueError("No data to decode")
        return content_type.model_validate_json(self.data)

    @staticmethod
    def from_body(content: str) -> "ServerSideEvent":
        import yaml
        content = yaml.safe_load(content)
        return ServerSideEvent.model_validate(content)



@dataclass
class NobsClient:
    settings: NobsServer = field(default_factory=NobsServer.read)

    async def auth_cli(self, login_request_id: UUID) -> str:
        url = f"{self.settings.nobs_api}/users/cli-login/{login_request_id}"

        async with AsyncClient() as client:
            res = await client.get(url, timeout=60 * 2)

        res.raise_for_status()
        return res.json()["id"]


    async def docker_creds(self) -> DockerCreds:
        url = f"{self.settings.nobs_api}/users/registry"
        headers = {
            "Authorization": f"Bearer {self.settings.nobs_token.get_secret_value()}"
        }
        async with AsyncClient() as client:
            res = await client.get(url, headers=headers)
        res.raise_for_status()

        return DockerCreds.model_validate(res.json())

    async def deploy(self, project_env_id: UUID) -> None:
        url = f"{self.settings.nobs_api}/projects/env/{project_env_id}/deploy"
        headers = {
            "Authorization": f"Bearer {self.settings.nobs_token.get_secret_value()}"
        }

        async with AsyncClient() as client:
            async with client.stream(method="POST", url=url, headers=headers, timeout=60 * 10) as stream:
                async for body in stream.aiter_text():
                    if not body.strip():
                        continue
                    try:
                        event = ServerSideEvent.from_body(body)
                        if event.event == "close":
                            continue

                        if event.event == "error":
                            console.print(
                                f"[bold red]❌ {event.data}[/bold red]",
                            )
                        elif event.event == "success":
                            console.print(
                                f"[bold green]✅ {event.data}[/bold green]",
                            )
                        else:
                            console.print(event.data)
                    except Exception as e:
                        console.print(
                            f"[bold red]An Error Occurred {e}[/bold red]",
                        )


    async def update(self, project: Project, env: str, packages: list[str]) -> UpdateProjectResponse:
        url = f"{self.settings.nobs_api}/projects/{project.name}/{env}"
        compiled = CompiledProject.from_project(project, packages=packages)

        headers = {
            "Authorization": f"Bearer {self.settings.nobs_token.get_secret_value()}",
            "Content-Type": "application/json"
        }
        async with AsyncClient(timeout=10) as client:
            res = await client.put(url, headers=headers, content=compiled.model_dump_json())

        res.raise_for_status()

        return UpdateProjectResponse.model_validate(res.json())


    async def notify_about_failure(self, project_name: str, job_id: str, exception: Exception) -> None:
        url = f"{self.settings.nobs_api}/projects/{project_name}/jobs/{job_id}/notify/failure"

        headers = {
            "Authorization": f"Bearer {self.settings.nobs_token.get_secret_value()}"
        }

        body = NotifyFailure(
            exception=str(exception)
        )
        async with AsyncClient() as client:
            res = await client.post(url, headers=headers, json=body.model_dump())
        res.raise_for_status()



class QueueMessage(BaseModel):
    function_ref: str
    arguments: dict

    async def run(self) -> None:
        import importlib
        import inspect

        module_name, func_name = self.function_ref.split(":")
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)

        assert callable(func)

        sign = inspect.signature(func)   

        input_args = {}

        for param in sign.parameters.values():

            annotation = param.annotation
            is_optional = False

            if isinstance(annotation, types.UnionType):
                args = annotation.__args__
                is_optional = NoneType in args
                annotation = next(iter(arg for arg in args if NoneType != arg))

            if is_optional and param.name not in self.arguments:
                input_args[param.name] = None
                continue

            if issubclass(annotation, BaseModel):
                input_args[param.name] = annotation.model_validate(self.arguments[param.name])
            else:
                input_args[param.name] = self.arguments[param.name]

        if inspect.iscoroutinefunction(func):
            await func(**input_args)
        else:
            func(**input_args)


class NotifyFailure(BaseModel):
    exception: str
