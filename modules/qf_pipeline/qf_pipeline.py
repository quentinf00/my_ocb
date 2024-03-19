import logging

import hydra
import hydra_zen

log = logging.getLogger(__name__)


def run(
    to_run=[],
    stages=dict(),
    params=dict(),
):
    for stage in to_run:
        stages[stage]()


# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)


# Store the config
def register_pipeline(name, stages, params):
    stages_store = hydra_zen.store(
        stages, group="ocb_pipeline/stages", package="stages", name=name
    )
    params_store = hydra_zen.store(
        params, group="ocb_pipeline/params", package="_global_", name=name
    )
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    store(
        hydra_zen.make_config(
            dict(to_run=tuple(sorted(stages))),
            bases=(base_config,),
            hydra_defaults=["_self_", {"stages": name, "params": name}],
        ),
        name=name,
        package="_global_",
        group="ocb_pipeline",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    stages_store.add_to_hydra_store(overwrite_ok=True)
    params_store.add_to_hydra_store(overwrite_ok=True)

    # Create CLI endpoint
    api_endpoint = hydra.main(config_name=name, version_base="1.3", config_path=".")(
        zen_endpoint
    )
    return api_endpoint
