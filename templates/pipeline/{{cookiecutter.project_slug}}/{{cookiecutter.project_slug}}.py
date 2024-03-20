import logging
import hydra_zen
import hydra
from hydra.conf import HydraConf, HelpConf
from pathlib import Path

log = logging.getLogger(__name__)

PIPELINE_DESC = "{{cookiecutter.pipeline_desc}}"

## VALIDATE: Specifying input output format
stage_cfgs = dict(
)

def run_pipeline(
    to_run=('dl_tracks', 'filter_and_merge', 'interp_on_track', 'lambdax', 'mu'),
    stages=stage_cfgs,
    ):
    for stage in to_run:
        stages[stage]()


# TODO: programatically generate the docstring
run_pipeline.__doc__ = """
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
main_config = hydra_zen.builds(run_pipeline, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run_pipeline)

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
