"""Integration tests for the full generate() and diagnose() pipeline."""
import os
import pytest
import random
import numpy as np
import yaml
from alparc import generate, diagnose
from alparc.types import Stream, Word, Register


@pytest.fixture(autouse=True)
def seed():
    random.seed(99)
    np.random.seed(99)


def test_generate_returns_streams():
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=2, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
    )
    assert isinstance(streams, list)
    assert len(streams) > 0
    assert all(isinstance(v, Stream) for v in streams)


def test_generate_stream_has_syllables():
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
    )
    for stream in streams:
        assert len(stream.syllables) > 0


def test_generate_stream_has_rhythmicity():
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
    )
    for stream in streams:
        assert len(stream.rhythmicity) > 0
        assert all(0.0 <= v <= 1.0 for v in stream.rhythmicity.values())


def test_generate_all_tp_modes():
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=2, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
        tp_modes=("random", "word_structured", "position_controlled"),
        require_all_tp_modes=True,
    )
    tp_modes = {s.tp_mode for s in streams}
    assert "random" in tp_modes
    assert "word_structured" in tp_modes
    assert "position_controlled" in tp_modes


def test_generate_cv_pattern():
    streams = generate(
        phoneme_pattern="cv",
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
    )
    assert len(streams) > 0


def test_generate_from_custom_lexicon():
    """generate() with a custom lexicon should skip phoneme/word generation."""
    streams = generate(
        lexicons=[[
        "f_oː|ɡ_uː|r_iː",
        "b_aː|d_eː|n_yː",
        "l_iː|k_uː|t_eː",
        "m_oː|p_aː|s_eː",
    ]],
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
    )
    assert len(streams) > 0


def test_diagnose_returns_register():
    lexicon_words = [
        "k_a|t_a|l_a",
        "m_a|r_a|s_a",
        "b_o|n_a|d_i",
        "f_u|ɡ_e|s_i",   # ɡ = IPA voiced velar stop (not ASCII g)
    ]
    reg = diagnose(lexicon_words)
    assert isinstance(reg, Register)
    assert len(reg) == 4
    assert all(isinstance(w, Word) for w in reg)


def test_diagnose_overlap_info():
    lexicon_words = [
        "k_a|t_a|l_a",
        "m_a|r_a|s_a",
        "b_o|n_a|d_i",
        "f_u|ɡ_e|s_i",
    ]
    reg = diagnose(lexicon_words)
    assert "cumulative_feature_repetitiveness" in reg.info
    assert "max_pairwise_feature_repetitiveness" in reg.info
    assert isinstance(reg.info["cumulative_feature_repetitiveness"], int)


def test_diagnose_word_ids():
    lexicon_words = ["k_a|t_a", "m_i|r_u"]
    reg = diagnose(lexicon_words)
    assert "kata" in reg.keys()
    assert "miru" in reg.keys()


def test_generate_writes_output(tmp_path):
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
        tp_modes=("random",), require_all_tp_modes=False,
        out_dir=str(tmp_path),
    )
    # A single timestamped run dir should have been created
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert run_dir.name.startswith("generate_")

    # config.yaml must exist and contain expected keys
    config_path = run_dir / "config.yaml"
    assert config_path.exists()
    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert "n_repetitions" in config
    assert "tp_modes" in config
    assert config["n_repetitions"] == 4

    # streams.yaml must exist with at least one entry
    streams_path = run_dir / "streams.yaml"
    assert streams_path.exists()
    with open(streams_path) as f:
        data = yaml.safe_load(f)
    assert "streams" in data
    assert len(data["streams"]) == len(streams)
    record = data["streams"][0]
    assert "tp_mode" in record
    assert "syllables" in record
    assert "rhythmicity" in record
    assert "|" in record["syllables"]

    # debug.log must exist
    assert (run_dir / "debug.log").exists()


def test_generate_no_output_by_default(tmp_path):
    """When out_dir is not set, no files should be written."""
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=4,
        n_repetitions=4, n_streams_per_lexicon=1, progress_bars=False,
        tp_modes=("random",), require_all_tp_modes=False,
    )
    assert len(streams) > 0
    # tmp_path should be completely empty
    assert list(tmp_path.iterdir()) == []


def test_generate_stream_length():
    """Stream length = n_words * n_sylls * n_words * n_reps."""
    n_reps = 4
    n_words = 4
    n_sylls = 3  # default
    streams = generate(
        n_words=200, max_word_tries=3000, n_lexicons=1, n_words_per_lexicon=n_words,
        n_repetitions=n_reps, n_streams_per_lexicon=1, progress_bars=False,
        tp_modes=("random",), require_all_tp_modes=False,
    )
    expected = n_words * n_sylls * n_words * n_reps
    for stream in streams:
        assert len(stream.syllables) == expected


def test_generate_with_diphthong_lexicon_rhythmicity():
    """Streams generated from a custom lexicon containing diphthong vowels must
    have a fully-populated rhythmicity dict (one entry per binary feature)."""
    from alparc.types import LABELS_C, LABELS_V
    n_features = len(LABELS_C) + len(LABELS_V)  # 15

    lexicon = [
        "p_eɪ|b_oʊ|t_a",
        "m_i|d_oʊ|k_eɪ",
        "f_a|s_oʊ|n_eɪ",
        "l_oʊ|ɡ_i|v_eɪ",
    ]
    streams = generate(
        lexicons=[lexicon],
        n_repetitions=4,
        n_streams_per_lexicon=1,
        tp_modes=("word_structured",),
        require_all_tp_modes=False,
        progress_bars=False,
    )
    assert len(streams) > 0
    for stream in streams:
        assert len(stream.rhythmicity) == n_features, (
            f"expected {n_features} rhythmicity entries, got {len(stream.rhythmicity)}"
        )
