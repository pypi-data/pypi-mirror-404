"""Generate VS Code debug configuration."""

import json
from pathlib import Path

LAUNCH_CONFIG = {
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attach to algo run",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "127.0.0.1",
                "port": 5678
            }
        }
    ]
}


def execute(path: str) -> int:
    project_dir = Path(path).resolve()
    vscode_dir = project_dir / ".vscode"
    launch_file = vscode_dir / "launch.json"

    vscode_dir.mkdir(exist_ok=True)

    if launch_file.exists():
        print(f"Warning: {launch_file} already exists, overwriting")

    launch_file.write_text(json.dumps(LAUNCH_CONFIG, indent=2))
    print(f"Created: {launch_file}")

    print("\nTo debug:")
    print("  1. Set breakpoints in your code")
    print("  2. Run: algo run <service> --debug")
    print("  3. Press F5 in VS Code to attach")

    return 0
