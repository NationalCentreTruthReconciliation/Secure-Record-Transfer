# For Developers

The developer documentation here assumes you are using [VSCode](https://code.visualstudio.com/).

## Contributions

Follow [the NCTR's Python Style Guide](https://github.com/NationalCentreTruthReconciliation/Python-Development-Guide) when making contributions. The only difference is that the `ruff.toml` is automatically pulled when the git pre-commit hook is set up in the following section.

## Linting + Formatting

Before beginning development, please configure git to use the git hooks (`.git/hooks`) provided in the repository. This will ensure that the linting configuration is updated before each commit.

```bash
git config core.hooksPath .githooks
```

Additionaly, add this configuration to your [local VSCode settings.json](https://code.visualstudio.com/docs/getstarted/settings#_settings-json-file) for JavaScript linting/formatting:

```json
{
    "editor.codeActionsOnSave": {
        "source.fixAll.eslint": "explicit",
    },
    "eslint.validate": [
        "javascript"
    ]
}
```

## Debugging the Application

The ports 8009 and 8010 are exposed to allow you to debug the web application, and the asynchronous job queue, respectively. This functionality is only available when `DEBUG = True`. These ports can be attached to with `debugpy`

Use this `launch.json` configuration in VSCode to debug the application:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Django",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "127.0.0.1",
                "port": 8009,
            },
            "django": true,
            "justMyCode": true,
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/bagitobjecttransfer/",
                    "remoteRoot": "/app/bagitobjecttransfer/"
                },
            ]
        },
        {
            "name": "Python Debugger: RQ",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "127.0.0.1",
                "port": 8010,
            },
            "django": true,
            "justMyCode": true,
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/bagitobjecttransfer/",
                    "remoteRoot": "/app/bagitobjecttransfer/"
                },
            ]
        }
    ]
}
```

## Continuous Integration

A GitHub Actions workflow is set up to run Django tests on every pull request to the master branch. All tests must pass before a merge is allowed. The workflow configuration can be found in `.github/workflows/django-tests.yml`.

## Javascript Development

If you're editing any of the `.js` files in this repo, add these settings to your [local VSCode settings.json](https://code.visualstudio.com/docs/getstarted/settings#_settings-json-file) for this project to set your environment up.

```json
{
    "[javascript]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "vscode.typescript-language-features",
        "editor.rulers": [
            99
        ]
    }
}
```

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

Use these settings in your [local VSCode settings.json](https://code.visualstudio.com/docs/getstarted/settings#_settings-json-file) for this project so that tests are discovered correctly in the Testing menu:

```json
{
    "python.testing.pytestEnabled": true,
    "python.analysis.extraPaths": [
        "./bagitobjecttransfer"
    ],
}
```
The tests can be run with [pytest](https://docs.pytest.org/en/stable/how-to/usage.html) (using [pytest-django](https://pytest-django.readthedocs.io/en/latest/#example-using-pyproject-toml)):

```shell
pytest
```

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
