import logging
import json
from functools import partial
import hydra_zen
import hydra
from hydra.conf import HydraConf, HelpConf
from pathlib import Path
import numpy as np
import xarray as xr
from ocn_tools._src.preprocessing.alongtrack import select_track_segments
from ocn_tools._src.metrics.stats import nrmse_ds

log = logging.getLogger(__name__)

PIPELINE_DESC = "Compute effective resolution mu on the track geometry."


def run(
    study_path: str = 'data/outputs/noisy_c2.nc',
    study_var: str = 'ssh',
    ref_path: str = 'data/prepared/c2.nc',
    ref_var: str = 'ssh',
    dims: str = None,
    output_path: str = 'data/metrics/mu.json',
):
    log.info("Starting")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    study_da = xr.open_dataset(study_path)[study_var]
    ref_da = xr.open_dataset(ref_path)[ref_var]

    xr.testing.assert_allclose(
        ref_da.coords.to_dataset(), study_da.coords.to_dataset(),
    )

    eval_ds = (
        xr.Dataset(dict(study=study_da, ref=ref_da))
        # .where(eval_ds.ref.pipe(np.isfinite), drop=True)
        # .interpolate_na(dim='time', method='nearest')
    )

    partial_track_fn = partial(
        select_track_segments,
        variable_interp='study',
        variable='ref',
    )

    partial_score_fn = partial(
        nrmse_ds,
        target='study',
        reference='ref',
        dim='time',
    )

    mu = (
        eval_ds
        # .pipe(partial_track_fn)
        .pipe(partial_score_fn)
        .item()
    )

    log.debug(mu)

    with open(Path(output_path), 'w') as f:
        json.dump(dict(mu=mu), f)


run.__doc__ = f"""
Pipeline description:
    {PIPELINE_DESC}

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
