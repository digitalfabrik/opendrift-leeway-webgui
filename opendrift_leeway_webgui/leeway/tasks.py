import os
import subprocess
from datetime import datetime, timedelta

from celery import shared_task
from django.apps import apps
from django.conf import settings

from .celery import app
from .utils import send_result_mail


@app.task
def run_leeway_simulation(request_id):
    """
    Get parameters for simulation from database and kick off the simulation
    process in a docker container. The result is then mailed to the user.
    """
    LeewaySimulation = apps.get_model(app_label="leeway", model_name="LeewaySimulation")
    simulation = LeewaySimulation.objects.get(uuid=request_id)
    simulation.simulation_started = datetime.now()
    simulation.save()
    params = [
        "docker",
        "run",
        "--volume",
        "{}:/code/leeway".format(settings.SIMULATION_ROOT),
        "opendrift/opendrift",
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
        "--duration",
        str(simulation.duration),
        "--id",
        str(simulation.uuid),
    ]
    sim_proc = subprocess.Popen(params)
    sim_proc.communicate()
    simulation.simulation_finished = datetime.now()
    send_result_mail(simulation)
    simulation.save()


@app.task
def clean_simulations():
    """
    Clean old simulations
    """
    print("Cleaing old simulation data.")
    for simulation in apps.get_model(
        app_label="leeway", model_name="LeewaySimulation"
    ).objects.filter(datetime.now() - timedelta(days=settings.SIMULATION_RETENTION)):
        os.remove(os.path.join(settings.SIMULATION_OUTPUT, f"{simulation.uuid}.png"))
        os.remove(os.path.join(settings.SIMULATION_OUTPUT, f"{simulation.uuid}.csv"))
        print("Removed simulation {}.".format(simulation.uuid))
        simulation.delete()
