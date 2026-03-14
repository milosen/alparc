"""ALPARC — Artificial Languages with Phonological, Acoustic, and Rhythmicity Controls.

Public API:
    generate(...)  — full pipeline: phonemes → syllables → words → lexicons → streams
    diagnose(...)  — analyse a custom lexicon supplied as IPA strings
"""
import datetime
import logging
import os
from typing import Dict, List, Literal, Optional, Tuple

import yaml

from .types import Phoneme, Syllable, Word, Stream, Register, LABELS_C, LABELS_V
from .corpus import load_phonemes
from .syllables import make_syllables, syllable_from_phonemes
from .words import make_words, word_overlap_matrix
from .lexicons import make_lexicons
from .streams import make_streams, make_stream, rhythmicity_index, get_oscillation_patterns
from .display import print_stream

logger = logging.getLogger(__name__)

__all__ = [
    # types
    "Phoneme", "Syllable", "Word", "Stream", "Register",
    "LABELS_C", "LABELS_V",
    # corpus
    "load_phonemes",
    # pipeline stages
    "make_syllables", "make_words", "make_lexicons", "make_streams",
    # helpers
    "syllable_from_phonemes", "word_overlap_matrix",
    "rhythmicity_index", "get_oscillation_patterns",
    # top-level
    "generate", "diagnose",
]


# ── Logging + output helpers ──────────────────────────────────────────────────

