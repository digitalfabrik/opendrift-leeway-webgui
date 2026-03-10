"""
Download ICON EU 10m wind data (U/V components) from DWD OpenData,
unpack bz2 GRIB2 files in parallel, and merge into a single NetCDF file
compatible with OpenDrift's GenericModelReader.

Requirements:
    pip install requests cfgrib xarray netCDF4 eccodes
    (eccodes must also be installed system-wide: apt install libeccodes-dev
     or conda install -c conda-forge eccodes)
"""
import os
import bz2
import re
import argparse
import tempfile
import json
import requests

import numpy as np
import xarray as xr

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# ──────────────────────────────── Helpers ─────────────────────────────────── #

def list_bz2_files(url: str) -> list[str]:
    """Fetch the DWD directory listing and return all sorted .bz2 filenames."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    files = re.findall(r'href="([^"]+\.bz2)"', resp.text)
    return sorted(set(files))


def download_and_decompress(url: str, dest_path: Path) -> Path:
    """Download a .bz2 file, decompress it in-memory, write GRIB2 to *dest_path*.

    Returns *dest_path* on success so futures can report it easily.
    Raises on any HTTP or decompression error.
    """
    resp = requests.get(url, timeout=120, stream=True)
    resp.raise_for_status()
    dest_path.write_bytes(bz2.decompress(resp.content))
    return dest_path


def parallel_download(tasks: list[tuple[str, Path]], max_workers:int) -> list[Path]:
    """Download and decompress *tasks* = [(url, dest_path), …] in parallel.

    Uses a ThreadPoolExecutor with MAX_WORKERS threads. Progress is printed
    as each file completes (thread-safe). Returns a sorted list of paths.
    Raises RuntimeError if any download fails.
    """
    completed = 0
    results: list[Path] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_and_decompress, url, dest): url
            for url, dest in tasks
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            fname = url.split("/")[-1]
            try:
                path = future.result()
                results.append(path)
                completed += 1
            except Exception as exc:
                errors.append(fname)

    if errors:
        raise RuntimeError(
            f"{len(errors)} download(s) failed:\n  " + "\n  ".join(errors)
        )

    return sorted(results)


def rename_for_opendrift(ds: xr.Dataset) -> xr.Dataset:
    """Rename variables/coordinates so OpenDrift's GenericModelReader
    can auto-detect them.

    OpenDrift expects:
        x_wind / y_wind  (CF standard_name)
        longitude / latitude
        time
    """

    # CF standard_name attributes

    ds = ds.rename({"valid_time": "time"})
    
    ds["u10"].attrs.update({
        "standard_name": "x_wind",
        "units": "m s-1",
        "long_name": "10 metre U wind component",
    })

    ds["v10"].attrs.update({
        "standard_name": "y_wind",
        "units": "m s-1",
        "long_name": "10 metre V wind component",
    })

    ds.attrs.update({
        "Conventions": "CF-1.7",
        "title": "ICON-EU 10 m wind – DWD OpenData",
        "source": "https://opendata.dwd.de/weather/nwp/icon-eu/",
    })

    return ds

def merge_netCDF(big_file:str, new_ds, cutoff_hours=None):
    big_ds = xr.open_dataset(big_file)

    # Remove overlapping times from big_ds
    ds1_no_overlap = big_ds.sel(time=~big_ds.time.isin(new_ds.time))

    # Concatenate along time
    big_ds = xr.concat([ds1_no_overlap, new_ds], dim="time")
    big_ds = big_ds.sortby("time")

    now = np.datetime64("now")
    cutoff_time = now - np.timedelta64(cutoff_hours, "h")

    big_ds = big_ds.sel(time=big_ds.time >= cutoff_time)
    big_ds.to_netcdf(f"{big_file}.PART")
    os.remove(big_file)
    os.rename(f"{big_file}.PART", big_file)

def load_previous_downloads(file: str):
    if os.path.exists(file):
        with open(file, "r") as f:
            last_downloads = json.load(f)
    else:
        last_downloads={''
        '00':[],
        '03':[],
        '06':[],
        '09':[],
        '12':[],
        '15':[],
        '18':[],
        '21':[]
        }
    return last_downloads


# ────────────────────────────────── Main ─────────────────────────────────── #

def download_and_merge(last_downloads_file, max_workers : int, output_file : str = None, cutoff_hours : int = 120):

    last_downloads = load_previous_downloads(last_downloads_file)
        
    for frt in last_downloads.keys(): #frt = forecast time
        print(f"looking up {frt}")
        BASE_URL_U = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{frt}/u_10m/"
        BASE_URL_V = f"https://opendata.dwd.de/weather/nwp/icon-eu/grib/{frt}/v_10m/"

        # Download and merge U and V components
        print("Listing available files …")
        u_files = list_bz2_files(BASE_URL_U)
        v_files = list_bz2_files(BASE_URL_V)

        if u_files is None or v_files is None:
            print("No files found.")
            continue

        if sorted([*u_files,*v_files]) == last_downloads[frt]:
            print(f"{frt} already downloaded.")
            continue
        
        last_downloads[frt] = sorted([*u_files,*v_files])

        print(f"  U files: {len(u_files)}   V files: {len(v_files)}")
        print(f"\nDownloading in parallel with {max_workers} workers")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            # Build task lists: (url, destination_path)
            u_tasks = [(BASE_URL_U + f, tmp / f.replace(".bz2", "")) for f in u_files]
            v_tasks = [(BASE_URL_V + f, tmp / f.replace(".bz2", "")) for f in v_files]

            u_gribs = parallel_download( u_tasks, max_workers=max_workers)
            v_gribs = parallel_download( v_tasks, max_workers=max_workers)

            print("\nLoading GRIB2 files into xarray …")
            ds_u = xr.open_mfdataset(
                u_gribs,
                engine="cfgrib",
                combine="nested",
                concat_dim="valid_time",
                coords='different',
                compat='no_conflicts',
                join="outer",
                parallel=True,
                backend_kwargs={"errors": "ignore"},
            )
            ds_v = xr.open_mfdataset(
                v_gribs,
                engine="cfgrib",
                combine="nested",
                concat_dim="valid_time",
                coords='different',
                compat='no_conflicts',
                join="outer",
                parallel=True,
                backend_kwargs={"errors": "ignore"},
            )

            # Drop scalar coords that differ between timesteps to avoid merge conflicts
            keep = {"valid_time", "latitude", "longitude"}
            ds_u = ds_u.drop_vars([c for c in ds_u.coords if c not in keep], errors="ignore")
            ds_v = ds_v.drop_vars([c for c in ds_v.coords if c not in keep], errors="ignore")

            ds = xr.merge([ds_u, ds_v],join="outer")

            print("\nRenaming variables for OpenDrift compatibility …")
            ds = rename_for_opendrift(ds)

            if output_file:
                if os.path.exists(output_file):
                    merge_netCDF(output_file, ds, cutoff_hours)
                else:
                    ds.to_netcdf(output_file)
                with open(last_downloads_file, "w") as f:
                    json.dump(last_downloads, f)
            print("exiting temp file.")
    print("\nDone.")



if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Download ICON-EU 10 m wind from DWD OpenData",
    )

    arg_parser.add_argument(
        "--max_workers",
        type=int,
        default=8,
        help="Number of parallel download workers",
    )

    arg_parser.add_argument(
        "--output",
        type=str,
        default='ICON_EU_120.nc',   
        help="Existing netCDF file",
    )

    arg_parser.add_argument(
        "--last_downloads",
        type=str,
        default="last_downloads.json",
        help="Last downloaded files",
    )

    arg_parser.add_argument(
        "--cutoff_hours",
        type=int,
        default=120,
        help="data that is older than cutoff hours will be deleted",
    )
    
    args = arg_parser.parse_args()

    download_and_merge(max_workers=args.max_workers,
                        output_file=args.output,
                        last_downloads_file=args.last_downloads,
                        cutoff_hours=args.cutoff_hours)