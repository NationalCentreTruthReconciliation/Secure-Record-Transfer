"""Update all the version files in this repository.

Call it like:

  python scripts/update_version.py 2025.07.07

"""

import argparse
import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


BASE_DIR = Path(__file__).parent.parent

PACKAGE_JSON = BASE_DIR / "package.json"
PACKAGE_LOCK_JSON = BASE_DIR / "package-lock.json"
PYPROJECT_TOML = BASE_DIR / "pyproject.toml"


def calver(version_string: str) -> str:
    """Validate that version string matches YYYY-MM-DD format."""
    pattern = r"\d{4}\.\d{2}\.\d{2}"
    if not re.match(pattern, version_string):
        raise argparse.ArgumentTypeError(
            f"Version must match format YYYY-MM-DD, got: {version_string}"
        )
    return version_string


def get_arg_parser() -> argparse.ArgumentParser:
    """Create an argument parser for this script."""
    parser = argparse.ArgumentParser(
        description="Update version in package.json, package-lock.json, and pyproject.toml"
    )
    parser.add_argument("version", type=calver, help="Version string to set (e.g., '2025.07.07')")
    return parser


def update_node_version_files(version: str) -> bool:
    """Update version in package.json and package-lock.json files."""
    changed = False
    package_name = ""

    for file_path in [PACKAGE_JSON, PACKAGE_LOCK_JSON]:
        with open(file_path, "r") as f:
            data = json.load(f)

        if file_path == PACKAGE_JSON:
            package_name = data.get("name", "")

        if version == data["version"]:
            logging.info("Version in %s is already %s", file_path.name, version)
            continue

        logging.info("Updating version in %s to %s", file_path.name, version)

        data["version"] = version

        # Update the version of this package in package-lock.json
        if file_path == PACKAGE_LOCK_JSON and "" in data.get("packages", {}):
            this_package = data["packages"][""]
            if this_package["name"] == package_name:
                this_package["version"] = version

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
            f.write("\n")

        changed = True

    return changed


def update_python_version_files(version: str) -> bool:
    """Update version in pyproject.toml file."""
    content = PYPROJECT_TOML.read_text()

    # Find the version line in [project] section
    version_pattern = r'(version\s*=\s*")[^"\s]*(")'
    match = re.search(version_pattern, content)

    if match:
        old_version = content[match.start(1) + len('version = "') : match.end(2) - 1]
        if version == old_version:
            logging.info("Version in %s is already %s", PYPROJECT_TOML.name, version)
            return False

        logging.info("Updating version in %s to %s", PYPROJECT_TOML.name, version)
        new_content = re.sub(version_pattern, rf"\g<1>{version}\g<2>", content)
        PYPROJECT_TOML.write_text(new_content)
        return True

    else:
        logging.error("Could not find version field in %s", PYPROJECT_TOML.name)
        return False


def main() -> None:
    """Change the version in all the required files."""
    arg_parser = get_arg_parser()

    parsed = arg_parser.parse_args()

    changed = update_node_version_files(parsed.version)
    changed = update_python_version_files(parsed.version) or changed

    if changed:
        logging.info("Version(s) updated, you can commit the updated files now")


if __name__ == "__main__":
    err = False
    for file in (PACKAGE_JSON, PACKAGE_LOCK_JSON, PYPROJECT_TOML):
        if not file.exists():
            logging.error("Could not find %s", file)
            err = True

    if not err:
        main()
