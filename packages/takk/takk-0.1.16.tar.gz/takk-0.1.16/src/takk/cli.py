from contextlib import suppress
import functools
import json
from pathlib import Path
from uuid import uuid4
import click
import logging
import asyncio

from docker import DockerClient
from pydantic import BaseModel, SecretStr, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from takk.docker import build_image, dev_volumes, find_lockfile, packages_from_lockfile, prepare_project
from takk.models import CompiledJob, Job, NetworkApp, Project, Subscriber, NobsClient, NobsServer, secrets_for
from takk.runners import default_runner


logger = logging.getLogger(__name__)
console = Console()

def async_(func):  # noqa
    """Decorator to run async functions."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # noqa
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group(help="""
takk - A CLI for managing and deploying Python applications.

Define your project in a project.py file, then use these commands to build,
run, test, and deploy your applications with Docker-based infrastructure.

\b
Quick Start:
  takk up              Start local development environment
  takk deploy          Deploy to production
  takk test            Run tests in isolated containers
""")
def cli():
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.ERROR)

    load_dotenv(".env")


@cli.command(help="Show the current version of takk.")
def version() -> None:
    from takk import __version__
    click.echo(__version__)


def read_project_at(ref: str | None = None, env: str | None = None) -> Project:
    import sys

    if ref is None:
        ref = "project:project"

    path = Path.cwd().as_posix()
    if path not in sys.path:
        sys.path.append(path)

    return project_at(ref)


def project_at(ref: str, env: str | None = None) -> Project:
    import importlib
    import inspect
    import os

    if env:
        os.environ["NOBS_ENV"] = env

    module_name, attr_name = ref.split(":")

    module = importlib.import_module(module_name)
    project = getattr(module, attr_name)

    assert isinstance(project, Project), f"Expected a project got '{type(project)}'"

    project.project_file = inspect.getsource(module)
    return project


@cli.command(help="Deploy the project to a remote server.")
@click.option("--ref", help="Project reference in format 'module:attribute' (default: project:project).")
@click.option("--server", help="Override the server API URL.")
@click.option("--env", default="test", help="Target environment (default: test).")
@click.option("--no-push", is_flag=True, help="Skip building and pushing the Docker image.")
@click.option("--create-resources", is_flag=True, help="Create cloud resources after deployment.")
@click.option("--context", "-c", help="Docker build context directory.")
@click.option("--dockerfile", "-f", help="Path to Dockerfile.")
@async_
async def deploy(
    ref: str | None, 
    server: str | None, 
    env: str, 
    no_push: bool, 
    context: str | None = None,
    dockerfile: str | None = None,
    create_resources: bool = False
) -> None:
    import sys

    click.echo("Deploying project")

    path = Path.cwd().as_posix()

    if ref is None:
        ref = "project:project"

    if server:
        config = NobsServer(nobs_api=server) # type: ignore
    else:
        config = NobsServer.read()

    if path not in sys.path:
        sys.path.append(path)

    project = project_at(ref, env)

    lockfile_info = packages_from_lockfile(
        find_lockfile()
    )
    if not project.name:
        project.name = lockfile_info.current_package

    if not no_push:
        local_image = build_image(
            project, 
            tag=env, 
            context=context, 
            dockerfile_path=dockerfile
        )
        await push_image(project, env, local_image)
        click.echo("Source image is updated")

    client = NobsClient(settings=config)
    res = await client.update(project, env=env, packages=lockfile_info.packages)

    if create_resources:
        await client.deploy(res.project_env_id)



@cli.command(help="Run a specific component from the project.")
@click.argument("name", metavar="COMPONENT")
@click.option("--ref", help="Project reference in format 'module:attribute' (default: project:project).")
@click.option("--platform", help="Docker platform (default: linux/amd64).")
@click.option("--env-file", help="Path to environment variables file.")
@async_
async def run(name: str, ref: str | None, platform: str | None, env_file: str | None = None) -> None:
    import sys
    import inspect

    if ref is None:
        ref = "project:project"

    path = Path.cwd().as_posix()
    if path not in sys.path:
        sys.path.append(path)

    if platform is None:
        platform = "linux/amd64"

    project = project_at(ref)

    if name not in project.components:
        raise ValueError(f"Unable to find '{name}'")

    comp = project.components[name]

    logger.info(comp)

    if isinstance(comp, NetworkApp):
        command = comp.command
    elif isinstance(comp, Job):
        from dotenv import load_dotenv

        load_dotenv()

        if inspect.iscoroutinefunction(comp.main_function):
            await comp.main_function(comp.arguments)
        else:
            comp.main_function(comp.arguments)
        return
    elif isinstance(comp, Subscriber):
        return
    else:
        command = comp.network_app(Path.cwd()).command

    logger.info(f"Running command {command} in docker file {project.docker_image}")

    base_image = f"{project.name}:latest"
    if project.docker_image:
        base_image = project.docker_image

    assert command

    if env_file:
        command = ["docker", "run", f"--platform={platform}", f"--env-file={env_file}", base_image, *command]
    else:
        command = ["docker", "run", f"--platform={platform}", base_image, *command]

    _ = default_runner(command)




@cli.command(name="run-job", help="Execute a job function directly (used internally by the scheduler).")
@click.option("--project-name", required=True, help="Name of the project.")
@click.option("--job-id", required=True, help="Unique identifier for the job.")
@click.option("--file-ref", required=True, help="Function reference in format 'module:function'.")
@click.option("--args", help="JSON-encoded arguments for the job function.")
@async_
async def run_job(project_name: str, job_id: str, file_ref: str, args: str) -> None:
    import importlib
    import inspect

    click.echo(f"Running ref: {file_ref}")

    try:
        from logging_loki import LokiHandler # type: ignore
        from takk.secrets import LokiLoggerConfig

        config = LokiLoggerConfig() # type: ignore

        auth = None
        if config.loki_user and config.loki_token:
            auth = (config.loki_user, config.loki_token.get_secret_value())

        handler = LokiHandler(
            url=config.loki_push_endpoint,
            auth=auth,
            tags={"job_function": file_ref},
            version=f"{config.loki_logger_version}"
        )

        logging.basicConfig(level=logging.INFO)
        logging.getLogger("").addHandler(handler)
        logger.info("Managed to setup Loki logger")
    except Exception:
        print(f"Unable to setup Loki logger for '{file_ref}'. Make sure `logging_loki` is installed")

    logger.info(f"Running function at '{file_ref}'")
    file, function_name = file_ref.split(":")

    try:
        function_module = importlib.import_module(file)
        function = getattr(function_module, function_name)
    except Exception as e:
        logger.exception(e)
        raise ValueError("Unable to load job function to run.") from e


    assert callable(function)
    sign = inspect.signature(function)   
    params = sign.parameters
    if len(params) == 0:
        if inspect.iscoroutinefunction(function):
            await function()
        else:
            function()
        return

    assert len(params) == 1
    _, param = list(params.items())[0]

    arg_type = param.annotation
    assert not isinstance(arg_type, str), f"Make sure to not use string annotations for {arg_type}"
    assert issubclass(arg_type, BaseModel), f"Expected a subclass of BaseModel got {arg_type}"

    if args:
        encoded_args = arg_type.model_validate_json(args.strip("'"))
    else:
        encoded_args = arg_type()

    try:
        if inspect.iscoroutinefunction(function):
            await function(encoded_args)
        else:
            function(encoded_args)
    except Exception as e:
        logger.exception(e)

        with suppress(Exception):
            client = NobsClient()
            await client.notify_about_failure(project_name, job_id=job_id, exception=e)
        raise e




@cli.command(name="process-queue", help="Start a worker to process messages from a queue.")
@click.argument("name", metavar="QUEUE_NAME")
@async_
async def process_queue(name: str) -> None:
    from takk.secrets import SqsConfig
    from takk.models import QueueMessage
    from takk.queue import QueueBroker, SqsQueueBroker

    project = read_project_at()
    assert project.workers, f"Expected at least one worker got {project.workers}"

    queue = next(queue for queue in project.workers if queue.name == name)
    broker: QueueBroker = SqsQueueBroker(
        config=SqsConfig(), # type: ignore
        queue_settings=queue.queue_settings 
    )
    queue = broker.with_name(name)

    logger.info(f"Ready to receive work at queue '{name}'")

    while True:
        messages = await queue.receive()
        while messages:
            message = messages[0]

            try:
                content = QueueMessage.model_validate_json(message.body)

                _, name = content.function_ref.split(":")
                logger.info(f"Running function named '{name}'")

                await content.run()
                await queue.delete(message)
            except Exception as e:
                logger.exception(e)

            if len(messages) > 1:
                messages = messages[1:]
            else:
                messages = await queue.receive()


@cli.command(help="Start a NATS subscriber for the specified component.")
@click.argument("name", metavar="SUBSCRIBER_NAME")
@async_
async def subscriber(name: str, ref: str | None = None) -> None:
    import inspect
    import nats

    project = read_project_at(ref)

    sub = project.components[name]
    assert isinstance(sub, Subscriber)

    sign = inspect.signature(sub.method)   
    params = sign.parameters

    assert len(params) == 1
    _, param = list(params.items())[0]

    arg_type = param.annotation
    assert not isinstance(arg_type, str), f"Make sure to not use string annotations for {arg_type}"
    assert issubclass(arg_type, BaseModel), f"Expected a subclass of BaseModel got {arg_type}"

    con = await nats.connect("nats://nats:4222")
    subscriber = await con.subscribe(sub.subject)

    while True:
        try:
            message = await subscriber.next_msg()
        except TimeoutError:
            await asyncio.sleep(1)
            continue

        try:
            content = arg_type.model_validate_json(message.data)
            sub.method(content)
        except ValidationError as e:
            logger.exception(e)
            logger.error("Unable to decode message")
        except Exception as e:
            logger.exception(e)



@cli.command(help="Stop and remove running containers.")
@click.option("--all", is_flag=True, help="Stop all takk containers, not just the current project.")
@async_
async def down(all: bool) -> None:
    client = DockerClient.from_env()

    container_labels = ["nobs"]
    if not all:
        project = read_project_at()
        container_labels.append(project.name)

    conts: list = client.containers.list(
        all=True, filters={"label": container_labels}
    )

    for cont in conts:
        click.echo(f"Stopping container {cont.name}")
        cont.remove(force=True)

    click.echo("All container managed by nobs are down.")


@cli.command(help="""Start the local development environment.

