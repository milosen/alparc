"""Pseudo-word generation and corpus-based filtering."""
import logging
import random
from copy import copy
from typing import List, Optional, Union

import numpy as np
from tqdm import tqdm

from .types import Word, Syllable, Register, PHONEME_FEATURES
from .streams import get_oscillation_patterns

logger = logging.getLogger(__name__)


# ── Phonotactic control ───────────────────────────────────────────────────────

def _no_feature_overlap(syllables: List[Syllable]) -> bool:
    """Return True if no phonotactic feature tag appears in more than one syllable."""
    all_tags = [
        tag
        for syll in syllables
        for phon_tags in syll.phonotactic_features
        for tag in phon_tags
    ]
    return len(all_tags) == len(set(all_tags))


def _phonotactically_valid_candidates(
    syllables: Register, lookback: List[Syllable]
) -> List[Syllable]:
    """Filter syllables to those compatible with the phonotactic lookback window."""
    return [s for s in syllables if _no_feature_overlap(lookback + [s])]


# ── Word generation ───────────────────────────────────────────────────────────

def generate_words(
    syllables: Register,
    n_syllables: int = 3,
    n_words: int = 10_000,
    max_tries: int = 100_000,
    phonotactic_control: bool = True,
    n_look_back: int = 2,
    progress_bar: bool = True,
) -> Register:
    """Randomly assemble pseudo-words from syllables.

    Each word uses *n_syllables* unique syllables.  With phonotactic_control
    the last n_look_back syllables constrain which syllables can follow.

    Returns a Register[Word] with .info set.
    """
    pool = list(syllables.values())
    words: dict = {}

    pbar = tqdm(total=n_words) if progress_bar else None

    for _ in range(max_tries):
        chosen: List[Syllable] = []
        for _ in range(n_syllables):
            candidates = [s for s in pool if s.id not in {c.id for c in chosen}]
            if phonotactic_control:
                candidates = _phonotactically_valid_candidates(
                    syllables, chosen[-n_look_back:]
                )
            if not candidates:
                break
            chosen.append(random.choice(candidates))

        if len(chosen) != n_syllables:
            continue

        word_id = "".join(s.id for s in chosen)
        if word_id in words:
            continue

        # binary_features: list of n_features lists, each of length n_syllables
        # = transpose of stacked syllable feature vectors
        binary_features = [
            list(col) for col in zip(*[s.binary_features for s in chosen])
        ]
        words[word_id] = Word(id=word_id, syllables=chosen, binary_features=binary_features)

        if pbar is not None:
            pbar.update(1)

        if len(words) >= n_words:
            break

    if pbar is not None:
        pbar.close()

    result = Register(words)
    result.info = {
        "n_syllables_per_word": n_syllables,
        "n_look_back": n_look_back,
        "phonotactic_control": phonotactic_control,
        "syllables_info": dict(syllables.info),
    }
    logger.info("Generated %d pseudo-words", len(result))
    return result


# ── N-gram / positional filters ───────────────────────────────────────────────

def filter_by_bigrams(words: Register, p_val: Optional[float] = None) -> Register:
    """Remove words containing phoneme bigrams not attested (or too rare) in German."""
    from .corpus import load_bigrams
    bigrams = load_bigrams()
    if p_val is not None:
        bigrams = {k: v for k, v in bigrams.items() if v > p_val}
    valid = set(bigrams.keys())

    def _valid(word: Word) -> bool:
        phonemes = [ph for syll in word for ph in syll]
        return all(ph1.id + ph2.id in valid for ph1, ph2 in zip(phonemes, phonemes[1:]))

    result = words.filter(_valid)
    result.info = dict(words.info)
    result.info["bigram_pval"] = p_val
    logger.info("After bigram filter: %d words", len(result))
    return result


def filter_by_trigrams(words: Register, p_val: Optional[float] = None) -> Register:
    """Remove words containing phoneme trigrams not attested in German."""
    from .corpus import load_trigrams
    trigrams = load_trigrams()
    if p_val is not None:
        trigrams = {k: v for k, v in trigrams.items() if v > p_val}
    valid = set(trigrams.keys())

    def _valid(word: Word) -> bool:
        phonemes = [ph for syll in word for ph in syll]
        return all(
            ph1.id + ph2.id + ph3.id in valid
            for ph1, ph2, ph3 in zip(phonemes, phonemes[1:], phonemes[2:])
        )

    result = words.filter(_valid)
    result.info = dict(words.info)
    result.info["trigram_pval"] = p_val
    logger.info("After trigram filter: %d words", len(result))
    return result


