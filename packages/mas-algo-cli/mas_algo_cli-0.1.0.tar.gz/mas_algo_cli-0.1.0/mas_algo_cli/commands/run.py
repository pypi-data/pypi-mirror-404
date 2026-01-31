"""Run algorithm service locally for testing."""

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_python_executable(service_dir: Path) -> str:
    """Find the Python executable to use for running the service.

    Tries in order:
    1. .venv/bin/python in service directory
    2. Current Python executable (fallback)
    """
    venv_python = service_dir / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)

    logger.warning(f"No .venv found in {service_dir}, using current Python interpreter")
    logger.warning("Consider creating a virtual environment: python -m venv .venv")
    return sys.executable


def load_env_vars(service_dir: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = os.environ.copy()
    env_file = service_dir / ".env"

    if not env_file.exists():
        logger.warning(".env file not found. Copy .env.example to .env and configure it.")
        return env_vars

    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def execute(path: str, host: str, port: int, debug: bool = False, debug_port: int = 5678) -> int:
    service_dir = Path(path).resolve()
    main_file = service_dir / "main.py"

    if not main_file.exists():
        print(f"Error: main.py not found in {service_dir}")
        return 1

    python_exe = find_python_executable(service_dir)
    env_vars = load_env_vars(service_dir)

    # Pass configuration through environment
    env_vars.update({
        "ALGO_SERVICE_DIR": str(service_dir),
        "ALGO_HOST": host,
        "ALGO_PORT": str(port),
        "ALGO_DEBUG": "1" if debug else "0",
        "ALGO_DEBUG_PORT": str(debug_port),
    })

    # Get the runner script path
    runner_script = Path(__file__).parent.parent / "runner.py"

    logger.info(f"Using Python: {python_exe}")
    logger.info(f"Service directory: {service_dir}")

    try:
        result = subprocess.run(
            [python_exe, str(runner_script)],
            env=env_vars,
            cwd=str(service_dir.parent),
        )
        return result.returncode
    except KeyboardInterrupt:
        logger.info("Shutting down")
        return 0
    except Exception as e:
        logger.error(f"Failed to run service: {e}")
        return 1
