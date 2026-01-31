"""Install stub packages for local development."""

import shutil
import subprocess
from importlib import resources


def execute() -> int:
    stubs_dir = resources.files("mas_algo_cli.stubs")

    # Try uv first, fall back to pip
    uv_path = shutil.which("uv")

    with resources.as_file(stubs_dir) as stubs_path:
        print(f"Installing rest-stubs from {stubs_path}")

        if uv_path:
            cmd = [uv_path, "pip", "install", "-e", str(stubs_path)]
        else:
            import sys
            cmd = [sys.executable, "-m", "pip", "install", "-e", str(stubs_path)]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return 1

        print("Installed rest-stubs package")
        print("\nThe 'rest.process_base' import will now resolve for linting/IDE support.")
        return 0
