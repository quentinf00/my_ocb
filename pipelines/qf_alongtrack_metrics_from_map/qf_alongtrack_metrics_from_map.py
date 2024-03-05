import hydra_zen
import hydra
from hydra.conf import HydraConf, HelpConf
import alongtrack_lambdax
import dz_download_ssh_tracks
import qf_filter_merge_daily_ssh_tracks
import qf_interp_grid_on_track
import dz_alongtrack_mu
from functools import partial


b = hydra_zen.make_custom_builds_fn(populate_full_signature=True)
pb = hydra_zen.make_custom_builds_fn(zen_partial=True, populate_full_signature=True)

# /!\ il faut que les dataset d'entrée soient préparés (unités, longitude formatées)


stages =  {
    'method': 'default',
    'dl_tracks': pb(
        dz_download_ssh_tracks.run,
        filters=('*2017*',),
    ),
    'filter_and_merge': pb(
       qf_filter_merge_daily_ssh_tracks.run,
        input_dir='${..dl_tracks.download_dir}',
        output_path='data/prepared/${..dl_tracks.sat}.nc',
    ),
    'interp_on_track': pb(
        qf_interp_grid_on_track.run,
        grid_path='data/method_outputs/${..method}.nc',
        track_path='${..filter_and_merge.output_path}',
        output_path='data/method_outputs/${..method}_on_track.nc',
    ),
    'lambdax': pb(alongtrack_lambdax.main_api,
        ref_path='${..filter_and_merge.output_path}',
        study_path='${..interp_on_track.output_path}',
        study_var='${..interp_on_track.grid_var}',
        output_lambdax_path='data/metrics/lambdax_${..method}.json',
        output_psd_path='data/metrics/psd_${..method}.json',
    ),
    'mu': pb(dz_alongtrack_mu.run,
        ref_path='${..filter_and_merge.output_path}',
        study_path='${..interp_on_track.output_path}',
        study_var='${..interp_on_track.grid_var}',
        output_path='data/metrics/mu_${..method}.json',
    ),
}

def run_pipeline(
    to_run=('dl_tracks', 'filter_and_merge', 'interp_on_track', 'lambdax', 'mu'),
    stages=stages,
    ):
    for stage in to_run:
        stages[stage]()

run_pipeline.__doc__ = f"""
    Stages:
        dl_tracks:
    {dz_download_ssh_tracks.PIPELINE_DESC}
    more info with: `dz_download_ssh_tracks --help`

        filter_and_merge:
    {qf_filter_merge_daily_ssh_tracks.PIPELINE_DESC}
    more info with: `qf_filter_merge_daily_ssh_tracks --help`

        interp_on_track:
    {qf_interp_grid_on_track.PIPELINE_DESC}
    more info with: `qf_interp_grid_on_track --help`

        lambdax:
    {alongtrack_lambdax.PIPELINE_DESC}
    more info with: `alongtrack_lambdax --help`

        mu:
    {dz_alongtrack_mu.PIPELINE_DESC}
    more info with: `dz_alongtrack_mu --help`
"""

# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(run_pipeline, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run_pipeline)

#Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run_pipeline.__doc__, app_name=__name__,)))
store(main_config, name=__name__)
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=__name__, version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
