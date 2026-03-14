"""Stream generation with three TP (transitional probability) control modes.

The three modes differ in how syllable ordering is controlled:
    random              — uniform TP across all syllables
    word_structured     — TPs respect word boundaries (words = atomic units)
    position_controlled — syllables constrained to their within-word position

All three modes now use an Eulerian-circuit approach for exact, uniform TPs
in O(stream_length) time. Previously the original code used rejection sampling
which could take O(stream_length² × max_tries).

Algorithmic background
-----------------------
A stream with uniform TPs can be constructed by:
1. Building a directed multigraph where each node has out_degree = in_degree (a balanced
   digraph), with edges distributed as evenly as possible between all allowed pairs.
2. Finding an Eulerian circuit in this graph (Hierholzer's algorithm, O(edges)).
3. The circuit visits every edge exactly once, giving exactly the desired TP counts.
"""
import logging
import random
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np

from .types import Syllable, Word, Stream, Register

logger = logging.getLogger(__name__)


# ── Utility ───────────────────────────────────────────────────────────────────

def get_oscillation_patterns(lag: int) -> List[List[int]]:
    """Return binary oscillation kernels with period 2*lag.

    Used to detect features that repeat at the word-frequency rate.
    """
    kernel = [1] + [0] * (lag - 1) + [1] + [0] * (lag - 1)
    return [list(np.roll(kernel, i)) for i in range(lag)]


def _tp_matrix(v: List[int]) -> List[List[float]]:
    """Compute transitional probability matrix from a sequence of integer indices."""
    n = 1 + max(v)
    counts: List[List[float]] = [[0.0] * n for _ in range(n)]
    for a, b in zip(v, v[1:]):
        counts[a][b] += 1
    for row in counts:
        s = sum(row)
        if s > 0:
            for k in range(n):
                row[k] /= s
    return counts


# ── Eulerian-circuit graph builders ──────────────────────────────────────────

def _build_balanced_digraph(n_nodes: int, out_degree: int) -> dict:
    """Build a balanced directed multigraph: every node has exactly *out_degree* outgoing edges.

    Edges are distributed as uniformly as possible over all (n_nodes-1) other nodes.
    The cyclic remainder assignment ensures in_degree == out_degree for all nodes,
    guaranteeing the existence of an Eulerian circuit.
    """
    base, remainder = divmod(out_degree, n_nodes - 1)
    adj: dict = {i: [] for i in range(n_nodes)}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if j != i:
                adj[i].extend([j] * base)
        # Distribute remainder cyclically so every node also receives 'remainder' extras
        for k in range(1, remainder + 1):
            adj[i].append((i + k) % n_nodes)
    for i in adj:
        random.shuffle(adj[i])
    return adj


def _build_position_controlled_digraph(
    n_words: int, n_sylls_per_word: int, n_repetitions: int
) -> dict:
    """Build position-constrained directed multigraph.

    Syllable in position group k can only transition to group (k+1) % n_sylls_per_word.
    Each cross-group pair (i, j) gets exactly *n_repetitions* directed edges.
    in_degree == out_degree == n_words * n_repetitions for every node.
    """
    n_total = n_words * n_sylls_per_word
    pools = [list(range(k, n_total, n_sylls_per_word)) for k in range(n_sylls_per_word)]
    adj: dict = {i: [] for i in range(n_total)}
    for k in range(n_sylls_per_word):
        src_pool = pools[k]
        tgt_pool = pools[(k + 1) % n_sylls_per_word]
        for i in src_pool:
            adj[i] = tgt_pool * n_repetitions
            random.shuffle(adj[i])
    return adj


def _hierholzer(adj: dict, start: int) -> List[int]:
    """Eulerian circuit via Hierholzer's algorithm.

    Returns a node sequence where the first and last elements are equal.
    adj is consumed (modified in place on the copy).
    Time complexity: O(edges).
    """
    adj_copy: dict = {i: list(v) for i, v in adj.items()}
    stack = [start]
    circuit: List[int] = []
    while stack:
        v = stack[-1]
        if adj_copy[v]:
            stack.append(adj_copy[v].pop())
        else:
            circuit.append(stack.pop())
    circuit.reverse()
    return circuit  # circuit[0] == circuit[-1]


