import xarray as xr
import pandas as pd
import json
from ocn_tools._src.preprocessing.alongtrack import select_track_segments
from ocn_tools._src.metrics.power_spectrum import psd_welch_score
from functools import partial
import hydra_zen
import hydra
import numpy as np
from pathlib import Path

PIPELINE_DESC = "Compute effective resolution lambda_x on the track geometry"

def main_api(
    study_path: str = 'data/outputs/noisy_c2.nc',
    study_var: str = 'ssh',
    ref_path: str = 'data/prepared/c2.nc',
    ref_var: str = 'ssh',
    delta_t: float = 0.9434,
    velocity: float = 6.77,
    length_scale: float = 1000,
    segment_overlapping: float = 0.25,
    output_lambdax_path='data/metrics/lambdax.json',
    output_psd_path='data/metrics/psd_score.json',
):
    """
    TODO: doc for alongtrack_lambdax 
    """
    study_da = xr.open_dataset(study_path)[study_var]
    ref_da = xr.open_dataset(ref_path)[ref_var]
    xr.testing.assert_allclose(ref_da.coords.to_dataset(), study_da.coords.to_dataset())
    eval_ds = xr.Dataset(dict(study=study_da, ref=ref_da,))
    eval_ds = (eval_ds
        .where(eval_ds.ref.pipe(np.isfinite), drop=True)
        .interpolate_na(dim='time', method='nearest')
    )
    # eval_ds = eval_ds.where(eval_ds.ref.pipe(np.isfinite), drop=True)
    delta_x = velocity * delta_t

    partial_track_fn = partial(
        select_track_segments,
        variable_interp='study',
        variable='ref',
        velocity=velocity,
        delta_t=delta_t,
        length_scale=length_scale,
        segment_overlapping=segment_overlapping,
    )

    partial_score_fn = partial(
        psd_welch_score,
        variable='study',
        variable_ref='ref',
        delta_x=delta_x,
        nperseg=length_scale // delta_x
    )

    ds, _ = eval_ds.pipe(partial_track_fn).pipe(partial_score_fn)

    ## Robust lambda_x computation when small wavelength reach score > 0.5
    df = ds.to_dataframe().assign(wl=lambda df: 1 / (df.index+1e-15))
    df = df.reset_index().set_index('wl')
    largest_unresolved_scale = df.loc[df.score < 0.5].index.max()
    dff = df.loc[df.index >= largest_unresolved_scale].reset_index().set_index('score')
    dff = dff.T
    dff.insert(0, 0.5, np.nan)
    dff = dff.T.sort_index()
    lambda_x = dff.wl.interpolate().loc[0.5]


    Path(output_lambdax_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_psd_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_psd_path)
    with open(Path(output_lambdax_path), 'w') as f:
        json.dump(dict(lambdax=lambda_x), f)
    

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

