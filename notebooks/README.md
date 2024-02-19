# Demonstration Notebooks
This repository uses [jupytext](https://jupytext.readthedocs.io/en/latest/) to synchronize `.py` and `.ipynb` versions of notebooks/scripts

## Requirements:
- Install conda environment
- Run from repo root directory
- login in to copernicusmarine (for data download) (`copernicusmarine login` from conda environment)

## Run from colab:
If you want to run these notebooks from colab, just execute the two cells below beforehand
```
!pip install --quiet condacolab
import condacolab
condacolab.install_mambaforge()
```
```
!git clone https://github.com/quentinf00/my_ocb.git
%cd my_ocb
!mamba env update -q -f env.yaml -n base
```
## Table of contents