def _hierholzer_greedy(
    adj: dict, start: int, n_nodes: int
) -> List[int]:
    """
    Eulerian circuit via Hierholzer's algorithm with greedy edge selection.
    At each step, among all available outgoing edges from the current node,
    prefer the neighbour whose (current -> neighbour) count is minimal.
    This encourages incremental TP balance throughout the walk.
    """
    adj_copy: dict = {i: list(v) for i, v in adj.items()}
    counts = np.zeros((n_nodes, n_nodes), dtype=int)
    stack = [start]
    circuit: List[int] = []

    while stack:
        v = stack[-1]
        if adj_copy[v]:
            # Greedy: pick neighbour with minimum current transition count
            min_count = min(counts[v, w] for w in adj_copy[v])
            candidates = [w for w in adj_copy[v] if counts[v, w] == min_count]
            chosen = random.choice(candidates)
            adj_copy[v].remove(chosen)
            counts[v, chosen] += 1
            stack.append(chosen)
        else:
            circuit.append(stack.pop())

    circuit.reverse()
    return circuit


# ── TP mode functions ─────────────────────────────────────────────────────────

def pseudo_rand_tp_uniform(
    n_words: int = 4, n_sylls_per_word: int = 3, n_repetitions: int = 15
) -> Tuple[List[int], np.ndarray]:
    """Generate a syllable stream with exactly uniform transitional probabilities.

    Every ordered pair of distinct syllables appears ⌊k⌋ or ⌈k⌉ times where
    k = n_iters / (n_total - 1).

    Returns:
        (syllable_index_sequence, tp_matrix)
        Stream length: n_words * n_sylls_per_word * n_words * n_repetitions
    """
    n_total = n_sylls_per_word * n_words
    n_iters = n_words * n_repetitions  # out-degree per node

    adj = _build_balanced_digraph(n_total, n_iters)
    circuit = _hierholzer_greedy(adj, start=random.randrange(n_total), n_nodes=n_total)
    v = circuit[:-1]  # drop the repeated start node

    v.append(v[0])
    M = np.array(_tp_matrix(v))
    v.pop()
    return v, M


def pseudo_rand_tp_struct(
    n_words: int = 4, n_sylls_per_word: int = 3, n_repetitions: int = 15
) -> Tuple[List[int], np.ndarray]:
    """Generate a word-index stream with uniform word-level transitional probabilities.

    Words are treated as atomic units; this function returns *word indices* (not syllable
    indices). The caller expands each word index to its constituent syllables.

    Returns:
        (word_index_sequence, tp_matrix_over_words)
        Sequence length: n_words * n_words * n_repetitions
    """
    out_degree = n_words * n_repetitions  # each word "appears" this many times

    adj = _build_balanced_digraph(n_words, out_degree)
    circuit = _hierholzer_greedy(adj, start=random.randrange(n_words), n_nodes=n_words)
    v = circuit[:-1]

    v.append(v[0])
    M = np.array(_tp_matrix(v))
    v.pop()
    return v, M


def pseudo_rand_tp_uniform_position_controlled(
    n_words: int = 4, n_sylls_per_word: int = 3, n_repetitions: int = 15
) -> Tuple[List[int], np.ndarray]:
    """Generate a syllable stream where each syllable is constrained to its within-word position.

    Each pos-k syllable only follows a pos-(k-1) syllable, and TPs within each
    cross-position group are uniform (1/n_words).

    Returns:
        (syllable_index_sequence, tp_matrix)
        Stream length: n_words * n_sylls_per_word * n_words * n_repetitions
    """
    adj = _build_position_controlled_digraph(n_words, n_sylls_per_word, n_repetitions)
    # Start from a position-0 syllable for a clean stream beginning
    pos0_nodes = list(range(0, n_words * n_sylls_per_word, n_sylls_per_word))
    circuit = _hierholzer_greedy(adj, start=random.choice(pos0_nodes), n_nodes=n_words*n_sylls_per_word)
    v = circuit[:-1]

    v.append(v[0])
    M = np.array(_tp_matrix(v))
    v.pop()
    return v, M


# ── Rhythmicity ───────────────────────────────────────────────────────────────

def rhythmicity_index(
    stream_syllables: List[Syllable], lag: int
) -> List[float]:
    """Compute the Pattern Repetition Index (PRI) for each feature.

    For each feature, PRI = fraction of stream positions where the feature
    matches one of the oscillation patterns at the given lag.

    Returns a list of PRI values, one per feature dimension.
    """
    patterns = [tuple(p) for p in get_oscillation_patterns(lag)]
    feature_streams = list(zip(*[s.binary_features for s in stream_syllables]))
    window = max(len(p) for p in patterns)

    counts: List[float] = []
    for feat_stream in feature_streams:
        n = len(feat_stream) - window
        if n <= 0:
            counts.append(0.0)
            continue
        c = sum(
            1 for i in range(n)
            if any(feat_stream[i: i + len(p)] == p for p in patterns)
        )
        counts.append(c / n)

    return counts


