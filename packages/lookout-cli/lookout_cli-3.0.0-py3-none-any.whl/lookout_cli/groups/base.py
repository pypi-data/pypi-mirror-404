import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, cast

import click
from greenstream_config.types import Camera, CameraSensor, CameraSensorType
from lookout_cli.auth_helpers import configure_auth_prompt
from lookout_cli.helpers import (
    call,
    docker_bake,
    docker_compose_path,
    docker_manifest,
    generate_sboms,
    get_installer,
    get_project_root,
    get_version,
    make_dir_set_permission,
)
from lookout_config import get_config_io
from lookout_config.types import (
    Discovery,
    DiscoverySimple,
    GeolocationMode,
    LogLevel,
    LookoutConfig,
    Mode,
)
from python_on_whales.components.compose.models import ComposeConfig
from python_on_whales.docker_client import DockerClient
from python_on_whales.exceptions import NoSuchImage
from python_on_whales.utils import ValidPath

# Reusable option decorator for config_dir
config_dir_option = click.option(
    "-c",
    "--config-dir",
    type=str,
    default="~/.config/greenroom",
    show_default=True,
    help="The directory where the lookout config is stored.",
)

DOCKER = docker_compose_path("./docker-compose.yaml")
DOCKER_DEV = docker_compose_path("./docker-compose.dev.yaml")
DOCKER_PROD = docker_compose_path("./docker-compose.prod.yaml")
DOCKER_CACHE = docker_compose_path("./docker-compose.cache.yaml")
DOCKER_NETWORK_HOST = docker_compose_path("./docker-compose.network-host.yaml")
DOCKER_NETWORK_PROXY = docker_compose_path("./docker-compose.network-proxy.yaml")
DOCKER_JETSON = docker_compose_path("./docker-compose.jetson.yaml")

SERVICES = [
    "lookout_core",
    "lookout_ui",
    "lookout_greenstream",
    "lookout_docs",
    "lookout_proxy",
]

PYTHON_PACKAGES = ["lookout-config", "lookout-cli"]


DEBIAN_DEPENDENCIES = [
    "docker-ce",
    "docker-ce-cli",
    "containerd.io",
    "docker-buildx-plugin",
    "docker-compose-plugin",
    "python3",
    "python3-pip",
]


def _get_compose_files(
    prod: bool = False, cache: bool = False, proxy: bool = False
) -> List[ValidPath]:
    compose_files: List[ValidPath] = [DOCKER]

    if prod:
        compose_files.append(DOCKER_PROD)

    if not prod:
        compose_files.append(DOCKER_DEV)

    if is_arm():
        compose_files.append(DOCKER_JETSON)

    if proxy:
        compose_files.append(DOCKER_NETWORK_PROXY)
    else:
        compose_files.append(DOCKER_NETWORK_HOST)

    if cache:
        compose_files.append(DOCKER_CACHE)

    return compose_files


def _get_docker_client(
    prod: bool = False, cache: bool = False, proxy: bool = False
) -> DockerClient:
    """Get a configured DockerClient with appropriate compose files and profiles"""
    compose_files = _get_compose_files(prod=prod, cache=cache, proxy=proxy)

    if proxy:
        return DockerClient(
            compose_files=compose_files,
            compose_project_directory=get_project_root(),
            compose_profiles=["proxy"],
        )
    else:
        return DockerClient(
            compose_files=compose_files,
            compose_project_directory=get_project_root(),
        )


def is_arm():
    machine = platform.machine().lower()
    return machine in ["arm", "arm64", "aarch64", "armv6l", "armv7l", "armv8l"]


def log_config(config: LookoutConfig):
    click.echo(click.style("[+] Lookout Config:", fg="green"))
    config_io = get_config_io()
    click.echo(click.style(f" ⠿ Path: {config_io.get_path()}", fg="white"))
    for attr, value in config.__dict__.items():
        click.echo(
            click.style(f" ⠿ {attr}: ".ljust(27), fg="white") + click.style(str(value), fg="green")
        )


def get_discovery_range(discovery: Discovery) -> str:
    if isinstance(discovery, DiscoverySimple):
        if discovery.discovery_range == "localhost":
            return "LOCALHOST"
        elif discovery.discovery_range == "subnet":
            return "SUBNET"
    return "SYSTEM_DEFAULT"


