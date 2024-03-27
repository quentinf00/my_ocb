from pathlib import Path
import toolz
import os
import s3fs
import hydra_zen
import numpy as np
import ocn_tools._src.geoprocessing.gridding as ocngrid
import pandas as pd
import xarray as xr

import qf_run_recipe

pb = hydra_zen.make_custom_builds_fn(
    zen_partial=True,
)


# GRIDDING

b = hydra_zen.make_custom_builds_fn()
params = dict(
    input_path="data/prepared/inference_combined.nc",
    grid=dict(
        time=b(pd.date_range, start="2016-12-01", end="2018-01-31", freq="1D"),
        lat=b(np.arange, start=32, stop=44, step=0.05),
        lon=b(np.arange, start=-66, stop=-54, step=0.05),
    ),
    output_path="data/prepared/gridded.nc",
)
grid_cfg = dict(
    _01_read_tracks=pb(
        xr.open_dataset,
        filename_or_obj="${...params.input_path}",
    ),
    _02_grid=pb(
        ocngrid.coord_based_to_grid,
        target_grid_ds=b(
            xr.Dataset,
            coords="${....params.grid}",
        ),
    ),
    _03_write_grid=pb(xr.Dataset.to_netcdf, path="${...params.output_path}"),
)

qf_grid_fn, grid_recipe, grid_params = qf_run_recipe.register_recipe(name="qf_grid", steps=grid_cfg, params=params)


# GRIDDING DAILY

b = hydra_zen.make_custom_builds_fn()
params = dict(
    date='',
    date_min='20161201',
    date_max='20161202',
    # date_max='20180131',
    input_dir="data/downloads/input",
    glob='**/*${.date}*.nc',
    grid=dict(
        time=[b(pd.to_datetime, arg="'${...date}'")],
        lat=b(np.arange, start=32, stop=44, step=0.05),
        lon=b(np.arange, start=-66, stop=-54, step=0.05),
    ),
    output_dir="data/prepared/gridded",
)
import glob
grid_cfg = dict(
    _01_read_tracks=pb(
        xr.open_mfdataset,
        paths=b(glob.glob, pathname= '${....params.glob}', root_dir="${....params.input_dir}", recursive=True),
        combine='nested',
        concat_dim='time'
    ),
    _02_grid=pb(
        ocngrid.coord_based_to_grid,
        target_grid_ds=b(
            xr.Dataset,
            coords="${....params.grid}",
        ),
    ),
    _03_write_grid=pb(xr.Dataset.to_netcdf, path="${...params.output_dir}/${...params.date}"),
)


import operator
sweep = {'params.date': b(toolz.pipe, b(pd.date_range, start='${params.date_min}', end='${params.date_min}'), b(operator.methodcaller, 'strftime', date_format='%Y%m%d'), pb(list))}
qf_gridday_fn, gridday_recipe, gridday_params = qf_run_recipe.register_recipe(name="qf_gridday", steps=grid_cfg, params=params, default_sweep=sweep)


# CONCAT
params = dict(
    input_dir="data/prepared/inference",
    concat_dim="time",
    output_path="data/prepared/concatenated.nc",
)
concat_cfg = dict(
    _01_glob=pb(
        Path.glob,
        b(Path, "${......params.input_dir}"),
        pattern="**/*.nc",
    ),
    _02_read=pb(map, pb(xr.open_dataset)),
    _03_concat=pb(xr.concat, dim="${...params.concat_dim}"),
    _04_write=pb(xr.Dataset.to_netcdf, path="${...params.output_path}"),
)

qf_concat_fn, concat_recipe, concat_params = qf_run_recipe.register_recipe(
    name="qf_concat", steps=concat_cfg, params=params, inp=None
)

# Get from s3
b = hydra_zen.make_custom_builds_fn()
params = dict(
    remote_path='???',
    local_path='${.remote_path}',
)

mkdir = pb(os.makedirs, name=b(os.path.dirname, p='${......params.local_path}'), exist_ok=True)
get_s3_cfg = dict(
    _01_get_s3fs=b(toolz.juxt, mkdir,
        pb(s3fs.S3FileSystem.get,
        b(s3fs.S3FileSystem, anon=True, client_kwargs={"endpoint_url": 'https://s3.eu-central-1.wasabisys.com'}),
        rpath='${.....params.remote_path}',
        lpath='${.....params.local_path}',
    ))
)

qf_get_s3_fn, get_s3_recipe, get_s3_params = qf_run_recipe.register_recipe(name="qf_s3_get", steps=get_s3_cfg, params=params)
