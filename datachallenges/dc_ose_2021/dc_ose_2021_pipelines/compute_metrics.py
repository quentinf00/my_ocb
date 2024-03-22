import alongtrack_lambdax
import dz_alongtrack_mu
import dz_download_ssh_tracks
import hydra_zen
import qf_filter_merge_daily_ssh_tracks
import qf_interp_grid_on_track
import qf_pipeline

b = hydra_zen.make_custom_builds_fn(populate_full_signature=True)
pb = hydra_zen.make_custom_builds_fn(zen_partial=True, populate_full_signature=True)

stages = {
    "_01_dl_tracks": pb(
        dz_download_ssh_tracks.run,
        sat='${...params.sat}',
        min_time="${...params.min_time}",
        max_time="${...params.max_time}",
        download_dir="data/downloads/ref/${.sat}",
    ),
    "_02_filter_and_merge": pb(
        qf_filter_merge_daily_ssh_tracks.run,
        input_dir="${.._01_dl_tracks.download_dir}",
        output_path="data/downloads/ref/${.._01_dl_tracks.sat}.nc",
        min_lon="${...params.min_lon}",
        max_lon="${...params.max_lon}",
        min_lat="${...params.min_lat}",
        max_lat="${...params.max_lat}",
        min_time="${...params.min_time}",
        max_time="${...params.max_time}",
    ),
    "_03_interp_on_track": pb(
        qf_interp_grid_on_track.run,
        grid_path="${...params.study_path}",
        grid_var="${...params.study_var}",
        track_path="${.._02_filter_and_merge.output_path}",
        output_path="data/method_outputs/${...params.method}_on_track.nc",
    ),
    "_04_1_lambdax": pb(
        alongtrack_lambdax.run,
        ref_path="${.._02_filter_and_merge.output_path}",
        study_path="${.._03_interp_on_track.output_path}",
        study_var="${.._03_interp_on_track.grid_var}",
        output_lambdax_path="data/metrics/lambdax_${...params.method}.json",
        output_psd_path="data/metrics/psd_${...params.method}.nc",
    ),
    "_04_2_mu": pb(
        dz_alongtrack_mu.run,
        ref_path="${.._02_filter_and_merge.output_path}",
        study_path="${.._03_interp_on_track.output_path}",
        study_var="${.._03_interp_on_track.grid_var}",
        output_path="data/metrics/mu_${...params.method}.json",
    ),
}


params = dict(
    method="default",
    study_path="data/method_outputs/${.method}.nc",
    study_var="ssh",
    sat='c2',
    min_time="2017-01-01", max_time="2017-12-31",
    min_lon=-65.0, max_lon=-55.0,
    min_lat=33.0, max_lat=43.0,
)
pipeline, recipe, params = qf_pipeline.register_pipeline(
        name='dc_ose_2021_alongtrack_metrics', stages=stages, params=params
)
