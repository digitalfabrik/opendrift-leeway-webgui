import logging
import os
import subprocess
from pathlib import Path

import requests as http_requests
from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.utils import timezone

from .utils import download_and_merge, send_result_mail

logger = logging.getLogger(__name__)


@shared_task
def run_leeway_simulation(request_id):
    """
    Get parameters for simulation from database and kick off the simulation
    process in a docker container. The result is then mailed to the user.
    """
    # pylint: disable=invalid-name
    LeewaySimulation = apps.get_model(app_label="leeway", model_name="LeewaySimulation")
    simulation = LeewaySimulation.objects.get(uuid=request_id)
    simulation.simulation_started = timezone.now()
    simulation.save()
    params = [
        "docker",
        "run",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "HOME=/tmp/code/leeway",
        "-e",
        "MPLCONFIGDIR=/tmp/code/leeway/.matplotlib",
        "-e",
        f"COPERNICUSMARINE_SERVICE_USERNAME={settings.COPERNICUSMARINE_SERVICE_USERNAME}",
        "-e",
        f"COPERNICUSMARINE_SERVICE_PASSWORD={settings.COPERNICUSMARINE_SERVICE_PASSWORD}",
        "-e",
        f"COPERNICUSMARINE_USERNAME={settings.COPERNICUSMARINE_SERVICE_USERNAME}",
        "-e",
        f"COPERNICUSMARINE_PASSWORD={settings.COPERNICUSMARINE_SERVICE_PASSWORD}",
        "--volume",
        f"{settings.SIMULATION_ROOT}:/tmp/code/leeway",
        "--volume",
        f"{settings.SIMULATION_SCRIPT_PATH}:/tmp/code/leeway/simulation.py",
        "opendrift-leeway-custom:latest",
        "python3",
        "leeway/simulation.py",
        "--longitude",
        str(simulation.longitude),
        "--latitude",
        str(simulation.latitude),
        "--radius",
        str(simulation.radius),
        "--number",
        str(settings.OPENDRIFT_NUMBER_DRIFTERS),
        "--start-time",
        str(simulation.start_time.strftime("%Y-%m-%d %H:%M")),
        "--object-type",
        str(simulation.object_type),
        "--duration",
        str(simulation.duration),
        "--id",
        str(simulation.uuid),
    ]
    with subprocess.Popen(params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True) as sim_proc:
        stdout, stderr = sim_proc.communicate()
    logger.info("Output from simulation %s: %s", simulation.uuid, stdout)
    if stderr:
        logger.error("Error during simulation %s: %s", simulation.uuid, stderr)
        simulation.traceback = stderr.strip()
    simulation.simulation_finished = timezone.now()
    # Check if output files exist
    simulation_output = Path(settings.SIMULATION_OUTPUT)
    img_filename = f"{simulation.uuid}.png"
    if (simulation_output / img_filename).is_file():
        simulation.img.name = img_filename
    else:
        logger.error("Could not find simulation result.")

    geojson_filename = f"{simulation.uuid}.geojson"
    if (simulation_output / geojson_filename).is_file():
        simulation.geojson.name = geojson_filename

    netcdf_filename = f"{simulation.uuid}.nc"
    if (simulation_output / netcdf_filename).is_file():
        simulation.netcdf.name = netcdf_filename
    simulation.save()
    send_result_mail(simulation)
    # Dispatch a webhook delivery task for each of the user's configured webhooks
    for webhook in simulation.user.webhooks.all():
        deliver_webhook.apply_async([webhook.pk, str(simulation.uuid)])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deliver_webhook(self, webhook_id, simulation_uuid):
    """
    POST the simulation UUID to a user-configured webhook URL.
    Retries up to 5 times with a 60-second delay on any failure.
    """
    # pylint: disable=invalid-name
    Webhook = apps.get_model(app_label="leeway", model_name="Webhook")
    webhook = Webhook.objects.get(pk=webhook_id)
    try:
        response = http_requests.post(webhook.url, json={"uuid": simulation_uuid}, timeout=10)
        response.raise_for_status()
        logger.info(
            "Webhook %s delivered for simulation %s (HTTP %s)",
            webhook.url,
            simulation_uuid,
            response.status_code,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning(
            "Webhook %s failed for simulation %s: %s — retrying",
            webhook.url,
            simulation_uuid,
            exc,
        )
        self.retry(exc=exc)


@shared_task
def download_icon_weather_data():
    """
    Download EU ICON wind data for all forecast times.
    """
    frts = ["00", "03", "06", "09", "12", "15", "18", "21"]
    for frt in frts:
        download_and_merge(frt)
    logger.info("EU ICON weather data download completed.")