def set_initial_env(config_dir: str):
    version = get_version()
    os.environ["LOOKOUT_CONFIG_DIR"] = config_dir
    os.environ["LOOKOUT_VERSION"] = version

    if config_dir.startswith("/"):
        click.echo(
            click.style(
                "Warning: Using an absolute path requires the path to be accessible from the host and within the docker container.",
                fg="yellow",
            )
        )


def set_env_from_config(config: LookoutConfig):
    os.environ["LOOKOUT_NAMESPACE_VESSEL"] = config.namespace_vessel
    os.environ["LOOKOUT_CONFIG"] = config.model_dump_json()
    os.environ["LOOKOUT_PROXY_ENABLED"] = "true" if config.proxy.enabled else "false"
    os.environ["LOOKOUT_PROXY_HTTP_PORT"] = str(config.proxy.http_port)
    os.environ["LOOKOUT_PROXY_HTTPS_PORT"] = str(config.proxy.https_port)

    # Middleware settings
    os.environ["ROS_DOMAIN_ID"] = (
        str(config.discovery.ros_domain_id) if config.discovery.type in ["simple", "easy"] else "0"
    )
    os.environ["ROS_AUTOMATIC_DISCOVERY_RANGE"] = get_discovery_range(config.discovery)
    os.environ["RMW_IMPLEMENTATION"] = (
        "rmw_zenoh_cpp" if config.discovery.type == "zenoh" else "rmw_fastrtps_cpp"
    )
    if config.discovery.type == "zenoh":
        os.environ[
            "ZENOH_CONFIG_OVERRIDE"
        ] = f'connect/endpoints=["tcp/{config.discovery.discovery_server_ip}:7447"]'

    # Launch commands
    if config.prod:
        os.environ["LOOKOUT_CORE_COMMAND"] = "ros2 launch lookout_bringup configure.launch.py"
        os.environ[
            "LOOKOUT_GREENSTREAM_COMMAND"
        ] = "ros2 launch lookout_greenstream_bringup configure.launch.py"
    else:
        os.environ[
            "LOOKOUT_CORE_COMMAND"
        ] = "platform ros launch lookout_bringup configure.launch.py --build --watch"
        os.environ[
            "LOOKOUT_GREENSTREAM_COMMAND"
        ] = "platform ros launch lookout_greenstream_bringup configure.launch.py --build --watch"


@click.command(name="up")
@click.option(
    "--build",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we rebuild the docker containers? Default: False",
)
@click.option(
    "--pull",
    help="Should we do a docker pull",
    is_flag=True,
)
@config_dir_option
@click.argument(
    "services",
    required=False,
    nargs=-1,
    type=click.Choice(SERVICES),
)
def up(
    build: bool,
    pull: bool,
    config_dir: str,
    services: List[str],
):
    """Starts lookout"""
    set_initial_env(config_dir)

    config = get_config_io().read()
    log_config(config)

    if config.prod and build:
        raise click.UsageError("Cannot build in production mode. Run `lookout build` instead")

    # Make the log and recordings directories
    log_directory = Path(config.log_directory).expanduser()
    recording_directory = Path(config.recording_directory).expanduser()
    models_directory = Path(config.models_directory).expanduser()
    sockets_directory = Path("/tmp/greenroom/sockets")
    get_config_io().get_path().chmod(0o777)
    make_dir_set_permission(log_directory)
    make_dir_set_permission(recording_directory)
    make_dir_set_permission(models_directory)
    make_dir_set_permission(sockets_directory)
    set_env_from_config(config)
    os.environ["LOOKOUT_LOG_DIR"] = str(log_directory)
    os.environ["LOOKOUT_RECORDING_DIR"] = str(recording_directory)
    os.environ["LOOKOUT_MODEL_DIR"] = str(models_directory)

    services_list = list(services) if services else None

    docker = _get_docker_client(prod=config.prod, proxy=config.proxy.enabled)
    docker.compose.up(
        services_list, detach=True, build=build, pull="always" if pull else "missing"
    )

    ui_host = (
        f"https://localhost:{config.proxy.https_port} and http://localhost:{config.proxy.http_port}"
        if config.proxy.enabled
        else "http://localhost:4000"
    )
    click.echo(click.style(f"UI Started on {ui_host}", fg="green"))


