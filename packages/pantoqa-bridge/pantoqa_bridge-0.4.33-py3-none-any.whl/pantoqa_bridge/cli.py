import json

import click

from pantoqa_bridge.config import IS_RUNNING_IN_BRIDGE_APP, PKG_NAME, SERVER_HOST, SERVER_PORT
from pantoqa_bridge.logger import logger
from pantoqa_bridge.server import start_bridge_server
from pantoqa_bridge.tasks.executor import AppiumExecutable, MaestroExecutable, QAExecutable
from pantoqa_bridge.utils.deps import deps
from pantoqa_bridge.utils.misc import make_sync
from pantoqa_bridge.utils.pkg import get_pkg_version
from pantoqa_bridge.utils.process import send_outdated_signal_to_bridge_app


@click.group(help="PantoAI QA Extension CLI", invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.option(
  "--skip-autoupgrade",
  is_flag=True,
  default=False,
  help="Skip pre-check of required tools",
)
@click.pass_context
def cli(ctx: click.Context, version: bool, skip_autoupgrade: bool) -> None:
  if version:
    click.echo(f"PantoQA Bridge version: {get_pkg_version(PKG_NAME)}")
    ctx.exit(0)

  deps.init()

  if not skip_autoupgrade:
    if IS_RUNNING_IN_BRIDGE_APP:
      is_outdated, _, _ = deps.is_outdated()
      if is_outdated:
        click.echo("Auto-upgrade requested. Sending signal to Bridge App...")
        send_outdated_signal_to_bridge_app()
    else:
      deps.auto_upgrade(exit_after_upgrade=True)

  if ctx.invoked_subcommand is None:
    ctx.invoke(serve)


@cli.command()
@click.option("--host", default=SERVER_HOST, show_default=True, help="Bind address")
@click.option("--port", default=SERVER_PORT, show_default=True, type=int, help="Port to listen on")
def serve(host: str, port: int) -> None:
  start_bridge_server(host, port)


@cli.command()
@click.option("--framework",
              type=click.Choice(["appium", "maestro"], case_sensitive=False),
              required=True,
              help="QA framework to use")
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--maestro-bin", help="Path to Maestro binary (for maestro framework)")
@click.option("--appium-url", help="Appium server URL (for appium framework)")
@click.option("--device", help="Device serial number to run tests on")
@click.option(
  "--env-vars",
  type=click.Path(exists=True),
  help="Path to JSON file containing environment variables",
)
@make_sync
async def execute(
  framework: str,
  files: list[str],
  maestro_bin: str | None = None,
  appium_url: str | None = None,
  device: str | None = None,
  env_vars: str | None = None,
) -> None:
  parsed_env_vars: dict[str, str | None] | None = None
  if env_vars:
    try:
      with open(env_vars) as f:
        parsed_env_vars = json.load(f)
    except json.JSONDecodeError as e:
      raise click.ClickException(f"Invalid JSON in env-vars file: {e}")

  executable: QAExecutable | None = None
  if framework.lower() == "maestro":
    executable = MaestroExecutable(
      files=files,
      maestro_bin=maestro_bin,
      device_serial=device,
      env_vars=parsed_env_vars,
    )
  elif framework.lower() == "appium":
    executable = AppiumExecutable(
      files=files,
      appium_url=appium_url,
      device_serial=device,
      env_vars=parsed_env_vars,
    )
  else:
    raise click.ClickException(f"Unsupported framework: {framework}")

  logger.info("Starting Testing...")
  await executable.execute()
  click.echo("Execution completed.")


if __name__ == "__main__":
  cli()
