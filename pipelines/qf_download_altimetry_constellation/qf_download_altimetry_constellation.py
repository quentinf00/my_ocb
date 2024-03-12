import logging

import hydra
import hydra_zen
import ocn_tools._src.geoprocessing.gridding as obgrid
import toolz
import xarray as xr
from dz_download_ssh_tracks import run_cfg as dl_conf
from hydra.conf import HelpConf, HydraConf
from omegaconf import OmegaConf
from qf_filter_merge_daily_ssh_tracks import run_cfg as filter_conf
from qf_simple_chaining import chain_config, chain_store
from xarray.core.combine import combine_nested

log = logging.getLogger(__name__)

PIPELINE_DESC = "Download tracks from a satellite constellation"


# Create zen store for pipeline
store = hydra_zen.ZenStore(overwrite_ok=True)
pipe_inference_data_stages = store(group="dc_ose_2021/inference")


pipe_inference_data_stages(
    dl_conf(
        sat="???",
        min_time="${..min_time}",
        max_time="${..max_time}",
        download_dir="data/downloads/inference/${.sat}",
    ),
    name="_01_fetch_inference_tracks",
)

pipe_inference_data_stages(
    filter_conf(
        input_dir="data/downloads/inference/${.._01_fetch_inference_tracks.sat}",
        output_path="data/prepared/inference/${.._01_fetch_inference_tracks.sat}.nc",
        min_lon="${..min_lon}",
        max_lon="${..max_lon}",
        min_lat="${..min_lat}",
        max_lat="${..max_lat}",
        min_time="${..min_time}",
        max_time="${..max_time}",
    ),
    name="_02_filter_tracks",
)

combine_nested_cfg = chain_store[("ocb_mods/qf_chains", "combine_nested")]

steps = OmegaConf.merge(
    combine_nested_cfg,
    dict(
        _01_read_mf_nested_dataset=dict(
            paths="data/prepared/inference/*.nc",
        ),
        _02_write_dataset=dict(path="data/prepared/inference_combined.nc"),
    ),
)
pipe_inference_data_stages(
    hydra_zen.make_config(
        steps=steps,
        bases=(chain_config,),
    ),
    name="_03_merge_tracks",
)

stage_configs = toolz.keymap(
    lambda t: t[1], pipe_inference_data_stages["dc_ose_2021/inference"]
)

stages = dict(
    sats=["alg", "h2ag", "j2g", "j2n", "j3", "s3a"],
    min_time="2016-01-01",
    max_time="2018-02-01",
    min_lon=-66.0,
    max_lon=-54.0,
    min_lat=32.0,
    max_lat=44.0,
    **stage_configs,
)


def run(
    to_run=tuple(sorted(stage_configs)),
    stages=stages,
):
    for stage in to_run:
        stages[stage]()


go = hydra.utils.get_object
run.__doc__ = """
Stages:
""" + """
""".join(
    [
        f"""{stage}:
    {go(go(stage_configs[stage]._target_).__module__ + '.PIPELINE_DESC')}
    more info with: `{hydra.utils.get_object(stage_configs[stage]._target_).__module__} --help`
    """
        for stage in sorted(stage_configs)
    ]
)

# Create a configuration associated with the above function (cf next cell)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

# Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))
main_config = hydra_zen.builds(run, populate_full_signature=True)
store(main_config, name=__name__)
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(config_name=__name__, version_base="1.3", config_path=None)(
    zen_endpoint
)


if __name__ == "__main__":
    api_endpoint()
