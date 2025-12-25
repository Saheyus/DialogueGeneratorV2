"""Application launcher for DialogueGenerator.

This module ensures Python dependencies are installed (based on `requirements.txt`)
and then starts `main_app.py` reliably regardless of the caller's working directory.
"""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path
from typing import List

def _read_requirements(requirements_path: Path) -> List[str]:
    """Read `requirements.txt` and return requirement specifiers (non-empty, non-comment)."""
    try:
        with requirements_path.open("r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]
    except FileNotFoundError:
        print(f"Error: requirements.txt not found at: {requirements_path}")
        sys.exit(1)


def install_dependencies(project_dir: Path) -> None:
    """Install missing dependencies from `requirements.txt` in the given project directory."""
    requirements_path = project_dir / "requirements.txt"
    requirements = _read_requirements(requirements_path)

    missing_packages = []
    for req in requirements:
        package_name = re.split(r"[=<>!~\[]", req, maxsplit=1)[0].strip()
        try:
            importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            # Clean requirement from comments
            clean_req = req.split("#")[0].strip()
            if clean_req:
                missing_packages.append(clean_req)

    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            sys.exit(1)


def main() -> None:
    """Install dependencies (if needed) and launch the application."""
    project_dir = Path(__file__).resolve().parent
    main_app_path = project_dir / "main_app.py"

    install_dependencies(project_dir)
    print("All dependencies are satisfied. Launching the application...")
    try:
        # Use an absolute path + an explicit working directory to avoid CWD-related failures
        # and to keep relative resource paths (config/data/logs) consistent.
        subprocess.run(
            [sys.executable, str(main_app_path)],
            check=True,
            cwd=str(project_dir),
        )
    except FileNotFoundError:
        print(f"Error: main_app.py not found at: {main_app_path}")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Application exited with an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 