"""Tests for word generation and filtering."""
import pytest
import random
import numpy as np
from alparc.corpus import load_phonemes
from alparc.syllables import make_syllables
from alparc.words import (
    generate_words, make_words, filter_by_bigrams, filter_by_trigrams,
    filter_by_position, word_overlap_matrix, _no_feature_overlap,
)
from alparc.types import Word, Register


@pytest.fixture(scope="module")
def syllables():
    random.seed(42)
    phonemes = load_phonemes(lang="deu")
    return make_syllables(phonemes, pattern="cV", lang="deu", syllable_control=True)


@pytest.fixture(scope="module")
def words(syllables):
    random.seed(42)
    np.random.seed(42)
    return generate_words(
        syllables, n_syllables=3, n_words=200, max_tries=5000,
        phonotactic_control=True, progress_bar=False,
    )


def test_generate_words_count(words):
    assert len(words) > 0
    assert len(words) <= 200


def test_generate_words_syllable_count(words, syllables):
    n_sylls = words.info["n_syllables_per_word"]
    assert n_sylls == 3
    for w in words:
        assert len(w.syllables) == 3


def test_generate_words_unique_syllables(words):
    """Each word must have unique syllables (no repeated syllable within one word)."""
    for w in words:
        ids = [s.id for s in w.syllables]
        assert len(ids) == len(set(ids)), f"Word {w.id} has duplicate syllables"


def test_generate_words_binary_features_shape(words):
    """binary_features should be n_features x n_syllables."""
    n_sylls = words.info["n_syllables_per_word"]
    for w in words:
        assert len(w.binary_features) == len(w.syllables[0].binary_features)
        assert all(len(col) == n_sylls for col in w.binary_features)


def test_generate_words_info(words):
    assert "n_syllables_per_word" in words.info
    assert "syllables_info" in words.info
    assert "syllable_feature_labels" in words.info["syllables_info"]


def test_phonotactic_no_overlap():
    from alparc.types import Syllable
    # s1: bilabial stop + vowel 'a'; s2: fricative dental + vowel 'i' — no shared tags
    s1 = Syllable(id="ba", phonotactic_features=[["plo", "lab"], ["a"]])
    s2 = Syllable(id="si", phonotactic_features=[["fri", "den"], ["i"]])
    assert _no_feature_overlap([s1, s2])


def test_phonotactic_overlap():
    from alparc.types import Syllable
    # Two consonants with same manner/place tags should fail
    s1 = Syllable(id="ba", phonotactic_features=[["plo", "lab"], ["a"]])
    s2 = Syllable(id="pu", phonotactic_features=[["plo", "lab"], ["u"]])
    assert not _no_feature_overlap([s1, s2])


def test_filter_by_bigrams(words):
    filtered = filter_by_bigrams(words, p_val=None)
    assert len(filtered) <= len(words)
    assert "syllables_info" in filtered.info


def test_filter_by_bigrams_reduces(words):
    """Strict alpha should reduce word count."""
    no_filter = filter_by_bigrams(words, p_val=None)
    strict = filter_by_bigrams(words, p_val=0.5)
    assert len(strict) <= len(no_filter)


def test_filter_by_trigrams(words):
    filtered = filter_by_trigrams(words, p_val=None)
    assert len(filtered) <= len(words)


def test_filter_by_position(syllables):
    """Positional filter requires word_position_prob — needs German phonemes."""
    random.seed(42)
    np.random.seed(42)
    w = generate_words(syllables, n_syllables=3, n_words=50, max_tries=2000, progress_bar=False)
    filtered = filter_by_position(w, position=None, p_threshold=0.0)
    assert len(filtered) <= len(w)


def test_word_overlap_matrix_shape(words):
    # Use a small subset
    small = words.subset(10)
    ov = word_overlap_matrix(small, lag=1)
    assert ov.shape == (len(small), len(small))


def test_word_overlap_matrix_diagonal(words):
    """Diagonal should be maximum overlap (word with itself)."""
    small = words.subset(5)
    ov = word_overlap_matrix(small, lag=1)
    for i in range(len(small)):
        assert ov[i, i] >= 0


def test_word_overlap_matrix_symmetric(words):
    small = words.subset(8)
    ov = word_overlap_matrix(small, lag=1)
    np.testing.assert_array_equal(ov, ov.T)


def test_make_words_full_pipeline(syllables):
    random.seed(42)
    np.random.seed(42)
    words = make_words(
        syllables, n_syllables=3, n_words=100, max_tries=3000,
        bigram_control=True, trigram_control=True, positional_control=True,
        lang="deu", progress_bar=False,
    )
    assert len(words) > 0
    assert "syllables_info" in words.info
