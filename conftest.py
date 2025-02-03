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
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            subprocess.run(
                [npm_cmd, "run", "build"],
                check=True,
                env={
                    **os.environ,
                    "WEBPACK_MODE": "development",
                },
            )
        except subprocess.CalledProcessError as e:
            pytest.exit(f"Failed to run npm build: {e}")
        except FileNotFoundError as e:
            pytest.exit(
                f"npm command not found (got: {e}). npm must be installed to run e2e tests."
            )

