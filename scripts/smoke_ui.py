"""UI smoke runner for DialogueGenerator (Windows-friendly).

Runs `main_app.py`, verifies it stays alive for N seconds (i.e., doesn't crash on startup),
then terminates it.

This is meant for automation and avoids fragile one-liner PowerShell quoting.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def _project_root_from_this_file() -> Path:
    """Return the project root assuming this file lives under `scripts/`."""
    return Path(__file__).resolve().parent.parent


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run a short UI smoke check.")
    parser.add_argument(
        "--seconds",
        type=float,
        default=3.0,
        help="How long the app must stay alive to be considered healthy.",
    )
    parser.add_argument(
        "--app",
        type=str,
        default="main_app.py",
        help="Path to the UI entrypoint, relative to project root unless absolute.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG logging via DIALOGUEGEN_DEBUG=1.",
    )
    return parser.parse_args(argv)


def run_smoke(seconds: float, app_path: Path, project_root: Path, debug: bool) -> int:
    """Run the app, ensure it stays alive for `seconds`, then terminate."""
    if seconds <= 0:
        raise ValueError("--seconds must be > 0")

    if not app_path.is_absolute():
        app_path = (project_root / app_path).resolve()

    if not app_path.exists():
        raise FileNotFoundError(f"App entrypoint not found: {app_path}")

    env = os.environ.copy()
    if debug:
        env["DIALOGUEGEN_DEBUG"] = "1"

    proc = subprocess.Popen(
        [sys.executable, str(app_path)],
        cwd=str(project_root),
        env=env,
    )

    try:
        time.sleep(seconds)
        exit_code = proc.poll()
        if exit_code is not None:
            raise RuntimeError(f"App exited early with code {exit_code}")
        return 0
    finally:
        # Best-effort termination (the UI is expected to run forever).
        try:
            proc.terminate()
        except Exception:
            pass

        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    project_root = _project_root_from_this_file()
    try:
        return run_smoke(
            seconds=float(args.seconds),
            app_path=Path(args.app),
            project_root=project_root,
            debug=bool(args.debug),
        )
    except Exception as exc:
        print(f"[smoke_ui] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


