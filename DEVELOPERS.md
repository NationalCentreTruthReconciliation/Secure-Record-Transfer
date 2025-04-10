# For Developers

The developer documentation here assumes you are using [VSCode](https://code.visualstudio.com/).

## Supported Operating Systems

This application is primarily designed for UNIX-based operating systems (Linux, macOS). Some functionality may not work correctly on Windows.

If you're developing on Windows, we recommend using Windows Subsystem for Linux (WSL) to ensure compatibility. You can install Python on [WSL](https://code.visualstudio.com/docs/remote/wsl) and then develop within that Linux environment.

## Contributions

Follow [the NCTR's Python Style Guide](https://github.com/NationalCentreTruthReconciliation/Python-Development-Guide) when making contributions. You can skip the "Setup" section of the guide as this repository already includes the necessary VSCode settings in `.vscode/settings.json`.

## Linting + Formatting

Install the [ESLint VSCode extension](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint).

Then, install Node dependencies for development:

```shell
npm install --include=dev
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
docker compose -f compose.dev.yml exec app npm run watch

# Using Podman:
podman-compose -f compose.dev.yml exec app npm run watch
```

This will re-build the bundled JS files any time you save a change to a `.js` file which is useful while you're writing Javascript. This command does not exit until you press CTRL-C, so make sure to run it in a separate terminal.

## Local Python Environment Stup

Python dependencies are managed with [Poetry](https://python-poetry.org/). `poetry` can be installed on your local machine with the [offical installer](https://python-poetry.org/docs/#installing-with-the-official-installer). Install version `1.8.5` with the following command:

```shell
curl -sSL https://install.python-poetry.org | python3 - --version 1.8.5
```

Next, create and activate a virtual environment from the root of the repository:

```shell
python3 -m venv env
source env/bin/activate
```

When VSCode prompts if you want to select the new environment for this workspace folder, select **Yes**.

Finally, install the dependencies with `poetry`:

```shell
poetry install -E dev
```

## Running Tests

Ensure you follow the instructions in the [Local Python Environment Setup](#local-python-environment-setup) section before continuing.

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

## Building the Documentation

The documentation for this repository is built with [Sphinx](https://sphinx-doc.org).

Ensure you follow the instructions in the [Local Python Environment Setup](#local-python-environment-setup) section before continuing.

To build the docs, run:

```shell
sphinx-build docs docs/_build
```

The built documentation will be available in `docs/_build`. Open the `index.html` in your browser to view the docs.

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

To also populate the database with test data and  populate corresponding uploaded files, add the
`--seed` option to the command.

```shell
# Using Docker:
docker compose -f compose.dev.yml exec app python manage.py reset --seed

# Using Podman:
podman-compose -f compose.dev.yml exec app python manage.py reset --seed
```

An admin user will be created with the username `admin` and password `123`, , along with test
submissions and a test submission group.