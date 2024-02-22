from functools import partial
import logging
import hydra_zen
import hydra
from hydra.conf import HydraConf, HelpConf
from pathlib import Path
import pandas as pd
import ocn_tools._src.geoprocessing.validation as ocnval
import xarray as xr

log = logging.getLogger(__name__)

PIPELINE_DESC = "Filter the input files with the given ranges and merge them into a single file "
## VALIDATE: Specifying input output format

def input_validation(input_dir: str): # The expected format can depend on other parameters
    """
    Folder which contains the daily netcdfs with SSH tracks from CMEMS
    Requirements:
      - input_dir points to a file
      - input_dir contains netcdf files

    """
    log.debug('Starting input validation')
    try:
        assert Path(input_dir).exists(), "input_dir points to a file"
        assert len(list(Path(input_dir).glob('**/*.nc'))) > 0, "input_dir contains netcdf files"
        log.debug('Succesfully validated input')
    except:
        log.error('Failed to validate input, continuing anyway', exc_info=1)

def output_validation(
    output_path: str,
    min_lon: float, max_lon: float,
    min_lat: float, max_lat: float,
    min_time: str, max_time: str,
): # The expected format can depend on other parameters
    """
    Single netcdf with the concatenated altimetry measurements
    Requirements:
      - output_path points to a file
      - output_path can be open with xarray
      - output_ds contain an SSH variable
      - output_ds is sorted in the time dimension
      - output_ds respect the given ranges
    """
    log.debug('Starting output validation')
    try:
        assert Path(output_path).exists(), "output_path points to a file"
        ds = xr.open_dataset(output_path)
        assert 'ssh' in ds, "output_ds contains a SSH variable"
        xr.testing.assert_equal(ds.time, ds.time.sortby('time'))
        assert ds.time.min() >= pd.to_datetime(min_time), "output_ds respect the given time range"
        assert ds.time.max() <= pd.to_datetime(max_time), "output_ds respect the given time range"
        assert ds.lat.min() >= min_lat, "output_ds respect the given lat range"
        assert ds.lat.max() <= max_lat, "output_ds respect the given lat range"
        assert ds.lon.min() >= min_lon, "output_ds respect the given lon range"
        assert ds.lon.max() <= max_lon, "output_ds respect the given lon range"
        log.debug('Succesfully validated output')
    except:
        log.error('Failed to validate output', exc_info=1)

def preprocess(
    ds,
    min_lon: float= -66, max_lon: float=-54,
    min_lat: float = 32, max_lat: float=44,
    min_time: str = '2016-12-01', max_time: str='2018-02-01',
    ):
    return (
        ds.rename(longitude='lon', latitude='lat')
        .pipe(ocnval.validate_latlon)
        .pipe(ocnval.validate_time)
        .pipe(lambda d: d.where(
            (d.lon.load() >= min_lon) & (d.lon <= max_lon)
            & (d.lat.load() >= min_lat) & (d.lat <= max_lat)
            & (d.time.load() >= pd.to_datetime(min_time)) & (d.time <= pd.to_datetime(max_time))
            , drop=True,
        ))
        .assign(ssh = lambda d: d.sla_filtered + d.mdt - d.lwe)
        .pipe(ocnval.validate_ssh)
        .sortby('time')
        [['ssh']]
    )

## PROCESS: Parameterize and implement how to go from input_files to output_files
def run(
    input_dir: str = 'data/downloads/default',
    output_path: str = 'data/prepared/default.nc',
    min_lon: float= -65, max_lon: float=-55,
    min_lat: float = 33, max_lat: float=43,
    min_time: str = '2017-01-01', max_time: str='2018-01-01',
    _skip_val: bool = False,
):
    log.info("Starting")
    if not _skip_val:
      input_validation(input_dir=input_dir)

    partial_prepro = partial(
        preprocess,
        min_lon=min_lon, max_lon=max_lon,
        min_lat=min_lat, max_lat=max_lat,
        min_time=min_time, max_time=max_time
    )
    #  Curate
    ds = xr.open_mfdataset(
        Path(input_dir).glob('**/*.nc'),
        preprocess=partial_prepro,
        concat_dim='time',
        combine='nested', chunks='auto'
    )
    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    ds.load().sortby('time').to_netcdf(output_path)

    if not _skip_val:
      output_validation(
        output_path=output_path,
        min_lon=min_lon, max_lon=max_lon,
        min_lat=min_lat, max_lat=max_lat,
        min_time=min_time, max_time=max_time
      )


## EXPOSE: document, and configure CLI
run.__doc__ = f"""
Pipeline description: 
    {PIPELINE_DESC}

Input description:
    {input_validation.__doc__}

Output description:
    {output_validation.__doc__}

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
