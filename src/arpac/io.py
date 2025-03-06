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

import pandas as pd
import numpy as np
from scipy import stats

from arpac.phonecodes import phonecodes
from arpac.types.base_types import Register, RegisterType

from arpac.types.phoneme import PHONEME_FEATURE_LABELS, Phoneme
from arpac.types.syllable import Syllable
from arpac.types.word import Word
from arpac.types.lexicon import Lexicon, LexiconType
from arpac.types.stream import Stream

logger = logging.getLogger(__name__)


def get_data_path(fname):
    return importlib_resources.files("arpac") / "data" / fname


BINARY_FEATURES_DEFAULT_PATH = get_data_path("phonemes.csv")
PHONEMES_DEFAULT_PATH = get_data_path("phonemes.json")

CORPUS_DEFAULT_PATH_DEU_SPECIAL = get_data_path("german")
SYLLABLES_DEFAULT_PATH_DEU_SPECIAL = CORPUS_DEFAULT_PATH_DEU_SPECIAL / 'syllables.csv'
IPA_BIGRAMS_DEFAULT_PATH = CORPUS_DEFAULT_PATH_DEU_SPECIAL / 'bigrams.csv'
IPA_TRIGRAMS_DEFAULT_PATH = CORPUS_DEFAULT_PATH_DEU_SPECIAL / 'trigrams.csv'
IPA_SEG_DEFAULT_PATH = CORPUS_DEFAULT_PATH_DEU_SPECIAL / 'unigrams.csv'

CORPUS_DEFAULT_PATH_CELEX = get_data_path("english")
SYLLABLES_DEFAULT_PATH_ENG = CORPUS_DEFAULT_PATH_CELEX / "syllables.csv"
#SYLLABLES_DEFAULT_PATH_DEU = CORPUS_DEFAULT_PATH_CELEX / "GERMAN" / "EFS" / "EFS.CD"
# SYLLABLES_DEFAULT_PATH_NLD = CORPUS_DEFAULT_PATH_CELEX / "DUTCH" / "EFS" / "EFS.CD"

RESULTS_DEFAULT_PATH = pathlib.Path("arc_results")
SSML_RESULTS_DEFAULT_PATH = RESULTS_DEFAULT_PATH / "syllables"


