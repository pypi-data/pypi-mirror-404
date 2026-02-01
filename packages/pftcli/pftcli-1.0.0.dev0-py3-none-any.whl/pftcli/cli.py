"""
cli.py

CLI principal do pftcli.
"""

import click

from pftcli.logging import setup_logging
from pftcli.context import AppContext
from pftcli.plugin_loader import load_plugins

setup_logging()


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(package_name="pftcli")
@click.pass_context
def cli(ctx: click.Context):
    """
    pftcli

    CLI extensível baseada na Profit DLL.
    """
    if ctx.obj is None:
        app_ctx = AppContext()
        app_ctx.start()
        ctx.obj = app_ctx


# plugins carregados no topo
load_plugins(cli)


@cli.command()
@click.pass_obj
def status(app_ctx: AppContext):
    """Mostra status da conexão com a corretora."""
    if app_ctx.is_connected():
        click.echo("conectado a corretora")
    else:
        click.echo("nao conectado a corretora")


@cli.command()
@click.pass_obj
def stop(app_ctx: AppContext):
    """Finaliza a DLL."""
    app_ctx.stop()
    click.echo("Profit DLL finalizada.")


def main():
    cli()


if __name__ == "__main__":
    main()
