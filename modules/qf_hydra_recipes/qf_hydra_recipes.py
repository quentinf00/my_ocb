from pathlib import Path

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

qf_grid = qf_run_recipe.register_recipe(name="qf_grid", steps=grid_cfg, params=params)


params = dict(
    input_path="data/prepared/inference",
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

qf_concat = qf_run_recipe.register_recipe(
    name="qf_concat", steps=concat_cfg, params=params, input="${.params.input_path}"
)
