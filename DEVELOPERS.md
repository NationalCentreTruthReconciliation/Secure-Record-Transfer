# For Developers

The developer documentation here assumes you are using [VSCode](https://code.visualstudio.com/).

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


### Re-build JS as Changes are Made

After you run the dev container (`compose.dev.yml`), you can automatically re-build the JS files any time they change with this command:

```shell
# Using Docker:
docker compose -f compose.dev.yml exec app npm run watch

# Using Podman:
podman-compose -f compose.dev.yml exec app npm run watch
```

This will re-build the bundled JS files any time you save a change to a `.js` file which is useful while you're writing Javascript. This command does not exit until you press CTRL-C, so make sure to run it in a separate terminal.

# Virtual Environment and Poetry Setup

Python dependencies are managed with [Poetry](https://python-poetry.org/). To install Poetry and create a virtual environment with the minimally necessary packages, follow these instructions:

First, install `pipx` via the [official pipx installation instructions](https://pipx.pypa.io/stable/installation/).

After installing `pipx`, install [Poetry](https://python-poetry.org/):

```shell
pipx install poetry
```

Next, create and activate a virtual environment from the root of the repository:

```shell
# If on Windows:
python -m venv env
.\env\Scripts\Activate.ps1

# If on MacOS or Linux
python3 -m venv env
source env/bin/activate
```

Finally, install the dependencies with `poetry`:

```shell
poetry install
```

## Testing Setup

Ensure you follow the instructions in the [Virtual Environment and Poetry Setup](#virtual-environment-and-poetry-setup) section before continuing.

Install the `dev` dependencies with Poetry:

```shell
poetry install --extras "dev"
```

The tests can be run with [pytest](https://docs.pytest.org/en/stable/how-to/usage.html) (using [pytest-django](https://pytest-django.readthedocs.io/en/latest/#example-using-pyproject-toml)):
To run tests, use:
```shell
pytest
```

For unit tests only:
```shell
pytest -k "unit"
```

For E2E tests only:
```shell
pytest -k "e2e"
```

The tests should also be discoverable and runnable from the VSCode test explorer.

## Building the Documentation

The documentation for this repository is built with [Sphinx](https://sphinx-doc.org).

Ensure you follow the instructions in the [Virtual Environment and Poetry Setup](#virtual-environment-and-poetry-setup) section before continuing.

Install the `docs` dependencies with Poetry:
```shell
poetry install --extras "docs"
```

To build the docs, run:

```shell
sphinx-build docs docs/_build
```

The built documentation will be available in `docs/_build`. Open the `index.html` in your browser to view the docs.

The Sphinx configuration can be found in `docs/conf.py`. The documentation is also built automatically by [Read The Docs](https://about.readthedocs.com/) based on the configuration in `.readthedocs.yaml` and is published [here](https://secure-record-transfer.readthedocs.io/en/latest/) when changes are made to the default branch.
