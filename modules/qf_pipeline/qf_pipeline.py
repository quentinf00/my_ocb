import logging

import hydra
from hydra.conf import HydraConf
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
def register_pipeline(name, stages, params, default_sweep=None):
    if isinstance(params, dict):
        params = hydra_zen.make_config(**params)
    # stages_store = hydra_zen.store(group="ocb_pipeline/stages", package="stages")
    # params_store = hydra_zen.store(group="ocb_pipeline/params", package="params")
    stages_store = hydra_zen.store(group="stages", package="stages")
    params_store = hydra_zen.store(group="params", package="params")
    for stage_name, cfg in stages.items():
        stages_store(cfg, name=f"{name}-{stage_name}", package=f"stages.{stage_name}")
    params_store(params, name=name)
    store = hydra_zen.store()

    base_config = hydra_zen.builds(
        run,
        populate_full_signature=True,
        zen_partial=True,
    )

    _recipe = hydra_zen.make_config(
        to_run=tuple(sorted(stages)),
        bases=(base_config,),
        hydra=dict(sweeper=dict(params=default_sweep)),
        hydra_defaults=[
              {"stages": [f"{name}-{stage_name}" for stage_name in stages]},
                {"params": name},
            "_self_",
        ],
    )
    store(_recipe,
        name="ocb_pipeline_" + name,
        package="_global_",
        # group="ocb_pipeline",
    )
    # Create a  partial configuration associated with the above function (for easy extensibility)

    store.add_to_hydra_store(overwrite_ok=True)
    stages_store.add_to_hydra_store(overwrite_ok=True)
    params_store.add_to_hydra_store(overwrite_ok=True)

    with hydra.initialize(version_base='1.3', config_path='.'):
        cfg = hydra.compose("ocb_pipeline_" + name,)

    recipe = hydra_zen.make_config(
        **{k: node for k,node in cfg.items()
            if k not in ('_target_', '_partial_', '_args_', '_convert_', '_recursive_')},
        bases=(base_config,),
        zen_dataclass={'cls_name': f'{"".join(x.capitalize() for x in name.lower().split("_"))}Recipe'}
    )
    # Create CLI endpoint
    # api_endpoint = hydra.main(config_name="ocb_pipeline/" + name, version_base="1.3", config_path=".")(
    api_endpoint = hydra.main(config_name="ocb_pipeline_" + name, version_base="1.3", config_path=".")(
        zen_endpoint
    )

    return api_endpoint, recipe, params
