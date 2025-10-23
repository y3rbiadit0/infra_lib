from collections.abc import Callable
import logging
from typing import Dict

logger = logging.getLogger(__name__)

TASK_REGISTRY: Dict[str, Callable[[], None]] = {}


def infra_task(func: Callable) -> Callable:
	"""
	A decorator to register a method as a runnable task for infra-cli.

	The task name is derived from the function name
	(e.g., `deploy_app` becomes `deploy-app`).
	"""

	task_name = func.__name__.replace("_", "-")

	if task_name in TASK_REGISTRY:
		existing_func = TASK_REGISTRY[task_name]
		logger.warning(
			f"Duplicate task name '{task_name}': "
			f"{func.__qualname__} is overriding {existing_func.__qualname__}"
		)

	TASK_REGISTRY[task_name] = func
	return func


def get_tasks_from_class(infra_class) -> Dict[str, Callable]:
	available_tasks = {}
	for t_name, t_func in TASK_REGISTRY.items():
		task_class_name = t_func.__qualname__.split(".")[0]
		if task_class_name == infra_class.__class__.__name__:
			available_tasks[t_name] = t_func
	return available_tasks
