# 🧱 infra-lib

> A lightweight framework for managing **Infrastructure as Code (IaC)** templates with a unified CLI.

_**infra-lib** helps you **bootstrap new projects** or **add infrastructure** to existing ones — with **AWS-ready templates** that can also **run locally via Docker Compose**_

Built for reproducibility, extensibility, and developer productivity.

---

## ✨ Features

- 📦 **Template Registry** — Reusable, Jinja2-based IaC boilerplates.
- ⚙️ **Environment-Aware Runner** — Run infrastructure for `local`, `stage`, or `prod` environments.
- 🧩 **Extensible Handlers** — Plug in new stacks, templates, and providers easily.
- 🖥️ **Developer-Friendly** — Local `.env`, Docker, and VSCode support out-of-the-box.

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

## 🧰 Usage

The main entrypoint is:

```bash
infra-cli [COMMAND] [OPTIONS]
```

### Commands

| Command | Description |
|----------|-------------|
| `init` | Initialize a new infrastructure stack from templates |
| `run` | Build and run local or staging infrastructure |
| `deploy` | Execute a specific infrastructure task (e.g., setup, teardown) |

---

### 1. 🏗️ Initialize a New Template

Create a new stack from a predefined template:

```bash
infra-cli init --stack net8_lambda --provider aws
```

**Example:**
> Creates a new AWS Lambda project using .NET 8.  
> The project includes IaC templates, Jinja2 configurations, and environment folders.

---

### 2. ▶️ Run Infrastructure

Build and run a local or staging environment:

```bash
infra-cli run --project MyProject -e local
```

**What this does:**
- Spins up Docker Compose services for the given project.
- Runs pre/post compose actions.
- Executes environment-specific _`setup`_ tasks (like seeding data or configuring mock services).

---

### 3. ⚙️ Deploy Specific Tasks

Execute a single infrastructure task defined in your environment class:

```bash
infra-cli deploy -t setup -e stage
```

If you omit `--task`, it lists all available tasks for that environment:

```bash
infra-cli deploy -e prod
```

---

## 🧩 Example Project Structure

When you initialize a new project via `infra-cli init`, it creates a structure like this:

```
infrastructure/
├── local/               # Local development environment
│   ├── .env
│   ├── Dockerfile.debug
│   └── infra_local.py   # Defines local infrastructure
│
├── stage/               # Staging environment
│   ├── .env
│   └── infra_stage.py
│
├── prod/                # Production environment
│   ├── .env
│   └── infra_prod.py
│
├── docker-compose.yml   # Top-level Docker Compose configuration
└── __init__.py
```

---

## 🧠 How It Works

`infra-lib` operates in two layers:

1. **Environment Layer (`BaseInfra`)**  
   - Defines environment-specific logic for `local`, `stage`, or `prod`.
   - Uses a `ComposeSettings` class to configure Docker profiles and actions.

2. **Task Layer (`@infra_task`)**  
   - Registers methods as runnable CLI tasks.
   - Task names are derived automatically (`deploy_app` → `deploy-app`).

**Example:**

```python
from infra_lib.core.task import infra_task
from infra_lib.enums import InfraEnvironment
from infra_lib.infra.base_infra import BaseInfra

class LocalInfra(BaseInfra):
    @infra_task
    def setup(cls):
        print("Setting up local infrastructure...")

    @infra_task
    def teardown(cls):
        print("Cleaning up...")
```

Running:
```bash
infra-cli deploy -t setup -e local
```

Will automatically find and execute `LocalInfra.setup`.

---

## 🧱 Core Concepts

### 🔹 `infra_task` Decorator

Registers a method as a runnable CLI task.

```python
@infra_task
def setup(cls):
    ...
```

Tasks are auto-discovered via the `TASK_REGISTRY`.

### 🔹 Environment Builders

`EnvBuilder` automates:
- Running Docker Compose (build, up, down)
- Executing pre/post actions
- Running `setup` tasks for local environments

---

## 🧭 Command Flow

```
infra-cli run
 ├──> EnvBuilder.execute()
      ├──> pre_compose_actions
      ├──> docker compose up
      ├──> post_compose_actions
      └──> local setup task
```

```
infra-cli deploy
 ├──> Load BaseInfra (by environment)
 ├──> Discover registered @infra_task
 └──> Execute requested task
```

---

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