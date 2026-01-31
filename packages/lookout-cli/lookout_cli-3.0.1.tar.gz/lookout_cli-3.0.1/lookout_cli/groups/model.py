import shutil
import tempfile
from pathlib import Path

import click
import mlflow
from lookout_cli.groups.base import config_dir_option, set_initial_env
from lookout_cli.helpers import make_dir_set_permission
from lookout_config import get_config_io
from mlflow.tracking import MlflowClient

MLFLOW_URL = "http://gr-nuc-visionai:4242"
MODEL_NAME = "rtdetrv2"


@click.group(help="ONNX model management commands")
def model():
    pass


@click.command(name="download")
@click.option(
    "--type",
    "model_type",
    type=click.Choice(["all", "rgb", "ir"]),
    default="all",
    show_default=True,
    help="Type of model to download.",
)
@click.option(
    "--alias",
    type=str,
    default="champion",
    show_default=True,
    help="Alias of model to download.",
)
@config_dir_option
def download(model_type: str, alias: str, config_dir: str):
    """Download ONNX models from MLflow."""
    set_initial_env(config_dir)

    config = get_config_io().read()
    models_directory = Path(config.models_directory).expanduser()
    make_dir_set_permission(models_directory)

    mlflow.set_tracking_uri(MLFLOW_URL)
    client = MlflowClient()

    types_to_download: list[str] = ["rgb", "ir"] if model_type == "all" else [model_type]

    for sensor_type in types_to_download:
        model_name = f"{MODEL_NAME}.{sensor_type}"

        try:
            model_version = client.get_model_version_by_alias(model_name, alias)
            run_id = model_version.run_id
            version = model_version.version
            output_filename = f"{model_name}.v{version}.{alias}.onnx"

            click.echo(click.style(f"Downloading {output_filename} to {models_directory}"))

            with tempfile.TemporaryDirectory() as temp_dir:
                local_path = client.download_artifacts(
                    run_id=run_id,
                    path="onnx_model_fixed/model.onnx",
                    dst_path=temp_dir,
                )

                output_path = models_directory / output_filename
                shutil.move(local_path, output_path)

            click.echo(click.style(f"Downloaded {output_filename}", fg="green"))

        except Exception as e:
            click.echo(click.style(f"Failed to download {model_name}: {e}", fg="red"))

    click.echo(click.style("Download complete.", fg="green"))


model.add_command(download)