@click.command(name="down")
@config_dir_option
@click.argument("args", nargs=-1)
def down(config_dir: str, args: List[str]):
    """Stops lookout"""
    set_initial_env(config_dir)

    config = get_config_io().read()

    docker = _get_docker_client(prod=config.prod, proxy=config.proxy.enabled)
    docker.compose.down()


@click.command(name="build")
@click.option(
    "--no-cache",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we rebuild without the docker cache?",
)
@click.option("--cache", is_flag=True, help="Enable GitHub Actions cache")
@config_dir_option
@click.argument(
    "services",
    required=False,
    nargs=-1,
    type=click.Choice(SERVICES),
)
@click.option("--pull", is_flag=True, help="Pull the latest images")
def build(
    no_cache: bool,
    config_dir: str,
    services: List[str],
    pull: bool = False,
    cache: bool = False,
):
    """Builds the Lookout docker containers"""
    set_initial_env(config_dir)
    config = get_config_io().read()
    os.environ["LOOKOUT_NAMESPACE_VESSEL"] = config.namespace_vessel

    docker = _get_docker_client(prod=False, cache=cache)
    services_list = list(services) if services else None

    docker.compose.build(
        services=services_list,
        cache=not no_cache,
        pull=pull,
    )


@click.command(name="bake")
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version to bake. Default: latest",
)
@click.option(
    "--push",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we push the images to the registry? Default: False",
)
@click.argument(
    "services",
    required=False,
    nargs=-1,
    type=click.Choice(SERVICES),
)
def bake(version: str, push: bool, services: List[str]):  # type: ignore
    """Bakes the docker containers"""
    compose_files = _get_compose_files()
    docker_bake(
        version=version,
        services=services,
        push=push,
        compose_files=compose_files,
    )


@click.command(name="lint")
def lint():
    """Lints all the things"""
    call("pre-commit run --all")


@click.command(name="generate")
@config_dir_option
@click.option(
    "--launch_parameters",
    type=bool,
    default=False,
    is_flag=True,
    help="Should we generate models for launch parameters",
)
def generate(config_dir: str, launch_parameters: bool):
    """Generates models, types and schemas"""
    set_initial_env(config_dir)
    config = get_config_io().read()

    os.environ["ROS_DOMAIN_ID"] = (
        str(config.discovery.ros_domain_id) if config.discovery.type in ["simple", "easy"] else "0"
    )
    docker = _get_docker_client()
    if launch_parameters:
        click.echo(click.style("Generating models from launch params...", fg="green"))
        nodes = []

        docker.compose.execute(
            "lookout_core",
            [
                "bash",
                "-l",
                "-c",
                'exec "$@"',
                "--",
                "python3",
                "-m",
                "parameter_persistence.generate_models",
                "-o",
                "/home/ros/lookout_core/src/lookout_config/lookout_config",
                *nodes,
            ],
        )

    click.echo(click.style("Generating schemas for Lookout Config", fg="green"))
    subprocess.run(
        ["python3", "-m", "lookout_config.generate_schemas"],
        check=True,
        text=True,
        capture_output=True,
    )

    click.echo(click.style("Generating ts types...", fg="green"))
    docker.compose.execute("lookout_core", ["npx", "-y", "ros-typescript-generator"])


@click.command(name="upgrade")
@click.option("--version", help="The version to upgrade to.")
def upgrade(version: str):
    """Upgrade Lookout CLI"""
    click.echo(f"Current version: {get_version()}")
    result = click.prompt(
        "Are you sure you want to upgrade?", default="y", type=click.Choice(["y", "n"])
    )
    if result == "n":
        return

    installer = get_installer("lookout-cli")
    if version:
        call(f"{installer} install --upgrade lookout-config=={version}")
        call(f"{installer} install --upgrade lookout-cli=={version}")
    else:
        call(f"{installer} install --upgrade lookout-config")
        call(f"{installer} install --upgrade lookout-cli")

    click.echo(click.style("Upgrade of Lookout CLI complete.", fg="green"))


