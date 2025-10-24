from collections.abc import Callable
import logging
from typing import Dict
import inspect

from ...infra.base_infra import BaseInfra


logger = logging.getLogger(__name__)

TASK_REGISTRY: Dict[str, Dict[str, Callable[[], None]]] = {}


def infra_task(func: Callable) -> Callable:
	"""
	A decorator to register a method as a runnable task for infra-cli.

	The task name is derived from the function name
	(e.g., `deploy_app` becomes `deploy-app`).
	"""

	task_name = func.__name__.replace("_", "-")

	qualname_parts = func.__qualname__.split(".")
	if len(qualname_parts) < 2:
		logger.error(f"Task '{func.__name__}' is not a method of a class. Cannot register.")
		return func

	class_name = qualname_parts[-2]

	if task_name not in TASK_REGISTRY:
		TASK_REGISTRY[task_name] = {}

	if class_name in TASK_REGISTRY[task_name]:
		existing_func = TASK_REGISTRY[task_name][class_name]
		logger.warning(
			f"Duplicate task name '{task_name}' for class '{class_name}': "
			f"{func.__qualname__} is overriding {existing_func.__qualname__}"
		)

	TASK_REGISTRY[task_name][class_name] = func
	return func


def get_tasks_from_class(infra_class_instance: BaseInfra) -> Dict[str, Callable]:
	"""
	Gets all tasks available for a given infra class instance,
	respecting inheritance.
	"""
	available_tasks = {}
	target_class = infra_class_instance.__class__

	try:
		mro = inspect.getmro(target_class)
	except TypeError:
		logger.error(f"Could not determine MRO for {target_class.__name__}")
		mro = [target_class]

	for t_name, class_map in TASK_REGISTRY.items():
		for cls in mro:
			cls_name = cls.__name__
			if cls_name in class_map:
				available_tasks[t_name] = class_map[cls_name]
				break

	return available_tasks
