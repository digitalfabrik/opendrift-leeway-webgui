"""
Wrapper/Helper script for Leeway simulations with OpenDrift.

Use it with the docker container by mounting a directory and copying the file to it:

docker run -it --volume ./simulation:/code/leeway opendrift/opendrift python3 leeway/simulation.py\
    --longitude 11.9545 --latitude 35.2966 --start-time "2022-12-05 03:00" --duration 12
"""
import argparse
import uuid
import os

from datetime import datetime, timedelta

from opendrift.models.leeway import Leeway

from opendrift.readers import reader_netCDF_CF_generic
from opendrift.readers import reader_global_landmask

PARSER = argparse.ArgumentParser(description='Simulate drift of object')
PARSER.add_argument('--longitude',
                    help="Start longitude of the drifting object",
                    type=float)
PARSER.add_argument('--latitude',
                    help="Start latitude of the drifting object",
                    type=float)
PARSER.add_argument('--start-time',
                    help='Starting time (YYYY-MM-DD HH:MM) of the simulation. Default: Now',
                    default=datetime.now().strftime('%Y-%m-%d %H:%M'))
PARSER.add_argument('--duration',
                    help='Duration of the simulation in hours. Default: 12h.',
                    type=int,
                    default=12)
PARSER.add_argument('--object-type',
                    help=('Object type integer ID from https://github.com/OpenDrift/'
                          'opendrift/blob/master/opendrift/models/OBJECTPROP.DAT'),
                    type=int,
                    default=27)
PARSER.add_argument('--number',
                    help='Number of drifters simulated.',
                    type=int,
                    default=100)
PARSER.add_argument('--radius',
                    help=('Radius for distributing drifting particles around the start coordinates '
                          'in meters.'),
                    type=int,
                    default=1000)
PARSER.add_argument('--id',
                    help='ID used for result image name.',
                    default=str(uuid.uuid4()))
PARSER.add_argument('--no-web',
                    help='Disable fetching simulation data from web.',
                    action='store_true',
                    default=False)
ARGS = PARSER.parse_args()

SIMULATION = Leeway(loglevel=50)

SOURCES = []

INPUTDIR = "/code/leeway/input"
for data_file in os.listdir(INPUTDIR):
    if data_file.endswith(".nc"):
        SOURCES.append(os.path.join(INPUTDIR, data_file))

if not ARGS.no_web:
    SOURCES.append('https://tds.hycom.org/thredds/dodsC/GLBy0.08/latest')
    SOURCES.append(('https://pae-paha.pacioos.hawaii.edu/thredds/dodsC/'
                    'ncep_global/NCEP_Global_Atmospheric_Model_best.ncd'))

print("Using sources:\n - {}".format("\n - ".join(SOURCES)))

SIMULATION.add_readers_from_list(SOURCES,
                                 lazy=True)

READER_LANDMASK = reader_global_landmask.Reader(extent=[0, 0, 360, 90])
SIMULATION.add_reader([READER_LANDMASK])

SIMULATION.seed_elements(lon=ARGS.longitude,
                         lat=ARGS.latitude,
                         time=datetime.strptime(ARGS.start_time, '%Y-%m-%d %H:%M'),
                         number=ARGS.number, radius=ARGS.radius,
                         object_type=ARGS.object_type)

SIMULATION.run(duration=timedelta(hours=ARGS.duration), time_step=600)

OUTFILE = os.path.join("/code", "leeway", "output", ARGS.id)
SIMULATION.plot(fast=True, legend=True, filename=OUTFILE)
print("{}.png written.".format(OUTFILE))
