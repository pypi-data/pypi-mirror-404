import logging
from typing import Annotated

import typer
from typer import Context, Typer

from zephyr_shell import __version__

cli_app = Typer(name=f"Zephyr Shell Client [{__version__}]")

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


@cli_app.callback()
def main(
    ctx: Context,
    loglevel: Annotated[
        str,
        typer.Option(
            "--loglevel",
            "-l",
            help="Set the logging level (debug, info, warning, error, critical)",
        ),
    ] = "warning",
) -> None:
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("ditto_client").setLevel(LOG_LEVELS.get(loglevel, logging.WARNING))
