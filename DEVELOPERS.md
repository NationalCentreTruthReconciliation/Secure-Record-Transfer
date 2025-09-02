# For Developers

This page contains information relevant to developers working on this application.

## Contributions

Follow [the NCTR's Python Style Guide](https://github.com/NationalCentreTruthReconciliation/Python-Development-Guide) when making contributions. You can skip the "Setup" section of the guide as this repository already includes the necessary VSCode settings in `.vscode/settings.json`.

## Supported Operating Systems

This application is primarily designed for UNIX-based operating systems (Linux, macOS). Some functionality may not work correctly on Windows.

If you're developing on Windows, we strongly recommend using Windows Subsystem for Linux (WSL) to ensure compatibility.

## Setting up Your Development Environment

This section outlines the tools you need to install and the steps you need to take to prepare your machine for development.

### All Platforms

These instructions apply to all operating systems. First, install the following tools:

- **VSCode** is our recommended IDE for development ([Download VSCode](https://code.visualstudio.com/)).
- **Docker Desktop** or **Podman Desktop** is needed to run the containerized development environment ([Install Docker Desktop](https://docs.docker.com/get-docker/)) / ([Install Podman Desktop](https://podman.io/getting-started/installation)).
  - If you have no preference over either tool, use Docker.

### Mac/Linux-Specific Instructions

If developing on Mac or Linux, you'll need the following tools:

1. **Node.js 22+** for Javascript dependency management and builds ([Download Node.js](https://nodejs.org/en/download/))
2. **pnpm** for Javascript package management ([pnpm.io](https://pnpm.io/)). Use the following command to install pnpm:

```shell
npm install -g pnpm@latest-10
```

3. **uv 0.8.8** for Python dependency management ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)). Use the following command to install uv:

```shell
curl -LsSf https://astral.sh/uv/0.8.8/install.sh | sh
```

### Windows-Specific Instructions

If developing on Windows, you'll need the following tools:

1. **WSL 2** ([Microsoft WSL Installation Guide](https://docs.microsoft.com/en-us/windows/wsl/install)). Note that WSL 2 may have already been installed when installing Docker or Podman; in that case, you can skip this step.
2. **uv 0.8.8** for Python dependency management ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)). Use the following command to install uv:

```shell
# In your WSL terminal:
curl -LsSf https://astral.sh/uv/0.8.8/install.sh | sh
```

3. **Node.js 22+** ([Node.js on WSL Installation Guide](https://learn.microsoft.com/en-us/windows/dev-environment/javascript/nodejs-on-wsl#install-nvm-nodejs-and-npm))

4. **pnpm** for Javascript package management ([pnpm.io](https://pnpm.io/)). After installing npm, use the following command to install pnpm:

```shell
# In your WSL terminal:
npm install -g pnpm@latest-10
```

5. **Configure Docker Desktop with WSL 2**. Follow the instructions in the [Docker Desktop WSL 2](https://docs.docker.com/desktop/features/wsl/#turn-on-docker-desktop-wsl-2) documentation to enable WSL 2 integration with Docker. If using **Podman**, follow the instructions instead in [Podman Desktop WSL 2](https://podman-desktop.io/docs/installation/windows-install#use-wsl2-as-machine-provider).
6. **VSCode Remote Development Extension Pack** ([VS Code Remote Development](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack))

### Repository Setup

Once all the above tools have been installed, clone this repository and open it in VSCode. If on Windows, use the "WSL: Open Folder in WSL" command to open the cloned repository in WSL.

You'll be prompted to install recommended extensions specified in `.vscode/extensions.json`. Click on "Install All" to install them. These include:

- [Python](https://marketplace.visualstudio.com/items/?itemName=ms-python.python): Python language support and debugging
- [Ruff](https://marketplace.visualstudio.com/items/?itemName=charliermarsh.ruff): Python linting and formatting
- [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint): JavaScript linting and formatting
- [Even Better TOML](https://marketplace.visualstudio.com/items/?itemName=tamasfe.even-better-toml): TOML file formatting
- [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss): Tailwind CSS support
- [Django](https://marketplace.visualstudio.com/items?itemName=batisteo.vscode-django): Django template syntax highlighting and template path jumping
- [djLint](https://marketplace.visualstudio.com/items?itemName=monosans.djlint): Django template linting and formatting

If you're not automatically prompted, you can install recommended extensions manually by:

1. Opening the Extensions view in VSCode (`Ctrl+Shift+X` or `Cmd+Shift+X`)
2. Typing "@recommended" in the search bar
3. Installing each listed extension

## Local Python Environment Setup

After installing `uv` as mentioned in the [Setting up Your Development Environment](#setting-up-your-development-environment) section, install the dependencies with:

```shell
# This will also install Python if you don't already have a compatible version
# The required version is set in .python-version
uv sync --extra dev
```

**Note:** If you're using **Podman** instead of Docker, you'll need to install the podman extras as well:

```shell
uv sync --extra dev --extra podman
```

When VSCode prompts if you want to select the new environment for this workspace folder, select **Yes**.

## Local Javascript Environment Setup

For JavaScript development, you need to install Node dependencies to gain access to the source code, build tools, and linting/formatting:

```shell
pnpm install
```

You can then use the provided pnpm scripts for various tasks:

- `pnpm run build` - Build JavaScript files for production
- `pnpm run watch` - Rebuild JavaScript files whenever they change (see [Re-build JS as Changes are Made](#re-build-js-as-changes-are-made))
- `pnpm run lint` - Run ESLint to check JavaScript files

## Running the Development Container

To start the development container, run:

```shell
# Using Docker:
docker compose -f compose.dev.yml up -d --build --remove-orphans

# Using Podman:
podman-compose -f compose.dev.yml up -d --build --remove-orphans
```

By passing the `--build` option, the image will be re-built whenever it's needed; otherwise, the image is cached and reused if nothing changed that requires a rebuild.

The `--remove-orphans` argument is useful when you're switching between running the development image and the production image.

To stop the container, run:

```shell
# Using Docker:
docker compose -f compose.dev.yml down

# Using Podman:
podman-compose -f compose.dev.yml down
```

## Debugging the Application

The ports 8009 and 8010 are exposed to allow you to debug the web application, and the asynchronous job queue, respectively. This functionality is only available when `DEBUG = True`. These ports can be attached to with `debugpy`

The debugging configuration has already been set up in the `.vscode/launch.json` file. To start debugging, select the appropriate configuration from the dropdown in the top menu of VSCode and press the green play button.

## Continuous Integration

A GitHub Actions workflow is set up to run Django tests on every pull request to the master branch. All tests must pass before a merge is allowed. The workflow configuration can be found in `.github/workflows/django-tests.yml`.

## Re-build JS as Changes are Made

After you run the dev container (`compose.dev.yml`), you can automatically re-build the JS files any time they change with this command:

```shell
# Using Docker:
docker compose -f compose.dev.yml exec app pnpm run watch

# Using Podman:
podman-compose -f compose.dev.yml exec app pnpm run watch
```

This will re-build the bundled JS files any time you save a change to a `.js` file which is useful while you're writing Javascript. This command does not exit until you press CTRL-C, so make sure to run it in a separate terminal.

## Running Tests

Ensure you follow the instructions in the [Local Python Environment Setup](#local-python-environment-setup) section before continuing.

**Note:** Some file acceptance tests require the `libmagic` library for MIME type validation. If you don't have `libmagic` installed, these tests will be automatically skipped. To install `libmagic`:

- **macOS**: `brew install libmagic`
- **Ubuntu/Debian**: `sudo apt-get install libmagic1`

The tests can be run in a few different ways:

1. Using [pytest](https://docs.pytest.org/en/stable/how-to/usage.html) (this uses [settings in the `pyproject.toml` file](https://pytest-django.readthedocs.io/en/latest/#example-using-pyproject-toml))
2. The [Django test runner](https://docs.djangoproject.com/en/4.2/ref/django-admin/#test)
3. The [VS Code test runner](https://code.visualstudio.com/docs/python/testing#_run-tests)

This document focuses only on the first two options. For information on [running and debugging tests with VS Code, click here](https://code.visualstudio.com/docs/python/testing#_run-tests).

The `pytest` commands can be run from the root of the repository. The Django admin tests must be run from the `app` directory.

To run all tests:

```shell
pytest

# Or, from the app/ directory:
python manage.py test
```

To run only the unit tests:

```shell
pytest -k "unit"

# Or, from the app/ directory:
python manage.py test --exclude-tag=e2e
```

To run only the end-to-end tests:

```shell
pytest -k "e2e"

# There is currently no way to do this with python manage.py test (yet)
```

To display skipped tests and the reason why they were skipped, add the `-rs` flag to any pytest command:

```shell
pytest -rs
```

### Debugging Tests with VSCode

You can debug Python tests directly in VSCode using the pre-configured launch settings in `.vscode/launch.json`. To access these launch settings, open the Run & Debug menu (press `Ctrl+Shift+D` on Windows/Linux or `Cmd+Shift+D` on Mac).

Two useful configurations are provided:

- **Debug Pytest: Current File**
  Runs and debugs all tests in the currently open file. Open the test file you want to debug, select this configuration from the Run and Debug panel, set desired breakpoints, and press the green play button.

- **Debug Pytest: Specific Test**
  Prompts you to enter the full test name (e.g., `app/upload/tests/unit/test_models.py::TestUploadSession::test_new_session_creation`). This allows you to debug a specific test or test case.

While debugging, you can step through your application code in addition to the test code.

## Building the Documentation

The documentation for this repository is built with [Sphinx](https://sphinx-doc.org).

Ensure you follow the instructions in the [Local Python Environment Setup](#local-python-environment-setup) section before continuing.

To build the docs, run:

```shell
uv run sphinx-build docs docs/_build
```

Sphinx has its own cache that it uses for builds. Because of that, Sphinx might hide errors from you if it encountered them on a previous build. You can execute a "clean" build with this command that will show all errors if there are any:

```shell
# -a: Re-write all files. See: https://www.sphinx-doc.org/en/master/man/sphinx-build.html#cmdoption-sphinx-build-a
# -E: Read all files. See: https://www.sphinx-doc.org/en/master/man/sphinx-build.html#cmdoption-sphinx-build-E
uv run sphinx-build -aE docs docs/_build
```

The built documentation will be available in `docs/_build`. To view the docs, either:

Open the file `docs/_build/index.html` in your web browser.

**OR:**

Start an http server with `uv run python -m http.server -d docs/_build 8001` and open http://localhost:8001 in your browser.

The Sphinx configuration can be found in `docs/conf.py`. The documentation is also built automatically by [Read The Docs](https://about.readthedocs.com/) based on the configuration in `.readthedocs.yaml` and is published [here](https://secure-record-transfer.readthedocs.io/en/latest/) when changes are made to the default branch.

## Resetting the Database

During development, you may need to reset the database to a clean state. You can do this with the following command:

```shell
# Using Docker:
docker compose -f compose.dev.yml exec app python manage.py reset

# Using Podman:
podman-compose -f compose.dev.yml exec app python manage.py reset
```

This will prompt you to confirm the deletion of all data in the database. Type "y" to proceed.
This command deletes the development, and re-applies all migrations on a fresh one.

To also populate the database with test data and populate corresponding uploaded files, add the
`--seed` option to the command.

```shell
# Using Docker:
docker compose -f compose.dev.yml exec app python manage.py reset --seed

# Using Podman:
podman-compose -f compose.dev.yml exec app python manage.py reset --seed
```

An admin user will be created with the username `admin` and password `123`, , along with test
submissions and a test submission group.

### Updating Seed Data

After making model changes, the existing seed data may become incompatible with the database schema, and you may need to update the seed data fixture. To do this:

1. **Reset the database without seeding** to start with a clean state:

   ```shell
   # Using Docker:
   docker compose -f compose.dev.yml exec app python manage.py reset

   # Using Podman:
   podman-compose -f compose.dev.yml exec app python manage.py reset
   ```

2. **Create the desired database state manually** by either:

   - Creating an admin user with `python manage.py createsuperuser`
   - Signing up as a regular user through the web app's Sign Up page
   - Then creating whatever data you wish by filling out forms, creating groups, etc.

3. **Important**: Any files you upload during the "Upload Files" step of forms must be present in `app/fixtures/` or they will not be available after seeding. Right now, only one test upload file is included in the fixture and available for upload, `app/fixtures/nctr_logo.jpg`.

4. **Export the new seed data** once you're satisfied with the database state:

   ```shell
   # Using Docker:
   docker compose -f compose.dev.yml exec app python manage.py dumpdata recordtransfer caais --indent 4 > app/fixtures/seed_data.json

   # Using Podman:
   podman-compose -f compose.dev.yml exec app python manage.py dumpdata recordtransfer caais --indent 4 > app/fixtures/seed_data.json
   ```

5. **Commit the updated seed data** to the repository.

## Updating the Application Version

For each new release of this application, the version string in these files needs to be updated:

- `package.json`
- `package-lock.json`
- `pyproject.toml`
- `uv.lock`

To make it easy to update these files, a script can be run to update these files with the same version. From the root of the repository, you can update the version of the application like this:

```shell
python scripts/update_version.py "2025.07.07"
```

This project uses [Calendar versioning](https://calver.org/), and version strings should match the format YYYY.MM.DD. The update script accepts zero-padded months and days (e.g., 2025.07.07), but it will strip leading zeros, so the actual version used will have non-padded month and day numbers (e.g., 2025.7.7).
