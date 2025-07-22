# Secure Record Transfer Application

[AGENT.md](https://ampcode.com/AGENT.md) is for AI agents to understand this codebase. Human dvelopers can reference [DEVELOPERS.md](/DEVELOPERS.md) instead.

The Secure Record Transfer App is a full-stack web application built with Django for Archives to receive to digital donations of files. Form data is captured by donors in a way that complies with the Canadian Archival Accession Information Standard (CAAIS) version 1.0.

The documentation is stored in `docs/`, and the code is stored in `app/`. The models that adhere to the CAAIS standard are stored in `app/caais`. The bulk of the application is in `app/recordtransfer`.

We use Docker to build and test this application. The services for this application are defined in `compose.dev.yml` and `compose.prod.yml` for the development and production version of the app, respectively. `Containerfile` is the multi-stage Docker build file for this app.

Asynchronous jobs are run by RQ, which uses Redis as a message broker.

## Build & Commands

- If on WSL, use `/usr/bin/docker` instead of `docker`
- Run unit tests locally: `uv run pytest -k unit`
- Run end-to-end tests locally: `uv run pytest -k e2e`
- Build static resources locally (for testing Webpack config): `npm run build`
- Start the dev app: `docker compose -f compose.dev.yml up -d --build --remove-orphans`
- Start the prod app: `docker compose -f compose.prod.yml up -d --build --remove-orphans`
- Build static resources in dev app: `docker compose -f compose.dev.yml exec app npm run build`
- Watch and re-build static resources in dev app: `docker compose -f compose.dev.yml exec app npm run watch`
- Build docs: `uv run sphinx-build docs docs/_build`
- Start local web server on port 8001 for docs: `uv run python -m http.server -d docs/_build 8001`
- Reset the development database: `docker compose -f compose.dev.yml exec app python manage.py reset`
- Reset the development database and populate with seed data: `docker compose -f compose.dev.yml exec app python manage.py reset --seed`

### Development Environment

- Frontend dev server: http://localhost:8000
- Mailpit email interceptor: http://localhost:8025
- pydebug port is open on port 8009 for the app
- pydebug port is open on port 8010 for the rq workers

## Dependencies

- Python: use `uv` for dependency management.
- Python: production-only dependencies should go in the `prod` optional dependencies.
- Python: developer-only dependencies should go in the `dev` optional dependencies.
- Python: sync dependencies for local development: `uv sync --extra dev`
- NodeJS: use `npm` for dependency management.
- NodeJS: sync dependencies for local development: `npm install --include=dev`

## Code Style

- For Python, see `ruff.toml` for linting rules
- For Django HTML templates, see `djlint.toml` for linting rules
- For Javascript, see `eslint.config.mjs` for linting rules

## Testing

- Unit tests are written with unittest
- E2E tests are written for Selenium
- All tests use pytest as the test runner. The pytest config is in `pyproject.toml`

## Architecture

- Frontend: Django templates with HTMX
- Backend: Django
- Database: MySQL in production, SQLite in development
- Styling: Tailwind CSS + DaisyUI
- Static bundler: Webpack
- Package managers: uv, npm

## Security

- Use appropriate data types that limit exposure of sensitive information
- Never commit secrets or API keys to repository
- Validate all user inputs on both client and server
- Regular dependency updates
- Follow principle of least privilege

## Configuration

- Settings that are safe to change by an admin while the site is running can go in the `SiteSetting` model in `app/recordtransfer/models.py`
- The `SiteSetting` model class in `recordtransfer` has detailed information on how to add new runtime-configurable settings
- Settings that are safe to change during runtime should be documented in `docs/admin_guide/site_settings.rst`
- Settings that are not safe to change during runtime should go in `app/app/settings`
- Settings that are not safe to change during runtime should be documented in `docs/settings/index.rst`
- Prefer settings that can be changed during runtime
- Add sample required dependencies that cannot be changed during runtime to `example.prod.env`
- The dev configuration should work without any config options (zero-config)

## Git Workflow

- Run `npm run lint` before committing any changes to JS files, and fix linting errors before continuing
- Run `uv run ruff check <FILE_PATH>` before commiting changes to Python files, and fix linting errors before continuing
- If there are fixable errors from `ruff`, run `uv run ruff format <FILE_PATH>` to fix the errors
- Run `uv run djlint --check --lint <FILE_PATH>` before committing any changes to HTML files, and fix linting errors before continuing
- Never use `git push --force`
