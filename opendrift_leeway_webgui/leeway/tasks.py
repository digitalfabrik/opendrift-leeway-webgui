import logging
import subprocess
from datetime import timedelta
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.utils import timezone

from .celery import app
from .utils import get_opengribs_data, send_result_mail

logger = logging.getLogger(__name__)


@app.task
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
    get_opengribs_data(simulation.longitude, simulation.latitude)
    params = [
        "docker",
        "run",
        "--volume",
        f"{settings.SIMULATION_ROOT}:/code/leeway",
        "--volume",
        f"{settings.SIMULATION_SCRIPT_PATH}:/code/leeway/simulation.py",
        "opendrift-leeway-custom:latest",
        "python3",
        "/code/leeway/simulation.py",
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
        "--no-web",
    ]
    print(" ".join(params))
    with subprocess.Popen(
        params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    ) as sim_proc:
        stdout, stderr = sim_proc.communicate()
    logger.debug("Output from simulation %s: %s", simulation.uuid, stdout)
    if stderr:
        logger.error("Error during simulation %s: %s", simulation.uuid, stderr)
        simulation.traceback = stderr.strip()
    simulation.simulation_finished = timezone.now()
    # Check if output files exist
    simulation_output = Path(settings.SIMULATION_OUTPUT)
    img_filename = f"{simulation.uuid}.png"
    if (simulation_output / img_filename).is_file():
        simulation.img.name = img_filename
    netcdf_filename = f"{simulation.uuid}.nc"
    if (simulation_output / netcdf_filename).is_file():
        simulation.netcdf.name = netcdf_filename
    simulation.save()
    send_result_mail(simulation)


@app.task
def clean_simulations():
    """
    Clean old simulations
    """
    print("Cleaning old simulation data.")
    for simulation in apps.get_model(
        app_label="leeway", model_name="LeewaySimulation"
    ).objects.filter(timezone.now() - timedelta(days=settings.SIMULATION_RETENTION)):
        print(f"Removed simulation {simulation.uuid}.")
        if simulation.img:
            simulation.img.delete()
        if simulation.netcdf:
            simulation.netcdf.delete()
        simulation.delete()
