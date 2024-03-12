import logging
from pathlib import Path

import copernicusmarine
import hydra
import hydra_zen
import pandas as pd
from hydra.conf import HelpConf, HydraConf

log = logging.getLogger(__name__)

PIPELINE_DESC = "Download the SSH reprocessed tracks of a given satellite from copernicus marine store (requires cmems credentials)"


def output_validation(
    download_dir: str,
):  # The expected format can depend on other parameters
    """
    Daily netcdf ordered by folder with for a given satellite
    Requirements:
      - download_dir points to a directory
      - download_dir contains netcdf files
    """
    log.debug("Starting output validation")
    try:
        assert Path(download_dir).exists(), "download_dir points to a directory"
        assert (
            len(list(Path(download_dir).glob("**/*.nc"))) > 0
        ), "download_dir contains netcdf files"
        log.debug("Succesfully validated output")
    except:
        log.error("Failed to validate output", exc_info=1)


## PROCESS: Parameterize and implement how to go from input_files to output_files
def run(
    sat: str = "c2",
    download_dir: str = "data/downloads/${.sat}",
    min_time: str = "2017-01-01",
    max_time: str = "2017-12-31",
    regex: str = None,
    _skip_val: bool = False,
):
    log.info("Starting")

    regex = (
        regex
        if regex is not None
        else "("
        + "|".join(
            list(
                set(
                    [
                        f"*{d.year}{d.month:02}*"
                        for d in pd.date_range(min_time, max_time)
                    ]
                )
            )
        )
        + ")"
    )

    dataset_id = f"cmems_obs-sl_glo_phy-ssh_my_{sat}-l3-duacs_PT1S"

    Path(download_dir).mkdir(exist_ok=True, parents=True)
    copernicusmarine.get(
        dataset_id=dataset_id,
        regex=regex,
        output_directory=download_dir,
        force_download=True,
        overwrite_output_data=True,
        # sync=True, # use exit(1) and kill pipeline
    )

    if not _skip_val:
        output_validation(download_dir=download_dir)


## EXPOSE: document, and configure CLI
run.__doc__ = f"""
 {PIPELINE_DESC}
To specify the files to be downloaded, two options:
- specify min_time and max_time parameters and the months encompassing the period
will be downloaded
- specify a list of filters in the form "*YYYY*" or "*YYYYMM*" or "*YYYYMMDD*" to
have more fine grained control

Pipeline description: 
    {PIPELINE_DESC}

Input description: None
    

Output description:
    {output_validation.__doc__}

Returns:
    None
"""


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

# Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))

store(
    hydra_zen.builds(run, populate_full_signature=True),
    name=__name__,
    group="ocb_mods",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)
run_cfg = hydra_zen.builds(run, populate_full_signature=True, zen_partial=True)

store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=f"ocb_mods/{__name__}", version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == "__main__":
    api_endpoint()
