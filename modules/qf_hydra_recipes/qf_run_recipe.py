import logging
from typing import Any, Callable, Optional

import hydra
import hydra_zen
from omegaconf import OmegaConf
import toolz
from hydra.conf import HelpConf, HydraConf

log = logging.getLogger(__name__)

PIPELINE_DESC = "Apply sequence of configurable steps"


def run(
    inp: Optional[Any] = None,
    steps: dict[str, Callable] = None,
    params: Optional[dict] = None,
):
    log.info("Starting simple chaining with steps:")
    log.info("\n".join(sorted(steps)))
    log.debug(f"{params=}")

    if not steps:
        log.info("No steps returning input")
        return inp

    sorted_steps = sorted(steps)
    if inp is None:
        log.info("No input given, computing it from first step")
        k=sorted_steps.pop(0)
        log.info(("Running ", k))
        log.debug(("Step details ", k, steps[k]))
        inp = steps[k]()
        log.debug((k, "Input ", inp))

    for k in sorted_steps:
        log.info(("Running ", k))
        log.debug(("Step details ", k, steps[k]))
        log.debug((k, "Input ", inp))
        inp = steps[k](inp)
        log.debug((k, "Output ", inp))



run.__doc__ = f"""
Pipeline description:
    {PIPELINE_DESC}

Args:
    inp: input to pipe through the steps, if none call first step without input
    steps: dictionnary of key <-> callable that will be called in order of key

Returns:
    None
"""

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)


# Store the config
def register_recipe(name, steps, params=dict(), inp=None, default_sweep=None):
    if isinstance(params, dict):
        params = hydra_zen.make_config(**params)
    steps_store = hydra_zen.store(group="hydra_recipe", package="steps")
    params_store = hydra_zen.store(group="hydra_recipe/params", package="params")
    steps_store(steps, name=name, to_config=lambda x: x)
    params_store(params, name=name, to_config=lambda x: x)
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    _recipe = hydra_zen.make_config(
        inp=inp,
        hydra=dict(sweeper=dict(params=default_sweep)),
        hydra_defaults=['_self_', {"hydra_recipe": name,},{"hydra_recipe/params": name,}, ],
        bases=(base_config,),
    )
    store(
        _recipe,
        name="ocb_mods_" + name,
        package="_global_",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    steps_store.add_to_hydra_store(overwrite_ok=True)

    with hydra.initialize(version_base='1.3', config_path='.'):
        cfg = hydra.compose("/ocb_mods_" + name)

    recipe = hydra_zen.make_config(
        **{k: node for k,node in cfg.items()
            if k not in ('_target_', '_partial_', '_args_', '_convert_', '_recursive_')},
        bases=(base_config,),
        zen_dataclass={'cls_name': f'{"".join(x.capitalize() for x in name.lower().split("_"))}Recipe'}
    )

    # Create CLI endpoint
    api_endpoint = hydra.main(config_name="ocb_mods_" + name, version_base="1.3", config_path=".")(
        zen_endpoint
    )
    return api_endpoint, recipe, params