@click.command(name="authenticate")
@click.option(
    "--username",
    help="The username to use for authentication.",
    required=True,
    prompt=True,
)
@click.option("--token", help="The token to use for authentication.", required=True, prompt=True)
def authenticate(username: str, token: str):
    """
    Authenticate with the package repository so that you can pull images.

    To get a username and token you'll need to contact a Greenroom Robotics employee.
    """
    call(f"echo {token} | docker login ghcr.io -u {username} --password-stdin")


@click.command(name="config")
@config_dir_option
def config(
    config_dir: str,
):
    """Read Config"""
    set_initial_env(config_dir)
    config = get_config_io().read()
    log_config(config)


@click.group(name="configure", invoke_without_command=True)
@click.pass_context
def configure(ctx):
    """Configure Lookout"""
    if ctx.invoked_subcommand is None:
        # Default to 'all' if no subcommand is provided
        ctx.invoke(configure_all)


@click.command(name="all")
@click.option("--default", is_flag=True, help="Use default values")
@click.option(
    "--include-defaults",
    type=bool,
    help="Include default values in the generated config file",
    is_flag=True,
)
@config_dir_option
def configure_all(default: bool, include_defaults: bool, config_dir: str):
    """Configure all Lookout settings"""
    set_initial_env(config_dir)

    if default:
        config = LookoutConfig()
        get_config_io().write(config)
    else:
        # Check if the file exists
        config_io = get_config_io()
        if os.path.exists(config_io.get_path()):
            click.echo(
                click.style(
                    f"Lookout config already exists: {config_io.get_path()}",
                    fg="yellow",
                )
            )
            result = click.prompt(
                "Do you want to overwrite it?", default="y", type=click.Choice(["y", "n"])
            )
            if result == "n":
                return

        try:
            config_current = get_config_io().read()
        except Exception as e:
            print(f"could not read config {e}")
            config_current = LookoutConfig()

        cameras: Optional[List[Camera]] = None
        if not config_current.cameras:
            gen_cameras = click.prompt(
                "No Cameras found, do you want to generate a template?",
                default="y",
                type=click.Choice(["y", "n"]),
            )
            if gen_cameras == "y":
                cameras = [
                    Camera(
                        name="bow",
                        sensors=[CameraSensor(name="bow_color", type=CameraSensorType.COLOR)],
                    )
                ]
        auth_credentials = configure_auth_prompt(config_current)

        config = LookoutConfig(
            namespace_vessel=click.prompt(
                "Namespace Vessel", default=config_current.namespace_vessel
            ),
            mode=click.prompt(
                "Mode",
                default=config_current.mode.value,
                type=click.Choice([item.value for item in Mode]),
            ),
            gama_vessel=click.prompt(
                "Is this running on a Gama Vessel?",
                default=config_current.gama_vessel,
                type=bool,
            ),
            log_level=click.prompt(
                "Log level",
                default=config_current.log_level.value,
                type=click.Choice([item.value for item in LogLevel]),
            ),
            cameras=cameras if cameras else config_current.cameras,
            geolocation_mode=GeolocationMode.NONE,
        )
        config.proxy.auth_credentials = auth_credentials
        get_config_io().write(config, include_defaults=include_defaults)


@click.command(name="auth")
@config_dir_option
def configure_auth(config_dir: str):
    """Configure authentication credentials only"""
    set_initial_env(config_dir)

    try:
        config_current = get_config_io().read()
    except Exception as e:
        click.echo(click.style(f"Error reading config: {e}", fg="red"))
        click.echo("Creating new config with default values...")
        config_current = LookoutConfig()

    # Configure auth using the existing helper
    auth_credentials = configure_auth_prompt(config_current)

    # Update only the auth section of the config
    config_current.proxy.auth_credentials = auth_credentials
    get_config_io().write(config_current)

    click.echo(click.style("Authentication configuration updated successfully!", fg="green"))


