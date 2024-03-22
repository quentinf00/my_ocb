import hydra_zen
import operator
import toolz
import qf_pipeline
from dz_download_ssh_tracks import run_cfg as dl_conf
from qf_filter_merge_daily_ssh_tracks import run_cfg as filter_conf

stages = {
    "_01_fetch_inference_tracks": dl_conf(
        sat='${...params.sweep}',
        min_time="${...params.min_time}",
        max_time="${...params.max_time}",
        download_dir="${...params.dl_dir}/${.sat}",
    ),
    "_02_filter_tracks": filter_conf(
        input_dir="${...params.dl_dir}",
        output_path="${...params.output_dir}/${.._01_fetch_inference_tracks.sat}.nc",
        min_lon="${...params.min_lon}",
        max_lon="${...params.max_lon}",
        min_lat="${...params.min_lat}",
        max_lat="${...params.max_lat}",
        min_time="${...params.min_time}",
        max_time="${...params.max_time}",
    ),
}


b = hydra_zen.make_custom_builds_fn(populate_full_signature=True)
params = dict(
    sweep=None,
    sat_list=["alg", "h2ag", "j2g", "j2n", "j3", "s3a"],
    dl_dir="data/downloads/input",
    output_dir="data/prepared/input",
    min_time="2016-12-01",
    max_time="2018-02-01",
    min_lon=-66.0,
    max_lon=-54.0,
    min_lat=32.0,
    max_lat=44.0,
)

sweep = {'params.sweep': dict(_target_="builtins.str.join", _args_=[',', "${params.sat_list}"])}

pipeline, recipe, params = qf_pipeline.register_pipeline(
    "dc_ose_2021_inference_data", stages=stages, params=params, default_sweep=sweep
)
