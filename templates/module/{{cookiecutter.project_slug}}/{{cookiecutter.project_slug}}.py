import logging
from pathlib import Path

import hydra
import hydra_zen
from hydra.conf import HelpConf, HydraConf

log = logging.getLogger(__name__)

PIPELINE_DESC = "{{cookiecutter.pipeline_desc}}"

## VALIDATE: Specifying input output format

def input_validation(input_path: str): # The expected format can depend on other parameters
    """
    {{cookiecutter.input_data_desc}}
    Requirements:
      - input_path points to a file

    """ ## TODO: implement and document validation steps
    log.debug('Starting input validation')
    try:
        assert Path(input_path).exists(), "input_path points to a file"
        log.debug('Succesfully validated input')
    except:
        log.error('Failed to validate input, continuing anyway', exc_info=1)

def output_validation(output_path: str): # The expected format can depend on other parameters
    """
    {{cookiecutter.output_data_desc}}
    Requirements:
      - output_path points to a file
    """ ## TODO: implement and document validation steps
    log.debug('Starting output validation')
    try:
        assert Path(output_path).exists(), "output_path points to a file"
        log.debug('Succesfully validated output')
    except:
        log.error('Failed to validate output', exc_info=1)


## PROCESS: Parameterize and implement how to go from input_files to output_files
def run(
    input_path: str = '???',
    output_path: str = '???',
    ## TODO: Add pipeline parameters
    _skip_val: bool = False,
):
    log.info("Starting")
    if not _skip_val:
      input_validation(input_path=input_path)


    Path(output_path).mkdir(parents=True, exist_ok=True) # Make output directory

    ## TODO: actual stuff

    if not _skip_val:
      output_validation(output_path=output_path)


## EXPOSE: document, and configure CLI
run.__doc__ = f"""
Pipeline description: 
    {PIPELINE_DESC}

Input description:
    {input_validation.__doc__}

Output description:
    {output_validation.__doc__}

Returns:
    None
"""

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

#Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))

store(
    hydra_zen.builds(run, populate_full_signature=True),
    name=__name__,
    group='ocb_mods',
    package='_global_',

)
# Create a  partial configuration associated with the above function (for easy extensibility)
run_cfg =  hydra_zen.builds(run, populate_full_signature=True, zen_partial=True)

store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name='ocb_mods/'  + __name__, version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
