import xarray as xr
import hydra_zen
import hydra
from hydra.conf import HydraConf, HelpConf
import alongtrack_lambdax
import ssh_tracks_loading
import qf_interp_grid_on_track
from functools import partial

b = hydra_zen.make_custom_builds_fn(populate_full_signature=True)
pb = hydra_zen.make_custom_builds_fn(zen_partial=True, populate_full_signature=True)

# /!\ il faut que les dataset d'entrée soient préparés (unités, longitude formatées)


stages =  {
    'method': 'default',
    'dl_tracks': pb(
        ssh_tracks_loading.main_api,
        filters=('*2017*',),
    ),
    'interp_on_track': pb(
        qf_interp_grid_on_track.run,
        grid_path='data/method_outputs/${..method}.nc',
        track_path='data/prepared/${..dl_tracks.sat}.nc',
        output_path='data/method_outputs/${..method}_on_track.nc',
    ),
    'lambdax': pb(alongtrack_lambdax.main_api,
        ref_path='${..interp_on_track.track_path}',
        study_path='${..interp_on_track.output_path}',
        study_var='${..interp_on_track.grid_var}',
        output_lambdax_path='data/metrics/lambdax_${..method}.nc',
        output_psd_path='data/metrics/psd_${..method}.nc',
    ),
}

def run_pipeline(
    to_run=('dl_tracks', 'interp_on_track', 'lambdax'),
    stages=stages
    ):
    for stage in to_run:
        stages[stage]()

run_pipeline.__doc__ = f"""
    {ssh_tracks_loading.main_api.__doc__}

    {qf_interp_grid_on_track.run.__doc__}

    {alongtrack_lambdax.main_api.__doc__}
"""

# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(run_pipeline, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run_pipeline)

#Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run_pipeline.__doc__, app_name='alongtrack_lambdax_from_map',)))
store(main_config, name='alongtrack_lambdax_from_map')
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name='alongtrack_lambdax_from_map', version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
