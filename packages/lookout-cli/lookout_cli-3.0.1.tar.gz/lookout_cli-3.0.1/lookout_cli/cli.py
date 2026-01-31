import lookout_cli.groups.base as base
import lookout_cli.groups.model as model
import lookout_cli.groups.setup as setup
from lookout_cli.helpers import is_dev_version, get_version
from lookout_cli.banner import get_banner
import click
import os
import sys


def cli():
    dev_mode = is_dev_version()
    version = get_version()
    mode = "Developer" if dev_mode else "User"
    banner = get_banner(mode, version)

    os.environ["LOOKOUT_CLI_DEV_MODE"] = "true" if dev_mode else "false"

    @click.group(help=banner)
    def lookout_cli():
        pass

    lookout_cli.add_command(base.authenticate)
    lookout_cli.add_command(base.upgrade)
    lookout_cli.add_command(base.down)
    lookout_cli.add_command(base.up)
    lookout_cli.add_command(base.configure)
    base.configure.add_command(base.configure_all)
    base.configure.add_command(base.configure_auth)
    lookout_cli.add_command(base.config)
    lookout_cli.add_command(base.download)

    if dev_mode:
        lookout_cli.add_command(base.build)
        lookout_cli.add_command(base.lint)
        lookout_cli.add_command(base.bake)
        lookout_cli.add_command(base.manifest)
        lookout_cli.add_command(base.sbom)
        lookout_cli.add_command(base.generate)
        lookout_cli.add_command(model.model)
        lookout_cli.add_command(setup.setup)
        setup.setup.add_command(setup.secrets)
    try:
        lookout_cli()
    except Exception as e:
        click.secho("\nCLI ERROR", fg="white", bg="red")
        click.secho(e, fg="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
