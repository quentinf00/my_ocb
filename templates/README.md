# My OceanBench templates

Building shareable and composable blocks rely on the compliance to guidelines and good practices.
In the oceanbench ecosystem, the up to date guidelines are described here ## TODO.
The templates provided here use the [cookiecutter](https://cookiecutter.readthedocs.io/en/stable/index.html) and contain the boilerplate files and code necessary to implement new blocks.
See below how to use each of the template:

## Module template.
The module template allows to package a simple data processing step.
It contains two files:
- the `<module>.py`
- the `pyproject.toml`


To use this template:
- have `cookiecutter` installed (`pip install cookiecutter`)
- from your modules directory run the command: `cookiecutter ../templates/module`
- fill the information
- in the `<module>.py` file, fill the `##TODO` items


