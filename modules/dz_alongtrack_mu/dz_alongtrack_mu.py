import json
import logging
from functools import partial
from pathlib import Path

import hydra
import hydra_zen
import numpy as np
import xarray as xr
from hydra.conf import HelpConf, HydraConf
from ocn_tools._src.metrics.stats import nrmse_ds
from ocn_tools._src.preprocessing.alongtrack import select_track_segments

log = logging.getLogger(__name__)

PIPELINE_DESC = "Compute effective resolution mu on the track geometry."


def run(
    study_path: str = "data/outputs/noisy_c2.nc",
    study_var: str = "ssh",
    ref_path: str = "data/prepared/c2.nc",
    ref_var: str = "ssh",
    output_path: str = "data/metrics/mu.json",
):
    log.info("Starting")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    study_da = xr.open_dataset(study_path)[study_var]
    ref_da = xr.open_dataset(ref_path)[ref_var]

    xr.testing.assert_allclose(
        ref_da.coords.to_dataset(),
        study_da.coords.to_dataset(),
    )

    eval_ds = (
        xr.Dataset(dict(study=study_da, ref=ref_da))
        # .where(eval_ds.ref.pipe(np.isfinite), drop=True)
        # .interpolate_na(dim='time', method='nearest')
    )


    partial_score_fn = partial(
        nrmse_ds,
        target="study",
        reference="ref",
        dim="time",
    )

    mu = (
        eval_ds
        .pipe(partial_score_fn).item()
    )

    log.info(f"Mu score: {mu}" )
    log.info(f"Writing to : {output_path}" )

    with open(Path(output_path), "w") as f:
        json.dump({"$\mu$": mu}, f)


run.__doc__ = f"""
Pipeline description:
    {PIPELINE_DESC}

Returns:
    None
"""


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

# Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))

store(
    hydra_zen.builds(run, populate_full_signature=True),
    name=f"ocb_mods_{__name__}",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)
run_cfg = hydra_zen.builds(run, populate_full_signature=True, zen_partial=True)

store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=f"ocb_mods_{__name__}", version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == "__main__":
    api_endpoint()
