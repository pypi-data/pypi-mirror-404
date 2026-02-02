import json
import yaml
from uuid import uuid4
from pydantic import AnyUrl, BaseModel, Field
from rich import status
import tomli
from threading import Thread, Event
from contextlib import suppress
from dataclasses import dataclass
import logging
from pathlib import Path
from time import sleep
from typing import Literal
from docker import DockerClient
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from docker.models.containers import Container as DockerContainer
from takk.models import CompiledJob, CompiledProject, Project, secrets_for, settings_for_secrets
from takk.models import NobsEnvironment
from takk.runners import default_runner
from takk.secrets import Environments, ResourceTags, S3StorageConfig, ServiceUrl, settings_for_resources
from hashlib import sha256 

logger = logging.getLogger(__name__)
console = Console()

class ImageKeys:
    lock_hash = "com.takkthon.lockhash"
    source_dir = "com.takkthon.source-dir"

@dataclass
class ProjectContainer:
    source_dir: str

@dataclass
class Container:
    name: str
    image: str
    restart: str
    environments: dict[str, str]
    volumes: list[str]
    ports: dict[str, int]


class GrafanaSource(BaseModel):
    name: str
    type: str
    url: AnyUrl

    access: str = Field(default="proxy")
    orgId: int = Field(default=1)
    basicAuth: bool = Field(default=False)
    isDefault: bool = Field(default=False)
    version: int = Field(default=1)
    editable: bool = Field(default=False)
    

class GrafanaSourcesFile(BaseModel):
    datasources: list[GrafanaSource]
    apiVersion: int = Field(default=1)


