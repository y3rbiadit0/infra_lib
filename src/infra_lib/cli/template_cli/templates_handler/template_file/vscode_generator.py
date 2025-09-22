from dataclasses import dataclass
import json
from pathlib import Path
from typing import List, Dict
import json5

@dataclass
class VSCodeLaunchConfig:
    """Represents a VS Code debug configuration."""
    name: str
    type: str
    request: str
    processId: int
    pipeTransport: Dict
    sourceFileMap: Dict
    justMyCode: bool
    symbolOptions: Dict

    def to_dict(self) -> Dict:
        """Convert the dataclass to dictionary for JSON serialization."""
        return self.__dict__


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



def dotnet_local_task(container_name: str = "debug-local") -> VSCodeLaunchConfig:
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