# 🧱 infra-lib
> A lightweight framework for managing **Infrastructure as Code (IaC)** templates with a unified CLI.

_**infra-lib** helps you **bootstrap new projects** or **add infrastructure** to existing ones — with **AWS-ready templates** that can also **run locally via Docker Compose**_

Built for reproducibility, extensibility, and developer productivity.

---

## ✨ Features

* 📦 **Project Bootstrapping**: `infra-cli init` scaffolds new projects with environment-aware templates (for example `aws/net8_lambda`).
* ⚙️ **Operation Runner**: `infra-cli run` executes infrastructure tasks for specific environments (`local`, `stage`, `prod`).
* 🔗 **Dependency Management**: Automatically runs operations in the correct order based on `depends_on` declarations (DAG execution).
* 🔌 **Extensible Operations**: Define custom operations with a simple `@infra_operation` decorator.
* ☁️ **Cloud Providers**: Includes built-in utilities for AWS (S3, Lambda, SQS, etc.) via `AWSInfraProvider`.
* 🐳 **Local Development**: Helpers for Docker Compose (`DockerCompose` class) to integrate with local setups.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/y3rbiadit0/infra-lib.git
cd infra-lib
```

### 2. Install Dependencies

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Or via pip in editable mode:

```bash
pip install -e .
```

---
## 🚀 Getting Started

Here's the fastest way to get up and running:

### 1. 🏗️ Initialize Your Project

First, use the `init` command to create a new project from a template. This sets up your directory structure and all the boilerplate.

```bash
# Example: Create a .NET 8 AWS Lambda project
infra-cli init --template aws/net8_lambda
```

### 2. ▶️ Run Your Infrastructure
Next, use the run command to execute your infra tasks. You just need to tell it which environment to run (`-e`) and where your infra folder is (--project-root).
```bash
# See all operations for the 'local' environment
infra-cli run -e local --project-root ./infra

# Run the 'deploy-api' operation for the 'stage' environment
infra-cli run -e stage --project-root ./infra -op deploy-api
```
---

### 1. 🏗️ Initialize a New Template

Create a new stack from a predefined template:

```bash
infra-cli init --template aws/net8_lambda
```

**Example:**
> Creates a new AWS Lambda project using .NET 8.  
> The project includes IaC templates, Jinja2 configurations, and environment folders.

Available templates:

- `aws/generic`
- `aws/net8`
- `aws/net8_lambda`
- `aws/python-lambda`

---

### 2. ▶️ Run Operations

This command discovers and executes your defined infrastructure operations.


#### 2.1 List Available Operations 
```bash
infra-cli run -e local --project-root ./my-project/infra

# Example output
No specific operation selected. Available operations:
   - setup-localstack
   - deploy-s3-buckets
   - deploy-lambdas
   - run-migrations
```

#### 2.2 Run a Specific Operation

```bash
infra-cli run -e stage --project-root ./my-project/infra -op deploy-api
```

What this does:

- Loads the `EnvironmentContext` from `my-project/infra/environments/stage/stage.py`.
- Discovers all `@infra_operation` functions in `my-project/infra/operations/`.
- Finds the `deploy-api` operation.
- Checks its depends_on list (e.g., ["deploy-s3-buckets"]).
- Runs `deploy-s3-buckets` first, then `deploy-api`.

#### 2.3 Run Multiple Operations
You can specify -op multiple times. Each operation and its dependency tree will be executed.
```bash
infra-cli run -e prod --project-root ./my-project/infra -op deploy-api -op run-migrations
```
---

### 3. 📁 Project Root Rules

`infra-cli run` expects an `infra/` project root. By default it uses `./infra`, so these are equivalent:

```bash
infra-cli run -e local
infra-cli run -e local --project-root ./infra
```

The `run` command imports user code from these locations:

```text
infra/environments/<env>/<env>.py
infra/operations/**/*.py
```

---

## 🧩 Example Project Structure

When you initialize a new project via `infra-cli init`, the structure should look like this. The run command automatically discovers files in `environments` and `operations`.

```
my_project/
└── infra/
   ├── environments/
   │   ├── local/
   │   │   ├── .env           # Vars for local
   │   │   └── local.py       # Defines LocalContext(EnvironmentContext)
   │   ├── stage/
   │   │   ├── .env
   │   │   └── stage.py       # Defines StageContext(EnvironmentContext)
   │   └── prod/
   │      ├── .env
   │      └── prod.py
   │
   └── operations/
      ├── __init__.py
      ├── aws_infra.py   # Defines operations (e.g., deploy-s3)
      └── db_ops.py      # Defines operations (e.g., run-migrations)
