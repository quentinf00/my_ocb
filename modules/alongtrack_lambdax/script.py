import xarray as xr
from ocn_tools._src.preprocessing.alongtrack import select_track_segments
from ocn_tools._src.metrics.power_spectrum import psd_welch_score
from functools import partial

study_path = 'data/outputs/noisy_c2.nc'
study_var = 'ssh'
ref_path = 'data/prepared/c2.nc'
ref_var = 'ssh'
delta_t = 0.9434
velocity = 6.77
length_scale = 1000
segment_overlapping = 0.25

if __name__ == '__main__':
    # Validate study format
    study_da = xr.open_dataset(study_path)[study_var]
    ref_da = xr.open_dataset(ref_path)[ref_var]
    assert study_da.dims == ref_da.dims
    assert study_da.size == ref_da.size
    eval_ds = xr.Dataset(dict(study=study_da, ref=ref_da,))
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

    ds, lambda_x = eval_ds.pipe(partial_track_fn).pipe(partial_score_fn)
    print(lambda_x)
    print(ds)