\b
Examples:
  takk up                    Start all components
  takk up api worker         Start only api and worker
  takk up --env-file .env    Use custom environment file
""")
@click.argument("components", nargs=-1, metavar="[COMPONENTS]...")
@click.option("--env", default="dev", help="Target environment (default: dev).")
@click.option("--context", "-c", default=None, help="Docker build context directory.")
@click.option("--dockerfile", "-f", default=None, help="Path to Dockerfile.")
@click.option("--env-file", default=None, help="Path to environment variables file.")
@async_
async def up(
    components: list[str],
    env: str,
    ref: str | None = None,
    context: str | None = None,
    env_file: str | None = None,
    dockerfile: str | None = None
) -> None:
    from takk.docker import compose
    from pathlib import Path 

    current_dir = Path.cwd()
    project = read_project_at(ref)

    project_container = prepare_project(project, context, dockerfile)
    volumes = dev_volumes(project, current_dir, project_container.source_dir)

    if env in ["prod", "test"]:
        console.print(Panel(
            f"Loading resources to connect to '[bold yellow]{env}[/bold yellow]'\n"
            "However, this is not supported yet but will be!",
            title="Environment Setup",
            border_style="yellow",
            title_align="left"
        ))
    else:
        console.print(Panel(
            "Setting up local '[bold green]dev[/bold green]' resources",
            title="Environment Setup",
            border_style="green",
            title_align="left"
        ))

    volume_names = [Path(path).name for path in volumes.keys()]
    volumes_text = Text()
    volumes_text.append("Mounted volumes: ", style="bold")
    volumes_text.append(", ".join(volume_names), style="cyan")
    console.print(volumes_text)

    compose(
        project, 
        base_image=f"{project.name}:latest",
        volumes=volumes,
        env_file=env_file,
        components=components if components else None
    )



@cli.command(help="Build the Docker image for the project.")
@click.option("--context", "-c", help="Docker build context directory.")
@click.option("--dockerfile", "-f", help="Path to Dockerfile.")
@click.option("--tag", help="Image tag (default: latest).")
@click.option("--push", is_flag=True, help="Push the image to the registry after building.")
@async_
async def build(
    push: bool,
    tag: str | None = None,
    ref: str | None = None,
    context: str | None = None,
    dockerfile: str | None = None
) -> None:
    project = read_project_at(ref)

    if project.docker_image is not None:
        click.echo("Found docker image definition so will skip build.")
        return 

    if not tag:
        tag = "latest"

    local_image = build_image(project, tag, context, dockerfile)

    if push:
        await push_image(project, tag, local_image)


@cli.command(help="Open an interactive shell inside the project's Docker container.")
@async_
async def shell() -> None:
    project = read_project_at(None)

    if project.docker_image is not None:
        click.echo("Found docker image definition so will skip build.")
        return 


    default_runner([
        "docker", "run", "-it", "--platform=linux/amd64", project.name, "bash"
    ])



@cli.command(name="exec", help="""Execute a command in the project's Docker container with all resources running.

