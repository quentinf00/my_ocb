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

#### From a python script
## Tooling
### Hydra / HydraZen
Documentations:
- [Hydra](https://hydra.cc/docs/intro/)
- [Hydra Zen](https://mit-ll-responsible-ai.github.io/hydra-zen/)


### DVC
TBD



## Pipeline Wishlist/Checklist:
- [ ] Naming convention: `<pipeline_id>__<authorid>`
  - [ ] python module or package
  - [ ] hydra config
  - [ ] script
  - [ ] logger

- [ ] Input/output validation
  - [ ] type
  - [ ] Nan allowed 
  - [ ] Dimensions, sizes
  - [ ] fields, variables, columns labels
  - [ ] numeric constraints (range...)
  - [ ] metadata (xarray attrs, units

- [ ] Pipeline:
  - [ ] Sensible arguments: Do different values encompass the different usecase I can Imagine
  - [ ] Pure version & FileSystem version
  - [ ] Hooks

- Doc:
  - [ ] Docstring Input validation
  - [ ] Docstring Output validation
  - [ ] Docstring Pipeline
  - [ ] CLI --help
  - [ ] logging
  - [ ] Readme (Install, dependencies...)


- Packaging
  - [ ] conda-lock
  - [ ] script

- Notebook demonstration:
  - [ ] Install
  - [ ] Run

- Testing:
  - [ ] test pip install (CI)
  - [ ] test notebook (CI)
  - [ ] validation (unit test)

## DataChallenge Wishlist/Checklist:
  - [ ] Specification 
    - [ ] Offlimit data
    - [ ] Inference data
    - [ ] Expected output data

  - [ ] Pipelines  
    - [ ] Inference data loading
    - [ ] Diagnostics

  - [ ] Pipeline versioning
    - [ ]  Stockage
    
  - [ ] CI:
    - [ ]  Automatic metrics computation

  - [ ] Notebooks:
    - [ ] Metrics computation
    - [ ] Method integration with inference
    [ ] 

## OceanBench Wishlist/Checklist:
- [ ] Example pipeline
- [ ] Example datachallenge
- [ ] CookieCutter pipeline (scaffolding)
- [ ] CookieCutter datachallenge (scaffolding)

## Next steps:
- [ ] Notebook install + generate all lambdaxs from oceanbench
- [ ] Clean up all pipelines with current requirements
- [ ] split requirements between nice to have and mandatory
