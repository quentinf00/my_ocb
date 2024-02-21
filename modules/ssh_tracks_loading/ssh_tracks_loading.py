import hydra_zen
import hydra
import pandas as pd
from functools import partial
from pathlib import Path
import xarray as xr
import copernicusmarine
import ocn_tools._src.geoprocessing.validation as ocnval

## Functions
def download(
       download_directory: str,
        dataset_id = f'cmems_obs-sl_glo_phy-ssh_my_c2-l3-duacs_PT1S',
        filters: list[str]= ('*201612*', '*2017*', '*201801*'),
    ):
    Path(download_directory).mkdir(parents=True, exist_ok=True)
    for filt in filters:
        copernicusmarine.get(
            dataset_id=dataset_id,
            filter=filt,
            output_directory = download_directory,
            force_download=True,
            overwrite_output_data=True,
            # sync=True, # use exit(1) and kill pipeline
        )

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

def main_api(
        sat: str='c2',
        min_lon: float= -65, max_lon: float=-55,
        min_lat: float = 33, max_lat: float=43,
        min_time: str = '2017-01-01', max_time: str='2017-12-31',
        filters=None,
        download_dir='data/downloads/${.sat}',
        output_path='data/prepared/${.sat}.nc'
):
    """
    TODO: doc for ssh_tracks_loading 
    """
    filters = filters if filters is not None else set([
        f"*{d.year}{d.month:02}*" for d in pd.date_range(min_time, max_time)]
    )
    dataset_id = f'cmems_obs-sl_glo_phy-ssh_my_{sat}-l3-duacs_PT1S'

    Path(download_dir).mkdir(exist_ok=True, parents=True)
    download(download_directory=download_dir, filters=filters, dataset_id=dataset_id)

    partial_prepro = partial(
        preprocess,
        min_lon=min_lon, max_lon=max_lon,
        min_lat=min_lat, max_lat=max_lat,
        min_time=min_time, max_time=max_time
    )
    #  Curate
    ds = xr.open_mfdataset(
        Path(download_dir).glob('**/*.nc'),
        preprocess=partial_prepro,
        concat_dim='time',
        combine='nested', chunks='auto'
    )
    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    ds.load().sortby('time').to_netcdf(output_path)



# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(main_api, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(main_api)

#Store the config
store = hydra_zen.ZenStore()
store(main_config, name='ssh_tracks_loading')
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name='ssh_tracks_loading', version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
