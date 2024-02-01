# pylint: disable=too-many-function-args
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
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np

# pylint: disable=import-error
from cartopy.mpl import gridliner
from matplotlib import ticker
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap

# pylint: disable=import-error, disable=no-name-in-module
from opendrift.models.leeway import Leeway
from opendrift.readers import reader_global_landmask

INPUTDIR = "/code/leeway/input"


# pylint: disable=too-many-locals, disable=too-many-statements
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

    # Plotting results
    lon, lat = np.array(simulation.get_lonlats())
    lon[lon == 0] = np.nan
    lat[lat == 0] = np.nan

    crs = ccrs.Mercator()  # Mercator projection to have angle true projection
    gcrs = ccrs.PlateCarree(globe=crs.globe)  # PlateCarree for straight lines

    fig = plt.figure(figsize=(8, 8))  # figsize set low to get small files
    ax = plt.axes(projection=crs)

    # base map layer
    ax.add_wms(wms="https://sgx.geodatenzentrum.de/wms_topplus_open", layers=["web"])
    # quote source: Kartendarstellung: © Bundesamt für Kartographie und Geodäsie
    # (2021), Datenquellen:
    # https://gdz.bkg.bund.de/index.php/default/wms-topplusopen-wms-topplus-open.html

    stranded=[[],[]]
    active=[[],[]]

    for i in range(lon.shape[0]):
        points = np.array([lon[i, ...], lat[i, ...]]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        lc = LineCollection(
            segments, cmap="jet", norm=plt.Normalize(0, args.duration), transform=gcrs
        )
        lc.set_array(np.linspace(0, args.duration, len(segments)))
        lc.set_linewidth(2)
        line = ax.add_collection(lc)

        nan_filter=np.isnan(lon[i])
        if any(nan_filter):
            stranded[0].append(lon[i,~nan_filter][-1])
            stranded[1].append(lat[i,~nan_filter][-1])
        else:
            active[0].append(lon[i][-1])
            active[1].append(lat[i][-1])

    # print legend for points
    initial=ax.scatter(lon[...,0],
                       lat[...,0],
                       transform=gcrs,
                       color='green',
                       zorder=args.number,
                       s=15,
                       edgecolor='black',
                       linewidth=0.5)
    initial.set_label('Initial')

    if len(stranded[0])>0:
        stranded=ax.scatter(*stranded,
                            transform=gcrs,
                            color='red',
                            zorder=args.number+1,
                            s=15,
                            edgecolor='black',
                            linewidth=0.5)
        stranded.set_label('Stranded')
    if len(active[0])>0:
        active=ax.scatter(*active,
                          transform=gcrs,
                          color='blue',
                          zorder=args.number+2,
                          s=30,
                          edgecolor='black',
                          linewidth=0.5)
        active.set_label('Active')

    ax.legend(loc="center right", bbox_to_anchor=(0, 0.5))

    # add colorbar with hours
    cbar = fig.colorbar(line, location="bottom")
    cbar.set_label("Hours")

    # set map extent
    x_max = np.nanmax(lon)
    x_min = np.nanmin(lon)
    y_max = np.nanmax(lat)
    y_min = np.nanmin(lat)

    dis_x = (x_max - x_min) * 0.02
    dis_y = (y_max - y_min) * 0.02
    extent = [
        floor_min(x_min - dis_x),
        ceil_min(x_max + dis_x),
        floor_min(y_min - dis_y),
        ceil_min(y_max + dis_y),
    ]
    ax.set_extent(extent)

    # prepare gridlines on good position
    x_step = 1 / 60  # step size for grid lines a line every minute
    x_step_div = 10  # num of zebra stripes between grid lines
    y_step = 1 / 60
    y_step_div = 10

    x_ticks = np.arange(extent[0], extent[1], x_step)
    y_ticks = np.arange(extent[2], extent[3], y_step)

    # check if too many grid lines:
    if len(x_ticks) > 100:  # a line every 5 minutes
        x_step = 1 / 12
        x_step_div = 5
        x_ticks = np.arange(extent[0], extent[1], x_step)
    if len(y_ticks) > 100:
        y_step = 1 / 12
        y_step_div = 5
        y_ticks = np.arange(extent[2], extent[3], y_step)
    if len(x_ticks) > 100:  # a line every 10 minutes
        x_step = 1 / 6
        x_step_div = 10
        x_ticks = np.arange(extent[0], extent[1], x_step)
    if len(y_ticks) > 100:
        y_step = 1 / 6
        y_step_div = 10
        y_ticks = np.arange(extent[2], extent[3], y_step)

    xloc = ticker.FixedLocator(x_ticks)
    yloc = ticker.FixedLocator(y_ticks)

    longitude_formatter = gridliner.LongitudeFormatter(dms=True, auto_hide=False)
    latitude_formatter = gridliner.LatitudeFormatter(dms=True, auto_hide=False)

    gl = ax.gridlines(
        draw_labels=True, linewidth=1, color="gray", alpha=0.5, rotate_labels=True
    )
    gl.ylocator = yloc
    gl.xlocator = xloc
    gl.xlabels_top = False
    gl.ylabels_left = False
    gl.xformatter = longitude_formatter
    gl.yformatter = latitude_formatter

    # add zebra frame
    zebra_x = np.arange(extent[0], extent[1] + x_step / x_step_div, x_step / x_step_div)
    zebra_y = np.arange(extent[2], extent[3] + y_step / y_step_div, y_step / y_step_div)

    if len(zebra_x) > 200 or len(zebra_y) > 200:
        x_step_div = 2
        zebra_x = np.arange(
            extent[0], extent[1] + x_step / x_step_div, x_step / x_step_div
        )
        y_step_div = 2
        zebra_y = np.arange(
            extent[2], extent[3] + y_step / y_step_div, y_step / y_step_div
        )

    points = np.array([zebra_x, np.zeros_like(zebra_x) + extent[2]]).T.reshape(-1, 1, 2)
    lc = get_zebra_line(points, gcrs)
    line = ax.add_collection(lc)
    points = np.array([zebra_x, np.zeros_like(zebra_x) + extent[3]]).T.reshape(-1, 1, 2)
    lc = get_zebra_line(points, gcrs)
    line = ax.add_collection(lc)
    points = np.array([np.zeros_like(zebra_y) + extent[0], zebra_y]).T.reshape(-1, 1, 2)
    lc = get_zebra_line(points, gcrs)
    line = ax.add_collection(lc)
    points = np.array([np.zeros_like(zebra_y) + extent[1], zebra_y]).T.reshape(-1, 1, 2)
    lc = get_zebra_line(points, gcrs)
    line = ax.add_collection(lc)

    start = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M")
    end = start + timedelta(hours=args.duration)

    plt.title(
        f"Leeway Simulation Object Type: {simulation.get_config('seed:object_type')}\n"
        f" From {start.strftime('%d-%m-%Y %H:%M')} to {end.strftime('%d-%m-%Y %H:%M')} UTC"
    )
    fig.text(
        0,
        0,
        "Kartendarstellung: © Bundesamt für Kartographie und Geodäsie (2021),\nDatenquellen:"
        " https://gdz.bkg.bund.de/index.php/default/wms-topplusopen-wms-topplus-open.html",
        fontsize=8,
    )

    fig.savefig(f"{outfile}.png")

    print(f"Success: {outfile}.png written.")


def floor_min(decimal):
    """
    floor funtion for arc minutes
    """
    deg = np.floor(decimal)
    minutes = (decimal - deg) * 60
    minutes = np.floor(minutes)
    return deg + (minutes / 60)


def ceil_min(decimal):
    """
    ceil fnction for arc minutes
    """
    deg = np.floor(decimal)
    minutes = (decimal - deg) * 60
    minutes = np.ceil(minutes)
    return deg + (minutes / 60)


def get_zebra_line(points, gcrs):
    """
    Define a blak/white dashed line for a map frame
    """
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    cmap = ListedColormap(["k", "w"])
    lc = LineCollection(segments, cmap=cmap, norm=plt.Normalize(0, 1), transform=gcrs)
    array = np.zeros(points.shape[0])
    array[::2] = 1
    lc.set_array(array)
    lc.set_linewidth(4)
    return lc


if __name__ == "__main__":
    main()