@click.command(name="download")
@click.option(
    "--include-deps",
    help="Should we include the deps",
    is_flag=True,
    default=False,
)
@config_dir_option
@click.argument(
    "output-directory",
    required=False,
    nargs=1,
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
def download(include_deps: bool, config_dir: str, output_directory: Optional[ValidPath]):
    """
    Saves off the Lookout+ docker images to a tar file and optionally downloads the depependencies.
    Note: This assumes you have a working Lookout+ installation with the images already downloaded.
    It also does not download nvidia drivers - you will need to install those separately if you want to use the GPU.
    """
    set_initial_env(config_dir)

    version = get_version()
    if version == "latest":
        raise click.ClickException(
            "You must install a pinned version of marops-cli to use this command."
        )

    config = get_config_io().read()
    docker_client = _get_docker_client(prod=config.prod, proxy=config.proxy.enabled)
    docker_config = cast(ComposeConfig, docker_client.compose.config())
    docker_services = docker_config.services or {}
    docker_images = [docker_services[service].image for service in docker_services.keys()]
    docker_images = [image for image in docker_images if image]

    if not output_directory:
        output_directory = os.getcwd()

    if include_deps:
        # Download the deps
        click.echo(click.style("Downloading dependencies", fg="green"))

        # Download debian's for the docker install
        os.makedirs(f"{output_directory}/debs", exist_ok=True)

        # Get all the dependencies save to a folder of debs
        # This gross thing parses the output from apt-rdepends so ALL the dependencies are downloaded
        debs = DEBIAN_DEPENDENCIES
        debs.append("nvidia-container-toolkit")

        rdepends_cmd = """
            apt-rdepends {0} | awk '/^[^ ]/ {{print $1}}' | sort -u | while read pkg; do
                if apt-cache policy "$pkg" | grep -q 'Candidate: [^ ]'; then
                    apt download "$pkg"
                else
                    echo "Skipping virtual package: $pkg"
                fi
            done
        """.format(
            " ".join(debs)
        )
        subprocess.call(rdepends_cmd, shell=True, cwd=f"{output_directory}/debs")
        click.echo(click.style(f"Debian's saved to {output_directory}/debs", fg="green"))

        # Download the python deps
        click.echo(click.style("Downloading python deps", fg="green"))

        python_folder = "python_packages"
        os.makedirs(f"{output_directory}/{python_folder}", exist_ok=True)
        python_packages = [f"{package}=={version}" for package in PYTHON_PACKAGES]
        subprocess.call(
            f"pip download --dest={output_directory}/{python_folder}/ "
            + " ".join(python_packages),
            shell=True,
        )
    else:
        click.echo(click.style("Skipping deps download", fg="yellow"))

    click.echo(click.style(f"Found images from docker compose: {docker_images}.", fg="green"))

    docker_download_dir = os.path.join(output_directory, "docker_images")
    # Create the directory if it doesn't exist
    os.makedirs(docker_download_dir, exist_ok=True)

    try:
        click.echo(
            click.style(
                f"Downloading images to {docker_download_dir}. This takes a while...", fg="green"
            )
        )
        docker_client.save(
            docker_images, output=os.path.join(docker_download_dir, "docker_images.tar")
        )
    except NoSuchImage as e:
        click.echo(click.style(f"Image not found: {e}", fg="white"))
        click.echo(
            click.style(
                "At least one image wasn't found locally. Run `lookout up` to download the images.",
                fg="red",
            )
        )
        return

    # Save the images to a tar file
    click.echo(click.style("Images saved to {output_directory}/docker_images.tar", fg="green"))


@click.command(name="manifest")
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version to create manifests for",
)
def manifest(version: str):  # type: ignore
    """Create and push multi-arch Docker manifests for lookout images"""
    # Lookout service images
    images = [
        "lookout_ui",
        "lookout_core",
        "lookout_greenstream",
        "lookout_docs",
        "lookout_proxy",
    ]

    docker_manifest(version=version, images=images, archs=["amd64", "arm64"])


@click.command(name="sbom")
@click.option(
    "--version",
    type=str,
    required=True,
    help="The version to generate SBOMs for",
)
def sbom(version: str):  # type: ignore
    """Generate SBOMs for lookout Docker images"""
    # Lookout service images
    images = [
        "lookout_ui",
        "lookout_core",
        "lookout_greenstream",
        "lookout_docs",
        "lookout_proxy",
    ]

    generate_sboms(version=version, images=images)
