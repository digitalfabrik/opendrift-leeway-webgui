# AGENTS.md — Coding Agent Guide for `df-leeway`

## Project Overview
Web GUI for OpenDrift Leeway simulations.
**Stack:** Python 3.13+, Django 4, Celery, Redis, Docker, DRF.
**Boundaries:** Main application package is `opendrift_leeway_webgui/`.

## Critical Setup & Environment
- **Docker:** Simulations and integration tests require the custom image:
  `docker build -t opendrift-leeway-custom opendrift/`
- **Services:** Redis must be running on `localhost:6379` for Celery workers and tests.
- **Config:** Runtime config is read from `/etc/opendrift-leeway-webgui.ini`.
- **Secrets:** Local development requires the `LEEWAY_SECRET_KEY` environment variable.

## Developer Commands
- **Server:** `python3 manage.py runserver` (run from `opendrift_leeway_webgui/`)
- **Worker:** `celery -A leeway worker -l INFO`
- **Tests:** 
  - All: `pytest`
  - Faster iteration: `pytest --no-cov <file>`
  - DB tests: Use `@pytest.mark.django_db(transaction=True)`
- **Linting:** `pre-commit run --all-files` (Executes Black, isort, pylint, djlint)
- **Versioning:** `bumpver update` (Manages CalVer `YYYY.MM.INC0`)

## Hard-Earned Constraints
- **Imports:** Always use relative imports within sub-packages (e.g., `from .models import ...`).
- **Type Hints:** **Do NOT add Python type hints.** Use Sphinx-style docstrings for parameters and return types.
- **Django Views:**
  - Use Class-Based Views (CBVs).
  - `LoginRequiredMixin` MUST be the first base class for auth-protected views.
  - Document class attributes with `#:` Sphinx comments.
- **DRF API:** Compose ViewSets from mixins rather than subclassing `ModelViewSet` directly.
- **Error Handling:** Preserve exception context using `raise ... from exc`.
- **Logging:** Always define module-level loggers; never use `print()`.

## Project Layout
- `core/`: Settings, root URLs, WSGI, and global utilities.
- `leeway/`: Primary app logic, models, views, and Celery tasks.
- `api/v1/`: Versioned DRF API.
- `simulation.py`: Standalone script executed inside the Docker container.
