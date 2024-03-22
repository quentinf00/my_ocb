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
    ),
    "_02_filter_and_merge": pb(
        qf_filter_merge_daily_ssh_tracks.run,
        input_dir="${..dl_tracks.download_dir}",
        output_path="data/prepared/${..dl_tracks.sat}.nc",
    ),
    "_03_interp_on_track": pb(
        qf_interp_grid_on_track.run,
        grid_path="${...params.study_path}",
        track_path="${..filter_and_merge.output_path}",
        output_path="data/method_outputs/${..method}_on_track.nc",
    ),
    "_04_1_lambdax": pb(
        alongtrack_lambdax.run,
        ref_path="${..filter_and_merge.output_path}",
        study_path="${..interp_on_track.output_path}",
        study_var="${..interp_on_track.grid_var}",
        output_lambdax_path="data/metrics/lambdax_${..method}.json",
        output_psd_path="data/metrics/psd_${..method}.nc",
    ),
    "_04_2_mu": pb(
        dz_alongtrack_mu.run,
        ref_path="${..filter_and_merge.output_path}",
        study_path="${..interp_on_track.output_path}",
        study_var="${..interp_on_track.grid_var}",
        output_path="data/metrics/mu_${..method}.json",
    ),
}


params = dict(method="default", study_path="data/method_outputs/${.method}.nc")
pipeline, recipe, params = qf_pipeline.register_pipeline(
        name='dc_ose_2021_alongtrack_metrics', stages=stages, params=params
)
