# Repository Guidelines

## Project Structure & Module Organization

This is a Django project rooted at `manage.py`. Core configuration lives in `project_dashboard/`, including `settings.py`, `urls.py`, `wsgi.py`, and middleware. Feature code is split into Django apps such as `accounts/`, `dashboard/`, `creator_project/`, `creator_subproject/`, `reporter/`, `notifications/`, `notifications_sms/`, `activity_monitor/`, `session_manager/`, and `webhooks/`. Shared page templates are in `templates/`, static assets are in `static/`, collected deployment assets are in `staticfiles/`, and uploaded files are stored under `media/`. App tests currently live in each app’s `tests.py`.

## Build, Test, and Development Commands

- `python -m venv .venv && source .venv/bin/activate`: create and activate a local virtual environment.
- `pip install -r requirements.txt`: install Django and project dependencies.
- `python manage.py migrate`: apply database migrations.
- `python manage.py runserver`: run the local development server.
- `python manage.py test`: run the Django test suite.
- `python manage.py collectstatic`: collect static assets for deployment.

Use environment variables or a local `.env` with `python-decouple` for database credentials and secrets.

## Coding Style & Naming Conventions

Follow standard Python/Django style with 4-space indentation, descriptive function names, and app-local organization (`models.py`, `views.py`, `forms.py`, `urls.py`). Use `snake_case` for Python functions, variables, template tags, and management commands; use `PascalCase` for classes and Django models. Keep templates grouped by app under `templates/<app_name>/`, and keep static CSS/JS/images in the matching `static/` subfolders. Avoid committing generated files, logs, local credentials, or one-off backup files.

## Testing Guidelines

Use Django’s built-in test runner. Add tests near the code they cover, typically in the relevant app’s `tests.py`; split into a `tests/` package only when an app grows large. Name test methods with `test_` and focus on model behavior, permissions, forms, views, and critical workflows. Run `python manage.py test <app_name>` for targeted checks before running the full suite.

## Commit & Pull Request Guidelines

Recent history uses short, imperative messages such as `update` and `create the project`; prefer more specific messages like `fix project gallery upload` or `add notification provider form`. Pull requests should include a clear summary, affected apps, migration notes, test results, linked issues, and screenshots for UI changes.

## Security & Configuration Tips

Do not hard-code production secrets, passwords, API keys, or host-specific paths. Review changes to `project_dashboard/settings.py`, deployment scripts, and database fix scripts carefully. Keep `DEBUG=False` outside local development and validate uploaded media handling when touching file or image workflows.
