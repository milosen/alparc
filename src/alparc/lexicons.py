"""Lexicon generation with binary-feature overlap control."""
import itertools
import logging
import math
import random
from copy import copy
from typing import Generator, List, Optional

import numpy as np
from tqdm import tqdm

from .types import Register, Word
from .words import word_overlap_matrix

logger = logging.getLogger(__name__)


def _syllable_ids(word: Word):
    return frozenset(s.id for s in word.syllables)


def make_lexicon_generator(
    words: Register,
    n_words: int = 4,
    max_overlap: int = 1,
    lag: int = 1,
    control_features: Optional[List[str]] = None,
    max_yields: int = 1_000_000,
) -> Generator[Register, None, None]:
    """Yield lexicons with controlled pairwise feature overlap.

    Iterates over increasing allowed overlap budgets, yielding lexicons where:
    - No two words share syllables.
    - Pairwise binary-feature overlap ≤ max_overlap.
    - Cumulative overlap across all pairs stays within budget.

    Args:
        words: Register of Word objects.
        n_words: Number of words per lexicon.
        max_overlap: Maximum feature overlap allowed between any word pair.
        lag: Lag for computing overlap (passed to word_overlap_matrix).
        control_features: Features to include in overlap computation.
        max_yields: Stop after yielding this many lexicons.
    """
    overlap = word_overlap_matrix(words, lag=lag, control_features=control_features)
    word_list = list(words.values())
    yields = 0

    for max_pair_overlap, max_overlap_pairs in itertools.product(
        range(max_overlap + 1), range(1, math.comb(n_words, 2))
    ):
        max_cum_overlap = max_pair_overlap * max_overlap_pairs
        valid_pairs = (overlap <= max_pair_overlap)

        # Build set of valid (i, j) pairs with no shared syllables
        no_overlap_pairs = set()
        for (i, j) in zip(*np.where(valid_pairs)):
            i, j = int(i), int(j)
            if i == j:
                continue
            if _syllable_ids(word_list[i]).isdisjoint(_syllable_ids(word_list[j])):
                no_overlap_pairs.add(frozenset([i, j]))

        for start_pair in no_overlap_pairs:
            lexicon_idx = set(start_pair)
            cum_overlap = 0

            for candidate in range(len(word_list)):
                if candidate in lexicon_idx:
                    continue

                # Check pairwise overlap and syllable uniqueness
                if not all(
                    frozenset([known, candidate]) in no_overlap_pairs
                    for known in lexicon_idx
                ):
                    continue

                extra_overlap = sum(overlap[known, candidate] for known in lexicon_idx)
                if extra_overlap > max_cum_overlap - cum_overlap:
                    continue

                lexicon_idx.add(candidate)
                cum_overlap += extra_overlap

                if len(lexicon_idx) < n_words:
                    continue

                lexicon = Register({word_list[idx].id: word_list[idx] for idx in lexicon_idx})
                lexicon.info = dict(words.info)
                lexicon.info["cumulative_feature_repetitiveness"] = int(cum_overlap)
                lexicon.info["max_pairwise_feature_repetitiveness"] = int(max_pair_overlap)
                yield lexicon

                yields += 1
                if yields >= max_yields:
                    return


def make_lexicons(
    words: Register,
    n_lexicons: int = 2,
    n_words: int = 4,
    max_overlap: int = 1,
    lag: int = 1,
    max_word_matrix: int = 200,
    unique_words: bool = False,
    binary_feature_control: bool = True,
    control_features: Optional[List[str]] = None,
    progress_bar: bool = False,
) -> List[Register]:
    """Generate multiple lexicons from the word pool.

    Args:
        words: Register of pseudo-words.
        n_lexicons: How many lexicons to generate.
        n_words: Words per lexicon.
        max_overlap: Max pairwise feature overlap allowed.
        lag: Lag for overlap calculation.
        max_word_matrix: Subsample this many words before building overlap matrix.
        unique_words: Reject lexicons that share words with already-generated ones.
        binary_feature_control: If False, sample randomly (no feature control).
        control_features: Feature subset for overlap computation.
        progress_bar: Show tqdm progress bar.

    Returns:
        List of Register objects, each a lexicon.
    """
    word_pool = words.subset(max_word_matrix)
    lexicons: List[Register] = []
    pbar = tqdm(total=n_lexicons) if progress_bar else None

    if binary_feature_control:
        generator = make_lexicon_generator(
            word_pool,
            n_words=n_words,
            max_overlap=max_overlap,
            lag=lag,
            control_features=control_features,
        )
    else:
        generator = _random_lexicon_generator(word_pool, n_words=n_words)

    for lexicon in generator:
        if unique_words:
            all_known = {w_id for lex in lexicons for w_id in lex.keys()}
            if all_known & set(lexicon.keys()):
                continue

        lexicons.append(lexicon)
        if pbar:
            pbar.update(1)
        if len(lexicons) >= n_lexicons:
            break

    if pbar:
        pbar.close()

    if not binary_feature_control:
        # Annotate with overlap stats post-hoc
        for lexicon in lexicons:
            ov = word_overlap_matrix(lexicon)
            lexicon.info["cumulative_feature_repetitiveness"] = int(np.triu(ov, 1).sum())
            lexicon.info["max_pairwise_feature_repetitiveness"] = int(np.triu(ov, 1).max())

    return lexicons


def _random_lexicon_generator(words: Register, n_words: int = 4) -> Generator[Register, None, None]:
    """Yield random lexicons with non-overlapping syllables."""
    word_list = list(words.values())
    while True:
        sample = random.sample(word_list, n_words)
        all_sylls = [s.id for w in sample for s in w.syllables]
        if len(set(all_sylls)) == len(all_sylls):  # no duplicate syllables
            lexicon = Register({w.id: w for w in sample})
            lexicon.info = dict(words.info)
            yield lexicon