def _feature_labels_for_stream(lexicon: Register) -> List[str]:
    """Build feature label strings like 'phon_1_son' for rhythmicity dict keys."""
    feat_labels_nested = lexicon.info["syllables_info"]["syllable_feature_labels"]
    return [
        f"phon_{i + 1}_{label}"
        for i, labels in enumerate(feat_labels_nested)
        for label in labels
    ]


# ── Stream construction ───────────────────────────────────────────────────────

_TP_FUNCS = {
    "random": pseudo_rand_tp_uniform,
    "word_structured": pseudo_rand_tp_struct,
    "position_controlled": pseudo_rand_tp_uniform_position_controlled,
}


def _syllable_sequence(
    lexicon: Register,
    tp_mode: Literal["random", "word_structured", "position_controlled"],
    n_repetitions: int,
) -> List[Syllable]:
    """Generate one syllable sequence from *lexicon* using the given TP mode."""
    n_sylls = len(lexicon[0].syllables)
    n_words = len(lexicon)
    rand_func = _TP_FUNCS[tp_mode]

    if tp_mode == "word_structured":
        words_list = list(lexicon.values())
        indexes, _ = rand_func(n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_repetitions)
        return [syll for idx in indexes for syll in words_list[idx].syllables]
    else:
        sylls_list = [s for w in lexicon for s in w.syllables]
        indexes, _ = rand_func(n_words=n_words, n_sylls_per_word=n_sylls, n_repetitions=n_repetitions)
        return [sylls_list[idx] for idx in indexes]


def make_stream(
    lexicon: Register,
    n_repetitions: int = 15,
    tp_mode: Literal["random", "word_structured", "position_controlled"] = "word_structured",
    max_rhythmicity: Optional[float] = None,
    max_tries: int = 10,
) -> Optional[Stream]:
    """Build one stream from *lexicon* with the given TP mode.

    If max_rhythmicity is set, streams where any feature's PRI exceeds it are
    discarded and a new sequence is generated (up to max_tries attempts).

    Returns None if no valid stream found within max_tries.
    """
    n_sylls_per_word = len(lexicon[0].syllables)
    feat_labels = _feature_labels_for_stream(lexicon)
    seen: List[List[int]] = []

    for _ in range(max_tries):
        sylls = _syllable_sequence(lexicon, tp_mode, n_repetitions)
        syll_ids = [s.id for s in sylls]

        if syll_ids in seen:
            continue
        seen.append(syll_ids)

        ri = rhythmicity_index(sylls, lag=n_sylls_per_word)
        if max_rhythmicity is not None and max(ri) > max_rhythmicity:
            continue

        lexicon_id = "||".join(w.id for w in lexicon)
        stream_id = (
            "_".join(s.id for s in sylls[:5]) + "..." + "_".join(s.id for s in sylls[-5:])
        )
        return Stream(
            id=stream_id,
            syllables=sylls,
            tp_mode=tp_mode,
            rhythmicity={k: float(v) for k, v in zip(feat_labels, ri)},
            lexicon_id=lexicon_id,
            cum_pri=lexicon.info["cumulative_feature_repetitiveness"],
            max_pair_pri=lexicon.info["max_pairwise_feature_repetitiveness"]
        )

    return None


def make_streams(
    lexicons: List[Register],
    n_repetitions: int = 15,
    tp_modes: tuple = ("random", "word_structured", "position_controlled"),
    max_rhythmicity: Optional[float] = None,
    max_tries: int = 10,
    require_all_tp_modes: bool = True,
) -> Dict[str, Stream]:
    """Build streams for each lexicon × TP mode combination.

    If require_all_tp_modes is True, a lexicon is skipped unless all requested
    TP modes yield a valid stream (only relevant when max_rhythmicity is set).

    Returns a dict mapping stream_id → Stream.
    """
    streams = []

    for i, lexicon in enumerate(lexicons):
        new_streams = []
        all_found = True

        for tp_mode in tp_modes:
            stream = make_stream(
                lexicon,
                n_repetitions=n_repetitions,
                tp_mode=tp_mode,
                max_rhythmicity=max_rhythmicity,
                max_tries=max_tries,
            )
            if stream is None:
                logger.warning("No stream found for lexicon %d with tp_mode=%s", i, tp_mode)
                all_found = False
                break
            new_streams.append(stream)

        if all_found or not require_all_tp_modes:
            for new_stream in new_streams:
                streams.append(new_stream)

    return streams
