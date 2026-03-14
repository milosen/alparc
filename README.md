# ALPARC

**Artificial Languages with Phonological, Acoustic, and Rhythmicity Controls**

ALPARC is a Python package for generating controlled artificial-language stimuli for psycholinguistics and neuroscience experiments. It produces pseudo-word lexicons and continuous syllable streams whose phonological properties (feature overlap between words, corpus-based syllable frequencies, phonotactic plausibility) and statistical learning properties (transitional probabilities between syllables) are precisely controlled.

## How it works

![ALPARC pipeline](assets/info.png)

Generation proceeds through four stages:

```
Phonemes → Syllables → Words → Lexicons → Streams
```

1. **Phonemes** — loaded from a library of more than 5000 phonemes (including binary phonological features for each).
2. **Syllables** — formed by combining phonemes in a given pattern (e.g. `cV`, conconant + long vowel). Optionally filtered so that syllable frequency matches a corpus distribution (German by default).
3. **Pseudowords** — assembled from syllables, with phonotactic constraints (bigram, trigram, positional) to ensure naturalness (w.r.t German by default).
4. **Lexicons** — sets of words selected so that binary phonological feature overlap between words is minimised (or bounded).
5. **Streams** — the words are concatenated into a continuous syllable sequence. Three transitional-probability (TP) modes are available:
   - `random` — uniform TP across all syllables (no word structure)
   - `word_structured` — TP respects word boundaries (words are atomic units)
   - `position_controlled` — uniform TP, but each syllable position is constrained to its within-word slot

Streams are generated using an Eulerian-circuit algorithm that guarantees convergence to uniform TPs in linear time.

## Installation

Requires Python ≥ 3.9. Install with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

## Quick start

### One-line generation

```python
from alparc import generate

streams = generate(
    n_lexicons=4,
    n_streams_per_lexicon=3,
    out_dir="results/",
)
```

This runs the full pipeline with German phonemes and default settings, producing 4 lexicons × 3 streams × 3 TP modes = 36 streams. Results are saved to a timestamped directory under `results/`.

### Displaying a stream

```python
from alparc.display import print_stream

print_stream(streams[0], word_length=3)
```

This prints a binary phonological feature matrix over the syllable sequence, with syllable-by-syllable surprisal (negative log TP) shown at the top. Use `start_at` to view a later part of the stream while keeping surprisal values computed from the beginning:

```python
print_stream(streams[0], word_length=3, start_at=60)
```

### Step-by-step pipeline

```python
from alparc import load_phonemes, make_syllables, make_words, make_lexicons, make_streams

# 1. Load phonemes
phonemes = load_phonemes(lang="deu")   # or lang="eng"

# 2. Generate syllables (CV pattern, corpus-filtered)
syllables = make_syllables(phonemes, pattern="cV", alpha=0.05)

# 3. Generate pseudo-words
words = make_words(syllables, n_syllables=3, n_words=200)

# 4. Select lexicons with low feature overlap
lexicons = make_lexicons(words, n_lexicons=4, n_words=4)

# 5. Generate streams
streams = make_streams(lexicons, n_repetitions=15)
```

### Using a custom lexicon

You can bypass the generation stages and supply your own words in IPA notation. Phonemes are separated by `_`, syllables by `|`:

```python
from alparc import diagnose
from alparc.streams import make_stream

lexicon = diagnose([
    "n_o|n_i|x_e",
    "b_u|l_o|t_e",
    "r_e|m_o|f_u",
    "k_o|t_u|s_a",
])

stream = make_stream(lexicon, n_repetitions=15, tp_mode="word_structured")
```

`diagnose` also reports cumulative and pairwise binary-feature overlap across the lexicon.

### Analysing rhythmicity

Each stream carries a `.rhythmicity` dict with a Phonological Rhythmicity Index (PRI) for every phonological feature dimension:

```python
stream = streams[0]
print(stream.tp_mode)                      # e.g. "word_structured"
print(max(stream.rhythmicity.values()))    # highest PRI across features
```

PRI measures how often a feature oscillates at the word-frequency rate. A high PRI means a feature is rhythmically predictable, which can serve as an unintended acoustic cue.

## Key parameters

| Parameter | Default | Description |
|---|---|---|
| `lang` | `"deu"` | Phoneme inventory language (`"deu"` or `"eng"`) |
| `phoneme_pattern` | `"cV"` | Syllable structure (`"cV"` = consonant + long vowel, `"cv"` = short vowel) |
| `syllable_alpha` | `0.05` | Significance threshold for corpus frequency filter |
| `n_syllables_per_word` | `3` | Syllables per pseudo-word |
| `n_words_per_lexicon` | `4` | Words per lexicon |
| `n_lexicons` | `2` | Number of lexicons to generate |
| `binary_feature_control` | `True` | Enforce low phonological feature overlap between words |
| `max_overlap` | `1` | Maximum pairwise feature overlap allowed |
| `n_repetitions` | `15` | How many times each word appears in a stream |
| `n_streams_per_lexicon` | `2` | Number of streams per lexicon |
| `tp_modes` | all three | Which TP modes to generate streams for |
| `max_rhythmicity` | `None` | Reject streams whose max PRI exceeds this value |

Full defaults are listed in `publication/generate_defaults.csv`.

## Output files

When `out_dir` is set, each `generate()` call creates a timestamped subdirectory containing:

| File | Contents |
|---|---|
| `config.yaml` | All parameters passed to this run |
| `streams.yaml` | Per-stream syllable sequences, TP mode, lexicon, and PRI values |
| `debug.log` | Full debug-level log |

## Running tests

```bash
uv run pytest
```

## Project layout

```
src/alparc/
    __init__.py      — public API: generate(), diagnose()
    corpus.py        — phoneme loading from language data
    syllables.py     — syllable generation and corpus filtering
    words.py         — pseudo-word generation with phonotactic controls
    lexicons.py      — lexicon selection with feature-overlap control
    streams.py       — stream generation (Eulerian-circuit TP algorithm)
    display.py       — terminal and Jupyter display (print_stream)
    types.py         — core dataclasses: Phoneme, Syllable, Word, Stream, Register
publication/
    data_and_stats_from_the_paper.ipynb   — reproduce paper results
    plots_from_paper.ipynb                — reproduce paper figures
    experiment_parameters.csv            — parameters used per experiment
    generate_defaults.csv                — full list of generate() defaults
```
