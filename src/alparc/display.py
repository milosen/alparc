"""Terminal / Jupyter display utilities for ALPARC streams."""
import html
import math
from typing import Optional

import numpy as np

from .types import Stream, LABELS_C, LABELS_V

_ON  = "█"
_OFF = "░"


def _is_jupyter() -> bool:
    """Return True when running inside a Jupyter kernel."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
        return shell is not None and shell.__class__.__name__ == "ZMQInteractiveShell"
    except ImportError:
        return False


def _compute_incremental_tps(
    stream: list,
    n_symbols: int,
) -> np.ndarray:
    """Compute cumulative empirical transition probabilities at every time step.

    At each time step t, returns the row-normalised transition probability
    matrix estimated from transitions (v_1,v_2), ..., (v_{t-1}, v_t).

    Parameters
    ----------
    stream : list[int]
        Sequence of symbol indices in [0, n_symbols).
    n_symbols : int
        Alphabet size N.

    Returns
    -------
    np.ndarray, shape (T-1,)
        tps[t] is the empirical P(stream[t+1] | stream[t]) estimated from
        the first t+1 transitions (i.e. after observing v_1, ..., v_{t+2}).
    """
    T = len(stream)
    counts = np.zeros((n_symbols, n_symbols), dtype=float)
    tps = np.zeros((T - 1, n_symbols, n_symbols), dtype=float)

    for t in range(T - 1):
        i, j = stream[t], stream[t + 1]
        counts[i, j] += 1

        row_sums = counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        tps[t] = counts / row_sums

    return tps[np.arange(len(stream[:-1])), stream[:-1], stream[1:]].flatten()


def _empirical_surprisals(stream: Stream, n: int) -> list:
    """Return per-syllable surprisal (-log2 of incremental empirical TP) for the first *n* syllables.

    Surprisal at position i is -log2(P(syll[i] | syll[i-1])) under the empirical
    transition matrix estimated from all transitions up to and including position i.
    The first syllable has no predecessor and is represented as None.
    """
    all_sylls = stream.syllables

    # Map syllable id -> integer index (preserving first-seen order)
    seen: dict = {}
    for s in all_sylls:
        if s.id not in seen:
            seen[s.id] = len(seen)

    indices = [seen[s.id] for s in all_sylls]
    probs = _compute_incremental_tps(indices, len(seen))

    result: list = [None]  # position 0 has no predecessor
    for p in probs[:n - 1]:
        result.append(-math.log2(p) if p > 0 else float("inf"))
    return result


def _fmt_surprisal(v, col_w: int) -> str:
    """Format a surprisal value to fit in *col_w* characters, centred."""
    if v is None:
        return "·".center(col_w)
    if math.isinf(v):
        return "∞".center(col_w)
    # Choose precision that fits; fall back to least-precise if all overflow
    candidates = (f"{v:.2f}", f"{v:.1f}", f"{round(v)}")
    for fmt in candidates:
        if len(fmt) <= col_w:
            return fmt.center(col_w)
    return candidates[-1].center(col_w)  # let it overflow rather than lose the value


def _build_lines(stream: Stream, max_cols: int, word_length: Optional[int], start_at: int = 0) -> list[str]:
    """Build the display as a list of plain-text lines."""
    sylls = stream.syllables[start_at:start_at + max_cols]
    n = len(sylls)
    if n == 0:
        return [f"Stream {stream.id}  (empty)"]

    n_c = len(LABELS_C)
    col_w   = max(len(s.id) for s in sylls)
    label_w = max(len(l) for l in LABELS_C + LABELS_V + ["surprisal"])

    def _row(bits):
        cells = [(_ON if b else _OFF).center(col_w) for b in bits]
        if word_length:
            groups = [cells[i : i + word_length] for i in range(0, n, word_length)]
            return "│".join(" ".join(g) for g in groups)
        return " ".join(cells)

    def _syll_row():
        ids = [s.id.center(col_w) for s in sylls]
        if word_length:
            groups = [ids[i : i + word_length] for i in range(0, n, word_length)]
            return "│".join(" ".join(g) for g in groups)
        return " ".join(ids)

    sample  = _row([0] * n)
    sep     = " " * label_w + "  " + "─" * len(sample)
    pad     = " " * label_w

    lines = []

    # header
    header = f"Stream   {stream.id}"
    if stream.tp_mode:
        header += f"  [{stream.tp_mode}]"
    if stream.rhythmicity:
        vals = list(stream.rhythmicity.values())
        header += f"  mean_PRI={sum(vals)/len(vals):.3f}  max_PRI={max(vals):.3f}"
    lines.append(header)
    if stream.lexicon_id:
        lines.append(f"Lexicon  {stream.lexicon_id}")
    lines.append("")

    # surprisal row (below header/lexicon, aligned with feature columns)
    surp = _empirical_surprisals(stream, start_at + n)[start_at:]
    surp_cells = [_fmt_surprisal(v, col_w) for v in surp]
    if word_length:
        groups = [surp_cells[i : i + word_length] for i in range(0, n, word_length)]
        surp_row = "│".join(" ".join(g) for g in groups)
    else:
        surp_row = " ".join(surp_cells)
    lines.append("surprisal".rjust(label_w) + "  " + surp_row)
    lines.append(sep)

    # consonant features
    for i, lbl in enumerate(LABELS_C):
        lines.append(lbl.rjust(label_w) + "  " + _row([s.binary_features[i] for s in sylls]))
    lines.append(sep)

    # vowel features
    for i, lbl in enumerate(LABELS_V):
        lines.append(lbl.rjust(label_w) + "  " + _row([s.binary_features[n_c + i] for s in sylls]))
    lines.append(sep)

    # syllable labels
    lines.append(pad + "  " + _syll_row())

    remaining = len(stream.syllables) - start_at - max_cols
    if remaining > 0:
        lines.append(pad + f"Total: {len(stream.syllables)} Syllables. Visualized: [{start_at}, {start_at + max_cols}] ({max_cols} Syllables)")

    return lines


def print_stream(
    stream: Stream,
    max_cols: int = 40,
    word_length: Optional[int] = None,
    start_at: int = 0,
) -> None:
    """Pretty-print a stream as a binary feature matrix over syllables.

    In a terminal the output is printed directly. In a Jupyter notebook it is
    rendered as an HTML <pre> block with a pinned monospace font so that block
    characters (█ ░) and IPA syllable labels stay column-aligned.

    Args:
        stream:      the Stream to display
        max_cols:    maximum number of syllables to show (default 40)
        word_length: if given, insert │ boundaries every word_length syllables
        start_at:    index of the first syllable to display (default 0);
                     surprisal values are always computed from the beginning
                     of the stream
    """
    lines = _build_lines(stream, max_cols, word_length, start_at)

    if _is_jupyter():
        from IPython.display import display, HTML
        escaped = html.escape("\n".join(lines))
        display(HTML(
            "<pre style='"
            "font-family: monospace, monospace;"
            "font-size: 0.9em;"
            "line-height: 1.4;"
            "'>" + escaped + "</pre>"
        ))
    else:
        print("\n".join(lines))
