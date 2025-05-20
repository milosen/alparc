# ALPARC
This is code for our work [The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control](https://doi.org/10.1101/2024.05.24.595268)

## Setup
The following describes how you can set up the software and run the experiments from the paper.

### Install Package
The simplest is to clone this repository and install ALPARC in editable mode:
```shell
pip install -e .
```

If you want to use ALPARC as a package, you can install it directly from git with
```shell
pip install git+https://github.com/milosen/alparc.git
```

## Run the code from the paper

Clone this repository. Install jupyter
```shell
pip install jupyter
```
If you use a virtual environement, you also need to install the ipython-kernel:
```shell
python -m ipykernel install --user --name=alparc
```
In this case, don't forget to select the `alparc` kernel in the jupyter session's kernel option (Kernel -> Change kernel -> alparc).

Start jupyter
```shell
jupyter notebook
```
and select the notebook you want. 

1.  `publication/data_and_stats_from_the_paper.ipynb` reproduces the data for the figures and the appendices of the paper
2.  `publication/plots_from_the_paper.ipynb` reproduces the figures in the publication
3.  *Optional*: If you want to generate or diagnose your own data, please have a look at the tutorial on how to use the command line tool: `workshop/00_basic_command_line_usage.ipynb`. This notebook shows how to use the command line tool `alparc` to generate data and run the analysis. You can also use the command line tool directly from the terminal. The tool can be run with `alparc --help`
4.  *Optional*: If you want to adapt ALPARC to your own research needs, you'll probably want to take a closer look at the library, or even the internals of the toolbox. More notebooks on that can be found in [ALPARC's Workshop Directory](https://github.com/milosen/alparc_workshop)

# Citation
Please cite our work as
```
@article {Titone2024ALPARC,
	author = {Titone, Lorenzo and Milosevic, Nikola and Meyer, Lars},
	title = {The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control},
	elocation-id = {2024.05.24.595268},
	year = {2024},
	doi = {10.1101/2024.05.24.595268},
	publisher = {Cold Spring Harbor Laboratory},
	URL = {https://www.biorxiv.org/content/early/2024/05/24/2024.05.24.595268},
	eprint = {https://www.biorxiv.org/content/early/2024/05/24/2024.05.24.595268.full.pdf},
	journal = {bioRxiv}
}
```
