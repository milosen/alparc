import csv
import json
import logging
import os
import pathlib
from importlib import resources as importlib_resources
from os import PathLike
from typing import Iterable, Dict, Union, List, Type, Optional, Literal
from functools import partial
from copy import copy

logger = logging.getLogger(__name__)


def get_data_path(path):
    return importlib_resources.files("arpac") / "data" / path


BINARY_FEATURES_DEFAULT_PATH = get_data_path("phonemes.csv")
EXAMPLE_EXTERNAL_LEXICON_PATH = get_data_path("example_external_lexicon.txt")

# german corpus constants
GERMAN_CORPUS_PATH = get_data_path("german")
GERMAN_SYLLABLE_FREQUENCIES_PATH = GERMAN_CORPUS_PATH / 'syllable_frequency.txt'
GERMAN_IPA_BIGRAMS_PATH = GERMAN_CORPUS_PATH / 'ipa_bigrams_german.csv'
GERMAN_IPA_TRIGRAMS_PATH = GERMAN_CORPUS_PATH / 'ipa_trigrams_german.csv'
GERMAN_IPA_SEG_PATH = GERMAN_CORPUS_PATH / 'german_IPA_seg.csv'

ENGLISH_CORPUS_PATH = get_data_path("english")
SYLLABLES_DEFAULT_PATH_ENG = ENGLISH_CORPUS_PATH / "syllable_frequency.cd"

RESULTS_DEFAULT_PATH = pathlib.Path("arc_results")
SSML_RESULTS_DEFAULT_PATH = RESULTS_DEFAULT_PATH / "syllables"


def export_speech_synthesizer(syllables,
                              syllables_dir: Union[str, PathLike] = SSML_RESULTS_DEFAULT_PATH):
    logger.info("SAVE EACH SYLLABLE TO A TEXT FILE FOR THE SPEECH SYNTHESIZER")
    os.makedirs(syllables_dir, exist_ok=True)
    c = [s.id[0] for s in syllables]
    v = [s.id[1] for s in syllables]
    c = ' '.join(c).replace('ʃ', 'sch').replace('ɡ', 'g').replace('ç', 'ch').replace('ʒ', 'dsch').split()
    v = ' '.join(v).replace('ɛ', 'ä').replace('ø', 'ö').replace('y', 'ü').split()
    t = [co + vo for co, vo in zip(c, v)]
    for syllable, text in zip(syllables, t):
        synth_string = '<phoneme alphabet="ipa" ph=' + '"' + syllable.id + '"' + '>' + text + '</phoneme>'
        with open(os.path.join(syllables_dir, f'{str(syllable.id[0:2])}.txt'), 'w') as f:
            f.write(synth_string + "\n")
            csv.writer(f)

    print("Done")
