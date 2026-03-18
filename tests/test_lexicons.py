"""Tests for lexicon generation."""
import pytest
import random
import numpy as np
from alparc.corpus import load_phonemes
from alparc.syllables import make_syllables
from alparc.words import generate_words, word_overlap_matrix
from alparc.lexicons import make_lexicons, make_lexicon_generator, _random_lexicon_generator
from alparc.types import Register


@pytest.fixture(scope="module")
def words():
    random.seed(0)
    np.random.seed(0)
    phonemes = load_phonemes(lang="deu")
    syllables = make_syllables(phonemes, pattern="cV", lang="deu", syllable_control=True)
    return generate_words(
        syllables, n_syllables=3, n_words=300, max_tries=10_000,
        phonotactic_control=True, progress_bar=False,
    )


def test_make_lexicons_count(words):
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(words, n_lexicons=3, n_words=4)
    assert len(lexicons) == 3


def test_make_lexicons_word_count(words):
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(words, n_lexicons=2, n_words=4)
    for lex in lexicons:
        assert len(lex) == 4


def test_make_lexicons_no_duplicate_syllables(words):
    """No lexicon should contain the same syllable in two different words."""
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(words, n_lexicons=3, n_words=4)
    for lex in lexicons:
        all_sylls = [s.id for w in lex for s in w.syllables]
        assert len(all_sylls) == len(set(all_sylls)), (
            f"Lexicon has duplicate syllables: {all_sylls}"
        )


def test_make_lexicons_overlap_constraint(words):
    random.seed(0)
    np.random.seed(0)
    max_ov = 1
    lexicons = make_lexicons(words, n_lexicons=3, n_words=4, max_overlap=max_ov)
    for lex in lexicons:
        ov = word_overlap_matrix(lex)
        # Off-diagonal pairwise overlap should be ≤ max_ov
        n = len(lex)
        for i in range(n):
            for j in range(n):
                if i != j:
                    assert ov[i, j] <= max_ov, f"Pairwise overlap {ov[i,j]} > {max_ov}"


def test_make_lexicons_info_keys(words):
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(words, n_lexicons=2, n_words=4)
    for lex in lexicons:
        assert "cumulative_feature_repetitiveness" in lex.info
        assert "max_pairwise_feature_repetitiveness" in lex.info
        assert "syllables_info" in lex.info


def test_make_lexicons_unique_words(words):
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(words, n_lexicons=3, n_words=4, unique_words=True)
    all_word_ids = [w_id for lex in lexicons for w_id in lex.keys()]
    assert len(all_word_ids) == len(set(all_word_ids))


def test_make_lexicons_random_mode(words):
    """Without binary_feature_control, lexicons should still have no syllable duplicates."""
    random.seed(0)
    np.random.seed(0)
    lexicons = make_lexicons(
        words, n_lexicons=3, n_words=4, binary_feature_control=False
    )
    for lex in lexicons:
        all_sylls = [s.id for w in lex for s in w.syllables]
        assert len(all_sylls) == len(set(all_sylls))


def test_random_lexicon_generator_no_duplicate_syllables(words):
    random.seed(0)
    gen = _random_lexicon_generator(words, n_words=4)
    for _ in range(5):
        lex = next(gen)
        all_sylls = [s.id for w in lex for s in w.syllables]
        assert len(all_sylls) == len(set(all_sylls))
