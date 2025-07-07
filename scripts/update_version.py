"""Update all the version files in this repository.

Call it like:

  python scripts/update_version.py 2025.07.07

"""

import argparse
import logging
import re
import shutil
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def calver(version_string: str) -> str:
    """Validate that version string matches YYYY.MM.DD format."""
    pattern = r"\d{4}\.\d{2}\.\d{2}"
    if not re.match(pattern, version_string):
        raise argparse.ArgumentTypeError(
            f"Version must match format YYYY.MM.DD, got: {version_string}"
        )
    return version_string


def get_arg_parser() -> argparse.ArgumentParser:
    """Create an argument parser for this script."""
    parser = argparse.ArgumentParser(
        description="Update version in package.json, package-lock.json, and pyproject.toml"
    )
    parser.add_argument("version", type=calver, help="Version string to set (e.g., '2025.07.07')")
    return parser


def update_node_version_files(version: str) -> None:
    """Update version in package.json and package-lock.json files."""
    npm = shutil.which("npm") or "npm"

    result = subprocess.run(
        args=[npm, "version", "--no-git-tag-version", version],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    changed = "Version not changed" not in result.stderr.decode()

    if changed:
        logging.info("Updated package.json and package-lock.json version to %s", version)
    else:
        logging.info("Version in package.json and package-lock.json is already %s", version)


def update_python_version_files(version: str) -> None:
    """Update version in pyproject.toml file."""
    uv = shutil.which("uv") or "uv"

    subprocess.run(
        args=[uv, "version", version],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    logging.info("Updated version in pyproject.toml and uv.lock to %s", version)


def main() -> None:
    """Change the version in all the required files."""
    arg_parser = get_arg_parser()

    parsed = arg_parser.parse_args()

    update_node_version_files(parsed.version)
    update_python_version_files(parsed.version)

    logging.info("Version files updated, you can commit the updated files now")


if __name__ == "__main__":
    main()
