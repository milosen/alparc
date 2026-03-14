"""Load phoneme/syllable/n-gram corpora from bundled data files."""
import csv
from importlib import resources
from typing import Dict, Optional

import numpy as np
from scipy import stats

from .types import Phoneme, Syllable, Register, PHONEME_FEATURES


def _data(path: str):
    """Return an open-able path to a bundled data file."""
    return resources.files("alparc") / "data" / path


# ── Phonemes ──────────────────────────────────────────────────────────────────

def load_phonemes(lang: Optional[str] = "deu") -> Register:
    """Load phonemes with binary features.

    If lang='deu', restrict to phonemes appearing in the German corpus and
    attach word-position probability statistics.
    """
    with open(_data("phonemes.csv"), encoding="utf-8") as f:
        rows = list(csv.reader(f))

    feature_labels = rows[0][1:]
    assert feature_labels == PHONEME_FEATURES, "phonemes.csv feature columns changed"

    phonemes: Register = Register()
    for row in rows[1:]:
        phon_id = row[0]
        features = dict(zip(feature_labels, row[1:]))
        phonemes[phon_id] = Phoneme(id=phon_id, features=features)

    if lang == "deu":
        corpus = _load_phoneme_corpus_deu()
        filtered = Register()
        filtered.info = dict(phonemes.info)
        for phon_id in corpus:
            if phon_id in phonemes.keys():
                p = phonemes[phon_id]
                p.word_position_prob = corpus[phon_id].word_position_prob
                filtered[phon_id] = p
        return filtered

    return phonemes


def _load_phoneme_corpus_deu() -> Dict[str, Phoneme]:
    """Load German phoneme position statistics from unigrams.csv."""
    with open(_data("german/unigrams.csv"), encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]

    by_phoneme: Dict[str, list] = {}
    for phon, position in rows:
        phon = phon.replace('"', "").replace("g", "ɡ")
        by_phoneme.setdefault(phon, []).append(int(position))

    result: Dict[str, Phoneme] = {}
    for phon_id, positions in by_phoneme.items():
        max_pos = max(positions)
        word_pos_prob = {
            pos: positions.count(pos + 1) / len(positions)
            for pos in range(max_pos)
        }
        result[phon_id] = Phoneme(id=phon_id, features={}, word_position_prob=word_pos_prob)

    return result


# ── Syllable corpus ───────────────────────────────────────────────────────────

def load_syllable_corpus(lang: str = "deu", path: Optional[str] = None) -> Register:
    """Load syllable frequencies from corpus CSV.

    Returns a Register of Syllable objects with .freq and .prob populated.
    Used to filter generated syllables to those attested in the corpus.
    """
    if path is not None:
        csv_path = path
    elif lang == "deu":
        csv_path = _data("german/syllables.csv")
    elif lang == "eng":
        csv_path = _data("english/syllables.csv")
    else:
        raise ValueError(f"Language {lang!r} not supported")

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]

    result = Register()
    for syll_ipa, freq, prob in rows:
        result[syll_ipa] = Syllable(id=syll_ipa, freq=int(freq), prob=float(prob))
    return result


# ── N-gram corpora ────────────────────────────────────────────────────────────

def load_bigrams() -> Dict[str, float]:
    """Load German phoneme bigrams. Returns {bigram: p_uniform}.

    p_uniform is the two-sided p-value against a uniform distribution of
    log-frequencies. Higher values = more uniformly distributed = more natural.
    """
    with open(_data("german/bigrams.csv"), encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]

    freqs = [int(r[1]) for r in rows]
    p_vals = stats.uniform.sf(abs(stats.zscore(np.log(freqs))))

    return {
        row[0].replace("_", "").replace("g", "ɡ"): float(p)
        for row, p in zip(rows, p_vals)
    }


def load_trigrams() -> Dict[str, float]:
    """Load German phoneme trigrams. Returns {trigram: p_uniform}.

    Note: skips the first data row to match original corpus file behavior.
    """
    with open(_data("german/trigrams.csv"), encoding="utf-8") as f:
        rows = list(csv.reader(f))[1:]

    freqs = [int(r[1]) for r in rows]
    p_vals = stats.uniform.sf(abs(stats.zscore(np.log(freqs))))

    # rows[1:] matches original — first entry is skipped
    return {
        row[0].replace("_", "").replace("g", "ɡ"): float(p)
        for row, p in zip(rows[1:], p_vals)
    }
