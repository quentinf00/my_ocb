import logging
import hydra_zen
import hydra
from hydra import HydraConf, HelpConf
from pathlib import Path

log = logging.getLogger(__name__)


## VALIDATE: Specifying input output format

def input_validation(input_path: str): # The expected format can depend on other parameters
  """
  A netcdf containing a field on a regular time lat lon grid and alongtrack data with a time dimension
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
  alongtrack data in a netcdf with the same shape as the input alongtrack data
  Requirements:
    - output points to a file
  """ ## TODO: implement and document validation steps
    log.debug('Starting output validation')
    try:
        assert Path(output_path).exists(), "input_path points to a file"
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
Interpolates the input grid data on the input alongtrack data

Args:
    input_path: {input_validation.__doc__}
    output_path: {output_validation.__doc__}

Returns:
    None
"""
# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(run, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(run)

#Store the config
store = hydra_zen.ZenStore()
store(HydraConf(help=HelpConf(header=run.__doc__, app_name=__name__)))
store(main_config, name=__name__)
store.add_to_hydra_store(overwrite_ok=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=__name__, version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
