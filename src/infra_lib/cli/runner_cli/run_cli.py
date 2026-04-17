import logging
import sys
import os
import inspect
from pathlib import Path
from typing import Set, List, Dict, Any, Type
import click

from .infra_op_decorator import OP_REGISTRY, InfraOp
from .context_loader import load_env_context_from_arg, discover_ops
from ...infra import InfraEnvironment
from ...infra.env_context import EnvironmentContext
from .exceptions import ConfigError, OpError, CycleError

logger = logging.getLogger(__name__)


@click.command("run")
@click.option(
	"-e",
	"--environment",
	type=click.Choice([env.value for env in InfraEnvironment]),
	required=True,
	help="Environment to run against.",
)
@click.option(
	"-p",
	"--project-root",
	type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
	default=Path.joinpath(Path(os.getcwd()), "infra"),
	show_default=True,
	help="The root directory of the infrastructure project.",
)
@click.option(
	"-op",
	"--operation",
	"operations",
	multiple=True,
	help="Operation to run. Can be specified multiple times.",
)
def run_command(environment: str, project_root: Path, operations: tuple[str]):
	"""Run infrastructure operations for a specified environment."""
	env = InfraEnvironment(environment)

	# Allows imports from `infra.`
	if project_root.parent not in sys.path:
		sys.path.insert(0, str(project_root.parent))

	try:
		operations_dir = project_root / "operations"
		registry = discover_ops(operations_dir)
		if not registry:
			logger.warning("No operations found")
			return

		logger.info(f"Loading configuration for '{env}'")
		env_context = load_env_context_from_arg(env, project_root)
		logger.info(f"Loaded context for environment: {env_context.env()}")

		ops_to_run: List[str]
		instance_cache: Dict[Type, Any] = {}

		if not operations:
			ops_to_run = [op_name for op_name, op in registry.items() if env in op.target_envs]
			click.echo("Available operations:")
			for op_name in ops_to_run:
				click.echo(f"  - {op_name}")
			return
		else:
			logger.info(f"Running specified operations: {', '.join(operations)}")
			ops_to_run = list(operations)

		completed_actions = set()
		for op_name in ops_to_run:
			_execute_op_with_deps(
				op_name,
				env_context,
				completed_actions,
				visited=set(),
				registry=registry,
				instance_cache=instance_cache,
			)

		logger.info(f"Run completed successfully for environment '{environment}'")

	except (ConfigError, OpError, CycleError) as e:
		logger.error(f"Run failed: {e}")
		sys.exit(1)
	except Exception as e:
		logger.error(f"Unexpected error during run: {e}", exc_info=True)
		sys.exit(1)


def _execute_op_with_deps(
	op_name: str,
	context: EnvironmentContext,
	completed: Set[str],
	visited: Set[str],
	registry: Dict[str, InfraOp] | None = None,
	instance_cache: Dict[Type, Any] | None = None,
):
	"""
	Recursively executes an action and its dependencies (DAG runner).
	"""
	if op_name in completed:
		return

	if op_name in visited:
		raise CycleError(f"Circular dependency detected: {op_name}")
	visited.add(op_name)
	registry = registry if registry is not None else OP_REGISTRY
	instance_cache = instance_cache if instance_cache is not None else {}

	try:
		op: InfraOp = registry[op_name]
	except KeyError:
		raise OpError(f"Action '{op_name}' not found in registry.")

	for dep_name in op.depends_on:
		_execute_op_with_deps(
			dep_name,
			context,
			completed,
			visited,
			registry=registry,
			instance_cache=instance_cache,
		)

	args_to_pass = []
	handler = op.handler

	try:
		is_lambda_or_nested_fn = "<locals>" in handler.__qualname__
		is_method = (
			inspect.isfunction(handler)
			and not is_lambda_or_nested_fn
			and "." in handler.__qualname__
		)

		if is_method:
			module_name = handler.__module__
			if module_name not in sys.modules:
				raise OpError(f"Module {module_name} for op {op_name} not found.")

			module = sys.modules[module_name]
			qualname_parts = handler.__qualname__.split(".")

			if len(qualname_parts) < 2:
				raise OpError(f"Invalid qualname for op '{op_name}': {handler.__qualname__}")

			class_name = qualname_parts[-2]

			if not hasattr(module, class_name):
				raise OpError(f"Class {class_name} for op {op_name} not found in {module_name}.")

			ops_class = getattr(module, class_name)

			if not isinstance(ops_class, type):
				raise OpError(f"{ops_class} is not a class.")

			instance = _get_or_create_instance(ops_class, instance_cache)
			args_to_pass.append(instance)

		args_to_pass.append(context)

	except Exception as e:
		if not isinstance(e, OpError):
			raise OpError(f"Error preparing handler for op '{op_name}': {e}") from e
		raise e

	if "all" not in op.target_envs and context.env() not in op.target_envs:
		logger.info(f"Skipping action '{op.name}' for environment '{context.env()}'")
	else:
		logger.info(f"Running action '{op.name}'")
		try:
			op.handler(*args_to_pass)
			logger.info(f"Completed action '{op.name}'")
		except Exception as e:
			logger.error(f"Action '{op.name}' failed: {e}", exc_info=True)
			raise OpError(f"Failed during execution of '{op.name}'") from e

	completed.add(op_name)
	visited.remove(op_name)


def _get_or_create_instance(cls: Type, instance_cache: Dict[Type, Any]) -> Any:
	"""
	Gets a singleton instance of an operations class, creating it if needed.
	Assumes the class has a no-argument __init__ method.
	"""
	if cls not in instance_cache:
		try:
			instance_cache[cls] = cls()
		except Exception as e:
			raise OpError(
				f"Failed to auto-instantiate ops class {cls.__name__}. "
				"Classes containing infra operations must have a parameterless __init__."
			) from e
	return instance_cache[cls]


if __name__ == "__main__":
	run_command()