def needed_containers(project: CompiledProject, envs: dict[str, str | None], data_dir: Path | None = None) -> tuple[list[Container], dict[str, str]]:
    containers = []

    supported_types = [ResourceTags.psql_dsn, ResourceTags.redis_dsn, ResourceTags.mimir_base_url, ResourceTags.loki_push_endpoint]
    needed_res: set[str] = {
        val.data_type
        for val in project.shared_secrets
        if val.name.upper() not in envs and val.name.lower() not in envs and val.data_type in supported_types
    }

    resource_tags = set(ResourceTags)

    for secret in project.shared_secrets:
        tags = set(secret.tags).intersection(resource_tags)
        needed_res.update(tags)


    resource_values: dict[str, str] = {}

    if data_dir is None:
        data_dir = Path.cwd().absolute() / ".data"


    grafana_sources: list[GrafanaSource] = []

    if ResourceTags.loki_push_endpoint in needed_res:
        name = f"{project.name}-loki"

        base_url = f"http://{name}:3100"
        resource_values[ResourceTags.loki_base_url] = base_url
        resource_values[ResourceTags.loki_push_endpoint] = f"{base_url}/loki/api/v1/push"

        containers.append(
            Container(
                name=name,
                image="grafana/loki:3.1.0",
                restart="always",
                environments={ },
                volumes=[],
                ports={"3100/tcp": 3100},
            )
        )
        grafana_sources.append(
            GrafanaSource(
                name=f"{project.name}-Loki",
                type="loki",
                url=AnyUrl(base_url)
            )
        )

    # if ResourceTags.mimir_base_url in needed_res:
    #     name = f"{project.name}-mimir"
    #
    #     base_url = f"http://{name}:8080"
    #     resource_values[ResourceTags.mimir_base_url] = base_url
    #     containers.append(
    #         Container(
    #             name=name,
    #             image="grafana/mimir:2.12.0",
    #             restart="always",
    #             environments={ 
    #                 "JAEGER_AGENT_HOST": "otelcol"
    #             },
    #             volumes=[],
    #             ports={"8080/tcp": 8080},
    #         )
    #     )
    #     grafana_sources.append(
    #         GrafanaSource(
    #             name=f"{project.name}-Mimir",
    #             type="mimir",
    #             url=AnyUrl(base_url)
    #         )
    #     )

    if grafana_sources:
        name = f"{project.name}-grafana"

        grafana_dir = data_dir / "grafana"
        grafana_dir.mkdir(exist_ok=True, parents=True)

        grafana_source_file = grafana_dir / "sources.yaml"

        file = GrafanaSourcesFile(datasources=grafana_sources)
        grafana_source_file.write_text(yaml.dump(json.loads(file.model_dump_json())))


        containers.append(
            Container(
                name=name,
                image="grafana/grafana:11.0.0",
                restart="always",
                environments={ 
                    "GF_AUTH_ANONYMOUS_ENABLED": "true",
                    "GF_AUTH_ANONYMOUS_ORG_ROLE": "Admin",
                    "GF_AUTH_DISABLE_LOGIN_FORM": "true",
                    "GF_SECURITY_ALLOW_EMBEDDING": "true",
                },
                volumes=[f"{grafana_source_file.as_posix()}:/etc/grafana/provisioning/datasources/datasources.yaml"],
                ports={"3000/tcp": 3000},
            )
        )


    if ResourceTags.psql_dsn in needed_res:
        name = f"{project.name}-psql"
        protocol = "postgresql"

        with suppress(ImportError):
            import psycopg
            protocol = "postgresql+psycopg"

        with suppress(ImportError):
            import psycopg2
            protocol = "postgresql+psycopg2"

        with suppress(ImportError):
            import asyncpg
            protocol = "postgresql+asyncpg"

        resource_values[ResourceTags.psql_dsn] = f"{protocol}://user:pass@{name}:5432/db"
        resource_values[ResourceTags.database_host] = name
        resource_values[ResourceTags.database_name] = "db"
        resource_values[ResourceTags.database_username] = "user"
        resource_values[ResourceTags.database_password] = "pass"
        resource_values[ResourceTags.database_ssl] = "false"

        containers.append(
            Container(
                name=name,
                image="postgres:15",
                restart="always",
                environments={
                    "POSTGRES_USER": "user",
                    "POSTGRES_PASSWORD": "pass",
                    "POSTGRES_DB": "db"
                },
                volumes=[f"{data_dir.as_posix()}/postgresql:/var/lib/postgresql/data"],
                ports={"5432/tcp": 5432},
            )
        )

    if ResourceTags.redis_dsn in needed_res:
        name = f"{project.name}-redis"
        resource_values[ResourceTags.redis_dsn] = f"redis://{name}:6379"
        resource_values[ResourceTags.redis_username] = ""
        resource_values[ResourceTags.redis_password] = ""
        containers.append(
            Container(
                name=name,
                image="redis:7.2.11",
                restart="always",
                environments={},
                volumes=[
                    f"{data_dir.as_posix()}/valkey:/data"
                ],
                ports={"6379/tcp": 6379},
            )
        )


    if project.subscribers:
        name = f"{project.name}-nats"
        nats_url = f"nats://{name}:4222"

        resource_values[ResourceTags.nats_dsn] = nats_url
        containers.append(
            Container(
                name=name,
                image="nats:2.12.2-alpine",
                restart="always",
                environments={},
                volumes=[],
                ports={"4222/tcp": 4222},
            )
        )


    needs_localstack = False

    if ResourceTags.s3_secret_key in needed_res:
        needs_localstack = True

    if needs_localstack or project.workers:
        name = f"{project.name}-infra"

        resource_values.update({
            ResourceTags.sqs_endpoint: f"http://{name}:4566",
            ResourceTags.sqs_access_key: "local",
            ResourceTags.sqs_secret_key: "local",
            ResourceTags.sqs_region_name: "us-east-1",

            ResourceTags.s3_endpoint: f"http://{name}:4566",
            ResourceTags.s3_access_key: "local",
            ResourceTags.s3_secret_key: "local",
            ResourceTags.s3_region_name: "us-east-1",
            ResourceTags.s3_bucket_name: "local",
        })

        containers.append(
            Container(
                name=name,
                image="localstack/localstack",
                restart="always",
                ports={"4566/tcp": 4566},
                environments={},
                volumes=[
                    "/var/run/docker.sock:/var/run/docker.sock",
                    f"{data_dir.as_posix()}/localstack:/var/lib/localstack"
                ],
            )
        )

    return (containers, resource_values)


def setup_resource() -> None:
    pass


def stream_container(
    container_id: str,
    container_type: Literal["resource", "app", "worker", "subscriber", "primary"],
    event: Event | None = None
) -> None:

    color_map = {
        "resource": "blue",
        "app": "yellow",
        "worker": "green",
        "subscriber": "red",
        "primary": "bold magenta",
        "other": "cyan"
    }

    color = color_map.get(container_type, "cyan")
    is_primary = container_type == "primary"


    try:
        client = DockerClient.from_env()

        container = client.containers.get(container_id)
        console.print(f"[dim]  Waiting for {container.name} to start...[/dim]")
        

        is_ready_and_healthy = False

        while not is_ready_and_healthy:
            sleep(0.5)
            container.reload()

            if container.status != "running":
                continue

            if 'Health' not in container.attrs['State']:
                is_ready_and_healthy = True
                console.print(f"[bold green]✓[/bold green] {container.name} is running")

                if event: 
                    event.set()

                continue

            health_status = container.attrs['State']['Health']['Status']

            if health_status == 'healthy':
                is_ready_and_healthy = True
                console.print(f"[bold green]✓[/bold green] {container.name} is running")

                if event: 
                    event.set()
    except Exception as e:
        logger.exception(e)
        if event:
            event.set()
        return

    try:
        for log in client.api.logs(container_id, stream=True, follow=True):
            log_text = Text()
            if is_primary:
                log_text.append(">>> ", style="bold magenta")
            log_text.append(f"[{container.name}]", style=f"bold {color}")
            log_text.append(" ")
            log_text.append(log.decode('utf-8').rstrip())
            console.print(log_text)


    except Exception:
        console.print(f"[bold red]Run docker inspect {container_id} to get more info[/bold red]")

    cont = client.containers.get(container_id)

    status = cont.attrs.get("State", {})
    exit_code = status.get("ExitCode")
    error = status.get("Error")
    is_oom_killed = status.get("OOMKilled")

    logger.info(f"Container {cont.name} {cont.status} with exit code {exit_code}")

    if is_oom_killed:
        logger.error(f"OOM! Consider increasing the the memory limit of {cont.name}")

    if error:
        logger.error(f"Container had error message {error}")


