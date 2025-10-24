from collections.abc import Callable
import os
import sys
import logging
import click
import importlib.util
from pathlib import Path

from ..base_env_builder import BaseEnvBuilder
from .task import TASK_REGISTRY, get_tasks_from_class
from ...enums import InfraEnvironment
from ...infra.base_infra import BaseInfra

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def _discover_tasks_for_completion(environment_name: str):
	project_root = Path(os.getcwd())
	module_path = project_root / "infrastructure" / "__init__.py"

	if module_path.is_file():
		try:
			spec = importlib.util.spec_from_file_location("user_infra_tasks", module_path)
			module = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(module)
		except Exception:
			pass


def complete_tasks(ctx, param, incomplete):
	environment = ctx.params.get("environment", InfraEnvironment.stage.value)
	_discover_tasks_for_completion(environment)

	env_class_name = f"{environment.capitalize()}Infra"
	matches = []

	for task_name, task_func in TASK_REGISTRY.items():
		if not task_name.startswith(incomplete):
			continue

		task_class_name = task_func.__qualname__.split(".")[0]
		if task_class_name == env_class_name:
			matches.append(task_name)

	return sorted(matches)


@click.command("deploy")
@click.option(
	"-t",
	"--task",
	"task_name",
	type=str,
	required=False,
	default=None,
	help="Name of the task to run. Lists tasks if omitted.",
	shell_complete=complete_tasks,
)
@click.option("--project", type=str, required=False, help="Target project name for deployment.")
@click.option(
	"-e",
	"--environment",
	type=click.Choice([e.value for e in InfraEnvironment]),
	default=InfraEnvironment.stage.value,
	help="Environment to run tasks against (local, stage, prod)",
)
def deploy_infra(task_name: str, project: str, environment: str):
	"""Executes a specific infrastructure task."""
	try:
		env_enum = InfraEnvironment(environment)
		project_root = Path.joinpath(Path(os.getcwd()).resolve(), "infrastructure")

		env_builder = BaseEnvBuilder(
			project_name=project, project_root=project_root, environment=env_enum
		)

		infra_instance = env_builder.infra_instance
		task_func = _get_deploy_task(task_name, environment, infra_instance)

		logger.info(f"🚀 Executing task '{task_name}' on '{environment}'...")
		task_func(infra_instance)
		logger.info(f"✅ Task '{task_name}' completed successfully!")

	except (FileNotFoundError, AttributeError) as e:
		logger.error(f"Setup error: {e}")
		sys.exit(1)
	except Exception as e:
		logger.error(f"An error occurred during task execution: {e}", exc_info=True)
		sys.exit(1)


def _get_deploy_task(
	task_name: str, environment: InfraEnvironment, infra_instance: BaseInfra
) -> Callable:
	"""
	Retrieves a specific task function based on name, or lists available
	tasks if no name is provided.

	Uses click for styled output and error handling.
	"""
	available_tasks = get_tasks_from_class(infra_instance)

	if not task_name:
		click.echo("Please specify a task.")
		click.echo("Available tasks for '", nl=False)
		click.secho(f"{environment}", fg="cyan", bold=True, nl=False)
		click.echo("':")

		if not available_tasks:
			click.secho("  (No @tasks found for this environment)", dim=True)
		else:
			for name in sorted(available_tasks.keys()):
				click.echo("  - ", nl=False)
				click.secho(f"{name}", fg="green")
		sys.exit(0)

	task_func = available_tasks.get(task_name)
	if task_func:
		return task_func

	click.secho("Error: ", fg="red", bold=True, nl=False, err=True)
	click.secho("Task '", nl=False, err=True)
	click.secho(f"{task_name}", fg="magenta", bold=True, nl=False, err=True)
	click.secho("' not found for environment '", nl=False, err=True)
	click.secho(f"{environment}", fg="cyan", bold=True, nl=False, err=True)
	click.secho("'.", err=True)

	if TASK_REGISTRY.get(task_name):
		click.secho("  (Note: ", fg="yellow", nl=False, err=True)
		click.secho("Task '", nl=False, err=True)
		click.secho(f"{task_name}", fg="magenta", bold=True, nl=False, err=True)
		click.secho("' exists, but for a different environment)", err=True)

	sys.exit(1)