def filter_by_position(
    words: Register,
    position: Optional[int] = None,
    p_threshold: float = 0.0,
) -> Register:
    """Remove words where phonemes appear at unlikely positions (German corpus).

    If position is None, checks all positions.
    """
    def _phoneme_ok(phoneme, pos: int) -> bool:
        return phoneme.word_position_prob.get(pos, 0) >= p_threshold

    def _valid(word: Word) -> bool:
        phonemes = [ph for syll in word for ph in syll]
        if position is None:
            return all(_phoneme_ok(ph, i) for i, ph in enumerate(phonemes))
        return _phoneme_ok(phonemes[position], position)

    result = words.filter(_valid)
    result.info = dict(words.info)
    logger.info("After positional filter: %d words", len(result))
    return result


# ── Feature overlap matrix ────────────────────────────────────────────────────

def word_overlap_matrix(
    words: Register,
    lag: Union[int, List[int], None] = None,
    control_features: Optional[List[str]] = None,
) -> np.ndarray:
    """Compute pairwise binary-feature overlap between words.

    Overlap counts how many features repeat at the word-length period when
    two words are concatenated — a measure of rhythmic similarity.

    Args:
        words: Register of Word objects.
        lag: Controls the oscillation patterns used for overlap detection.
            - None (default): period = number of syllables per word.
            - int: oscillation period in syllables.
            - List[int]: custom kernel of length 2 * n_syllables, used directly
              as the oscillation pattern.
        control_features: Which feature names to include. Defaults to all features
            listed in words.info['syllables_info']['syllable_feature_labels'].

    Returns:
        n_words × n_words integer matrix.
    """
    n_words = len(words)
    n_sylls = len(words[0].syllables)
    if isinstance(lag, list):
        expected_len = 2 * n_sylls
        if len(lag) != expected_len:
            raise ValueError(
                f"Custom kernel must have length 2 * n_syllables = {expected_len}, got {len(lag)}."
            )
        oscillation_patterns = [lag]
    else:
        oscillation_patterns = get_oscillation_patterns(n_sylls if lag is None else lag)

    # Determine which feature indices to include
    feat_labels_nested = words.info["syllables_info"]["syllable_feature_labels"]
    all_features = [f for labels in feat_labels_nested for f in labels]
    if control_features is not None:
        feature_idx = {i for i, f in enumerate(all_features) if f in control_features}
    else:
        feature_idx = set(range(len(all_features)))

    word_list = list(words.values())
    overlap = np.zeros((n_words, n_words), dtype=int)

    for i in range(n_words):
        for j in range(n_words):
            pair_features = [
                f1 + f2
                for f1, f2 in zip(word_list[i].binary_features, word_list[j].binary_features)
            ]
            for fi, feat_seq in enumerate(pair_features):
                if fi in feature_idx and feat_seq in oscillation_patterns:
                    overlap[i, j] += 1

    return overlap


# ── Main entry point ──────────────────────────────────────────────────────────

def make_words(
    syllables: Register,
    n_syllables: int = 3,
    n_words: int = 10_000,
    max_tries: int = 100_000,
    phonotactic_control: bool = True,
    n_look_back: int = 2,
    bigram_control: bool = True,
    bigram_alpha: Optional[float] = None,
    trigram_control: bool = True,
    trigram_alpha: Optional[float] = None,
    positional_control: bool = True,
    positional_position: Optional[int] = None,
    position_alpha: float = 0.0,
    lang: str = "deu",
    progress_bar: bool = True,
) -> Register:
    """Full word-generation pipeline.

    1. Randomly assemble pseudo-words from syllables.
    2. Apply corpus-based bigram / trigram / positional filters (German only).
    """
    words = generate_words(
        syllables,
        n_syllables=n_syllables,
        n_words=n_words,
        max_tries=max_tries,
        phonotactic_control=phonotactic_control,
        n_look_back=n_look_back,
        progress_bar=progress_bar,
    )

    if lang == "deu":
        if bigram_control:
            words = filter_by_bigrams(words, p_val=bigram_alpha)
        if trigram_control:
            words = filter_by_trigrams(words, p_val=trigram_alpha)
        if positional_control:
            words = filter_by_position(words, position=positional_position, p_threshold=position_alpha)

    return words
