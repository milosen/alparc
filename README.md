# ALPARC
ALPARC is a Python package that allows you to generate artificial languages with phonological and acoustic rhythmicity control. It is designed to be used in psycholinguistic experiments, where you want to control the rhythmic properties of the stimuli you present to your participants. 

If you find the package useful, please consider citing our work:
[The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control](https://doi.org/10.1101/2024.05.24.595268)

```
Titone, L., Milosevic, N., & Meyer, L. (2024). 
The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control. 
bioRxiv, 2024.05.24.595268. https://doi.org/10.1101/2024.05.24.595268
```

# Use cases
The package is flexible and allows you to create a wide range of artificial languages with different rhythmic properties. It is based on the principles of phonological and acoustic rhythmicity, which are important for understanding how language is processed in the brain.

Depending on your use case, you can use ALPARC in one of two ways:
1. **As a dataset**: We have used ALPARC to generate a range of controlled artificial stimuli. You can readily [download the dataset here]() and use it for your experiments. This is useful if you want to make sure the rhythmic properties of your stimuli are properly statistically controlled, but don't want to do any coding in python yourself.
2. **As a library**: You can use ALPARC as a library in your own Python code. This allows you to generate artificial languages with phonological and acoustic rhythmicity controls in a custom manner, and use them in your own experiments. You can use the functions provided by ALPARC either in custom python scripts or in a jupyter notebook.

# Usage as a library
You can use ALPARC directly as a library for your own python scripts. The package provides a range of functions that allow you to create artificial languages with different rhythmic properties. You can use these functions to
1. **generate new stimuli** for your experiments from scratch, based on natural language statistics, or 
2. **analyze your existing stimuli**, for example pseudo-words created with [Wuggy](https://github.com/WuggyCode/wuggy).

## Setup
The following describes how you can set up the software and run the experiments from the paper.

### Install Package
//TODO: Simplify this section, maybe with a single command that installs everything needed. This could be done using uv.

The simplest is to clone this repository and install ALPARC in editable mode:
```shell
pip install -e .
```

If you want to use ALPARC as a package, you can install it directly from git with
```shell
pip install git+https://github.com/milosen/alparc.git
```
or from the [Python Package Index (PyPI)](https://pypi.org/project/alparc/) with
```shell
pip install alparc
```

## Generate new stimuli
// ToDo: Add a tutorial on how to use ALPARC functions to generate new stimuli

## Analyze existing stimuli
// TODo: Add a tutorial on how to use ALPARC functions to analyze existing stimuli

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
4.  *Optional*: If you want to adapt ALPARC to your own research needs, you'll probably want to take a closer look at the library, or even the internals of the toolbox. More notebooks on that can be found in [ALPARC's Workshop Directory](https://github.com/milosen/alparc/tree/main/workshop)

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
