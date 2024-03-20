import logging
from typing import Any, Callable, Optional

import hydra
import hydra_zen
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

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)


# Store the config
def register_recipe(name, steps, params=dict(), input=None):
    steps_store = hydra_zen.store(group="ocb_mods/hydra_recipe", package="steps")
    params_store = hydra_zen.store(
        group="ocb_mods/hydra_recipe/params", package="params"
    )
    steps_store(steps, name=name, to_config=lambda x: x)
    params_store(params, name=name, to_config=lambda x: x)
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    recipe = hydra_zen.make_config(
        input=input,
        hydra_defaults=[{"ocb_mods/hydra_recipe": name,},{"ocb_mods/hydra_recipe/params": name,}, "_self_"],
        bases=(base_config,),
    )
    store(
        recipe,
        name=name,
        package="_global_",
        group="ocb_mods",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    steps_store.add_to_hydra_store(overwrite_ok=True)

    # Create CLI endpoint
    api_endpoint = hydra.main(config_name="ocb_mods/" + name, version_base="1.3", config_path=".")(
        zen_endpoint
    )
    return api_endpoint, recipe
