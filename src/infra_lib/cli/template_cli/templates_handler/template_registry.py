from pathlib import Path

from .handlers import (
	AWSGenericTemplateHandler,
	AWSNet8TemplateHandler,
	AWSNet8LambdaTemplateHandler,
)

TEMPLATE_ROOT = Path(__file__).parent / "templates"

TEMPLATE_REGISTRY = {
	"aws": {
		"generic": (AWSGenericTemplateHandler, TEMPLATE_ROOT / "aws" / "generic"),
		"net8": (AWSNet8TemplateHandler, TEMPLATE_ROOT / "aws" / "net8"),
		"net8_lambda": (
			AWSNet8LambdaTemplateHandler,
			TEMPLATE_ROOT / "aws" / "net8_lambda",
		),
	},
	# "azure": { ... }  # future
}


def get_template_handler(provider: str, stack_type: str):
	provider = provider.lower()
	stack_type = stack_type.lower()
	if provider not in TEMPLATE_REGISTRY:
		raise ValueError(f"No templates registered for provider '{provider}'")
	if stack_type not in TEMPLATE_REGISTRY[provider]:
		raise ValueError(
			f"No templates registered for stack '{stack_type}' under provider '{provider}'"
		)
	handler_cls, template_dir = TEMPLATE_REGISTRY[provider][stack_type]
	return handler_cls, template_dir