def _make_run_dir(base: str, name: str) -> str:
    """Create a timestamped subdirectory under *base* and return its path."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join(base, f"{name}_{ts}")
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def _configure_logging(run_dir: str, log_console: bool) -> None:
    """Add a file handler (DEBUG) and optional console handler (INFO) to the root logger."""
    root = logging.getLogger()
    if not root.handlers:
        root.setLevel(logging.DEBUG)

    log_path = os.path.join(run_dir, "debug.log")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    root.addHandler(fh)

    if log_console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        root.addHandler(ch)


def _write_config(run_dir: str, config: dict) -> None:
    path = os.path.join(run_dir, "config.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)


def _write_streams(run_dir: str, streams: Dict[str, Stream]) -> None:
    """Write streams.yaml with per-stream metadata and full syllable sequences."""
    records = []
    for stream in streams:
        records.append({
            "tp_mode": stream.tp_mode,
            "lexicon_id": stream.lexicon_id,
            "syllables": "|".join(s.id for s in stream.syllables),
            "n_syllables": len(stream.syllables),
            "rhythmicity": {k: round(v, 6) for k, v in stream.rhythmicity.items()},
        })
    path = os.path.join(run_dir, "streams.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump({"streams": records}, f, allow_unicode=True, sort_keys=False)


# ── Custom lexicon parsing ────────────────────────────────────────────────────

def _parse_word(phoneme_syllables: List[List[str]], phonemes_reg: Register) -> Word:
    """Build a Word from a list of syllables, each a list of phoneme IDs."""
    sylls = [syllable_from_phonemes(phonemes_reg, phons) for phons in phoneme_syllables]
    word_id = "".join(s.id for s in sylls)
    binary_features = [list(col) for col in zip(*[s.binary_features for s in sylls])]
    return Word(id=word_id, syllables=sylls, binary_features=binary_features)


def diagnose(
    lexicon: List[str],
    phoneme_pattern: str = "cv",
) -> Register:
    """Parse and analyse a custom lexicon.

    Args:
        lexicon: List of word strings. Phonemes are separated by '_', syllables by '|'.
            Example: ["k_a|t_a|l_a", "m_a|r_a|s_a"]
        phoneme_pattern: Syllable structure to assume ('cv' or 'cV').

    Returns:
        Register of Word objects with overlap stats in .info.
    """
    from .words import word_overlap_matrix
    import numpy as np

    all_phonemes = load_phonemes(lang=None)
    parsed = [[syll.split("_") for syll in word.split("|")] for word in lexicon]
    word_objs = [_parse_word(syllables, all_phonemes) for syllables in parsed]

    reg = Register({w.id: w for w in word_objs})
    reg.info = {
        "syllables_info": {
            "syllable_feature_labels": [LABELS_C, LABELS_V],
            "syllable_type": phoneme_pattern,
        }
    }
    ov = word_overlap_matrix(reg)
    reg.info["cumulative_feature_repetitiveness"] = int(np.triu(ov, 1).sum())
    reg.info["max_pairwise_feature_repetitiveness"] = int(np.triu(ov, 1).max())
    return reg


# ── Full pipeline ─────────────────────────────────────────────────────────────

def generate(
    lang: str = "deu",
    # syllable stage
    phoneme_pattern: str = "cV",
    syllable_control: bool = True,
    syllable_alpha: Optional[float] = 0.05,
    syllable_corpus: Optional[str] = None,
    # word stage
    n_syllables_per_word: int = 3,
    n_words: int = 10_000,
    max_word_tries: int = 100_000,
    phonotactic_control: bool = True,
    n_look_back: int = 2,
    bigram_control: bool = True,
    bigram_alpha: Optional[float] = None,
    trigram_control: bool = True,
    trigram_alpha: Optional[float] = None,
    positional_control: bool = True,
    positional_position: Optional[int] = None,
    position_alpha: float = 0.0,
    # lexicon stage
    n_lexicons: int = 2,
    n_words_per_lexicon: int = 4,
    binary_feature_control: bool = True,
    max_overlap: int = 1,
    lag_of_interest: int = 1,
    max_word_matrix: int = 200,
    unique_words: bool = False,
    # stream stage
    n_repetitions: int = 15,
    n_streams_per_lexicon: int = 2,
    tp_modes: tuple = ("random", "word_structured", "position_controlled"),
    max_rhythmicity: Optional[float] = None,
    max_tries_randomize: int = 10,
    require_all_tp_modes: bool = True,
    # misc
    progress_bars: bool = True,
    lexicons: Optional[List[List[str]]] = None,
    # output
    out_dir: Optional[str] = None,
    log_console: bool = False,
) -> Dict[str, Stream]:
    """Run the full ALPARC pipeline and return generated streams.

    If *lexicons* is provided (list of list of IPA word strings), skips phoneme/syllable/word
    generation and goes straight to stream generation from that lexicon.

    If *out_dir* is set, a timestamped run directory is created inside it containing:
        config.yaml  — all parameters passed to this call
        streams.yaml — per-stream syllable sequences and rhythmicity values
        debug.log    — full DEBUG-level log

    Returns:
        Dict mapping stream ID → Stream object.
        Each stream has .tp_mode, .rhythmicity, .lexicon_id, and .syllables.
    """
    # Collect all parameters for config.yaml (exclude non-serialisable defaults)
    config = dict(
        lang=lang, phoneme_pattern=phoneme_pattern,
        syllable_control=syllable_control, syllable_alpha=syllable_alpha,
        syllable_corpus=syllable_corpus,
        n_syllables_per_word=n_syllables_per_word, n_words=n_words,
        max_word_tries=max_word_tries, phonotactic_control=phonotactic_control,
        n_look_back=n_look_back, bigram_control=bigram_control,
        bigram_alpha=bigram_alpha, trigram_control=trigram_control,
        trigram_alpha=trigram_alpha, positional_control=positional_control,
        positional_position=positional_position, position_alpha=position_alpha,
        n_lexicons=n_lexicons, n_words_per_lexicon=n_words_per_lexicon,
        binary_feature_control=binary_feature_control, max_overlap=max_overlap,
        lag_of_interest=lag_of_interest, max_word_matrix=max_word_matrix,
        unique_words=unique_words,
        n_repetitions=n_repetitions, n_streams_per_lexicon=n_streams_per_lexicon,
        tp_modes=list(tp_modes), max_rhythmicity=max_rhythmicity,
        max_tries_randomize=max_tries_randomize,
        require_all_tp_modes=require_all_tp_modes,
        lexicons=lexicons,
    )

    run_dir: Optional[str] = None
    if out_dir is not None:
        run_dir = _make_run_dir(out_dir, name="generate")
        _configure_logging(run_dir, log_console)
        _write_config(run_dir, config)
        logger.info("Run directory: %s", run_dir)

    if lexicons is not None:
        lexicons = [diagnose(lexicon) for lexicon in lexicons]
        streams = _generate_streams(
            lexicons,
            n_repetitions=n_repetitions,
            n_streams_per_lexicon=n_streams_per_lexicon,
            tp_modes=tp_modes,
            max_rhythmicity=max_rhythmicity,
            max_tries_randomize=max_tries_randomize,
            require_all_tp_modes=require_all_tp_modes,
        )
        if run_dir is not None:
            _write_streams(run_dir, streams)
        return streams

    # 1. Phonemes
    phonemes = load_phonemes(lang=lang)
    logger.info("Loaded %d phonemes", len(phonemes))

    # 2. Syllables
    try:
        syllables = make_syllables(
            phonemes,
            pattern=phoneme_pattern,
            lang=lang,
            syllable_control=syllable_control,
            alpha=syllable_alpha,
            corpus_path=syllable_corpus,
        )
        logger.info("Generated %d syllables", len(syllables))
    except FileNotFoundError:
        syllables = None
        logging.warning("Selected lenguage 'eng' but no denglish corpus dataset found. Please make sure to provide one.")

    if not syllables:
        raise RuntimeError("No syllables generated — check phoneme pattern and corpus settings.")

    # 3. Words
    words = make_words(
        syllables,
        n_syllables=n_syllables_per_word,
        n_words=n_words,
        max_tries=max_word_tries,
        phonotactic_control=phonotactic_control,
        n_look_back=n_look_back,
        bigram_control=bigram_control,
        bigram_alpha=bigram_alpha,
        trigram_control=trigram_control,
        trigram_alpha=trigram_alpha,
        positional_control=positional_control,
        positional_position=positional_position,
        position_alpha=position_alpha,
        lang=lang,
        progress_bar=progress_bars,
    )
    logger.info("Generated %d pseudo-words", len(words))

    if not words:
        raise RuntimeError("No words generated — try reducing filter strictness.")

    # 4. Lexicons
    lexicons = make_lexicons(
        words,
        n_lexicons=n_lexicons,
        n_words=n_words_per_lexicon,
        max_overlap=max_overlap,
        lag=lag_of_interest,
        max_word_matrix=max_word_matrix,
        unique_words=unique_words,
        binary_feature_control=binary_feature_control,
        progress_bar=progress_bars,
    )
    logger.info("Generated %d lexicons", len(lexicons))

    streams = _generate_streams(
        lexicons,
        n_repetitions=n_repetitions,
        n_streams_per_lexicon=n_streams_per_lexicon,
        tp_modes=tp_modes,
        max_rhythmicity=max_rhythmicity,
        max_tries_randomize=max_tries_randomize,
        require_all_tp_modes=require_all_tp_modes,
    )

    if run_dir is not None:
        _write_streams(run_dir, streams)
        logger.info("Results written to %s", run_dir)

    return streams


def _generate_streams(
    lexicons,
    n_repetitions,
    n_streams_per_lexicon,
    tp_modes: Tuple[Literal["random", "word_structured", "position_controlled"]],
    max_rhythmicity,
    max_tries_randomize,
    require_all_tp_modes,
) -> Dict[str, Stream]:
    all_streams = []
    for _ in range(n_streams_per_lexicon):
        batch = make_streams(
            lexicons,
            n_repetitions=n_repetitions,
            tp_modes=tp_modes,
            max_rhythmicity=max_rhythmicity,
            max_tries=max_tries_randomize,
            require_all_tp_modes=require_all_tp_modes,
        )
        for stream in batch:
            all_streams.append(stream)
    logger.info("Generated %d streams", len(all_streams))
    return all_streams
