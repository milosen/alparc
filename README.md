# ALPARC
ALPARC is a Python package that allows you to generate artificial languages with phonological and acoustic rhythmicity control. It is designed to be used in psycholinguistic experiments, where you want to control the rhythmic properties of the stimuli you present to your participants. 

![info](assets/info.png)

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
1. **As a dataset**: We have used ALPARC to generate a range of controlled artificial stimuli. You can readily [download the dataset here](https://github.com/milosen/alparc/releases/latest/download/results.tar.gz) and use it for your experiments. This is useful if you want to make sure the rhythmic properties of your stimuli are properly statistically controlled, but don't want to do any coding in python yourself.
2. **As a library**: You can use ALPARC as a library in your own Python code. This allows you to generate artificial languages with phonological and acoustic rhythmicity controls in a custom manner, and use them in your own experiments. You can use the functions provided by ALPARC either in custom python scripts or in a jupyter notebook.

# Usage as a library
You can use ALPARC directly as a library for your own python scripts. The package provides a range of functions that allow you to create artificial languages with different rhythmic properties. You can use these functions to
1. **generate new stimuli** for your experiments from scratch, based on natural language statistics, or 
2. **analyze your existing stimuli**, for example pseudo-words created with [Wuggy](https://github.com/WuggyCode/wuggy).

## Installation
The easiest setup is with pip
```bash
pip install alparc
```
For all features, it is best to clone this repository:
```shell
# On macOS and Linux.
git clone git@github.com:milosen/alparc.git && cd alparc
```
You can install dependencies using the environment manager [uv](https://github.com/astral-sh/uv). As of 2025, it is simply installed with the following one-liner:
```shell
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
````
```shell
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Then just run
```shell
uv sync
```
to install the dependencies in a virtual environment.

## Generate new stimuli
You can use the `generate` function from the `alparc` package to create new stimuli. This function allows you to specify various parameters, such as the number of stimuli, the phonological and acoustic properties, and more.

In a script or notebook you can use the following code to generate new stimuli:
```python
from alparc import generate
# Example usage for generating streams from scratch
# This will generate a set of streams with the default parameters.
# check out the documentation for more options, or run `help(generate)`.
streams, report = generate()
# Example usage for generating streams starting with a custom lexicon
# This will generate a set of streams based on the provided lexicon.
# The lexicon should be a list of words. Phonemes in the lexicon should be separated by an underscore _ and syllables by vertical bars |.
streams, report = generate(lexicon=["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"])
# you can use your own corpus of syllables to perform controls, but you have to prepare it in the right format. Please see `examples/generate_with_custom_corpus.py`. This feature is still experimental.
streams, report = generate(syllables="path/to/syllables.csv")
```
Run the script with uv or in the environment where you installed `alparc`:

Alternatively, you can use the command line interface. Run
```bash
# using uv
uv run alparc generate --help
```

```bash
# without uv
alparc generate --help
```
to see all options.

## Diagnose existing stimuli
You can use the `diagnose` function from the `alparc` package to analyze existing stimuli, including your own pseudowords, lexicons, and streams. This function allows you to specify the stimuli you want to analyze and returns various statistics about their phonological and acoustic properties.
```python
from alparc import diagnose
# Example usage
stimuli, report = diagnose(lexicon=["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"])
```

## Run the code from the paper

1.  `publication/data_and_stats_from_the_paper.ipynb` reproduces the data for the figures and the appendices of the paper
2.  `publication/plots_from_the_paper.ipynb` reproduces the figures in the publication
3.  *Optional*: If you want to generate or diagnose your own data, please have a look at the tutorial on how to use the library: `notebooks/00_library_line_usage.ipynb`. The `generate` and `diagnose` functions are also available as command line scripts. Run
```bash
alparc --help
```

# Citation
Please cite our work as
```
@article {Titone2024alparc,
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
