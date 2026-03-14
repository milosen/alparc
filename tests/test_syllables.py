"""Tests for syllable generation and filtering."""
import pytest
from alparc.corpus import load_phonemes
from alparc.syllables import (
    make_feature_syllables, make_syllables, syllable_from_phonemes,
    _phonotactic_features,
)
from alparc.types import Syllable, LABELS_C, LABELS_V


@pytest.fixture(scope="module")
def phonemes_deu():
    return load_phonemes(lang="deu")


@pytest.fixture(scope="module")
def phonemes_all():
    return load_phonemes(lang=None)


def test_syllable_from_phonemes_cV(phonemes_deu):
    # 'b' is consonant, 'eː' is long vowel
    syll = syllable_from_phonemes(phonemes_deu, ["b", "eː"])
    assert syll.id == "beː"
    assert len(syll.phonemes) == 2
    assert len(syll.binary_features) == len(LABELS_C) + len(LABELS_V)  # 15


def test_syllable_binary_features_are_binary(phonemes_deu):
    syll = syllable_from_phonemes(phonemes_deu, ["b", "eː"])
    assert all(f in (0, 1) for f in syll.binary_features)


def test_syllable_phonotactic_features_consonant(phonemes_deu):
    syll = syllable_from_phonemes(phonemes_deu, ["b", "eː"])
    c_tags = syll.phonotactic_features[0]
    # 'b' is a bilabial stop: should have 'plo' and 'lab'
    assert "plo" in c_tags
    assert "lab" in c_tags


def test_syllable_phonotactic_features_vowel(phonemes_deu):
    syll = syllable_from_phonemes(phonemes_deu, ["b", "eː"])
    v_tags = syll.phonotactic_features[1]
    assert len(v_tags) > 0


def test_make_feature_syllables_cV(phonemes_deu):
    sylls = make_feature_syllables(phonemes_deu, pattern="cV")
    assert len(sylls) > 0
    # All syllables should have one consonant + one long vowel
    for s in sylls:
        assert len(s.binary_features) == len(LABELS_C) + len(LABELS_V)


def test_make_feature_syllables_cv(phonemes_deu):
    sylls = make_feature_syllables(phonemes_deu, pattern="cv")
    assert len(sylls) > 0
    # Short vowel syllables
    for s in sylls:
        assert len(s.binary_features) == len(LABELS_C) + len(LABELS_V)


def test_make_feature_syllables_info(phonemes_deu):
    sylls = make_feature_syllables(phonemes_deu, pattern="cV")
    assert "syllable_feature_labels" in sylls.info
    assert "syllable_type" in sylls.info
    labels = sylls.info["syllable_feature_labels"]
    assert labels[0] == LABELS_C
    assert labels[1] == LABELS_V


def test_make_syllables_corpus_filtering(phonemes_deu):
    """Corpus-filtered syllables should be a subset of all generated syllables."""
    all_sylls = make_feature_syllables(phonemes_deu, pattern="cV")
    corpus_sylls = make_syllables(phonemes_deu, pattern="cV", lang="deu", syllable_control=True, alpha=None)
    assert len(corpus_sylls) <= len(all_sylls)
    assert all(k in all_sylls.keys() for k in corpus_sylls.keys())


def test_make_syllables_adds_freq(phonemes_deu):
    sylls = make_syllables(phonemes_deu, pattern="cV", lang="deu", syllable_control=True, alpha=None)
    # Syllables from corpus intersection should have freq > 0
    assert any(s.freq > 0 for s in sylls)


def test_make_syllables_alpha_filter(phonemes_deu):
    sylls_no_alpha = make_syllables(phonemes_deu, pattern="cV", lang="deu", syllable_control=True, alpha=None)
    sylls_alpha = make_syllables(phonemes_deu, pattern="cV", lang="deu", syllable_control=True, alpha=0.05)
    # Alpha filter should reduce the count
    assert len(sylls_alpha) <= len(sylls_no_alpha)


def test_make_syllables_preserves_info(phonemes_deu):
    sylls = make_syllables(phonemes_deu, pattern="cV", lang="deu")
    assert "syllable_feature_labels" in sylls.info


# ── Diphthong support ────────────────────────────────────────────────────────

def test_syllable_from_phonemes_diphthong_full_features(phonemes_all):
    """Diphthong vowel should produce the same number of binary features as a
    monophthong — both phonemes (C and V) must be present in .phonemes and
    their features encoded in .binary_features."""
    n_expected = len(LABELS_C) + len(LABELS_V)  # 15
    syll = syllable_from_phonemes(phonemes_all, ["p", "eɪ"])
    assert len(syll.phonemes) == 2, "diphthong syllable should have 2 phoneme objects"
    assert len(syll.binary_features) == n_expected, (
        f"expected {n_expected} binary features, got {len(syll.binary_features)}"
    )


def test_syllable_from_phonemes_diphthong_id(phonemes_all):
    """The diphthong phoneme object should carry the full diphthong id."""
    syll = syllable_from_phonemes(phonemes_all, ["p", "eɪ"])
    vowel_phoneme = syll.phonemes[1]
    assert vowel_phoneme.id == "eɪ"


def test_syllable_from_phonemes_diphthong_no_register_mutation(phonemes_all):
    """Building a diphthong syllable must not mutate the base phoneme in the
    register — a second call should still find the original phoneme."""
    syllable_from_phonemes(phonemes_all, ["p", "eɪ"])
    # 'e' should still be in the register with its original id
    assert "e" in phonemes_all.keys(), "register entry for 'e' was corrupted"
    assert phonemes_all["e"].id == "e", "phoneme id in register was mutated"
