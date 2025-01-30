"""Contains pytest hooks. The hooks defined here are used to modify the behavior of
pytest during test collection and execution.
"""

import subprocess
from pathlib import Path

import pytest


def pytest_collection_modifyitems(session, config, items) -> None:
    """Run npm build only if e2e tests are being run. `items` is a list of test items to be
    run.
    """
    e2e_tests = any("e2e" in str(Path(item.fspath)) for item in items)

    if e2e_tests:
        try:
            subprocess.run(["npm", "run", "build"], check=True)
        except subprocess.CalledProcessError as e:
            pytest.exit(f"Failed to run npm build: {e}")