def dev_volumes(
    project: Project, 
    current_dir: Path, 
    sub_source_dir: str,
    with_tests: bool = False
) -> dict[str, dict[str, str]]:
    source_dir = f"/app/{sub_source_dir}"

    if (current_dir / project.name).is_dir():
        src_dir = current_dir / project.name
        volumes = {
            src_dir.absolute().as_posix(): {
                "bind": f"{source_dir}/{src_dir.name}",
                "mode": "ro"
            }
        }
    elif (current_dir / "src").is_dir():
        src_dir = current_dir / "src"
        volumes = {
            src_dir.absolute().as_posix(): {
                "bind": f"{source_dir}/{src_dir.name}",
                "mode": "ro"
            }
        }
    else:
        import os
        src_dir = current_dir
        volumes = {}

        ignore_paths = [".venv", "venv", ".git", ".cursor", "tests", "__pycache__", ".github"]

        for sub_dir in os.listdir(src_dir.as_posix()):

            if sub_dir in ignore_paths:
                continue

            sub_path = src_dir / sub_dir

            if sub_path.is_dir():
                volumes[sub_path.absolute().as_posix()] = {
                    "bind": f"{source_dir}/{sub_dir}",
                    "mode": "ro"
                }

    project_file = current_dir / "project.py"
    if project_file.is_file():
        volumes[project_file.absolute().as_posix()] = {
            "bind": f"{source_dir}/{project_file.name}",
            "mode": "ro"
        }


    for path in project.additional_dirs or []:
        if path.is_dir() or path.is_file():
            volumes[path.absolute().as_posix()] = {
                "bind": f"{source_dir}/{path.as_posix()}",
                "mode": "ro"
            }

    for path in project.testing_dirs or []:
        if path.is_dir() or path.is_file():
            volumes[path.absolute().as_posix()] = {
                "bind": f"{source_dir}/{path.as_posix()}",
                "mode": "ro"
            }

    return volumes


def prepare_project(project: Project, context: str | None, dockerfile: str | None) -> ProjectContainer:
    client = DockerClient.from_env()

    should_build = True

    lockfile = find_lockfile()
    lockhash = sha256(lockfile.read_bytes(), usedforsecurity=False).hexdigest()

    with suppress(Exception):
        image = client.images.get(name=f"{project.name}:latest")
        labels = image.attrs.get("Config", {}).get("Labels", {})
        if labels.get(ImageKeys.lock_hash, "") == lockhash:
            should_build = False

    if should_build:
        with status.Status(f"[bold blue]Building image for {project.name}...", console=console):
            build_image(project, tag="latest", context=context, dockerfile_path=dockerfile)
        console.print("[bold green]✓[/bold green] Image built successfully")

    image = client.images.get(name=f"{project.name}:latest")
    labels = image.attrs.get("Config", {}).get("Labels", {})

    source_dir = labels.get(ImageKeys.source_dir, "")

    return ProjectContainer(source_dir=source_dir)