The command runs inside the project container with Postgres, Redis, and any
other declared resources started, and all shared secrets / environment
variables injected.

\b
Examples:
  nobs exec "alembic upgrade head"
  nobs exec "alembic revision --autogenerate -m 'add users'"
  nobs exec "python -m myapp.scripts.seed_db"
  nobs exec --ephemeral "python -c 'print(1)'"
""")
@click.argument("command", type=str)
@click.option("--context", "-c", default=None, help="Docker build context directory.")
@click.option("--dockerfile", "-f", default=None, help="Path to Dockerfile.")
@click.option("--env-file", default=None, help="Path to environment variables file.")
@click.option("--ephemeral", is_flag=True, default=False,
              help="Use temporary resource data (deleted after command finishes).")
@click.option("--read-only", is_flag=True, default=False,
              help="Mount source volumes as read-only (default is read-write).")
def exec_command(
    command: str,
    context: str | None = None,
    dockerfile: str | None = None,
    env_file: str | None = None,
    ephemeral: bool = False,
    read_only: bool = False,
) -> None:
    import sys
    import tempfile
    from takk.docker import compose

    current_dir = Path.cwd()
    project = read_project_at(None)

    project_container = prepare_project(project, context, dockerfile)
    volumes = dev_volumes(project, current_dir, project_container.source_dir)

    if not read_only:
        for vol in volumes.values():
            vol["mode"] = "rw"

    volume_names = [Path(path).name for path in volumes.keys()]
    volumes_text = Text()
    volumes_text.append("Mounted volumes: ", style="bold")
    volumes_text.append(", ".join(volume_names), style="cyan")
    console.print(volumes_text)

    runner_name = "exec-runner"
    primary = CompiledJob(
        name=runner_name,
        function_ref="",
        custom_command=command,
        description="",
        arguments={},
        secrets=secrets_for(project.shared_secrets or []),
    )

    if ephemeral:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code = compose(
                project,
                base_image=f"{project.name}:latest",
                volumes=volumes,
                env_file=env_file,
                data_dir=Path(temp_dir),
                primary_container=primary,
            )
    else:
        exit_code = compose(
            project,
            base_image=f"{project.name}:latest",
            volumes=volumes,
            env_file=env_file,
            primary_container=primary,
        )

    sys.exit(exit_code or 0)


async def push_image(project: Project, tag: str, local_image: str) -> None:
    from docker import DockerClient
    creds = await NobsClient().docker_creds()

    client = DockerClient.from_env()
    client.login(
        password=creds.password, 
        registry=creds.registry,
        username="nologin"
    )

    repo = f"{creds.registry}/{project.name}:{tag}"

    client.images.get(local_image).tag(
        repository=repo, tag=tag
    )
    client.images.push(repo, tag=tag)
    client.images.remove(repo)



@cli.command(help="Authenticate with the takk server via browser.")
@click.option("--api", default=None, help="Override the API server URL.")
@async_
async def login(api: str | None) -> None:
    import webbrowser
    from takk.models import default_nobs_file

    settings = NobsServer(nobs_token=SecretStr("auth"))
    if api:
        settings.nobs_api = api

    request_id = uuid4()
    non_api = settings.nobs_api.removesuffix("/api/v1")    
    url = f"{non_api}/users/cli-login/{request_id}"
    webbrowser.open(url)

    client = NobsClient(settings)
    token = await client.auth_cli(request_id)
    settings.nobs_token = SecretStr(secret_value=token)

    output = json.dumps({
        key: value.get_secret_value() if isinstance(value, SecretStr) else value
        for key, value in settings.model_dump().items()
    })
    default_nobs_file.write_text(output)

    click.echo(f"Created token with info {output}")


@cli.command(help="""Run tests in isolated Docker containers.

