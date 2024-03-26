import json
import logging
from functools import partial
from pathlib import Path

import hydra
import hydra_zen
import numpy as np
import pandas as pd
import xarray as xr
from hydra.conf import HelpConf, HydraConf
from ocn_tools._src.metrics.power_spectrum import psd_welch_score
from ocn_tools._src.preprocessing.alongtrack import select_track_segments

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

PIPELINE_DESC = "Compute effective resolution lambda_x on the track geometry"


def run(
    study_path: str = "data/outputs/noisy_c2.nc",
    study_var: str = "ssh",
    ref_path: str = "data/prepared/c2.nc",
    ref_var: str = "ssh",
    delta_t: float = 0.9434,
    velocity: float = 6.77,
    length_scale: float = 1000,
    segment_overlapping: float = 0.25,
    output_lambdax_path="data/metrics/lambdax.json",
    output_psd_path="data/method_outputs/psd_score.nc",
):
    """
    TODO: doc for alongtrack_lambdax
    """
    study_da = xr.open_dataset(study_path)[study_var]
    ref_da = xr.open_dataset(ref_path)[ref_var]
    xr.testing.assert_allclose(ref_da.coords.to_dataset(), study_da.coords.to_dataset())
    eval_ds = xr.Dataset(
        dict(
            study=study_da,
            ref=ref_da,
        )
    )
    eval_ds = eval_ds.where(eval_ds.ref.pipe(np.isfinite), drop=True).interpolate_na(
        dim="time", method="nearest"
    )
    # eval_ds = eval_ds.where(eval_ds.ref.pipe(np.isfinite), drop=True)
    delta_x = velocity * delta_t

    partial_track_fn = partial(
        select_track_segments,
        variable_interp="study",
        variable="ref",
        velocity=velocity,
        delta_t=delta_t,
        length_scale=length_scale,
        segment_overlapping=segment_overlapping,
    )

    partial_score_fn = partial(
        psd_welch_score,
        variable="study",
        variable_ref="ref",
        delta_x=delta_x,
        nperseg=length_scale // delta_x,
    )

    ds, _ = eval_ds.pipe(partial_track_fn).pipe(partial_score_fn)

    ## Robust lambda_x computation when small wavelength reach score > 0.5
    max_wnx = ds.isel(wavenumber=ds.score <= 0.5).wavenumber.min().item()
    log.debug(
        f"not considering wavelength below {1/max_wnx:.2f}, psd score: {ds.sel(wavenumber=max_wnx).score:.2f}"
    )
    lambda_x = 1 / (
        ds.isel(wavenumber=ds.wavenumber <= max_wnx)
        .swap_dims(wavenumber="score")
        .interp(score=0.5)
        .wavenumber.item()
    )
    log.debug(f"Effective scale resolved (interpolated at score 0.5) {lambda_x:.2f}")

    Path(output_lambdax_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_psd_path).parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output_psd_path)
    with open(Path(output_lambdax_path), "w") as f:
        json.dump({"$\lambda_x$": lambda_x}, f)


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
