"""Contains pytest hooks. The hooks defined here are used to modify the behavior of
pytest during test collection and execution.
"""

import os
import shutil
import subprocess

import pytest


def pytest_runtestloop(session: pytest.Session) -> None:
    """Install node dependencies and build static assets only if E2E tests are selected to
    run.
    """
    selected_items = session.items
    if not session.config.option.collectonly and any(
        "/e2e/" in item.nodeid for item in selected_items
    ):
        try:
            npm_cmd = shutil.which("pnpm") or "pnpm"
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
            pytest.exit(f"Failed to run pnpm install or build: {e}")
        except FileNotFoundError as e:
            pytest.exit(
                f"pnpm command not found (got: {e}). pnpm must be installed to run e2e tests."
            )
