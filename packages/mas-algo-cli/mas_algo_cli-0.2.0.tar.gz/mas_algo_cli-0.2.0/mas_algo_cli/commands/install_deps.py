"""Install a curated subset of hosting-environment packages locally."""

from __future__ import annotations

import shutil
import subprocess
import sys

HOSTING_DEPS = [
    "numpy",
    "pandas",
    "scipy",
    "scikit-learn",
    "requests",
    "flask",
    "opencv-python",
    "pillow",
    "pyyaml",
    "pydantic",
    "aiohttp",
    "openpyxl",
    "lxml",
]


def execute() -> int:
    uv_path = shutil.which("uv")
    if uv_path:
        cmd = [uv_path, "pip", "install"] + HOSTING_DEPS
    else:
        cmd = [sys.executable, "-m", "pip", "install"] + HOSTING_DEPS

    print(f"Installing hosting-environment dependencies...")
    print(f"  Packages: {', '.join(HOSTING_DEPS)}\n")

    result = subprocess.run(cmd, text=True)

    if result.returncode != 0:
        print("\nError: Failed to install some dependencies.")
        return 1

    print("\nDone. Hosting-environment dependencies installed.")
    return 0