def compose(
    project: Project,
    base_image: str,
    volumes: dict[str, dict[str, str]],
    env_file: str | None,
    components: list[str] | None = None,
    client: DockerClient | None = None,
    data_dir: Path | None = None,
    primary_container: CompiledJob | None = None,
    env: Environments | None = None
) -> int | None:
    from dotenv.main import dotenv_values, find_dotenv
    from docker.models.containers import Container as ContainerType

    console.print()
    console.print(Panel(
        f"Starting project: [bold cyan]{project.name}[/bold cyan]\n"
        f"Base image: [dim]{base_image}[/dim]",
        title="Docker Compose",
        border_style="blue",
        title_align="left"
    ))


    env_file = env_file or find_dotenv() or ".env"
    dotenvs = dotenv_values(dotenv_path=env_file)

    if not env:
        env = "dev"
    
    dotenvs.update(NobsEnvironment(nobs_env=env).model_dump())

    client = client or DockerClient.from_env()
    containers: list[ContainerType] = []
    log_treads: list[Thread] = []

    compiled = CompiledProject.from_project(project, packages=[])

    networks = [
        net for net in client.networks.list()
        if net.name == project.name
    ]
    platform_arc = "linux/amd64"

    container_labels = ["nobs", project.name]
    conts: list[ContainerType] = client.containers.list(
        all=True, filters={"label": container_labels}
    )

    existing_resources: list[str] = []

    if components:
        components = [
            f"{project.name}-{comp}" for comp in components
        ]

    for cont in conts:
        if primary_container:
            cont.remove(force=True)
        elif "resource" not in cont.labels and (components is None or cont.name in components):
            cont.remove(force=True)
        else:
            existing_resources.append(cont.name) # type: ignore

    other_containers: list[ContainerType] = client.containers.list(all=True)
    exposed_ports: list[int] = []
    for container in other_containers:
        for vals in container.ports.values():
            if vals:
                exposed_ports.extend(
                    [
                        int(val.get("HostPort"))
                        for val in vals
                    ]
                )

    def unexposed_ports(ports: dict[str, int]) -> dict[str, int]:
        new_ports = {}
        for internal_port, exposed_port in ports.items():
            modified_port = exposed_port
            while modified_port in exposed_ports:
                modified_port += 1
            new_ports[internal_port] = modified_port
            exposed_ports.append(modified_port)
        return new_ports

    if networks:
        network = networks[0]
    else:
        network = client.networks.create(name=project.name, driver="bridge")

    application_volume = volumes
    resource_containers, resource_values = needed_containers(compiled, dotenvs, data_dir)

    new_exposed_ports: dict[str, list[int]] = {}

    resource_ready: list[Event] = []

    for container in resource_containers:

        if container.name in existing_resources:
            console.print(f"[bold blue]→[/bold blue] Using existing resource: [cyan]{container.name}[/cyan]")
            continue

        console.print(f"[bold blue]→[/bold blue] Creating resource: [cyan]{container.name}[/cyan]")

        new_ports = unexposed_ports(container.ports)
        new_exposed_ports[container.name] = list(new_ports.values())
        event = Event()

        resource_ready.append(event)

        try:
            cont = client.containers.run(
                image=container.image,
                environment=container.environments,
                volumes=container.volumes,
                ports=new_ports,
                network=network.name,
                name=container.name,
                labels=[*container_labels, "resource"],
                detach=True,
                remove=True,

                # restart_policy=container.restart,
                # ports=container.ports,
            )
        except Exception as e:
            logger.exception(e)
            console.print(f"[bold red]Failed to start container named '{container.name}'.[/bold red]")


        containers.append(cont)
        thread = Thread(target=stream_container, args=(cont.id, "resource", event))
        thread.daemon = True
        thread.start()
        log_treads.append(thread)



    for event in resource_ready:
        event.wait(60)

    shared_secrets: dict[str, str] = {}

    for container in compiled.network_apps:

        name = f"{project.name}-{container.name}"
        new_ports = unexposed_ports({f"{container.port}/tcp": container.port})
        new_exposed_ports[name] = list(new_ports.values())

        port = next(iter(new_exposed_ports[name]))

        resource_values[ServiceUrl(container.name, "internal").to_string()] = f"http://{name}:{container.port}"
        resource_values[ServiceUrl(container.name, "external").to_string()] = f"http://localhost:{port}"

    for secret_type in project.shared_secrets or []:
        shared_secrets.update(
            settings_for_secrets(
                secrets_for(secret_type),
                resource_values, 
            )
        )

    if ResourceTags.s3_secret_key in resource_values:
        import boto3
        conf = settings_for_resources(resource_values, S3StorageConfig)

        assert conf.s3_endpoint
        url = conf.s3_endpoint.encoded_string().replace(conf.s3_endpoint.host or "", "localhost")

        s3 = boto3.client(
            "s3",
            endpoint_url=url,
            aws_access_key_id=conf.s3_access_key,
            aws_secret_access_key=conf.s3_secret_key.get_secret_value(),
            region_name=conf.s3_region
        )
        try:
            s3.head_bucket(Bucket=conf.s3_bucket)
            logger.info(f"Bucket '{conf.s3_bucket}' already exists")
        except Exception:
            logger.info(f"Creating bucket '{conf.s3_bucket}'")
            s3.create_bucket(Bucket=conf.s3_bucket)
            logger.info(f"Created bucket '{conf.s3_bucket}'")


    health_events: list[Event] = []

    for container in compiled.network_apps:

        if components and container.name not in components:
            continue

        console.print(f"[bold blue]→[/bold blue] Creating app: [yellow]{container.name}[/yellow]")

        envs = settings_for_secrets(
            container.secrets or [], resource_values
        )

        if container.command:
            if "uvicorn" in container.command[-1] and "--reload" not in container.command:
                container.command[-1] = container.command[-1] + " --reload"

            if "fastapi" in container.command[-1]:
                container.command[-1] = container.command[-1].replace("run", "dev")


        name = f"{project.name}-{container.name}"
        new_ports = {f"{container.port}/tcp": new_exposed_ports[name][0]}


        healthcheck = None
        health_event = None
        if container.health_check:
            check = container.health_check
            healthcheck = {
                "test": ["CMD", "python", "-c", f"import urllib.request; urllib.request.urlopen('http://localhost:{container.port}{check.url}')" ],
                "interval": check.interval * 000000000,  # 10 seconds in nanoseconds
                "timeout": check.timeout * 000000000,    # 5 seconds in nanoseconds
                "retries": check.retries,
                "start_period": 10000000000
            }
            health_event = Event()
            health_events.append(health_event)



        cont = client.containers.run(
            image=container.docker_image or base_image,
            name=name,
            environment={
                **(container.environments or {}),
                **envs,
                **shared_secrets,
                **{
                    key: value for key, value 
                    in dotenvs.items()
                    if key not in envs and key not in shared_secrets and value
                }
            },
            volumes=application_volume,
            command=container.command,
            network=network.name,
            detach=True,
            labels=container_labels,
            ports=new_ports,
            mem_limit=f"{container.compute.mb_memory_limit}m",
            cpu_quota=container.compute.mvcpu_limit * 100,
            cpu_period=100_000,
            platform=platform_arc,
            healthcheck=healthcheck
        )
        containers.append(cont)

        thread = Thread(target=stream_container, args=(cont.id, "app", health_event))
        thread.daemon = True
        thread.start()
        log_treads.append(thread)


    for container in compiled.subscribers:
        if components and container.name not in components:
            continue

        envs = settings_for_secrets(
            container.secrets or [], resource_values
        )

        console.print(f"[bold blue]→[/bold blue] Creating subscriber: [red]{container.name}[/red]")
        cont = client.containers.run(
            image=base_image,
            name=f"{project.name}-{container.name}",
            environment={
                **(container.environments or {}),
                **envs,
                **shared_secrets,
                **{
                    key: value for key, value 
                    in dotenvs.items()
                    if key not in envs and key not in shared_secrets and value
                }
            },
            volumes=application_volume,
            command=["/bin/bash", "-c", f"nobs subscriber {container.name}"],
            network=network.name,
            detach=True,
            labels=container_labels,
            cpu_quota=container.compute.mvcpu_limit * 100,
            cpu_period=100_000,
            mem_limit=f"{container.compute.mb_memory_limit}m",
            platform=platform_arc,
        )

        containers.append(cont)

        thread = Thread(target=stream_container, args=(cont.id, "subscriber"))
        thread.daemon = True
        thread.start()
        log_treads.append(thread)


    for container in compiled.workers:
        if components and container.name not in components:
            continue

        envs = settings_for_secrets(
            container.secrets or [], resource_values
        )
        console.print(f"[bold blue]→[/bold blue] Creating worker: [green]{container.name}[/green]")
        cont = client.containers.run(
            image=base_image,
            name=f"{project.name}-{container.name}",
            environment={ 
                **envs,
                **shared_secrets,
                **{
                    key: value for key, value 
                    in dotenvs.items()
                    if key not in envs and key not in shared_secrets and value
                }
            },
            volumes=application_volume,
            command=["/bin/bash", "-c", f"nobs process-queue {container.name}"],
            network=network.name,
            detach=True,
            labels=container_labels,
            cpu_quota=container.compute.mvcpu_limit * 100,
            cpu_period=100_000,
            mem_limit=f"{container.compute.mb_memory_limit}m",
            platform=platform_arc,
        )

        containers.append(cont)

        thread = Thread(target=stream_container, args=(cont.id, "worker"))
        thread.daemon = True
        thread.start()
        log_treads.append(thread)

    if components:
        for container in compiled.jobs:
            envs = settings_for_secrets(
                container.secrets or [], resource_values
            )
            console.print(f"[bold blue]→[/bold blue] Running job: [green]{container.name}[/green]")
            cont = client.containers.run(
                image=base_image,
                name=f"{project.name}-{container.name}",
                environment={ 
                    **envs,
                    **shared_secrets,
                    **{
                        key: value for key, value 
                        in dotenvs.items()
                        if key not in envs and key not in shared_secrets and value
                    }
                },
                volumes=application_volume,
                command=["/bin/bash", "-c", container.command(project.name)],
                network=network.name,
                detach=True,
                labels=container_labels,
                cpu_quota=container.compute.mvcpu_limit * 100,
                cpu_period=100_000,
                mem_limit=f"{container.compute.mb_memory_limit}m",
                platform=platform_arc,
            )

            containers.append(cont)

            thread = Thread(target=stream_container, args=(cont.id, "worker"))
            thread.daemon = True
            thread.start()
            log_treads.append(thread)





    table = Table(title="Running Containers", show_header=True, header_style="bold magenta")
    table.add_column("Container", style="cyan", no_wrap=True)
    table.add_column("ID", style="dim")
    table.add_column("Type", style="green")
    table.add_column("Access", style="blue")
    table.add_column("Credentials", style="blue")

    resource_names = {rc.name for rc in resource_containers}
    app_names = {f"{project.name}-{app.name}" for app in compiled.network_apps}
    worker_names = {f"{project.name}-{worker.name}" for worker in compiled.workers}
    subscriber_names = {f"{project.name}-{sub.name}" for sub in compiled.subscribers}

    conts: list[ContainerType] = client.containers.list(
        all=True, filters={"label": container_labels}
    )

    for container in conts:
        ports = new_exposed_ports.get(container.name or "Unknown", [])

        credentials = ""

        container_type = "other"
        if container.name in resource_names:
            container_type = "resource"

            if container.name == f"{project.name}-psql":
                print_values = {
                    "Username": ResourceTags.database_username,
                    "Password": ResourceTags.database_password,
                    "Database": ResourceTags.database_name
                }
                credentials = "\n".join([
                    f"{key}: {resource_values.get(value, '')}" for key, value in print_values.items()
                ])

            if container.name == f"{project.name}-redis":
                print_values = {
                    "Username": ResourceTags.redis_username,
                    "Password": ResourceTags.redis_password,
                }
                credentials = "\n".join([
                    f"{key}: {resource_values.get(value, '')}" for key, value in print_values.items()
                ])
        elif container.name in app_names:
            container_type = "app"
        elif container.name in worker_names:
            container_type = "worker"
        elif container.name in subscriber_names:
            container_type = "subscriber"

        if ports:
            port_numbers = sorted(ports)
            
            if len(port_numbers) > 3:
                min_port = min(port_numbers)
                max_port = max(port_numbers)
                access_urls = f"http://localhost:{min_port}-{max_port}"
            else:
                access_urls = "\n".join([
                    f"http://localhost:{port}"
                    for port in port_numbers
                ])
        else:
            access_urls = "background"

        table.add_row(
            container.name,
            container.id[:12],
            container_type,
            access_urls, 
            credentials
        )

    console.print()
    console.print(table)
    console.print()

    for event in health_events:
        event.wait(60)


    def shutdown_containers(reason: str, border_style: str = "red") -> None:
        console.print()
        console.print(Panel(
            reason,
            title="Shutdown",
            border_style=border_style,
            title_align="left"
        ))
        for container in reversed(containers):
            console.print(f"[dim]Stopping {container.name}...[/dim]")
            with suppress(Exception):
                container.stop()
        console.print("[bold green]✓[/bold green] All containers stopped")

    if primary_container:
        envs = settings_for_secrets(
            primary_container.secrets or [], resource_values
        )
        container_full_name = f"{project.name}-{primary_container.name}"
        console.print(f"[bold blue]→[/bold blue] Running primary: [bold magenta]{container.name}[/bold magenta]")

        cont = client.containers.run(
            image=base_image,
            name=container_full_name,
            environment={
                **envs,
                **shared_secrets,
                **{
                    key: value for key, value
                    in dotenvs.items()
                    if key not in envs and key not in shared_secrets and value
                }
            },
            volumes=application_volume,
            command=["/bin/bash", "-c", primary_container.command(project.name)],
            network=network.name,
            detach=True,
            labels=container_labels,
            cpu_quota=primary_container.compute.mvcpu_limit * 100,
            cpu_period=100_000,
            mem_limit=f"{primary_container.compute.mb_memory_limit}m",
            platform=platform_arc,
        )

        thread = Thread(target=stream_container, args=(cont.id, "worker"))
        thread.daemon = True
        thread.start()
        log_treads.append(thread)

        try:
            result = cont.wait()
            exit_code = result.get("StatusCode", 1)

            if exit_code == 0:
                shutdown_containers("Primary container completed successfully", "green")
            else:
                shutdown_containers(f"Primary container exited with code {exit_code}", "red")

            return exit_code
        except KeyboardInterrupt:
            shutdown_containers("Received shutdown signal, stopping all containers...")
            return 130
    else:
        try:
            while True:
                sleep(10000)
        except KeyboardInterrupt:
            shutdown_containers("Received shutdown signal, stopping all containers...")

    return None


