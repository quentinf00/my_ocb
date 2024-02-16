import logging
import hydra_zen
import hydra
from hydra import HydraConf, HelpConf
from pathlib import Path
import xarray as xr
import numpy as np
import ocn_tools._src.geoprocessing.validation as ocnval
import ocn_tools._src.geoprocessing.gridding as ocngri

log = logging.getLogger(__name__)


## VALIDATE: Specifying input output format

def input_validation(grid_path: str, grid_var: str, track_path: str): # The expected format can depend on other parameters
    """
    grid_path is a netcdf containing a field on a regular time lat lon grid
    track path is a netcf containing alongtrack data with a time dimension
    Requirements: 
    - grid_path and track_path point to files
    - grid_var is a variable of grid_ds
    - grid_path and track_path are xarray compatible
    - ssh is a variable of track_ds
    - track ssh does not contain NaN
    - grid_ds has (time, lat, lon) dimensions
    - track_var has (time) dimension and (lat, lon) coordinates

    """ 

    log.debug('Starting input validation')
    try:
        assert Path(grid_path).exists() and Path(track_path).exists(), "grid_path and track_path point to files"

        try:
            grid_ds, track_ds = xr.open_dataset(grid_path), xr.open_dataset(track_path)
        except Exception as e:
            raise AssertionError("grid_path and track_path are xarray compatible: {e}")

        assert grid_var in grid_ds, "grid_var is a variable of grid_ds"
        assert 'ssh' in track_ds, "'ssh' is a variable of track_ds"
        assert track_ds['ssh'].pipe(np.isnan).sum().item() == 0, "track ssh does not contain NaN"
        assert tuple(sorted(list(grid_ds.dims))) == ('lat', 'lon', 'time'), "grid_ds has (time, lat, lon) dimensions"
        assert (track_ds.dims == ('time',)) and 'lat' in track_ds.coords and "lon" in track_ds.coords, "track_var has (time) dimension and (lat, lon) coordinates"

        log.debug('Succesfully validated input')
    except:
        log.error('Failed to validate input, continuing anyway', exc_info=1)

def output_validation(output_path: str, track_path): # The expected format can depend on other parameters
    """
    alongtrack data in a netcdf with the same shape as the input alongtrack data
    Requirements:
    - output_path points to a file
    - output_path is xarray compatible
    - output_ds has the same shape as track_path
    """
    log.debug('Starting output validation')

    try:
        assert Path(output_path).exists(), "output_path points to a file"
        try:
            output_ds, track_ds = xr.open_dataset(output_path), xr.open_dataset(track_path)
        except Exception as e:
            raise AssertionError("output_path is xarray compatible: {e}")

        assert xr.testing.assert_equal(output_ds.coords.to_dataset(), track_ds.coords.to_dataset()), "output_ds has the same shape as track_path"
        log.debug('Succesfully validated output')
    except Exception as e:
        log.error('Failed to validate output', exc_info=1)


## PROCESS: Parameterize and implement how to go from input_files to output_files
def run(
    track_path: str = '???',
    grid_path: str = '???',
    grid_var: str = '???',
    output_path: str = '???',
    _skip_val: bool = False,
):
    log.info("Starting")
    if not _skip_val:
     input_validation(grid_path=grid_path, grid_var=grid_var, track_path=track_path)

    map = (
        xr.open_dataset(grid_path)
        .pipe(ocnval.validate_latlon)
        .pipe(ocnval.validate_time)
        .pipe(ocnval.validate_ssh) # TODO validate rec ssh (add partial) 
        [[grid_var]] 
        
    )
    ocngri.grid_to_coord_based(
        src_grid_ds=map,
        tgt_coord_based_ds=xr.open_dataset(track_path)
    ).interpolate_na(dim='time', method='nearest').to_netcdf(output_path)

    Path(output_path).mkdir(parents=True, exist_ok=True) # Make output directory

    if not _skip_val:
      output_validation(output_path=output_path)


## EXPOSE: document, and configure CLI
run.__doc__ = f"""
    Interpolates the input grid data on the input alongtrack data

    Args:
        input_path: {input_validation.__doc__}
        output_path: {output_validation.__doc__}

    Returns:
        None
"""
# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(run, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

#Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))
store(main_config, name=__name__)
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=__name__, version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
