"""Tests for corpus loading functions."""
import pytest
from alparc.corpus import load_phonemes, load_syllable_corpus, load_bigrams, load_trigrams
from alparc.types import Phoneme, Syllable, Register, PHONEME_FEATURES


def test_load_phonemes_all():
    phonemes = load_phonemes(lang=None)
    assert len(phonemes) > 50
    assert isinstance(phonemes[0], Phoneme)
    assert all(isinstance(k, str) for k in phonemes.keys())


def test_load_phonemes_features():
    phonemes = load_phonemes(lang=None)
    p = phonemes["b"]
    assert isinstance(p.features, dict)
    assert set(p.features.keys()) == set(PHONEME_FEATURES)
    assert all(v in ("+", "-", "0") for v in p.features.values())


def test_load_phonemes_deu():
    phonemes = load_phonemes(lang="deu")
    # German corpus has fewer phonemes than full IPA set
    all_phonemes = load_phonemes(lang=None)
    assert len(phonemes) < len(all_phonemes)
    # All German phonemes have word position probabilities
    for p in phonemes:
        assert isinstance(p.word_position_prob, dict)
        assert len(p.word_position_prob) > 0


def test_load_phonemes_deu_has_features():
    phonemes = load_phonemes(lang="deu")
    for p in phonemes:
        assert len(p.features) == len(PHONEME_FEATURES)


def test_load_phonemes_register():
    phonemes = load_phonemes(lang=None)
    # Should be a Register (supports int indexing)
    p = phonemes[0]
    assert isinstance(p, Phoneme)


def test_load_syllable_corpus_deu():
    corpus = load_syllable_corpus(lang="deu")
    assert len(corpus) > 100
    s = corpus[0]
    assert isinstance(s, Syllable)
    assert s.freq > 0
    assert 0.0 <= s.prob <= 1.0


def test_load_syllable_corpus_ids_are_ipa():
    corpus = load_syllable_corpus(lang="deu")
    # Syllable IDs should be IPA strings (not x-sampa)
    assert all(isinstance(k, str) for k in corpus.keys())


def test_load_bigrams():
    bigrams = load_bigrams()
    assert isinstance(bigrams, dict)
    assert len(bigrams) > 100
    assert all(isinstance(v, float) for v in bigrams.values())
    # p-values should be in [0, 1]
    assert all(0.0 <= v <= 1.0 for v in bigrams.values())


def test_load_trigrams():
    trigrams = load_trigrams()
    assert isinstance(trigrams, dict)
    assert len(trigrams) > 100
    assert all(isinstance(v, float) for v in trigrams.values())


def test_bigrams_no_underscore():
    bigrams = load_bigrams()
    assert all("_" not in k for k in bigrams.keys())


def test_trigrams_no_underscore():
    trigrams = load_trigrams()
    assert all("_" not in k for k in trigrams.keys())
