from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import List, Dict, Optional
import json5


@dataclass
class VSCodeLaunchConfig:
    """Represents a VS Code debug configuration."""

    name: Optional[str] = None
    type: Optional[str] = None
    request: Optional[str] = None
    processId: Optional[int] = None
    pipeTransport: Optional[Dict] = None
    sourceFileMap: Optional[Dict] = None
    justMyCode: Optional[bool] = None
    symbolOptions: Optional[Dict] = None
    args: Optional[List[str]] = None
    cwd: Optional[str] = None
    console: Optional[str] = None
    program: Optional[str] = None

    def to_dict(self) -> Dict:
        """Return a dict without None values, ready for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class VSCodeGenerator:
    """Generates or updates .vscode/launch.json with one or more VS Code tasks."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.vscode_dir = self.project_root / ".vscode"
        self.launch_file = self.vscode_dir / "launch.json"
        self.vscode_dir.mkdir(exist_ok=True)

    def add_tasks(self, tasks: List[VSCodeLaunchConfig]):
        """Add one or more VSCodeTask objects to launch.json."""
        if self.launch_file.exists():
            with self.launch_file.open("r", encoding="utf-8") as f:
                launch_data: Dict = json5.load(f)
        else:
            launch_data: Dict = {"version": "0.2.0", "configurations": []}

        existing_names = {c.get("name") for c in launch_data.get("configurations", [])}

        for task in tasks:
            if task.name not in existing_names:
                launch_data["configurations"].append(task.to_dict())

        with self.launch_file.open("w", encoding="utf-8") as f:
            json.dump(launch_data, f, indent=2)
            f.write("\n")


def dotnet_debug_container_task(
    container_name: str = "debug-local",
) -> VSCodeLaunchConfig:
    return VSCodeLaunchConfig(
        name=".NET-Local",
        type="coreclr",
        request="attach",
        processId=1,
        pipeTransport={
            "pipeProgram": "docker",
            "pipeArgs": ["exec", "-i", container_name],
            "debuggerPath": "/vsdbg/vsdbg",
            "pipeCwd": "${workspaceFolder}/",
            "quoteArgs": False,
        },
        sourceFileMap={"/build/": "${workspaceFolder}/"},
        justMyCode=True,
        symbolOptions={
            "searchMicrosoftSymbolServer": True,
            "searchNuGetOrgSymbolServer": True,
        },
    )
