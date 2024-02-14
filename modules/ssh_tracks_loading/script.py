from pathlib import Path
import xarray as xr
import pandas as pd
import ocn_tools._src.geoprocessing.validation as ocnval
import copernicusmarine

def download(
       download_directory: str,
        dataset_id = f'cmems_obs-sl_glo_phy-ssh_my_c2-l3-duacs_PT1S',
        filters: list[str]= ('*201612*', '*2017*', '*201801*'),
    ):
    for filt in filters:
        copernicusmarine.get(
            dataset_id=dataset_id,
            filter=filt,
            output_directory = download_directory,
            force_download=True
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
        [['ssh']]
    )

if __name__ == '__main__':
    #  Download
    download(download_directory="data/downloads/c2")

    #  Curate
    ds = xr.open_mfdataset(
        Path("data/downloads/c2").glob('**/*.nc'),
        preprocess=preprocess,
        concat_dim='time',
        combine='nested', chunks='auto'
    )
    Path("data/prepared/c2.nc").parent.mkdir(exist_ok=True, parents=True)
    ds.to_netcdf("data/prepared/c2.nc")
