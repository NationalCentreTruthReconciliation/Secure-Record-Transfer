# For Developers

The developer documentation here assumes you are using [VSCode](https://code.visualstudio.com/).

## Contributions

Follow [the NCTR's Python Style Guide](https://github.com/NationalCentreTruthReconciliation/Python-Development-Guide) when making contributions. The only difference is that the `ruff.toml` is automatically pulled when the git pre-commit hook is set up in the following section.

## Linting + Formatting

Before beginning development, please configure git to use the git hooks (`.git/hooks`) provided in the repository. This will ensure that the linting configuration is updated before each commit.

```bash
git config core.hooksPath .githooks
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

## Testing Setup

Ensure that you've installed the `dev` dependencies locally (preferably in a virtual environment):

```shell
pip install .[dev]
```

Use these settings in your [VSCode settings.json](https://code.visualstudio.com/docs/getstarted/settings#_settings-json-file) so that tests are discovered correctly in the Testing menu:

```json
{
    "python.testing.pytestEnabled": true,
    "python.analysis.extraPaths": [
        "./bagitobjecttransfer"
    ],
}
```
