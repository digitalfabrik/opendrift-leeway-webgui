import subprocess, sys

from datetime import datetime

from django.conf import settings

from .celery import app
from celery import shared_task
from leeway.models import LeewaySimulation

@app.task
def run_leeway_simulation(request_id):
    simulation = LeewaySimulation.objects.get(uuid=request_id)
    simulation.simulation_started = datetime.now()
    print("starting")
    simulation.save()
    params = ["docker", "run", "-it", "--volume",
              "{}:/code/leeway".format(settings.SIMULATION_PATH),
              "opendrift/opendrift",
              "python3", "leeway/simulation.py",
              "--longitude", str(simulation.longitude),
              "--latitude", str(simulation.latitude),
              "--start-time", str(simulation.start_time.strftime("%Y-%m-%d %H:%M")),
              "--duration", str(simulation.duration),
              "--id", str(simulation.uuid)]
    subprocess.Popen(params)
    simulation.simulation_finished = datetime.now()
    simulation.save()
