"""Syllable generation and filtering."""
import itertools
import logging
from copy import copy
from typing import List, Optional, Union

import numpy as np
from scipy import stats

from .types import Phoneme, Syllable, Register, LABELS_C, LABELS_V

logger = logging.getLogger(__name__)


def _get_feature_labels(phoneme: Phoneme) -> List[str]:
    return LABELS_C if phoneme.is_consonant() else LABELS_V


def _phonotactic_features(phonemes: List[Phoneme]) -> List[List[str]]:
    """Derive phonotactic feature tags for each phoneme in a syllable.

    Consonants get manner/place tags (son/plo/fri, lab/den/oth).
    Vowels get their vowel quality character.
    """
    result = []
    for phon in phonemes:
        tags: List[str] = []
        if phon.is_consonant():
            if phon.get("son"):
                tags.append("son")
            elif not phon.get("cont"):
                tags.append("plo")
            else:
                tags.append("fri")
            if phon.get("lab"):
                tags.append("lab")
            elif phon.get("cor") and not phon.get("hi"):
                tags.append("den")
            else:
                tags.append("oth")
        else:
            for v in ["a", "e", "i", "o", "u", "ɛ", "ø", "y"]:
                if v in phon.id:
                    tags.append(v)
        result.append(tags)
    return result


def syllable_from_phonemes(phonemes_reg: Register, combination: List[str]) -> Syllable:
    """Build a Syllable from a list of phoneme IDs, computing binary features."""

    phon_objs = []
    for p in combination:
        if len(p) == 1 or "ː" in p:
            phon_objs.append(phonemes_reg[p])
        else:
            # Diphthong: not in the feature library, approximate with first token's features.
            # Use a copy so the register entry for the base phoneme is not mutated.
            phon_obj = copy(phonemes_reg[p[0]])
            phon_obj.id = p
            phon_objs.append(phon_obj)

    binary_features: List[int] = []
    for phon in phon_objs:
        for label in _get_feature_labels(phon):
            binary_features.append(1 if phon.get(label) else 0)

    return Syllable(
        id="".join(combination),
        phonemes=phon_objs,
        binary_features=binary_features,
        phonotactic_features=_phonotactic_features(phon_objs),
    )


def make_feature_syllables(
    phonemes: Register,
    pattern: Union[str, List[str]] = "cV",
    max_combinations: int = 1_000_000,
) -> Register:
    """Generate all syllables matching *pattern* from the phoneme set.

    Pattern characters:
        c = single consonant   C = multi-character consonant
        v = short vowel        V = long vowel (ends in 'ː')

    The returned Register carries .info with 'syllable_feature_labels' and
    'syllable_type', needed downstream for the word overlap matrix.
    """
    valid = {"c", "C", "v", "V"}
    phoneme_types = list(pattern) if isinstance(pattern, str) else list(pattern)
    phoneme_types = [p for p in phoneme_types if p in valid]

    labels_map = {"c": LABELS_C, "C": LABELS_C, "v": LABELS_V, "V": LABELS_V}
    syll_feature_labels = [labels_map[t] for t in phoneme_types]

    single_c, multi_c, short_v, long_v = [], [], [], []
    for phon in phonemes:
        if phon.is_consonant():
            (multi_c if len(phon.id) > 1 else single_c).append(phon.id)
        else:
            if len(phon.id) == 2 and phon.get("long"):
                long_v.append(phon.id)
            elif len(phon.id) == 1 and not phon.get("long"):
                short_v.append(phon.id)

    pool_map = {"c": single_c, "C": multi_c, "v": short_v, "V": long_v}
    pools = [pool_map[t] for t in phoneme_types]

    syllables: dict = {}
    for i, combo in enumerate(itertools.product(*pools)):
        if i >= max_combinations:
            logger.warning(
                "Combinatorial explosion — truncated to %d combinations", max_combinations
            )
            break
        syll = syllable_from_phonemes(phonemes, list(combo))
        syllables[syll.id] = syll

    result = Register(syllables)
    result.info = {"syllable_feature_labels": syll_feature_labels, "syllable_type": pattern}
    return result


def _filter_corpus(syllables: Register, corpus: Register) -> Register:
    """Keep only syllables present in corpus, attaching freq/prob from corpus."""
    result = Register()
    result.info = dict(syllables.info)
    result.info.update(corpus.info)
    for key in syllables.keys():
        if key in corpus.keys():
            syll = syllables[key]
            corpus_syll = corpus[key]
            syll.freq = corpus_syll.freq
            syll.prob = corpus_syll.prob
            result[key] = syll
    return result


def _filter_uniform(syllables: Register, alpha: float = 0.05) -> Register:
    """Remove syllables whose log-frequency deviates significantly from uniform."""
    freqs = [s.freq for s in syllables]
    if not freqs or all(f == 0 for f in freqs):
        return syllables
    p_vals = stats.uniform.sf(abs(stats.zscore(np.log([max(f, 1) for f in freqs]))))
    result = Register()
    result.info = dict(syllables.info)
    for (key, syll), p in zip(syllables.items(), p_vals):
        if p > alpha:
            result[key] = syll
    return result


def make_syllables(
    phonemes: Register,
    pattern: str = "cV",
    lang: str = "deu",
    syllable_control: bool = True,
    alpha: Optional[float] = 0.05,
    corpus_path: Optional[str] = None,
) -> Register:
    """Build a filtered syllable register.

    1. Generate all combinations matching *pattern*.
    2. If syllable_control: intersect with corpus (lang or corpus_path).
    3. If alpha is set: remove syllables with non-uniform log-frequency.
    """
    from .corpus import load_syllable_corpus

    syllables = make_feature_syllables(phonemes, pattern)

    if syllable_control:
        corpus = load_syllable_corpus(lang=lang, path=corpus_path)
        syllables = _filter_corpus(syllables, corpus)
        if alpha is not None:
            syllables = _filter_uniform(syllables, alpha=alpha)

    logger.info("Generated %d syllables (pattern=%s)", len(syllables), pattern)
    return syllables
