import logging

import click

from .runner_cli import run_command
from .template_cli import template_command
from .__version__ import __version__


class ClickLogHandler(logging.Handler):
	def emit(self, record: logging.LogRecord):
		message = self.format(record)

		if record.levelno >= logging.ERROR:
			click.secho(message, fg="red", err=True)
		elif record.levelno >= logging.WARNING:
			click.secho(message, fg="yellow", err=True)
		else:
			click.echo(message)


def _configure_logging():
	root_logger = logging.getLogger()
	root_logger.handlers.clear()

	handler = ClickLogHandler()
	handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

	root_logger.addHandler(handler)
	root_logger.setLevel(logging.INFO)


@click.group()
@click.version_option(version=__version__, prog_name="infra-cli")
def infra_cli():
	"""Infra CLI for creating and managing infrastructure templates."""
	_configure_logging()


infra_cli.add_command(template_command)
infra_cli.add_command(run_command)

if __name__ == "__main__":
	infra_cli()
