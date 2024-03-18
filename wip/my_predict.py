import dz_4dvarnet_predict
from dz_4dvarnet_predict import load_from_cfg
import xrpatcher
import toolz
import operator
import pytorch_lightning as pl
import hydra_zen
import omegaconf
from omegaconf import OmegaConf
from pathlib import Path
import xarray as xr
import hydra

b = hydra_zen.make_custom_builds_fn()


trainer = b(
    pl.Trainer, inference_mode=False, accelerator='gpu'
)
solver = b(
    load_from_cfg,
    cfg_path='config.yaml',
    key='model',
    overrides=dict(model=dict(
        checkpoint_path='val_mse=3.01245-epoch=551.ckpt',
        map_location='cpu'),
    ),
    overrides_targets=dict(
        model='src.models.Lit4dVarNet.load_from_checkpoint',
    )
)
patcher = b(
    xrpatcher.XRDAPatcher,
    da=b(toolz.pipe,
         b(xr.open_dataset, filename_or_obj='${.....input_path}'),
         b(operator.itemgetter, 'ssh')
    ),
    patches=b(load_from_cfg, cfg_path='config.yaml', key='datamodule.xrds_kw.patch_dims', call=False)
,populate_full_signature=True)
dz_4dvarnet_predict.patcher_store(patcher, name='base')
dz_4dvarnet_predict.trainer_store(trainer, name='base')
dz_4dvarnet_predict.solver_store(solver, name='base')


dz_4dvarnet_predict.store(
    hydra_zen.make_config(
        bases=(dz_4dvarnet_predict.base_config,),
        hydra_defaults=[
            "_self_",
            {"/4dvarnet/patcher": "base"},
            {"/4dvarnet/trainer": "base"},
            {"/4dvarnet/solver": "base"},
            ],
    ),
    name=__name__,
    group="4dvarnet",
    package="_global_",
)
# Create a  partial configuration associated with the above function (for easy extensibility)

dz_4dvarnet_predict.store.add_to_hydra_store(overwrite_ok=True)
dz_4dvarnet_predict.patcher_store.add_to_hydra_store(overwrite_ok=True)
dz_4dvarnet_predict.trainer_store.add_to_hydra_store(overwrite_ok=True)
dz_4dvarnet_predict.solver_store.add_to_hydra_store(overwrite_ok=True)
# Create CLI endpoint


api_endpoint = hydra.main(
    config_name="4dvarnet/" + __name__, version_base="1.3", config_path="."
)(dz_4dvarnet_predict.zen_endpoint)



if __name__ == "__main__":
    api_endpoint()
