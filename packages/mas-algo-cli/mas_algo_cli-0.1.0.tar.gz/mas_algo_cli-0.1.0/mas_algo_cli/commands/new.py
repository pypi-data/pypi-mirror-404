"""Create a new algorithm service project."""

from __future__ import annotations

import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

TEMPLATES = {
    "1": "basic",
    "2": "predict",
    "3": "cv",
    "basic": "basic",
    "predict": "predict",
    "cv": "cv",
}

TEMPLATE_DESCRIPTIONS = {
    "basic": "Minimal service skeleton",
    "predict": "Prediction/ML with pandas",
    "cv": "Computer vision with Pillow",
}


def select_template() -> str:
    """Prompt user to select a template interactively."""
    print("Select a template:")
    print(f"  1. basic   - {TEMPLATE_DESCRIPTIONS['basic']}")
    print(f"  2. predict - {TEMPLATE_DESCRIPTIONS['predict']}")
    print(f"  3. cv      - {TEMPLATE_DESCRIPTIONS['cv']}")

    while True:
        choice = input("Enter number or name [1]: ").strip() or "1"
        if choice in TEMPLATES:
            return TEMPLATES[choice]
        print(f"Invalid choice: {choice}. Please enter 1, 2, 3, basic, predict, or cv.")


def install_stubs(project_dir: Path) -> bool:
    """Install rest-stubs package in project's virtual environment."""
    venv_python = project_dir / ".venv" / "bin" / "python"

    if not venv_python.exists():
        return False

    stubs_dir = resources.files("mas_algo_cli.stubs")

    try:
        with resources.as_file(stubs_dir) as stubs_path:
            # Try uv first, fall back to pip
            uv_path = shutil.which("uv")

            if uv_path:
                cmd = [uv_path, "pip", "install", "-e", str(stubs_path)]
            else:
                cmd = [str(venv_python), "-m", "pip", "install", "-e", str(stubs_path)]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_dir)
            )

            return result.returncode == 0
    except Exception:
        return False


def execute(name: str, parent_dir: str, template: str | None = None) -> int:
    if "-" in name:
        print(f"Error: Project name '{name}' contains hyphens. Use underscores instead: {name.replace('-', '_')}")
        return 1

    parent = Path(parent_dir).resolve()
    project_dir = parent / name

    if project_dir.exists():
        print(f"Error: Directory '{project_dir}' already exists")
        return 1

    if template is None:
        template = select_template()

    print(f"Creating new algorithm service: {project_dir} (template: {template})")
    project_dir.mkdir(parents=True)

    template_dir = resources.files(f"mas_algo_cli.templates.{template}")

    for item in template_dir.iterdir():
        if item.is_file():
            content = item.read_text()
            content = content.replace("${name}", name)
            dest = project_dir / item.name
            dest.write_text(content)
            print(f"  Created: {item.name}")

    # Create virtual environment
    print(f"\nCreating virtual environment...")
    try:
        uv_path = shutil.which("uv")
        if uv_path:
            result = subprocess.run(
                [uv_path, "venv"],
                cwd=str(project_dir),
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(
                [sys.executable, "-m", "venv", ".venv"],
                cwd=str(project_dir),
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"  Warning: Failed to create virtual environment: {result.stderr}")
        else:
            print(f"  Created: .venv")

            # Install stubs
            print(f"  Installing rest-stubs...")
            if install_stubs(project_dir):
                print(f"  Installed: rest-stubs")
            else:
                print(f"  Warning: Failed to install rest-stubs")

    except Exception as e:
        print(f"  Warning: Failed to create virtual environment: {e}")

    print(f"\nService created at: {project_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {name}")
    print(f"  2. source .venv/bin/activate  # Windows: .venv\\Scripts\\activate")
    print(f"  3. pip install -r requirements.txt")
    print(f"  4. cp .env.example .env")
    print(f"  5. Implement your algorithm in main.py")
    print(f"  6. algo run")
    print(f"  7. algo pack")

    return 0
