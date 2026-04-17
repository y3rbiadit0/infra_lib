import importlib.util
import inspect
import logging
from pathlib import Path
import sys
from types import ModuleType
from typing import Dict

from .infra_op_decorator import INFRA_OP_ATTR, OP_REGISTRY, InfraOp
from ...infra.env_context import EnvironmentContext
from .exceptions import ConfigError
from ...infra import InfraEnvironment

logger = logging.getLogger(__name__)


def _import_module_from_path(module_name: str, file_path: Path) -> ModuleType:
	"""Dynamically imports a Python module from a given file path."""
	try:
		spec = importlib.util.spec_from_file_location(module_name, file_path)

		if spec is None:
			raise ImportError(f"Could not find module spec at {file_path}")
		if spec.loader is None:
			raise ImportError(f"No loader available for module at {file_path}")

		module = importlib.util.module_from_spec(spec)
		sys.modules[module_name] = module
		spec.loader.exec_module(module)

		return module

	except Exception as e:
		raise ConfigError(f"Failed to import module {module_name} from {file_path}: {e}")


def load_env_context_from_arg(env: InfraEnvironment, project_root: Path) -> EnvironmentContext:
	"""
	Loads the environment-specific Context by finding and instantiating
	the EnvironmentContext subclass defined in 'env.py'.
	"""
	environment_dir = Path.joinpath(project_root, "environments", env.value)
	environment_py_path = Path.joinpath(environment_dir, f"{env.value}.py")
	logger.info(f"Loading environment '{env.value}'")

	if not environment_py_path.exists():
		raise ConfigError(f"Config file not found: {environment_py_path}")

	module = _import_module_from_path(f"infra.environments.{env.value}", environment_py_path)

	env_context_class = None
	for name, obj in module.__dict__.items():
		if (
			isinstance(obj, type)
			and issubclass(obj, EnvironmentContext)
			and obj is not EnvironmentContext
			and not inspect.isabstract(obj)
		):
			env_context_class = obj
			break

	if env_context_class is None:
		raise ConfigError(
			f"{environment_py_path} must define a class that inherits from EnvironmentContext"
		)

	try:
		env_context_instance = env_context_class(
			project_root=project_root, environment_dir=environment_dir
		)
		env_context_instance.load()
	except Exception as e:
		raise ConfigError(
			f"Error instantiating {env_context_class.__name__} from {environment_py_path}: {e}"
		)

	return env_context_instance


def discover_ops(ops_dir: Path) -> Dict[str, InfraOp]:
	OP_REGISTRY.clear()
	registry: Dict[str, InfraOp] = {}
	imported_modules: list[ModuleType] = []
	errors: list[str] = []

	if not ops_dir.is_dir():
		logger.warning(f"Operations directory not found: {ops_dir}")
		return registry

	for file_path in ops_dir.glob("**/*.py"):
		if file_path.name.startswith("_"):
			continue

		relative_path = file_path.relative_to(ops_dir)
		module_path = ".".join(relative_path.with_suffix("").parts)
		module_name = f"infra.operations.{module_path}"

		try:
			module = _import_module_from_path(module_name, file_path)
			imported_modules.append(module)
		except Exception as e:
			logger.error(f"Failed to load operation file '{file_path}': {e}")
			errors.append(str(file_path))

	for module in imported_modules:
		for op in _collect_ops_from_module(module).values():
			if op.name in registry:
				raise ConfigError(f"Duplicate operation name detected: {op.name}")
			registry[op.name] = op

	if errors and not registry:
		return registry

	return registry


def _collect_ops_from_module(module: ModuleType) -> Dict[str, InfraOp]:
	registry: Dict[str, InfraOp] = {}

	for _, obj in inspect.getmembers(module, inspect.isfunction):
		op = getattr(obj, INFRA_OP_ATTR, None)
		if op is not None:
			registry[op.name] = op

	for _, cls in inspect.getmembers(module, inspect.isclass):
		if cls.__module__ != module.__name__:
			continue

		for _, method in inspect.getmembers(cls, inspect.isfunction):
			op = getattr(method, INFRA_OP_ATTR, None)
			if op is not None:
				registry[op.name] = op

	return registry
