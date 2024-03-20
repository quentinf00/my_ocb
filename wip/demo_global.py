# %%
!qf_download_altimetry_constellation --cfg job
!python grid_chain.py --cfg job
!python my_predict.py --cfg job
# %%
!mkdir -p global/overrides
# %%
%%writefile global/overrides/dl.yaml
#@package stages
min_time: '2018-12-01'
max_time: '2020-02-01'
min_lon: -180
max_lon: 180
min_lat: -90
max_lat: 90
# %%
!qf_download_altimetry_constellation \
    'hydra.searchpath=[file://global]'\
     +overrides=dl --cfg job
# %%
!qf_download_altimetry_constellation -m \
    'hydra.searchpath=[file://global]'\
     +overrides=dl  \
    'to_run=[_01_fetch_inference_tracks]' \
     stages._01_fetch_inference_tracks.sat=j3,s3a,s3b,h2ag,h2b,c2
    #  stages._01_fetch_inference_tracks.sat=alg,h2ag,j2g,j2n,j3,s3a
# %%
!qf_download_altimetry_constellation -m \
    'hydra.searchpath=[file://global]'\
     +overrides=dl  \
    'to_run=[_02_filter_tracks]' \
     stages._01_fetch_inference_tracks.sat=j3,s3a,s3b,h2ag,h2b,c2
    #  stages._01_fetch_inference_tracks.sat=alg,h2ag,j2g,j2n,j3,s3a

# %%
for p in Path('data/prepared/inference').glob("*.nc"):
    xr.open_dataset(p) 

p
# %%


# !qf_download_altimetry_constellation 'to_run=[_03_merge_tracks]' \
#     'hydra.searchpath=[file://global]'\
#      +overrides=dl 
from pathlib import Path
import xarray as xr
tracks = xr.concat(
    [xr.open_dataset(p) for p in Path('data/prepared/inference').glob("*.nc")],
    dim='time'
)
tracks.to_netcdf('data/prepared/inference_combined.nc')
# %%
#%%
import xarray as xr
ds = xr.open_dataset('data/prepared/inference_combined.nc')
ds.close()
ds

#%%
import xarray as xr
ds = xr.open_dataset('/home/onyxia/work/data/prepared/gridded1.nc', engine='h5netcdf')
ds.close()
ds


#%%
import numpy as np
ds = xr.DataArray(np.zeros((300, 3000, 7000)))
#%%
ds.to_netcdf('1.nc')
# ds.to_netcdf('2.nc')
#%%
!python grid_chain.py --cfg job

# %%
!mkdir -p global/ocb_mods/overrides

# %%
%%writefile global/ocb_mods/overrides/grid1.yaml
#@package steps
_02_grid:
    target_grid_ds:
        coords:
            time: 
                start: '2018-12-01'
                end: '2018-12-02'
            lat:
                start: -90
                stop: 90
            lon:
                start: -180
                stop: 180
_03_write_grid:
    path: data/prepared/gridded1.nc

# %%
%%writefile global/ocb_mods/overrides/grid2.yaml
#@package steps
_02_grid:
    target_grid_ds:
        coords:
            time: 
                start: '2019-02-01'
                end: '2019-05-01'
            lat:
                start: -90
                stop: 90
            lon:
                start: -180
                stop: 180
_03_write_grid:
    path: data/prepared/gridded2.nc

# %%
%%writefile global/ocb_mods/overrides/grid3.yaml
#@package steps
_02_grid:
    target_grid_ds:
        coords:
            time: 
                start: '2019-05-01'
                end: '2019-08-01'
            lat:
                start: -90
                stop: 90
            lon:
                start: -180
                stop: 180
_03_write_grid:
    path: data/prepared/gridded3.nc

# %%
%%writefile global/ocb_mods/overrides/grid4.yaml
#@package steps
_02_grid:
    target_grid_ds:
        coords:
            time: 
                start: '2019-08-01'
                end: '2019-11-01'
            lat:
                start: -90
                stop: 90
            lon:
                start: -180
                stop: 180
_03_write_grid:
    path: data/prepared/gridded4.nc

# %%
%%writefile global/ocb_mods/overrides/grid5.yaml
#@package steps
_02_grid:
    target_grid_ds:
        coords:
            time: 
                start: '2019-11-01'
                end: '2020-02-01'
            lat:
                start: -90
                stop: 90
            lon:
                start: -180
                stop: 180
_03_write_grid:
    path: data/prepared/gridded5.nc

#%%
!python grid_chain.py \
    'hydra.searchpath=[file://global]'\
     '+overrides=grid1' --cfg job
# %%
%%time
!python grid_chain.py \
    'hydra.searchpath=[file://global]'\
     +overrides=grid1

# %%
%%time
!python grid_chain.py -m \
    'hydra.searchpath=[file://global]'\
     +overrides='grid2,grid3,grid4,grid5'
# %% 
!mkdir -p global/4dvarnet/overrides
# %%
%%writefile global/4dvarnet/overrides/strides.yaml
#@package @_global_
norm_stats: [0.46371766924858093, 0.4355253279209137]
patcher:
    strides:
        time: 1 
        lat: 120
        lon: 120

# %%
!python my_predict.py \
    'hydra.searchpath=[file://global]' \
     '+overrides=strides' \
    input_path=data/prepared/gridded.nc \
     output_dir=data/inferred_batches \
        batch_size=2 --cfg job
