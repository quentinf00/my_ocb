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
Provide guidelines for:
- Designing pipelines
- Specifying interfaces
- Sharing pipelines Naming and versioning 


Maintain a registry of:
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
- Is composable with other pipelines
- Is configurable with informed parameters
- Provides a CLI
- Provides python interface ("pip installable" in a specified conda environment)
- Provides conda.lock with exact python dependencies for reproducibility



### Specifying interface
- Displayed in the pipeline README
- Displayed in the CLI `--help`
- Displayed in the python function  DOCSTRING
- Expected data:
  - File format, dimensions, (nans allowed)
  - for dynamics specs add asserts

