"""
This module contains shared fixtures for pytest
"""

import time

import pytest
from celery.contrib.testing import tasks as _celery_testing_tasks  # noqa: F401

from opendrift_leeway_webgui.leeway.models import LeewaySimulation

from .leeway.test_simulation import _teardown_test_simulation

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="session")
def celery_includes():
    """
    Import the tasks module so the test worker has the simulation task registered
    """
    return ["opendrift_leeway_webgui.leeway.tasks"]


@pytest.fixture(scope="session")
def celery_enable_logging():
    """
    Enable Celery worker logging so output is visible in CI
    """
    return True


@pytest.fixture(scope="session")
def celery_config():
    """
    Use the real Redis broker so the test worker receives tasks submitted by the app
    """
    return {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/0",
    }


@pytest.fixture(scope="session")
def celery_worker_parameters():
    """
    Increase the shutdown timeout for celery workers and set log level to INFO
    """
    return {"shutdown_timeout": 600, "loglevel": "info"}


@pytest.fixture
def uuid_store():
    """
    A shared mutable container used to pass the simulation UUID from the test
    body to the teardown fixture without relying on stdout capture.
    """
    return []


@pytest.fixture(autouse=True)
# pylint: disable=redefined-outer-name,unused-argument
def _run_teardown(uuid_store, settings, celery_worker):
    """
    Run additional simulation checks after the test body and after the celery
    worker has finished processing, but before the worker shuts down.
    """
    yield
    if uuid_store:
        uuid = uuid_store[0]
        timeout = 120
        interval = 2
        elapsed = 0
        while elapsed < timeout:
            simulation = LeewaySimulation.objects.get(uuid=uuid)
            if simulation.simulation_finished:
                break
            time.sleep(interval)
            elapsed += interval
        _teardown_test_simulation(uuid, settings)
