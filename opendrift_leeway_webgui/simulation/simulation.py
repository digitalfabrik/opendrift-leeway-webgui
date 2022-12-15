"""
Wrapper/Helper script for Leeway simulations with OpenDrift.

Use it with the docker container by mounting a directory and copying the file to it:

docker run -it --volume ./simulation:/code/leeway opendrift/opendrift python3 leeway/simulation.py\
    --longitude 11.9545 --latitude 35.2966 --start-time "2022-12-05 03:00" --duration 12
"""

import argparse
import os
import uuid
from datetime import datetime, timedelta

# pylint: disable=import-error
from opendrift.models.leeway import Leeway
from opendrift.readers import reader_global_landmask

INPUTDIR = "/code/leeway/input"


def main():
    """Run opendrift leeway simulation"""
    parser = argparse.ArgumentParser(description="Simulate drift of object")
    parser.add_argument(
        "--longitude", help="Start longitude of the drifting object", type=float
    )
    parser.add_argument(
        "--latitude", help="Start latitude of the drifting object", type=float
    )
    parser.add_argument(
        "--start-time",
        help="Starting time (YYYY-MM-DD HH:MM) of the simulation. Default: Now",
        default=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    parser.add_argument(
        "--duration",
        help="Duration of the simulation in hours. Default: 12h.",
        type=int,
        default=12,
    )
    parser.add_argument(
        "--object-type",
        help=(
            "Object type integer ID from https://github.com/OpenDrift/"
            "opendrift/blob/master/opendrift/models/OBJECTPROP.DAT"
        ),
        type=int,
        default=27,
    )
    parser.add_argument(
        "--number", help="Number of drifters simulated.", type=int, default=100
    )
    parser.add_argument(
        "--radius",
        help=(
            "Radius for distributing drifting particles around the start coordinates "
            "in meters."
        ),
        type=int,
        default=1000,
    )
    parser.add_argument(
        "--id", help="ID used for result image name.", default=str(uuid.uuid4())
    )
    parser.add_argument(
        "--no-web",
        help="Disable fetching simulation data from web.",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    simulation = Leeway(loglevel=50)
    sources = [
        os.path.join(INPUTDIR, data_file)
        for data_file in os.listdir(INPUTDIR)
        if data_file.endswith(".nc")
    ]

    if not args.no_web:
        sources.extend(
            (
                "https://tds.hycom.org/thredds/dodsC/GLBy0.08/latest",
                "https://pae-paha.pacioos.hawaii.edu/thredds/dodsC/ncep_global/NCEP_Global_Atmospheric_Model_best.ncd",
            )
        )

    print("Using sources:\n - {}".format("\n - ".join(sources)))

    simulation.add_readers_from_list(sources, lazy=True)

    reader_landmask = reader_global_landmask.Reader()
    simulation.add_reader([reader_landmask])

    simulation.seed_elements(
        lon=args.longitude,
        lat=args.latitude,
        time=datetime.strptime(args.start_time, "%Y-%m-%d %H:%M"),
        number=args.number,
        radius=args.radius,
        object_type=args.object_type,
    )

    outfile = os.path.join("/code", "leeway", "output", args.id)

    simulation.run(
        duration=timedelta(hours=args.duration), time_step=600, outfile=f"{outfile}.nc"
    )
    simulation.plot(
        fast=True, legend=True, filename=f"{outfile}.png", linecolor="age_seconds"
    )
    simulation.plot(
        fast=True, legend=True, filename=f"{outfile}.jpg", linecolor="age_seconds"
    )
    print(f"Success: {outfile}.png written.")

    simulation.animation(
        background=["x_sea_water_velocity", "y_sea_water_velocity"],
        bgalpha=0.7,
        land_color="#666666",
        fast=True,
        filename=f"{outfile}-currents.mp4",
    )
    simulation.animation(
        background=["x_wind", "y_wind"],
        ocean_color="skyblue",
        land_color="burlywood",
        filename=f"{outfile}-wind.mp4",
    )


if __name__ == "__main__":
    main()
