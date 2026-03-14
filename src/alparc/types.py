"""Core types for ALPARC: dataclasses + Register container."""
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Phoneme feature labels ────────────────────────────────────────────────────
PHONEME_FEATURES = [
    "syl", "son", "cons", "cont", "delrel", "lat", "nas", "strid", "voi",
    "sg", "cg", "ant", "cor", "distr", "lab", "hi", "lo", "back", "round",
    "tense", "long",
]
# Subset of features used for syllable binary representation
LABELS_C = ["son", "back", "hi", "lab", "cor", "cont", "lat", "nas", "voi"]
LABELS_V = ["back", "hi", "lo", "lab", "tense", "long"]


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class Phoneme:
    id: str
    features: Dict[str, str]          # feature name -> '+' or '-'
    word_position_prob: Dict[int, float] = field(default_factory=dict)

    def get(self, label: str) -> bool:
        """Return True if the named feature is '+'."""
        return self.features.get(label) == "+"

    def is_consonant(self) -> bool:
        return self.get("cons")

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Phoneme) and self.id == other.id

    def __str__(self):
        return self.id


@dataclass
class Syllable:
    id: str
    phonemes: List[Phoneme] = field(default_factory=list)
    binary_features: List[int] = field(default_factory=list)
    phonotactic_features: List[List[str]] = field(default_factory=list)
    freq: int = 0
    prob: float = 0.0

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Syllable) and self.id == other.id

    def __str__(self):
        return self.id

    def __iter__(self):
        return iter(self.phonemes)


@dataclass
class Word:
    id: str
    syllables: List[Syllable] = field(default_factory=list)
    # binary_features[i] is the feature vector across all syllable positions for feature i
    # shape: n_features × n_syllables
    binary_features: List[List[int]] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Word) and self.id == other.id

    def __str__(self):
        return self.id

    def __iter__(self):
        return iter(self.syllables)


@dataclass
class Stream:
    id: str
    syllables: List[Syllable] = field(default_factory=list)
    tp_mode: str = ""
    rhythmicity: Dict[str, float] = field(default_factory=dict)
    lexicon_id: str = ""
    cum_pri: str = ""
    max_pair_pri: str = ""

    def __iter__(self):
        return iter(self.syllables)

    def __str__(self):
        ids = [s.id for s in self.syllables]
        if len(ids) > 10:
            return "|".join(ids[:5]) + "|...|" + "|".join(ids[-5:])
        return "|".join(ids)


# ── Register ──────────────────────────────────────────────────────────────────

class Register(OrderedDict):
    """Ordered mapping from element id → element, with metadata in .info.

    - Iterates over *values* (elements), not keys.
    - Supports integer indexing: reg[0] returns first element.
    - .info dict carries metadata through the pipeline.
    - Elements must have an `.id` attribute.
    """

    def __init__(self, elements=(), /, **kwargs):
        # Use object.__setattr__ to avoid OrderedDict's __setattr__ interference
        super().__init__()
        object.__setattr__(self, "_info", {})
        if isinstance(elements, dict):
            super().update(elements)
        else:
            for elem in elements:
                self[elem.id] = elem

    # -- metadata --------------------------------------------------------------

    @property
    def info(self) -> dict:
        return object.__getattribute__(self, "_info")

    @info.setter
    def info(self, value: dict):
        object.__setattr__(self, "_info", value)

    # -- access ----------------------------------------------------------------

    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.values())[item]
        return super().__getitem__(item)

    def __iter__(self):
        return iter(self.values())

    def __contains__(self, item):
        key = item.id if hasattr(item, "id") else item
        return super().__contains__(key)

    def __repr__(self):
        keys = list(self.keys())
        n = len(keys)
        shown = "|".join(keys[:10])
        if n > 10:
            shown += f"|... ({n} total)"
        return f"Register({shown})"

    # -- mutation --------------------------------------------------------------

    def append(self, elem) -> None:
        self[elem.id] = elem

    # -- derived registers -----------------------------------------------------

    def filter(self, func, **kwargs) -> "Register":
        """Return new Register containing only elements where func(elem, **kwargs) is True."""
        result = Register()
        result.info = dict(self.info)
        for elem in self:
            if func(elem, **kwargs):
                result.append(elem)
        return result

    def subset(self, n: int) -> "Register":
        """Return a random subset of size n (or self if n >= len)."""
        import random
        if n >= len(self):
            return self
        keys = random.sample(list(self.keys()), n)
        result = Register({k: self[k] for k in keys})
        result.info = dict(self.info)
        return result
