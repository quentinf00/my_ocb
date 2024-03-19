import hydra_zen
import qf_pipeline
from dz_download_ssh_tracks import run_cfg as dl_conf
from qf_filter_merge_daily_ssh_tracks import run_cfg as filter_conf

stages = {
    "_01_fetch_inference_tracks": dl_conf(
        sat="???",
        min_time="${..min_time}",
        max_time="${..max_time}",
        download_dir="${..params.dl_dir}",
    ),
    "_02_filter_tracks": filter_conf(
        input_dir="${..params.dl_dir}",
        output_path="${..params.output_path}",
        min_lon="${..params.min_lon}",
        max_lon="${..params.max_lon}",
        min_lat="${..params.min_lat}",
        max_lat="${..params.max_lat}",
        min_time="${..params.min_time}",
        max_time="${..params.max_time}",
    ),
}


b = hydra_zen.make_custom_builds_fn(populate_full_signature=True)
params = dict(
    dl_dir="data/downloads/inference/${.sat}",
    output_path="data/prepared/inference/${.sat}.nc",
    sat=b(str.join, ",", "${.all_sats}"),
    all_sats=["alg", "h2ag", "j2g", "j2n", "j3", "s3a"],
    min_time="2016-12-01",
    max_time="2018-02-01",
    min_lon=-66.0,
    max_lon=-54.0,
    min_lat=32.0,
    max_lat=44.0,
)


inference_data_pipeline = qf_pipeline.register_pipeline(
    "dc_ose_2021/inference_data", stages=stages, params=params
)
