# AGENTS.md — Coding Agent Guide for `df-leeway`

This file provides instructions for agentic coding tools (AI assistants, automated agents, etc.)
working in this repository.

---

## Project Overview

`opendrift-leeway-webgui` is a Django 4 web application that submits ocean drift simulations via
a Celery task queue. Simulations run inside a Docker container using the OpenDrift Leeway model.
Results are served via Django class-based views and a Django REST Framework API. There is no
JavaScript build step — the frontend is server-side rendered Django templates with static files.

**Stack:** Python 3.10+, Django 4, Celery, Redis, Docker, Django REST Framework, drf-spectacular.

---

## Environment Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install project + dev dependencies
pip install -e .[dev]

# Apply database migrations (run from opendrift_leeway_webgui/)
python3 manage.py migrate

# Build the custom OpenDrift Docker image (required for tests and simulations)
docker build -t opendrift-leeway-custom opendrift/
```

The application reads runtime config from `/etc/opendrift-leeway-webgui.ini`. For local
development, set `LEEWAY_SECRET_KEY` as an environment variable (any string works locally).

---

## Running the Application

```bash
# Django development server (run from opendrift_leeway_webgui/)
python3 manage.py runserver

# Celery worker (requires Redis running on localhost:6379)
celery -A leeway worker -l INFO
```

---

## Testing

**Prerequisites:** Redis must be running and `opendrift-leeway-custom:latest` Docker image must
exist (see setup above). The integration test runs an actual simulation via Celery.

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/leeway/test_simulation.py

# Run a single test by name
pytest tests/leeway/test_simulation.py::test_simulation

# Run with verbose output
pytest -v tests/leeway/test_simulation.py::test_simulation

# Skip coverage for faster iteration
pytest --no-cov tests/leeway/test_simulation.py
```

`DJANGO_SETTINGS_MODULE` and `LEEWAY_SECRET_KEY=dummy` are injected automatically by
`[tool.pytest.ini_options]` in `pyproject.toml` — no manual env setup needed.

Test files live under `tests/` and follow the `test_<module>.py` naming convention.
Use `@pytest.mark.django_db(transaction=True)` for tests that touch the database.

---

## Linting & Formatting

All tool config lives in `pyproject.toml`. Run the full suite via pre-commit:

```bash
# Run all pre-commit hooks against every file
pre-commit run --all-files

# Run individual tools
black .                                                    # format Python (line length 88)
isort .                                                    # sort imports
pylint opendrift_leeway_webgui                             # static analysis
djlint --lint --reformat --quiet opendrift_leeway_webgui  # lint/format Django HTML templates
```

CI runs Black, isort, djlint, and pylint as separate parallel jobs on every push and PR.
**All linting must pass before merging.**

Key formatting rules:
- **Black** line length: 88 characters (`skip-magic-trailing-comma = true`)
- **pylint** max line length: 120 characters
- **isort** `multi_line_output = 3` (vertical hanging indent, Black-compatible)

---

## Code Style Guidelines

### Import Ordering

Use `isort` conventions: stdlib → third-party → first-party → relative. Multi-line imports use
vertical hanging indent (isort `multi_line_output = 3`):

```python
import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from rest_framework import mixins

from .models import LeewaySimulation
from .utils import send_result_mail
```

Always use relative imports within sub-packages (`from .models import ...`,
`from ...leeway.models import ...`).

### Naming Conventions

| Kind | Convention | Example |
|---|---|---|
| Modules / packages | `snake_case` | `logging_formatter.py` |
| Classes | `PascalCase` | `LeewaySimulationCreateView` |
| Functions / methods | `snake_case` | `send_result_mail()` |
| Constants | `ALL_CAPS` | `LEEWAY_OBJECT_TYPES` |
| Template files | `snake_case` | `leewaysimulation_detail.html` |
| API versioning | directory-based | `api/v1/` |

### Type Annotations

The codebase does **not** use Python type hints (no mypy in the toolchain). Do not add type
annotations to existing code unless explicitly requested. For documenting parameter and return
types, use Sphinx-style docstring comments:

```python
def format(self, record):
    """
    :param record: The log record
    :type record: ~logging.LogRecord
    :rtype: str
    """
```

### Error Handling

- Use `raise ... from exc` to preserve exception context:
  ```python
  raise ValueError(f'"{value}" is not a valid bool value') from exc
  ```
- Raise `django.core.exceptions.ImproperlyConfigured` for misconfigured settings.
- Capture subprocess failures via `stderr` and persist them to the model's `traceback` field.
- Use Django form `clean_<field>()` methods for field-level validation.
- Use guard clauses / early returns in views (e.g., return `HttpResponseForbidden` before
  proceeding with destructive operations).

### Logging

Always define a module-level logger; never use `print()`:

```python
import logging

logger = logging.getLogger(__name__)
```

### Django Views

- Use **class-based views** throughout; inherit from Django generic views
  (`CreateView`, `ListView`, `DetailView`, `DeleteView`, etc.).
- Mix in `LoginRequiredMixin` as the **first** base class for auth-protected views:
  ```python
  class LeewaySimulationDeleteView(LoginRequiredMixin, DeleteView):
  ```
- Document class attributes with `#:` Sphinx docstring comments:
  ```python
  #: The model for this form view
  model = LeewaySimulation
  ```

### Django REST Framework

- Compose ViewSets from mixins rather than subclassing `ModelViewSet` directly:
  ```python
  class LeewaySimulationViewSet(
      mixins.CreateModelMixin,
      mixins.ListModelMixin,
      viewsets.GenericViewSet,
  ):
  ```
- Use `ModelSerializer` subclasses in `serializers.py`.
- API schema is auto-generated by `drf-spectacular` — keep views and serializers annotated
  enough for accurate OpenAPI output.

### Pylint Suppressions

Use inline `# pylint: disable=...` comments sparingly and only where genuinely justified.
The project enables `useless-suppression` checking, so remove suppressions that are no longer
needed.

---

## Project Layout

```
opendrift_leeway_webgui/   # Main Django project package
├── core/                  # Settings, root URLs, WSGI, utilities
├── leeway/                # Primary app: models, views, forms, tasks, Celery config
│   ├── migrations/        # Auto-generated Django migrations
│   ├── static/            # App-level static files
│   └── templates/         # Django HTML templates (djlint-formatted)
├── api/                   # DRF API
│   └── v1/                # Versioned API (serializers, views, urls)
├── simulation/            # Runtime input/output data (not committed)
└── simulation.py          # Standalone script executed inside Docker container
tests/
├── conftest.py            # Shared pytest fixtures (Celery worker setup/teardown)
└── leeway/
    └── test_simulation.py # Integration tests
```

---

## Versioning & Release

The project uses **CalVer** (`YYYY.MM.INC0`) managed by `bumpver`:

```bash
bumpver update          # bump version across pyproject.toml and source files
python3 -m build        # produce wheel + sdist for PyPI
```

PyPI publishing is automated via `.github/workflows/deployment.yml` and triggers on Git tag push.

---

## CI Overview (`.github/workflows/`)

| Workflow | Trigger | What it does |
|---|---|---|
| `linting.yml` | push / PR | Runs Black, djlint, isort, pylint as parallel jobs |
| `tests.yml` | push / PR | Starts Redis, builds Docker image, runs `pytest` on Python 3.10 & 3.11 |
| `deployment.yml` | push / tag | Builds package; publishes to PyPI on tag push |
