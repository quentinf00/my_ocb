import logging
from pathlib import Path
from typing import Any, Callable, Optional

import hydra
import hydra_zen
import toolz
import xarray as xr
from hydra.conf import HelpConf, HydraConf

log = logging.getLogger(__name__)

PIPELINE_DESC = "Apply sequence of configurable steps"


def run(
    inp: Optional = None,
    steps: dict[str, Callable] = dict(),
):
    log.info("Starting simple chaining with steps:")
    log.info("\n".join(sorted(steps)))

    if not steps:
        log.info("No steps returning input")
        return inp

    sorted_steps = sorted(steps)
    if inp is None:
        log.info("No input given, computing it from first step")
        inp = steps[sorted_steps.pop(0)]()
    toolz.compose_left(*(steps[k] for k in sorted_steps))(inp)


run.__doc__ = f"""
Pipeline description: 
    {PIPELINE_DESC}

Args:
    inp: input to pipe through the steps, if none call first step without input
    steps: dictionnary of key <-> callable that will be called in order of key

Returns:
    None
"""


chain_config = hydra_zen.make_config(
    steps=dict(), zen_dataclass=dict(cls_name="BaseQfChain")
)

chain_store = hydra_zen.store(group="ocb_mods/qf_chains", package="steps")

chain_store(
    hydra_zen.make_config(zen_dataclass=dict(cls_name="NoOpChain")),
    name="noop",
)


pb = hydra_zen.make_custom_builds_fn(
    zen_partial=True,
)
chain_store(
    hydra_zen.make_config(
        _01_read_mf_nested_dataset=pb(
            xr.open_mfdataset,
            paths="data/prepared/inference/*.nc",
            combine="nested",
        ),
        _02_write_dataset=pb(
            xr.Dataset.to_netcdf, path="data/prepared/inference_combined.nc"
        ),
        zen_dataclass=dict(cls_name="CombineNestedChain"),
    ),
    name="combine_nested",
)
# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)
# Store the config
store = hydra_zen.store()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))

chain_config = hydra_zen.builds(
    run,
    populate_full_signature=True,
    zen_partial=True,
    zen_dataclass=dict(cls_name="BaseChain"),
)

store(
    hydra_zen.make_config(
        bases=(chain_config,),
        hydra_defaults=["_self_", {"/ocb_mods/qf_chains": "noop"}],
    ),
    name=__name__,
    group="ocb_mods",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)

store.add_to_hydra_store(overwrite_ok=True)
chain_store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name="ocb_mods/" + __name__, version_base="1.3", config_path="."
)(zen_endpoint)


if __name__ == "__main__":
    api_endpoint()