def default_docker_image(
    uv_image: str, 
    source_code_dir: str, 
    pre_lock_add: str,
    lock_file: Path,
    pyproject_file: Path,
    project_file: Path,
    copy_additional_dirs: str,
    copy_path_packages: str,
    source_dir: Path
) -> str:

    docker_source = "/app" / source_dir

    return f"""FROM {uv_image} AS builder

WORKDIR /app

{pre_lock_add}
{copy_path_packages}
{copy_additional_dirs}

COPY {lock_file} {docker_source}/uv.lock
COPY {pyproject_file} {docker_source}/pyproject.toml

WORKDIR {docker_source}

RUN uv venv {docker_source}/.venv --clear
ENV UV_SYSTEM_PYTHON=true VIRTUAL_ENV={docker_source}/.venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-install-project --active

COPY {source_dir / source_code_dir} {docker_source / source_code_dir}

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --active

FROM {uv_image}

COPY --from=builder --chown=app:app {docker_source}/.venv {docker_source}/.venv

WORKDIR {docker_source}

{copy_additional_dirs}
COPY {project_file} {docker_source / 'project.py'}
COPY {source_dir / source_code_dir} {docker_source / source_code_dir}

ENV PATH="{docker_source}/.venv/bin:$PATH"
"""


def create_dockerfile_for(
    project: Project, dockerfile: Path, pyproject: Path, lockfile: Path, path_packages: list[str], python_version: str
) -> tuple[Path, Path]:
    import os

    context = Path(".")
    source_dir_sub_dir = Path()

    if path_packages:
        context = Path(os.path.commonpath([
            context.resolve(),
            *[
                Path(path).resolve() 
                for path in path_packages
            ]
        ]))
        source_dir_sub_dir = Path(".").resolve().relative_to(context)


    def copy_from_path(path: Path) -> str:
        if context.resolve() == Path(".").resolve():
            return path.as_posix()
        return path.resolve().relative_to(context.resolve()).as_posix()

    source_code_dir_name = "src" 
    source_code_dir = source_dir_sub_dir / source_code_dir_name

    if not (context / source_code_dir).is_dir():
        source_code_dir_name = project.name.replace("-", "_").replace("/", "")
        source_code_dir = source_dir_sub_dir / source_code_dir_name

    if not (context / source_code_dir).is_dir():
        source_code_dir = source_dir_sub_dir.resolve()
        source_code_dir_name = ""

    uv_image = f"ghcr.io/astral-sh/uv:python{python_version}-bookworm-slim"

    if not (context / source_code_dir).is_dir():
        raise ValueError(f"Expected to find source code at '{context / source_code_dir}', but found nothing.")

    pre_lock_add = ""
    copy_additional_dirs = ""
    copy_path_packages = ""

    apt_packages = set()

    deps = pyproject.read_text()
    if "git =" in deps or "git=" in deps:
        # Install git so that git dependencies can be loaded in the slim image
        apt_packages.add("git")
        pre_lock_add += "RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*\n"

    if "psycopg2-binary" in deps:
        apt_packages.update(["libpq-dev", "gcc"])

    if "pyodbc" in deps:
        apt_packages.add("g++")

    if apt_packages:
        packages = " ".join(sorted(apt_packages))
        pre_lock_add += f"RUN apt-get update && apt-get install -y {packages} && rm -rf /var/lib/apt/lists/*\n"


    if path_packages:
        rel_source = source_code_dir.resolve().relative_to(context.resolve())
        for path in path_packages:
            package_path = Path(path).resolve()
            rel_path = package_path.relative_to(context)

            if rel_path == rel_source or rel_source.is_relative_to(rel_path):
                logger.debug(f"Skipping to add package at '{rel_path}' as it contains the source code.")
                continue

            copy_path_packages += f"COPY {rel_path.as_posix()} /app/{rel_path.as_posix()}\n"

    if project.additional_dirs:
        copy_additional_dirs += "\n".join([
            f"COPY {copy_from_path(path)} /app/{source_dir_sub_dir / path.as_posix()}"
            for path in project.additional_dirs
        ])

    project_file = "project.py"

    if "workspace = " in deps or "workspace=" in deps:
        current = Path.cwd()

        paths = []

        while not (current / ".git").is_dir():
            paths.insert(0, current.name)
            current = (current / "..").resolve()

        context = current

        pre_lock_add += "COPY . ."
        if paths:
            source_code_dir_name = source_code_dir_name
            source_dir_sub_dir = Path("/".join(paths))
    else:
        lockfile = source_dir_sub_dir / lockfile

    if "../" in lockfile.as_posix():
        lockfile = lockfile.resolve().relative_to(context)

    file = default_docker_image(
        uv_image, 
        source_code_dir_name, 
        pre_lock_add,
        lock_file=lockfile,
        pyproject_file=source_dir_sub_dir / pyproject,
        copy_additional_dirs=copy_additional_dirs,
        copy_path_packages=copy_path_packages,
        source_dir=source_dir_sub_dir,
        project_file=source_dir_sub_dir / project_file
    )

    logger.debug(file)
    dockerfile.write_text(file)
    return context, source_dir_sub_dir