```

---

## 🧠 Core Concepts

The library is built on three main components:

1. [**`EnvironmentContext`**](src/infra_lib/infra/env_context/env_context.py)
This is a class you define for each environment. It's responsible for loading configuration (like `.env` files) and making it available to your `operations`.

- It must inherit from `EnvironmentContext` (or a provider-specific one like `AWSEnvironmentContext`).
- The file must be named `<env>.py` (e.g., `local.py`).
- The `run` command finds this class, instantiates it, and injects it into any operation that needs it.

Example: `infra/environments/local/local.py`
```python
from infra_lib.infra import InfraEnvironment
from infra_lib.infra.env_context.aws_env_context import AWSEnvironmentContext

# The class name doesn't matter, but the file name does.
class LocalContext(AWSEnvironmentContext):
    """My project's local environment configuration."""
    
    def env(self) -> InfraEnvironment:
        # This tells the library which environment this context is for.
        return InfraEnvironment.local
    
    # You can add custom methods
    def get_my_service_url(self) -> str:
        return self.get("MY_SERVICE_URL", "http://localhost:8080")
```

2. [**`@infra_operation`**](src/infra_lib/cli/runner_cli/infra_op_decorator/decorator.py) Decorator
This is how you define a runnable task. You create functions (or class methods) inside any `.py` file in the `infra/operations/` directory.

- `name`: (Optional) The name to use in the CLI. If not provided, it's derived from the function name (e.g., deploy_api -> deploy-api)
- `description`: A helpful description.
- `depends_on`: A list of other operation names that must run first.
- `target_envs`: (Optional) A list of `InfraEnvironment` enums. The operation will only run if the target environment matches.

Example: `infra/operations/aws_ops.py`
```python
from infra_lib import AWSInfraProvider, infra_operation
from ..environments.local.local import LocalContext

@infra_operation(
    description="Deploys the main S3 buckets",
    depends_on=["setup-iam-roles"] # Ensures 'setup-iam-roles' runs first
)
def deploy_s3_buckets(context: LocalContext):
    # 'context' is automatically injected by the runner
    print(f"Deploying S3 buckets for {context.env()}")
    
    # Use built-in providers
    aws = AWSInfraProvider(context)
    aws.s3_util.create_bucket(...)
    print(f"Service URL: {context.get_my_service_url()}")

@infra_operation(description="Sets up base IAM roles")
def setup_iam_roles(context: LocalContext):
    print("Setting up IAM...")
```

Method-based operations are also supported:

```python
from infra_lib import EnvironmentContext, infra_operation

class ApiOperations:

    def __init__(self):
        # A parameterless __init__ is required
        print("Initializing ApiOperations class...")

    @infra_operation(description="Deploys the main API")
    def deploy_api(self, context: EnvironmentContext):
        # Both 'self' and 'context' are injected
        print(f"Deploying API for {context.env()}")
```

3. [**`run`**](src/infra_lib/cli/runner_cli/run_cli.py) Command (DAG Runner)
    When you execute `infra-cli run -op deploy-s3-buckets -e local`:
    1. **Load Context**: The library finds `infra/environments/local/local.py`, finds the `LocalContext` class, and creates an instance.
    2. **Discover Ops**: It searches `infra/operations/` and finds all `@infra_operation` functions, building a registry.
    3. **Build Graph**: It finds the `deploy-s3-buckets` _`operation`_ and sees it _`depends_on`_ `setup-iam-roles`.
    4. **Execute**: It runs the operations in the correct order (a Directed Acyclic Graph, or DAG):
        - `setup-iam-roles(context=LocalContext_instance)`
        - `deploy-s3-buckets(context=LocalContext_instance)`
---

## 🧰 Built-in Utilities
Your operations can use helpers included with `infra_lib`:
- `AWSInfraProvider`: Provides pre-configured utility clients for S3, Lambda, SQS, EventBridge, Secrets Manager, etc.
- `DockerCompose`: A helper class to build, up, and down Docker Compose files, perfect for local operations.


## 📚 Example Project

👉 [.NET8 AWS Lambda Example](https://github.com/y3rbiadit0/IaC_example/blob/master/README.md)

---

## 📖 Extended Documentation

Read the full guide on **DeepWiki**:  
🔗 [https://deepwiki.com/y3rbiadit0/infra_lib](https://deepwiki.com/y3rbiadit0/infra_lib)

---

## 🧑‍💻 Contributing

1. Fork the repo  
2. Create a new branch (`feature/my-feature`)  
3. Commit your changes  
4. Open a pull request 🚀

---
