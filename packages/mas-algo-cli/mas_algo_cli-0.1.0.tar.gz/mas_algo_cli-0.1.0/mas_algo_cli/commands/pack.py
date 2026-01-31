"""Package algorithm service for deployment."""

from __future__ import annotations

import tarfile
from pathlib import Path

EXCLUDE_PATTERNS = {
    ".env",
    ".env.example",
    ".git",
    ".gitignore",
    "__pycache__",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.tar.gz",
    # Local dev files (provided by algo-cli)
    "server.py",
    "run.py",
    "pack.py",
    "test_client.py",
    "rest",
}


def should_exclude(name: str) -> bool:
    """Check if file should be excluded from package."""
    if name in EXCLUDE_PATTERNS:
        return True
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def execute(path: str, output: str | None) -> int:
    service_dir = Path(path).resolve()
    main_file = service_dir / "main.py"

    if not main_file.exists():
        print(f"Error: main.py not found in {service_dir}")
        return 1

    service_name = service_dir.name
    output_file = Path(output) if output else Path(f"{service_name}.tar.gz")

    print(f"Packaging {service_name}...")

    with tarfile.open(output_file, "w:gz") as tar:
        for item in service_dir.iterdir():
            if should_exclude(item.name):
                continue
            if item.is_file():
                # No top-level folder per spec
                tar.add(item, arcname=item.name)
                print(f"  Added: {item.name}")
            elif item.is_dir() and not should_exclude(item.name):
                for subitem in item.rglob("*"):
                    if subitem.is_file() and not should_exclude(subitem.name):
                        rel_path = subitem.relative_to(service_dir)
                        tar.add(subitem, arcname=str(rel_path))
                        print(f"  Added: {rel_path}")

    print(f"\nCreated: {output_file}")
    return 0