def find_lockfile() -> Path:
    max_checks = 10
    lockfile = Path("uv.lock")
    original_file = lockfile.resolve()
    n_checks = 0

    while not lockfile.is_file():
        lockfile = ".." / lockfile 
        n_checks += 1
        if n_checks > max_checks:
            raise ValueError(f"Unable to find a uv.lock file. Was looking in '{original_file}'")

    return lockfile


@dataclass
class LockfileInfo:
    packages: list[str]
    path_packages: list[str]
    current_package: str

def packages_from_lockfile(file: Path) -> LockfileInfo:
    packages: list[str] = []
    path_packages: list[str] = []
    current_package: str | None = None

    lock_file = tomli.loads(
        file.read_text()
    )
    for package in lock_file["package"]:
        packages.append(package["name"])

        source = package["source"]
        if "virtual" in source:
            path = source["virtual"]
            if path == ".":
                current_package = package["name"]
        elif "directory" in source:
            path_packages.append(source["directory"])
        elif "editable" in source:
            path = source["editable"]
            if path == ".":
                current_package = package["name"]
            else:
                path_packages.append(source["editable"])

    assert current_package, "Unable to find package name from lock file"
    return LockfileInfo(
        packages=packages, path_packages=path_packages, current_package=current_package
        
    ) 


