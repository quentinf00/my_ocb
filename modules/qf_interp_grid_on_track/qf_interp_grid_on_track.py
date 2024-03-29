import logging
from functools import partial
from pathlib import Path

import hydra
import hydra_zen
import numpy as np
import ocn_tools._src.geoprocessing.gridding as ocngri
import ocn_tools._src.geoprocessing.validation as ocnval
import xarray as xr
from hydra.conf import HelpConf, HydraConf

log = logging.getLogger(__name__)

PIPELINE_DESC = "Interpolates the input grid data on the input alongtrack data"
## VALIDATE: Specifying input output format


def input_validation(
    grid_path: str, grid_var: str, track_path: str
):  # The expected format can depend on other parameters
    """
    grid_path is a netcdf containing a field on a regular time lat lon grid
    track path is a netcf containing alongtrack data with a time dimension
    Requirements:
    - grid_path and track_path point to files
    - grid_var is a variable of grid_ds
    - grid_path and track_path are xarray compatible
    - ssh is a variable of track_ds
    - grid_ds has (time, lat, lon) dimensions
    - track_var has (time) dimension and (lat, lon) coordinates

    """

    log.debug("Starting input validation")
    try:
        assert (
            Path(grid_path).exists() and Path(track_path).exists()
        ), "grid_path and track_path point to files"

        try:
            grid_ds, track_ds = xr.open_dataset(grid_path), xr.open_dataset(track_path)
        except Exception as e:
            raise AssertionError("grid_path and track_path are xarray compatible: {e}")

        assert grid_var in grid_ds, "grid_var is a variable of grid_ds"
        assert "ssh" in track_ds, "'ssh' is a variable of track_ds"
        assert tuple(sorted(list(grid_ds.dims))) == (
            "lat",
            "lon",
            "time",
        ), "grid_ds has (time, lat, lon) dimensions"
        assert (
            (tuple(track_ds.dims) == ("time",))
            and "lat" in track_ds.coords
            and "lon" in track_ds.coords
        ), "track_var has (time) dimension and (lat, lon) coordinates"

        log.debug("Succesfully validated input")
    except:
        log.error("Failed to validate input, continuing anyway", exc_info=1)


def output_validation(
    output_path: str, track_path
):  # The expected format can depend on other parameters
    """
    alongtrack data in a netcdf with the same shape as the input alongtrack data
    Requirements:
    - output_path points to a file
    - output_path is xarray compatible
    - output_ds has the same shape as track_path
    """
    log.debug("Starting output validation")

    try:
        assert Path(output_path).exists(), "output_path points to a file"
        try:
            output_ds, track_ds = (
                xr.open_dataset(output_path),
                xr.open_dataset(track_path),
            )
        except Exception as e:
            raise AssertionError("output_path is xarray compatible: {e}")

        (
            xr.testing.assert_equal(
                output_ds.coords.to_dataset(), track_ds.coords.to_dataset()
            ),
            "output_ds has the same shape as track_path",
        )
        log.debug("Succesfully validated output")
    except Exception as e:
        log.error("Failed to validate output", exc_info=1)


## PROCESS: Parameterize and implement how to go from input_files to output_files
def run(
    track_path: str = "???",
    grid_path: str = "???",
    grid_var: str = "???",
    output_path: str = "???",
    _skip_val: bool = False,
):
    log.info("Starting")
    if not _skip_val:
        input_validation(grid_path=grid_path, grid_var=grid_var, track_path=track_path)

    map = (
        xr.open_dataset(grid_path)
        .pipe(ocnval.validate_latlon)
        .pipe(ocnval.validate_time)
        .pipe(partial(ocnval.validate_ssh, variable=grid_var))[
            [grid_var]
        ]  # TODO validate rec ssh (add partial)
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)  # Make output directory
    ocngri.grid_to_coord_based(
        src_grid_ds=map, tgt_coord_based_ds=xr.open_dataset(track_path)
    ).to_netcdf(output_path)

    if not _skip_val:
        output_validation(output_path=output_path, track_path=track_path)


## EXPOSE: document, and configure CLI
run.__doc__ = f"""
Pipeline description: 
    {PIPELINE_DESC}

Input description:
    {input_validation.__doc__}

Output description:
    {output_validation.__doc__}

"""


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

# Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))

store(
    hydra_zen.builds(run, populate_full_signature=True),
    name=f"ocb_mods_{__name__}",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)
run_cfg = hydra_zen.builds(run, populate_full_signature=True, zen_partial=True)

store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint

api_endpoint = hydra.main(
    config_name=f"ocb_mods_{__name__}", version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == "__main__":
    api_endpoint()