\b
Examples:
  takk test                              Run pytest
  takk test --command "npm test"         Run npm tests
  takk test api db                       Start api and db for tests
""")
@click.argument("components", nargs=-1, metavar="[COMPONENTS]...")
@click.option("--env", default="dev", help="Target environment (default: dev).")
@click.option("--context", "-c", default=None, help="Docker build context directory.")
@click.option("--dockerfile", "-f", default=None, help="Path to Dockerfile.")
@click.option("--env-file", default=None, help="Path to environment variables file.")
@click.option("--command", "-cmd", default="python -m pytest",
              help="Test command to run (default: python -m pytest).")
@async_
async def test(
    components: list[str],
    env: str,
    command: str,
    ref: str | None = None,
    context: str | None = None,
    env_file: str | None = None,
    dockerfile: str | None = None
) -> None:
    import sys
    import tempfile
    from takk.docker import compose

    current_dir = Path.cwd()
    project = read_project_at(ref)

    project_container = prepare_project(project, context, dockerfile)
    volumes = dev_volumes(project, current_dir, project_container.source_dir, with_tests=True)

    if env in ["prod", "test"]:
        console.print(Panel(
            f"Loading resources to connect to '[bold yellow]{env}[/bold yellow]'\n"
            "However, this is not supported yet but will be!",
            title="Environment Setup",
            border_style="yellow",
            title_align="left"
        ))
    else:
        console.print(Panel(
            "Setting up local '[bold green]dev[/bold green]' resources",
            title="Environment Setup",
            border_style="green",
            title_align="left"
        ))

    volume_names = [Path(path).name for path in volumes.keys()]
    volumes_text = Text()
    volumes_text.append("Mounted volumes: ", style="bold")
    volumes_text.append(", ".join(volume_names), style="cyan")
    console.print(volumes_text)

    test_runner_name = "test-runner"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_data_dir = Path(temp_dir)

        exit_code = compose(
            project,
            base_image=f"{project.name}:latest",
            volumes=volumes,
            env_file=env_file,
            components=components if components else None,
            data_dir=temp_data_dir,
            primary_container=CompiledJob(
                name=test_runner_name,
                function_ref="",
                custom_command=command,
                description="",
                arguments={},
                secrets=secrets_for(project.shared_secrets or [])
            ),
            env="test"
        )

    sys.exit(exit_code or 0)


if __name__ == "__main__":
    cli()
