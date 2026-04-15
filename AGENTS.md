# AGENTS.md

## Setup
- Use `uv` for local setup and execution. CI and `buildspec.yml` both use `uv sync` followed by `uv run pytest`.
- Install deps with `uv sync`.

## Verification
- Format check: `uv run ruff format --check .`
- Lint: `uv run ruff check .`
- Dead code analysis: `uv run vulture src`
- Full test suite: `uv run pytest`
- Focused test: `uv run pytest tests/test_cli/test_runner_cli/test_run_cli.py -k <pattern>`
- Formatting uses Ruff: `uv run ruff format .`

## Repo Shape
- This is a single Python package under `src/infra_lib`.
- CLI entrypoint is `infra-cli`, defined by `infra_lib.cli:infra_cli`.
- The actual CLI only exposes `init` and `run`. Do not rely on `README.md` examples mentioning `deploy`; that command is not registered in code.

## CLI Conventions
- `infra-cli init` creates or populates an `infra/` directory under the target project dir.
- Verified template names come from `src/infra_lib/cli/template_cli/templates_handler/template_registry.py`: `aws/generic`, `aws/net8`, `aws/net8_lambda`, `aws/python-lambda`.
- `infra-cli run` defaults `--project-root` to `<cwd>/infra`.
- `run` prepends `project_root.parent` to `sys.path`, and dynamically imports user code as `infra.environments.*` and `infra.operations.*`. Generated or test projects need that `infra/` layout to be importable.

## Runner Contracts
- Environment files must live at `infra/environments/<env>/<env>.py` and define one concrete `EnvironmentContext` subclass.
- Operations are discovered from every non-underscore Python file under `infra/operations/**`.
- `@infra_operation` names default to the function name with `_` converted to `-`.
- Operation names must be unique across the whole process; duplicates raise immediately from the global `OP_REGISTRY`.
- Method-based operations are supported, but the containing class must have a no-argument `__init__` because the runner auto-instantiates and caches one instance per class.

## Environment Gotchas
- `EnvironmentContext.load()` mutates global `os.environ` and also stores values on `self.env_vars`; it is not isolated to the instance.
- The loader always sets `TARGET_ENV` during `load()`. Tests and custom contexts can depend on that side effect.

## Style
- Ruff formatting is configured for `line-length = 100` and `indent-style = "tab"`. Preserve tabs in files that follow repo formatting.

## Test Notes
- Tests around the operation decorator and runner usually clear `infra_lib.cli.runner_cli.infra_op_decorator.decorator.OP_REGISTRY` before and after each case because registry state is global.