# %%
!python my_predict.py \
    'hydra.searchpath=[file://global]' \
     '+overrides=strides' \
    input_path=data/prepared/gridded.nc \
     output_dir=data/inferred_batches \
        batch_size=2

# %%
import xarray as xr
ds = xr.open_dataset('data/prepared/gridded.nc')
ds.close()
ds
#%%
from pathlib import Path
import numpy as np
import xarray as xr
import tqdm 
def triang(n, min=0.05):
    return np.clip(1 - np.abs(np.linspace(-1, 1, n)), min, 1.)

def hanning(n):
    import scipy
    return scipy.signal.windows.hann(n)

def bell(n, nstd=5):
    import scipy
    return scipy.signal.windows.gaussian(n, std=n/nstd)

def crop(n, crop=20):
    w = np.zeros(n)
    w[crop:-crop] = 1.
    return w

def build_weight(patch_dims, dim_weights=dict(time=triang, lat=crop, lon=crop)):
    return (
        dim_weights.get('time', np.ones)(patch_dims['time'])[:, None, None]
        * dim_weights.get('lat', np.ones)(patch_dims['lat'])[None, :, None]
        * dim_weights.get('lon', np.ones)(patch_dims['lon'])[None, None, :]
    )

def outer_add_das(das):
    out_coords = xr.merge([da.coords.to_dataset() for da in das])
    # print(f'{out_coords=}')
    fmt_das = [da.reindex_like(out_coords, fill_value=0.) for da in das]
    # print(fmt_das[0].shape)
    return sum(fmt_das)

def merge_batches(
    input_directory='data/inferred_batches',
    output_path='method_outputs/merged_batches.nc',
    weight=build_weight(patch_dims=dict(time=15, lat=240, lon=240)),
    batches_per_iter=10,
    ):
    batches = list(Path(input_directory).glob('*.nc'))
    rec = xr.open_dataset(batches.pop())
    wrec = xr.zeros_like(rec) + weight

    while batches:
        print(len(batches))
        das = [xr.open_dataset(batches.pop()) for _ in range(batches_per_iter) if batches]
        ws = [ xr.zeros_like(da) + weight for da in das]
        wdas = [ da * w for da, w in zip(das, ws)]
        rec = outer_add_das([rec, *wdas])
        wrec = outer_add_das([wrec, *ws])

    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    (rec / wrec).to_netcdf(output_path)

def better_merge_batches(
    input_directory='data/inferred_batches',
    output_path='method_outputs/merged_batches.nc',
    weight=build_weight(patch_dims=dict(time=15, lat=240, lon=240)),
    out_coord_ds='data/prepared/gridded.nc',
    out_shape=xr.open_dataarray('data/prepared/gridded.nc').shape,
    dims_labels=('time', 'lat', 'lon'),
    out_var='ssh',
):

    rec_da = xr.DataArray(
        np.zeros(out_shape), dims=dims_labels, coords=xr.open_dataarray('data/prepared/gridded.nc').coords
    )

    count_da = xr.zeros_like(rec_da)
    batches = list(Path(input_directory).glob('*.nc'))

    for b in tqdm.tqdm(batches):
        da = xr.open_dataarray(b)
        w = xr.zeros_like(da) + weight
        wda = da * w
        coords_labels = set(dims_labels).intersection(da.coords.dims)
        da_co = {c: da[c] for c in coords_labels}
        rec_da.loc[da_co] = rec_da.sel(da_co) + wda
        count_da.loc[da_co] = count_da.sel(da_co) + w

    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    return (rec_da / count_da) 
    # (rec_da / count_da).to_dataset(name=out_var).to_netcdf(output_path)

ds = better_merge_batches()
# %%
import time
import numpy as np
from global_land_mask import globe
lat = ds.lat.values
lon = ds.lon.values

# Make a grid
lon_grid, lat_grid = np.meshgrid(lon,lat)

# Get whether the points are on land using globe.is_land
start_time = time.time()
globe_ocean_mask = globe.is_ocean(lat_grid, lon_grid)
globe_run_time = time.time()-start_time
print(globe_run_time)
# %%
ds.where((ds.pipe(np.abs)<2) & globe_ocean_mask, xr.full_like(ds, np.nan)).isel(time=7).plot(figsize=(20,10))


# %%
import xarray as xr
ds = xr.open_dataarray('method_outputs/merged_batches.nc')
ds.close()
ds.isel(time=7).plot(col='time', col_wrap=2, figsize=(20,10))

#%%
import xarray as xr
obsds = xr.open_dataset('data/prepared/gridded.nc')
obsds.close()
# obsdsds.isel(time=slice(None, 4)).ssh.plot(col='time', col_wrap=2)
obsds.sel(lat=slice(33,43), lon=slice(-65,-55)).ssh.isel(time=8).plot()
# %%
from pathlib import Path
tracks = xr.concat(
    [xr.open_dataset(p) for p in Path('data/prepared/inference').glob("*.nc")],
    dim='time'
)

# %%
tracks.to_netcdf('data/prepared/inference_combined.nc')
# %%

!pip install global-land-mask


# %%
ds.to_dataset('method_outputs/merged_batches.nc')



# %%
xr.Dataset(coords=dict(
    time=b(pd.date_range, start='2016-12-01', end='2018-01-31', freq='1D'),
    lat=b(np.arange, start=32, stop=44, step=0.05),
    lon=b(np.arange, start=-66, stop=-54, step=0.05),
))