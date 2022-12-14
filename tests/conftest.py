"""
This module contains shared fixtures for pytest
"""
import pytest

from .leeway.test_simulation import _teardown_test_simulation

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def celery_worker_parameters():
    """
    Increase the shutdown timeout for celery workers
    """
    return {"shutdown_timeout": 600}


@pytest.fixture
def celery_app(capsys, settings):
    """
    The fixture provoding the celery application
    """
    # pylint: disable=unused-import,import-outside-toplevel
    from celery.contrib.testing import tasks

    from opendrift_leeway_webgui.leeway.celery import app

    yield app
    # This code runs on teardown of the celery app
    _teardown_test_simulation(capsys.readouterr().out.strip(), settings)