def build_image(
    project: Project, 
    tag: str, 
    context: str | None = None,
    dockerfile_path: str | None = None
) -> str:
    pyproject_path = Path("pyproject.toml")

    dockerfile = Path(dockerfile_path) if dockerfile_path else Path("Dockerfile")

    version: str = tomli.loads(
        pyproject_path.read_text()
    ).get("project", {}).get("requires-python", "3.12").split(",")[0]


    if version.startswith(">="):
        version = "3.13"
    else:
        version = "".join([
            c for c in version
            if c.isnumeric() or c == "."
        ])
    version = '.'.join(version.split(".")[0:2])


    lockfile = find_lockfile()
    lockhash = sha256(lockfile.read_bytes(), usedforsecurity=False).hexdigest()
    lockfile_info = packages_from_lockfile(lockfile)

    if not pyproject_path.is_file():
        raise ValueError("Expected a pyproject.toml file using uv.")

    should_delete_dockerfile = False

    source_dir = Path("")
    if dockerfile_path is None:
        if dockerfile.is_file():
            dockerfile = Path(f"Dockerfile-{uuid4()}")

        temp_context, source_dir = create_dockerfile_for(
            project, 
            dockerfile or Path("Dockerfile"), 
            pyproject_path, 
            lockfile=lockfile,
            path_packages=lockfile_info.path_packages,
            python_version=version or "3.12"
        )

        should_delete_dockerfile = True
        if context is None:
            context = temp_context.resolve().as_posix()

    platform = "linux/amd64"
    reg_url = f"{project.name}:{tag}"

    build_dir = Path.cwd()
    try:
        if context:
            context_path = (build_dir / context).resolve().as_posix()
            logger.info(f"Using context {context_path} with dockerfile {dockerfile.resolve().as_posix()}")
        else:
            context_path = "."

        docker_command = [
            "docker", "build", context_path, 
            "-t", reg_url, 
            "-f", dockerfile.resolve().as_posix(), 
            "--platform", platform,
            "--label", f"com.takkthon.lockhash={lockhash}",
            "--label", f"com.takkthon.source-dir={source_dir.as_posix()}"
        ]
        logger.debug(f"Running command {docker_command}")
        default_runner(docker_command)
    except Exception as e:
        if should_delete_dockerfile:
            dockerfile.unlink(True)

        logger.error("Unable to build image")
        raise ValueError("Unable to build image") from e

    if should_delete_dockerfile:
        dockerfile.unlink(True)

    return reg_url
