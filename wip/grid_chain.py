from qf_simple_chaining import chain_store, zen_endpoint, chain_config

import ocn_tools._src.geoprocessing.gridding as ocngrid
import xarray as xr
import hydra_zen
import pandas as pd
import hydra
import numpy as np
from hydra.conf import HelpConf, HydraConf

pb = hydra_zen.make_custom_builds_fn(
    zen_partial=True,
)
b = hydra_zen.make_custom_builds_fn()
grid_cfg = dict(
    _01_read_tracks=pb(
        xr.open_dataset,
        filename_or_obj='data/prepared/inference_combined.nc',
    ),
     _02_grid=pb(
        ocngrid.coord_based_to_grid,
            target_grid_ds=b(
                xr.Dataset,
                coords=dict(
                    time=b(pd.date_range, start='2016-12-01', end='2018-01-31', freq='1D'),
                    lat=b(np.arange, start=32, stop=44, step=0.05),
                    lon=b(np.arange, start=-66, stop=-54, step=0.05),
                )
            )
    ),
    _03_write_grid=pb(xr.Dataset.to_netcdf, path='data/prepared/gridded.nc', engine='h5netcdf')
)
chain_store(grid_cfg, name="to_grid")
store = hydra_zen.ZenStore(overwrite_ok=True)
store(HydraConf(help=HelpConf(header="Grid coord based dataset to specified regular grid", app_name=__name__)))

store(
    hydra_zen.make_config(
        bases=(chain_config,),
        hydra_defaults=["_self_", {"/ocb_mods/qf_chains": "to_grid"}],
    ),
    name=__name__,
    group="ocb_mods",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)

store.add_to_hydra_store(overwrite_ok=True)
chain_store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name="ocb_mods/" + __name__, version_base="1.3", config_path="."
)(zen_endpoint)


if __name__ == "__main__":
    api_endpoint()
