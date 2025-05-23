from copy import copy
import itertools
import logging
from typing import TypeVar, List, Dict, Any

import numpy as np
from pydantic import BaseModel
from tqdm import tqdm

from alparc.types.base_types import Register, Element, RegisterType
from alparc.types.phoneme import PHONEME_FEATURE_LABELS, TypePhonemeFeatureLabels
from alparc.types.syllable import Syllable, SyllableType
from alparc.types.word import Word, WordType

from alparc.controls.common import *
from alparc.controls.filter import filter_bigrams, filter_common_phoneme_words, filter_trigrams


logger = logging.getLogger(__name__)


def check_syll_feature_overlap(syllables):
    all_feats = [feat for syll in syllables for phon_feats in syll.info["phonotactic_features"] for feat in phon_feats]
    return len(all_feats) == len(set(all_feats))


def generate_subset_syllables(syllables, lookback_syllables):
    subset = []
    for new_syll in syllables:
        syll_test_set = lookback_syllables + [new_syll]
        if check_syll_feature_overlap(syll_test_set):
            subset.append(new_syll)

    return subset


def word_overlap_matrix(
        words: Register[str, Word], 
        lag_of_interest: int = 1,
        control_features: List[TypePhonemeFeatureLabels] = PHONEME_FEATURE_LABELS):
    n_words = len(words)
    n_sylls_per_word = len(words[0].syllables)

    oscillation_patterns = get_oscillation_patterns(lag=(n_sylls_per_word*lag_of_interest))

    overlap = np.zeros([n_words, n_words], dtype=int)

    feature_indexes = []
    features = [feature for phoneme_features in words.info["syllables_info"]["syllable_feature_labels"] for feature in phoneme_features]
    for i, feature in enumerate(features):
        if feature in control_features:
            feature_indexes.append(i)

    for i1, i2 in list(itertools.product(range(n_words), range(n_words))):
        word_pair_features = [f1 + f2 for f1, f2 in zip(words[i1].info["binary_features"],
                                                        words[i2].info["binary_features"])]

        for i, word_pair_feature in enumerate(word_pair_features):
            if (word_pair_feature in oscillation_patterns) and i in feature_indexes:
                overlap[i1, i2] += 1

    return overlap


def generate_feature_words(syllables, iter_tries, n_syllables, n_look_back, phonotactic_control, progress_bar, n_words):
    words = {}

    if progress_bar:
        pbar = tqdm(total=n_words)

    for _ in iter_tries:
        sylls = []
        for _ in range(n_syllables):
            sub = list(filter(lambda x: x.id not in sylls, syllables))
            if phonotactic_control:
                sub = generate_subset_syllables(sub, sylls[-n_look_back:])
            if sub:
                new_rand_valid_syllable = random.sample(sub, 1)[0]
                sylls.append(new_rand_valid_syllable)

        if len(sylls) == n_syllables:
            word_id = "".join(s.id for s in sylls)
            if word_id not in words:
                word_features = list(list(tup) for tup in zip(*[s.info["binary_features"] for s in sylls]))
                words[word_id] = Word(id=word_id, info={"binary_features": word_features}, syllables=sylls)
                if progress_bar:
                    pbar.update(1)

        if len(words) == n_words:
            logging.info(f"Done: Found {n_words} words.")
            break
    
    return Register(words, _info={"n_syllables_per_word": n_syllables, "n_look_back": n_look_back, "phonotactic_control": phonotactic_control})



def make_words(syllables: RegisterType,
               num_syllables=3,
               bigram_control=True,
               bigram_alpha=None,
               trigram_control=True,
               trigram_alpha=None,
               positional_control=True,
               positional_control_position=None,
               position_alpha=0,
               phonotactic_control=True,
               n_look_back=2,
               n_words=10_000,
               max_tries=100_000,
               progress_bar: bool = True,
               lang="deu"
               ) -> RegisterType:
    """_summary_

    Args:
        syllables (RegisterType): The Register of syllables to use as a basis for word generation
        num_syllables (int, optional): how many syllables are in a word. Defaults to 3.
        bigram_control (bool, optional): apply statistical control on the bigram level. Defaults to True.
        bigram_alpha (_type_, optional): which p-value to assume for bigram control. Defaults to None.
        trigram_control (bool, optional): apply statistical control on the trigram level. Defaults to True.
        trigram_alpha (_type_, optional): which p-value to assume for trigram control. Defaults to None.
        positional_control (bool, optional): control phoneme positions in words to be likely given the language. Defaults to True.
        positional_control_position (int, optional): At which position to control phoneme likelihood (None means all). Defaults to None.
        position_alpha (float, optional): probability throshold for positional control. Defaults to 0.
        phonotactic_control (bool, optional): control each syllabel for minimum feature overlap with previous syllables. Defaults to True.
        n_look_back (int, optional): how far to look back in the feature overlap control of the syllables. Defaults to 2.
        n_words (_type_, optional): how many words to generate. Defaults to 10_000.
        max_tries (_type_, optional): how often to attemt to add a word to the Register, before the function gives up. Defaults to 100_000.
        progress_bar (bool, optional): print a progress bar based on 'n_words'. Defaults to True.

    Returns:
        RegisterType: The Register of words.
    """

    iter_tries = range(max_tries)

    words_register = generate_feature_words(syllables, iter_tries, num_syllables, n_look_back, phonotactic_control, progress_bar, n_words)

    words_register.info["syllables_info"] = copy(syllables.info)

    if bigram_control and lang=="deu":
        logger.info("bigram control...")
        words_register = filter_bigrams(words_register, p_val=bigram_alpha)

    if trigram_control and lang=="deu":
        logger.info("trigram control...")
        words_register = filter_trigrams(words_register, p_val=trigram_alpha)

    if positional_control and lang=="deu":
        logger.info("positional control...")
        words_register = filter_common_phoneme_words(words_register, p_threshold=position_alpha, position=positional_control_position)

    return words_register
