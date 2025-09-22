# `infra-lib`

`infra-lib` is a framework for managing Infrastructure as Code (IaC) templates with a unified CLI.

_The idea is to help bootstrap new projects or add infrastructure to existing local projects, using AWS-based templates that can also run locally (via Docker, docker-compose, etc.)._

It provides:

1. `init` - A template creator to define new infrastructure stacks.

2. `run` - A runner that provisions and manages these stacks across environments (`local`, `stage`, `prod`).

Extensible support for multiple cloud providers (currently AWS).

### 🚀 **Features**

1. 📦 Template registry with reusable IaC boilerplates (Jinja2-based).

2. 🔧 Stack initialization (init) with stack type + provider.

3. ▶️ Runner (run) to build and execute infrastructure in different environments.

4. 🧩 Extensible handlers → add new stacks, templates, and providers.

5. 🖥️ Local developer support with auto-generated configs (e.g., VSCode, Docker).

## Installation
1. **Clone the repo**
```powershell
git clone https://github.com/your-org/infra-lib.git
cd infra-lib
```

2. **Install dependencies (via uv)**
```powershell
uv sync
```

3. **Or install locally in editable mode**
pip install -e .

## 🛠 Usage
**CLI Overview**
- The main entrypoint is: `infra-cli [COMMAND] [OPTIONS]`

### 1. Initialize a New Template

Create a new infrastructure stack from predefined templates:

```powershell
infra-cli init --stack net8_lambda --provider aws
# This will create a template assuming .NET8 and AWS as Cloud provider, for Lambda Functions project oriented.
# This generates a new project structure with Jinja2 templates, configs, and infra classes.
```

### 2. Run Infrastructure
Build and run a project for a specific environment:

```powershell
infra-cli run --project MyProject --environment local
# This will run a docker-compose.yml with what is specified as infrastructure in local/infra_local.py
```



## How it works?

The idea behind this tool is to have a project initializer that has `infra-lib` support with a set of files.
Whenever we do an `init` we create something like:
```powershell
infrastructure/
├── aws_config/          # Shared AWS (Localstack) configuration (API Gateway, Secrets, etc.)
│   ├── apigateway.json
│   └── secrets.json
│
├── local/               # Local development environment
│   ├── .env
│   ├── Dockerfile.debug
│   └── infra_local.py   # Describe Infrastructure as Code for `Local` Environment
│
├── stage/               # Staging environment
│   ├── .env
│   └── infra_stage.py   # Describe Infrastructure as Code for `Stage` Environment
│
├── prod/                # Production environment
│   ├── .env
│   └── infra_prod.py    # Describe Infrastructure as Code for `Prod` Environment   
│
├── volume/              # Reserved for persistent storage, logs, or mounted volumes
│
├── docker-compose.yml   # Top-level Docker services definition
└── __init__.py
```

- `docker-compose.yml` → Defines containerized services used across environments.

- `Environment folders (local/, stage/, prod/)` → Contain `.env` variables and `infra_*.py` files that describe the infrastructure for that environment.

- `aws_config/` → Stores reusable AWS JSON configuration (e.g., API Gateway routes, Secrets Manager).

