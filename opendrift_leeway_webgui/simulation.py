"""
Wrapper/Helper script for Leeway simulations with OpenDrift.

Use it with the docker container by mounting a directory and copying the file to it:

docker run -it --volume /opt/leeway/opendrift_leeway_webgui/simulation-files:/code/leeway\
    --volume /opt/leeway/opendrift_leeway_webgui/simulation.py:/code/leeway/simulation.py\
    opendrift/opendrift python3 leeway/simulation.py --longitude 12.0 --latitude 34.0 --radius 1000\
    --number 100 --start-time "2023-12-03 15:14" --object-type 27 --duration 12\
    --id b22cc8d6-1235-4cfa-9c8f-2ebca101e4fb
"""

import argparse
import os
import uuid
from datetime import datetime, timedelta

# pylint: disable=import-error
from opendrift.models.leeway import Leeway
from opendrift.readers import reader_global_landmask
from sklearn.cluster import KMeans
import pandas as pd

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

    print(f"Success: {outfile}.png written.")

    lon, lat = simulation.get_lonlats()
    coordinates = list(zip(lon[:, -1], lat[:, -1]))
    plot_k_means(coordinates)

def plot_k_means(coordinates, max_distance=3000):
    """
    Calculate k-means of final distribution of particles.
    max_dinstance indicates the maximum distance of each particle from the
    center of each cluster.
    """
    distance = 9999
    k = 0
    while distance > max_distance:
        k = k + 1
        kmeans = KMeans(n_clusters=k).fit(coordinates)
        coordinates_dist = kmeans.transform(coordinates)**2
        df = pd.DataFrame(coordinates_dist.sum(axis=1).round(2), columns=['sqdist'])
        print(df.head())

if __name__ == "__main__":
    main()
