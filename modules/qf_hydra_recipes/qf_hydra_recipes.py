from pathlib import Path
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
    _03_write_grid=pb(xr.Dataset.to_netcdf, path="${...params.input_path}"),
)

qf_grid_fn, grid_recipe = qf_run_recipe.register_recipe(name="qf_grid", steps=grid_cfg, params=params)



# CONCAT
params = dict(
    input_dir="data/prepared/inference",
    concat_dim="time",
    output_path="data/prepared/concatenated.nc",
)
concat_cfg = dict(
    _01_glob=pb(
        Path.glob,
        pattern="**/*.nc",
    ),
    _02_read=pb(map, xr.open_dataset),
    _02_concat=pb(xr.concat, dim="${...params.concat_dim}"),
    _03_write=pb(xr.Dataset.to_netcdf, path="${...params.output_path}"),
)

qf_concat_fn, concat_recipe = qf_run_recipe.register_recipe(
    name="qf_concat", steps=concat_cfg, params=params, inp="${.params.input_dir}"
)

# Get from s3
b = hydra_zen.make_custom_builds_fn()
params = dict(
    remote_path='???',
    local_path='${.remote_path}',
)

get_s3_cfg = dict(
    _01_get_s3fs=pb(
        s3fs.S3FileSystem.get,
        b(s3fs.S3FileSystem, anon=True, client_kwargs={"endpoint_url": 'https://s3.eu-central-1.wasabisys.com'}),
        rpath='${...params.remote_path}',
        lpath='${...params.remote_path}',
    )
)

qf_get_s3_fn, get_s3_recipe = qf_run_recipe.register_recipe(name="qf_s3_get", steps=get_s3_cfg, params=params)
