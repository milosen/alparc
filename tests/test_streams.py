"""Tests for stream generation and TP modes."""
import pytest
import random
import numpy as np
from alparc.corpus import load_phonemes
from alparc.syllables import make_syllables
from alparc.words import generate_words
from alparc.lexicons import make_lexicons
from alparc.streams import (
    get_oscillation_patterns, _tp_matrix,
    pseudo_rand_tp_uniform, pseudo_rand_tp_struct,
    pseudo_rand_tp_uniform_position_controlled,
    rhythmicity_index, make_stream, make_streams,
)
from alparc.types import Stream


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def lexicons():
    random.seed(1)
    np.random.seed(1)
    phonemes = load_phonemes(lang="deu")
    syllables = make_syllables(phonemes, pattern="cV", lang="deu", syllable_control=True)
    words = generate_words(
        syllables, n_syllables=3, n_words=300, max_tries=10_000, progress_bar=False
    )
    return make_lexicons(words, n_lexicons=2, n_words=4)


# ── Utility functions ─────────────────────────────────────────────────────────

def test_oscillation_patterns_length():
    patterns = get_oscillation_patterns(3)
    assert len(patterns) == 3
    assert all(len(p) == 6 for p in patterns)


def test_oscillation_patterns_values():
    patterns = get_oscillation_patterns(3)
    assert patterns[0] == [1, 0, 0, 1, 0, 0]
    assert patterns[1] == [0, 1, 0, 0, 1, 0]
    assert patterns[2] == [0, 0, 1, 0, 0, 1]


def test_tp_matrix_uniform():
    v = [0, 1, 2, 0, 1, 2]
    M = _tp_matrix(v)
    # From 0: goes to 1 (1x). From 1: goes to 2 (2x). From 2: goes to 0 (1x).
    assert M[0][1] == 1.0
    assert M[2][0] == 1.0


def test_tp_matrix_no_self_transitions_if_forced():
    # Verify that TP matrix rows sum to 1 for visited states
    v = [0, 1, 0, 2, 1, 2]
    M = _tp_matrix(v)
    for row in M:
        s = sum(row)
        assert s == 0.0 or abs(s - 1.0) < 1e-9


# ── TP modes ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n_words,n_sylls,n_reps", [(4, 3, 4), (2, 2, 3)])
def test_pseudo_rand_tp_uniform_length(n_words, n_sylls, n_reps):
    random.seed(42)
    np.random.seed(42)
    v, M = pseudo_rand_tp_uniform(n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_reps)
    expected = n_sylls * n_words * n_words * n_reps
    assert len(v) == expected


def test_pseudo_rand_tp_uniform_no_self_transitions():
    random.seed(42)
    np.random.seed(42)
    v, M = pseudo_rand_tp_uniform(n_words=4, n_sylls_per_word=3, n_repetitions=4)
    for i in range(len(v) - 1):
        assert v[i] != v[i + 1], "Self-transition found"


def test_pseudo_rand_tp_uniform_matrix_diagonal_zero():
    random.seed(42)
    np.random.seed(42)
    _, M = pseudo_rand_tp_uniform(n_words=4, n_sylls_per_word=3, n_repetitions=4)
    # Diagonal must be zero (no self-transitions)
    assert all(M[i][i] == pytest.approx(0.0) for i in range(len(M)))


def test_pseudo_rand_tp_uniform_matrix_uniform():
    """Off-diagonal TP values should all be floor(n_iters/n_iters) or ceil of that."""
    random.seed(42)
    np.random.seed(42)
    n_words, n_sylls, n_reps = 4, 3, 4
    n_total = n_words * n_sylls
    n_iters = n_words * n_reps  # out-degree per node
    _, M = pseudo_rand_tp_uniform(n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_reps)
    # TP values = edge_count / n_iters; edge count is base or base+1
    base = n_iters // (n_total - 1)
    lo = base / n_iters
    hi = (base + 1) / n_iters
    for i in range(n_total):
        for j in range(n_total):
            if i != j:
                assert M[i][j] == pytest.approx(lo, abs=1e-9) or M[i][j] == pytest.approx(hi, abs=1e-9)


@pytest.mark.parametrize("n_words,n_sylls,n_reps", [(4, 3, 4), (2, 2, 3)])
def test_pseudo_rand_tp_struct_length(n_words, n_sylls, n_reps):
    random.seed(42)
    np.random.seed(42)
    v, M = pseudo_rand_tp_struct(n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_reps)
    # word-structured: v is word indexes, length = n_words² * n_reps
    # (each word appears n_words * n_reps times)
    assert len(v) == n_words * n_words * n_reps


