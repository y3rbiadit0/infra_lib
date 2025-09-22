# infra-lib

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
git clone https://github.com/your-org/infra-lib.git
cd infra-lib

2. **Install dependencies (via uv)**
uv sync

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


