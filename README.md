# My OceanBench
**Reference repository with guidelines to contribute to open ocean observation science the OceanBench way**


## OceanBench Goals
### Open Ocean observation science experimental setups
This include having access to:
  - the data used as input for inference
  - the data used to evaluate the method
  - the code necessary to preprocess the data in a "method agnostic way" (validate units, format etc..)
  - the code necessary to compute the metrics and plots used in the diagnostics
  - the runtime environment to run the code



### Accelerate Ocean observation science
This rely on providing:
  - Standard Experimental setups and diagnostics with intercomparison of different methods:  **Data Challenge**
  - **Clear interface** requirements for integrating a method with a data Challenge
  - Standard way of **sharing, reusing and extending** the existing data loading and diagnostic **pipelines**


## OceanBench Users 
### Oceanbench Maintainer
-Provides guidelines for:
  - Designing pipelines
  - Specifying interfaces
  - Sharing pipelines Naming and versioning 

- Provides template for implementing pipelines

- Maintain a registry of:
  - Data Challenges complying with the guidelines
  - Methods complying with the guidelines
  

### Data challenge Maintainer
- Specify task: inference data, diagnostics, offlimit data
- Design shareable pipeline using the oceanbench guidelines
- Provide clear interface for method integration: **provided format of inference data**, **expected formats for diagnostics**
- Maintain Leaderboard of benchmarked methods


### Method Maintainer
#### Testing on a datachallenge
- Implement the bridge between provided inference data (by the DC) and method expected input
- Implement the bridge between  method output and expected diagnostics format (by the DC)

#### Sharing the method 
- Design method inference as a pipeline using oceanbench guidelines
- Provide clear interface for further integration: expected method input, expected method output
- Design method training using oceanbench guidelines

## OceanBench Solution
### Pipelines
- Reads input from disk or/and dump output to disk
- Is **composable** with other pipelines
- Is **configurable** with informed parameters
- Is "pip installable" in a specified conda environment
  - is versioned
  - Provides conda.lock 
  - Provides a CLI
  - Provides python interface 

### Specifying interface
- Displayed in the pipeline README
- Displayed in the CLI `--help`
- Displayed in the python function DOCSTRING
- Validation function for input and output
- Expected data:
  - File format, dimensions, (nans allowed)
  - for dynamics specs add asserts
- **is versioned**

### Testing
- pip install tested in CI
- Maintain input & output validation 
- Provide standalone colab notebook with example usage


## Usage

### Single pipeline
#### Install
```
mamba env update -f repo/pipeline_env.yaml
pip install my_pipeline

```
#### From a python script
```python
import my_pipeline
my_pipeline.validate_input(input_path, **kwargs)
my_pipeline.run(input_path, output_path, **kwargs)
my_pipeline.validate_output(output_path, **kwargs)
```

#### From the CLI
- Get the input requirements, and options
```bash
my_pipeline --help
```

- run the pipeline with default options
```bash
my_pipeline
```

- Override default options
```bash
my_pipeline input_path=data/my_input.nc param1=new_value
```


- Create reusable config
```bash
mkdir -p conf/my_pipeline_cfgs
echo 'input_path: data/my_input.nc \nparam1: new_value' > conf/my_pipeline_cfgs/xp1.yaml
my_pipeline --cs=conf/my_pipeline_cfgs +my_pipeline_cfgs=xp1
```
### Composing pipelines

## Tooling
### Hydra / HydraZen
Documentations:
- [Hydra](https://hydra.cc/docs/intro/)
- [Hydra Zen](https://mit-ll-responsible-ai.github.io/hydra-zen/)


### DVC
TBD


## Template module

```python
# qf__select_n_rename.py
import xarray as xr
import numpy as np
import hydra_zen
import hydra
from pathlib import Path

WHOAMI = "qf"
PIPELINE_ID =  "select_n_rename"
PIPELINE_NAME =  WHOAMI + "__" + PIPELINE_ID # Shoull be filename

def input_validation(input_path: str, param2: float): # The expected format can depend on other parameters
  """
  Requirements:
    - "input path should point to a netcdf and with variable input_var"
    - "Input data must not contain nans"
    - "Dimensions should be ('time', 'lat', 'lon') in that order"
    - "Latitude values should be smaller than param2"
  """
  try:
    study_da = xr.open_dataset(input_path)[input_var]
  except Exception as e:
    print("input path should point to a netcdf and with variable input_var")
    raise e

  assert study_da.pipe(np.isnan).sum().item == 0, "Input data must not contain nans"
  assert study_da.dims == ('time', 'lat', 'lon'), "Dimensions should be ('time', 'lat', 'lon') in that order"
  assert xr.testing.assert_equal(study_da.lat < param2, xr.full_like(study.lat, True)), "Latitude values should be smaller than param2"
  return study_da

def output_validation(output_path: str, param1: str): # The expected format can depend on other parameters
  """
  Requirements:
    - "output path should point to a netcdf"
    - "param1 should be a variable in the dataset"
    - "data must not contain nans"
    - "Dimensions should be ('time', 'lon', 'lat') in that order"
  """
  try:
    output_ds = xr.open_dataset(output_path)
  except Exception as e:
    print("input path should point to a netcdf and with variable input_var")
    raise e

  assert param1 in output_ds, "param1 should be a variable in the dataset"
  assert output_ds.pipe(np.isnan).sum().item == 0, "data must not contain nans"
  assert output_ds.dims == ('time', 'lat', 'lon'), "Dimensions should be ('time', 'lat', 'lon') in that order"

def run(
    input_path: str = '???', # Provide three question marks for argument without default values for automatic configuration generation
    input_var: str = '???',
    output_path: str = '???',
    param1: str = 'ssh',
    param2: float = 32,
    _skip_val: bool = False, # Add possibility to skip input output validation
):
    """
    Select variable from dataset, and transpose dimensions

    Args:
      input path: {input_validation.__doc__}
      input_var (str): variable to select
      output_path: {output_validation.__doc__}
      param1 (str): output variable name
      param2 (float): maximum latitude

    Returns:
      None
    """


    if not _skip_val:
      input_validation(input_path=input_path, input_var=input_var, param2=param2)

    input_da = xr.open_dataset(input_path)[input_var]
    ds = input_da.rename(param1).to_dataset()
    ds = ds.transpose('time', 'lon', 'lat')
    Path(output_path).mkdir(parents=True, exist_ok=True) # Make output directory
    ds.to_netcdf(Path(output_path))

    if not _skip_val:
      output_validation(output_path)

# Create a configuration associated with the above function (cf next cell)
main_config =  hydra_zen.builds(main_api, populate_full_signature=True)

# Wrap the function to accept the configuration as input
zen_endpoint = hydra_zen.zen(main_api)

#Store the config
store = hydra_zen.ZenStore()
store(main_config, name=PIPELINE_NAME)
store.add_to_hydra_store(overwrite=True)

# Create CLI endpoint
api_endpoint = hydra.main(
    config_name=PIPELINE_NAME, version_base="1.3", config_path=None
)(zen_endpoint)


if __name__ == '__main__':
    api_endpoint()
```