@pytest.mark.parametrize("n_words,n_sylls,n_reps", [(4, 3, 4), (2, 2, 3)])
def test_pseudo_rand_tp_position_controlled_length(n_words, n_sylls, n_reps):
    random.seed(42)
    np.random.seed(42)
    v, M = pseudo_rand_tp_uniform_position_controlled(
        n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_reps
    )
    expected = n_sylls * n_words * n_words * n_reps
    assert len(v) == expected


def test_pseudo_rand_tp_position_controlled_matrix():
    random.seed(42)
    np.random.seed(42)
    n_words = 4
    _, M = pseudo_rand_tp_uniform_position_controlled(
        n_words=n_words, n_sylls_per_word=3, n_repetitions=4
    )
    # Each row should only have 0 or 1/n_words as TP values
    valid = {0.0, 1 / n_words}
    for row in M:
        for val in row:
            assert round(val, 6) in {round(v, 6) for v in valid}, f"Unexpected TP value {val}"


# ── Rhythmicity ───────────────────────────────────────────────────────────────

def test_rhythmicity_index_returns_one_per_feature(lexicons):
    lex = lexicons[0]
    sylls = [s for w in lex for s in w.syllables]
    n_features = len(lex[0].syllables[0].binary_features)
    ri = rhythmicity_index(sylls, lag=3)
    assert len(ri) == n_features


def test_rhythmicity_index_range(lexicons):
    lex = lexicons[0]
    sylls = [s for w in lex for s in w.syllables]
    ri = rhythmicity_index(sylls, lag=3)
    assert all(0.0 <= v <= 1.0 for v in ri)


# ── Stream generation ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("tp_mode", ["random", "word_structured", "position_controlled"])
def test_make_stream_returns_stream(lexicons, tp_mode):
    random.seed(42)
    np.random.seed(42)
    lex = lexicons[0]
    stream = make_stream(lex, n_repetitions=4, tp_mode=tp_mode, max_tries=5)
    assert stream is not None
    assert isinstance(stream, Stream)


def test_make_stream_syllable_count(lexicons):
    random.seed(42)
    np.random.seed(42)
    lex = lexicons[0]
    n_words = len(lex)
    n_sylls = len(lex[0].syllables)
    n_reps = 4
    stream = make_stream(lex, n_repetitions=n_reps, tp_mode="random", max_tries=5)
    assert stream is not None
    expected = n_words * n_sylls * n_words * n_reps
    assert len(stream.syllables) == expected


def test_make_stream_has_rhythmicity(lexicons):
    random.seed(42)
    np.random.seed(42)
    stream = make_stream(lexicons[0], n_repetitions=4, tp_mode="random", max_tries=5)
    assert stream is not None
    assert len(stream.rhythmicity) > 0
    assert all(isinstance(v, float) for v in stream.rhythmicity.values())


def test_make_stream_tp_mode_stored(lexicons):
    random.seed(42)
    np.random.seed(42)
    for tp_mode in ["random", "word_structured", "position_controlled"]:
        stream = make_stream(lexicons[0], n_repetitions=4, tp_mode=tp_mode, max_tries=5)
        assert stream is not None
        assert stream.tp_mode == tp_mode


def test_make_streams_all_tp_modes(lexicons):
    random.seed(42)
    np.random.seed(42)
    streams = make_streams(
        lexicons, n_repetitions=4,
        tp_modes=("random", "word_structured", "position_controlled"),
        require_all_tp_modes=True, max_tries=5
    )
    assert len(streams) > 0
    tp_modes_found = {s.tp_mode for s in streams}
    assert "random" in tp_modes_found
    assert "word_structured" in tp_modes_found
    assert "position_controlled" in tp_modes_found


def test_make_streams_returns_list(lexicons):
    random.seed(42)
    np.random.seed(42)
    streams = make_streams(lexicons, n_repetitions=4, max_tries=5)
    assert isinstance(streams, list)
    assert all(isinstance(v, Stream) for v in streams)


def test_make_stream_max_rhythmicity(lexicons):
    """With max_rhythmicity=0 (impossible), make_stream should return None."""
    random.seed(42)
    np.random.seed(42)
    stream = make_stream(
        lexicons[0], n_repetitions=4, tp_mode="random",
        max_rhythmicity=0.0, max_tries=3
    )
    assert stream is None
