"""Contains pytest hooks. The hooks defined here are used to modify the behavior of
pytest during test collection and execution.
"""

import subprocess

import pytest


def pytest_collection_modifyitems(session, config, items) -> None:
    """Run npm build only if e2e tests are being run. `items` is a list of test items to be
    run.
    """
    # Check if running unit tests via -e2e parameter
    if config.getoption("-k") == "e2e":
        try:
            subprocess.run(["npm", "run", "build"], check=True)
        except subprocess.CalledProcessError as e:
            pytest.exit(f"Failed to run npm build: {e}")
