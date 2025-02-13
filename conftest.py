"""Contains pytest hooks. The hooks defined here are used to modify the behavior of
pytest during test collection and execution.
"""

import os
import shutil
import subprocess

import pytest


def pytest_runtestloop(session: pytest.Session) -> None:
    """Install node dependencies and isntall static assets only if E2E tests are selected to run."""
    selected_items = session.items
    if any("/e2e/" in item.nodeid for item in selected_items):
        try:
            npm_cmd = shutil.which("npm") or "npm"
            subprocess.run(
                [npm_cmd, "install"],
                check=True,
            )
            subprocess.run(
                [npm_cmd, "run", "build"],
                check=True,
                env={
                    **os.environ,
                    "WEBPACK_MODE": "development",
                },
            )
        except subprocess.CalledProcessError as e:
            pytest.exit(f"Failed to run npm install or build: {e}")
        except FileNotFoundError as e:
            pytest.exit(
                f"npm command not found (got: {e}). npm must be installed to run e2e tests."
            )