def export_speech_synthesizer(syllables: Iterable[Syllable],
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


def read_phoneme_corpus(
        lang: Literal["deu", "eng"] = "eng",
) -> Register[str, Phoneme]:
    """
    Read order of phonemes, i.e. phonemes from a corpus together with the positions at which they
    appear in a bag of words.

    :param ipa_seg_path:
    :return:
    """
    if not (lang == "deu"):
        logger.warning("Only german phoneme corpus available")
        return read_default_phonemes()

    logger.info("READ ORDER OF PHONEMES IN WORDS")

    # TODO: make language specific
    ipa_seg_path: Union[os.PathLike, str] = IPA_SEG_DEFAULT_PATH

    with open(ipa_seg_path, "r", encoding='utf-8') as csv_file:
        fdata = list(csv.reader(csv_file))[1:]

    phonemes = {}
    for phon, position_in_word in fdata:
        phon = phon.replace('"', '').replace("g", "ɡ")
        position_in_word = int(position_in_word)
        if phon in phonemes:
            phonemes[phon].info["order"].append(position_in_word)
        else:
            phonemes[phon] = Phoneme(id=phon, info={"order": [position_in_word]})

    for phon in phonemes:
        positions = max(phonemes[phon].info["order"])
        phonemes[phon].info["word_position_prob"] = {}
        for position in range(positions):
            phoneme_pos_prob = phonemes[phon].info["order"].count(position + 1) / len(phonemes[phon].info["order"])
            phonemes[phon].info["word_position_prob"][position] = phoneme_pos_prob
        del phonemes[phon].info["order"]

    return Register(phonemes)


def syll_to_ipa(syll, language="deu", from_format="xsampa"):
    if from_format == "xsampa":
        return phonecodes.xsampa2ipa(syll, language)
    elif from_format == "ipa":
        return syll
    else:
        raise ValueError(f"Unknown format {from_format}")


def read_syllables_corpus(
        lang: str = "deu",
) -> Register[str, Syllable]:
    logger.info("READ SYLLABLES, FREQUENCIES AND PROBABILITIES FROM CORPUS AND CONVERT SYLLABLES TO IPA")

    if lang == "deu":
        syllables_corpus_path: Union[os.PathLike, str] = SYLLABLES_DEFAULT_PATH_DEU_SPECIAL
    elif lang == "eng":
        syllables_corpus_path: Union[os.PathLike, str] = SYLLABLES_DEFAULT_PATH_ENG
    else:
        raise ValueError(f"Language {lang} not supported.")
    
    with open(syllables_corpus_path, "r", encoding='utf-8') as csv_file:
        data = list(csv.reader(csv_file))[1:]

    syllables_dict: Dict[str, Syllable] = {}

    for syll_ipa, freq, prob in data:
        info = {"freq": int(freq), "prob": float(prob)}
        if syll_ipa not in syllables_dict or syllables_dict[syll_ipa].info != info:
            syllables_dict[syll_ipa] = Syllable(
                id=syll_ipa, phonemes=[], info=info, binary_features=[], phonotactic_features=[])
        else:
            logger.info(
                f"Syllable '{syll_ipa}' with conflicting stats {info} != {syllables_dict[syll_ipa].info}."
            )

    return Register(syllables_dict)


def read_bigrams(
    ipa_bigrams_path: str = IPA_BIGRAMS_DEFAULT_PATH,
) -> Register[str, Syllable]:
    logger.info("READ BIGRAMS")

    with open(ipa_bigrams_path, "r", encoding='utf-8') as csv_file:
        fdata = list(csv.reader(csv_file))[1:]

    freqs = [int(data[1]) for data in fdata]
    p_vals_uniform = stats.uniform.sf(abs(stats.zscore(np.log(freqs))))

    bigrams_dict: Dict[str, Syllable] = {}

    for (bigram, freq), p_unif in zip(fdata, p_vals_uniform):
        bigram = bigram.replace('_', '').replace("g", "ɡ")
        info = {"freq": int(freq), "p_unif": p_unif}

        if bigram not in bigrams_dict or bigrams_dict[bigram].info == info:
            # a bigram is not necessarily a syllable but in our type system they are equivalent
            bigrams_dict[bigram] = Syllable(id=bigram, phonemes=[], info=info)
        else:
            logger.info(
                f"Bigram '{bigram}' with conflicting stats {info} != {bigrams_dict[bigram].info}."
            )
            # del bigrams_dict[bigram]

    return Register(bigrams_dict)


def read_trigrams(
        ipa_trigrams_path: str = IPA_TRIGRAMS_DEFAULT_PATH,
) -> Register[str, Syllable]:
    logger.info("READ TRIGRAMS")
    
    with open(ipa_trigrams_path, "r", encoding='utf-8') as csv_file:
        fdata = list(csv.reader(csv_file))[1:]

    freqs = [int(data[1]) for data in fdata]
    p_vals_uniform = stats.uniform.sf(abs(stats.zscore(np.log(freqs))))

    trigrams = Register()
    for (trigram, freq), p_unif in zip(fdata[1:], p_vals_uniform):
        trigram = trigram.replace('_', '').replace("g", "ɡ")
        info = {"freq": int(freq), "p_unif": p_unif}

        if trigram not in trigrams or trigrams[trigram].info == info:
            trigrams[trigram] = Syllable(id=trigram, phonemes=[], info=info)
        else:
            logger.info(
                f"Trigram '{trigram}' with conflicting stats {info} != {trigrams[trigram].info}."
            )

    return trigrams


def read_default_phonemes() -> Register:
    logger.info("READ MATRIX OF BINARY FEATURES FOR ALL IPA PHONEMES")

    with open(BINARY_FEATURES_DEFAULT_PATH, "r", encoding='utf-8') as csv_file:
        fdata = list(csv.reader(csv_file))

    phons = [row[0] for row in fdata[1:]]
    feats = [row[1:] for row in fdata[1:]]
    phoneme_feature_labels = fdata[0][1:]

    assert phoneme_feature_labels == PHONEME_FEATURE_LABELS

    phonemes_dict = {}
    for phon, features in zip(phons, feats):
        if phon not in phonemes_dict or features == phonemes_dict[phon].info["features"]:
            phonemes_dict[phon] = Phoneme(id=phon, info={"features": features})
        else:
            logger.info(
                f"Phoneme '{phon}' with conflicting "
                f"feature entries {features} != {phonemes_dict[phon].info['features']}.")
            # del phonemes_dict[phon]

    return Register(phonemes_dict, _info={"phoneme_feature_labels": phoneme_feature_labels})


def check_german(words: List[Word]):
    # TODO
    # SAVE WORDS IN ONE CSV FILE
    with open(os.path.join(RESULTS_DEFAULT_PATH, 'words.csv'), 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        for word in words:
            writer.writerows([[word.id, 0]])

    # TO ENSURE THAT THE TRIPLETS CANNOT BE MISTAKEN FOR GERMAN WORDS,
    # WE INSTRUCTED A NATIVE GERMAN SPEAKER TO MARK EACH TRIPLET AS...
    #     '1' IF IT CORRESPONDS EXACTLY TO A GERMAN WORD
    #     '2' IF IT COULD BE MISTAKEN FOR A GERMAN WORD-GROUP WHEN PRONOUNCED ALOUD
    #     '3' IF THE PRONUNCIATION OF THE FIRST TWO SYLLABLES IS A WORD CANDIDATE,
    #         i.e. the syllable pair could be mistaken for a German word, or
    #         it evokes a strong prediction for a certain real German word
    #     '4' IF IT DOES NOT SOUND GERMAN AT ALL
    #         (that is, if the phoneme combination is illegal in German morphology
    #         [do not flag if rule exceptions exist])
    #     '0' OTHERWISE (that is, the item is good)

    logger.info("LOAD WORDS FROM CSV FILE AND SELECT THOSE THAT CANNOT BE MISTAKEN FOR GERMAN WORDS")
    with open(os.path.join(RESULTS_DEFAULT_PATH, "words.csv"), 'r', encoding='utf-8') as f:
        fdata = list(csv.reader(f, delimiter='\t'))
    rows = [row[0].split(",") for row in fdata]
    words = [row[0] for row in rows if row[1] == "0"]

    return words


def arc_register_from_json(path: Union[str, PathLike], arc_type: Type) -> RegisterType:
    """
    Load an arc register from a json file.
    """
    with open(path, "r", encoding='utf-8') as file:
        d = json.load(file)

    # we have to process the "_info" field separately because it's not a valid ARC type
    register = Register({k: arc_type(**v) for k, v in d.items() if k != "_info"})
    register.info = d["_info"]

    return register


def load_phonemes(lang: Optional[Literal["deu", "eng"]] = "deu") -> RegisterType:
    """Load phoneme corpus with phonological features.

    Args:
        language_control (bool, optional): Filter out phonemes that are not common in the phoneme corpus (german). Defaults to True.

    Returns:
        RegisterType: _description_
    """
    phonemes = read_default_phonemes()
    
    if lang is not None:
        phonemes = phonemes.intersection(read_phoneme_corpus(lang=lang))

    return phonemes


def load_syllables(path_to_json: Union[str, PathLike]):
    return arc_register_from_json(path_to_json, Syllable)


def load_words(path_to_json: Union[str, PathLike]):
    return arc_register_from_json(path_to_json, Word)

def load_lexicons(path_to_json: Union[str, PathLike]):
    return arc_register_from_json(path_to_json, LexiconType)

def load_streams(path_to_json: Union[str, PathLike]):
    register = arc_register_from_json(path_to_json, Stream)
    #for stream in register:
    #    if "lexicon" in stream.info.keys():
    #        data = stream.info["lexicon"]
    #        print(data)
    #        lexicon = Lexicon({k: Word(**v) for k, v in data.items() if k != "info"})
    #        lexicon.info = data["info"]
    #        stream.info["lexicon"] = lexicon
    return register
