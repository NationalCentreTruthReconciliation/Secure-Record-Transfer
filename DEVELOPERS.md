# For Developers

Before beginning development, please configure git to use the git hooks (`.git/hooks`) provided in the repository. This will ensure that the linting configuration is updated before each commit.

```bash
git config core.hooksPath .githooks
```

## Testing Setup

Ensure that you've installed the `dev` dependencies locally (preferably in a virtual environment):

```shell
pip install .[dev]
```

If using VSCode for development, use these settings so that tests are discovered correctly:

```json
{
    "ruff.nativeServer": "on",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.rulers": [
            99
        ]
    },
    "python.analysis.typeCheckingMode": "standard",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.analysis.extraPaths": [
        "./bagitobjecttransfer"
    ],
}
```
