"""Tests for the core type system."""
import pytest
from alparc.types import Phoneme, Syllable, Word, Stream, Register, LABELS_C, LABELS_V


def make_phoneme(id="b", cons="+"):
    return Phoneme(id=id, features={"cons": cons, "son": "-", "lab": "+", "back": "-"})


def make_syllable(id="ba"):
    p = make_phoneme()
    return Syllable(id=id, phonemes=[p], binary_features=[1, 0, 1, 0])


def make_word(id="baba"):
    s1 = make_syllable("ba")
    s2 = make_syllable("da")
    return Word(id=id, syllables=[s1, s2], binary_features=[[1, 1], [0, 0]])


# ── Phoneme ───────────────────────────────────────────────────────────────────

def test_phoneme_get():
    p = make_phoneme(cons="+")
    assert p.get("cons") is True
    assert p.get("son") is False
    assert p.get("nonexistent") is False


def test_phoneme_is_consonant():
    c = make_phoneme("b", cons="+")
    v = make_phoneme("a", cons="-")
    assert c.is_consonant()
    assert not v.is_consonant()


def test_phoneme_hashable():
    p1 = make_phoneme("b")
    p2 = make_phoneme("b")
    p3 = make_phoneme("d")
    assert hash(p1) == hash(p2)
    assert hash(p1) != hash(p3)
    s = {p1, p2, p3}
    assert len(s) == 2


# ── Syllable ──────────────────────────────────────────────────────────────────

def test_syllable_str():
    s = make_syllable("ba")
    assert str(s) == "ba"


def test_syllable_iter():
    p = make_phoneme()
    s = Syllable(id="b", phonemes=[p])
    assert list(s) == [p]


def test_syllable_hashable():
    s1 = make_syllable("ba")
    s2 = make_syllable("ba")
    s3 = make_syllable("da")
    assert len({s1, s2, s3}) == 2


# ── Word ──────────────────────────────────────────────────────────────────────

def test_word_iter():
    w = make_word()
    sylls = list(w)
    assert len(sylls) == 2
    assert all(isinstance(s, Syllable) for s in sylls)


# ── Stream ────────────────────────────────────────────────────────────────────

def test_stream_str_short():
    sylls = [make_syllable(f"s{i}") for i in range(5)]
    stream = Stream(id="test", syllables=sylls)
    assert str(stream) == "|".join(f"s{i}" for i in range(5))


def test_stream_str_long():
    sylls = [make_syllable(f"s{i:02d}") for i in range(20)]
    stream = Stream(id="test", syllables=sylls)
    s = str(stream)
    assert "..." in s


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_from_dict():
    p1, p2 = make_phoneme("a"), make_phoneme("b")
    reg = Register({"a": p1, "b": p2})
    assert len(reg) == 2


def test_register_from_iterable():
    p1, p2 = make_phoneme("a"), make_phoneme("b")
    reg = Register([p1, p2])
    assert len(reg) == 2
    assert "a" in reg.keys()


def test_register_int_index():
    p1, p2 = make_phoneme("a"), make_phoneme("b")
    reg = Register([p1, p2])
    assert reg[0] is p1
    assert reg[1] is p2


def test_register_str_index():
    p = make_phoneme("a")
    reg = Register([p])
    assert reg["a"] is p


def test_register_iter_yields_values():
    p1, p2 = make_phoneme("a"), make_phoneme("b")
    reg = Register([p1, p2])
    values = list(reg)
    assert values == [p1, p2]


def test_register_contains_by_id():
    p = make_phoneme("a")
    reg = Register([p])
    assert p in reg
    assert "a" in reg


def test_register_append():
    reg = Register()
    p = make_phoneme("a")
    reg.append(p)
    assert len(reg) == 1
    assert reg["a"] is p


def test_register_filter():
    p1 = make_phoneme("b", cons="+")
    p2 = make_phoneme("a", cons="-")
    reg = Register([p1, p2])
    consonants = reg.filter(lambda p: p.is_consonant())
    assert len(consonants) == 1
    assert "b" in consonants.keys()


def test_register_info_preserved_in_filter():
    p1 = make_phoneme("b", cons="+")
    p2 = make_phoneme("a", cons="-")
    reg = Register([p1, p2])
    reg.info = {"test": 42}
    filtered = reg.filter(lambda p: p.is_consonant())
    assert filtered.info["test"] == 42


def test_register_subset():
    import random
    random.seed(0)
    phonemes = [make_phoneme(str(i)) for i in range(10)]
    reg = Register(phonemes)
    sub = reg.subset(3)
    assert len(sub) == 3
    assert all(k in reg.keys() for k in sub.keys())


def test_register_subset_returns_self_if_small():
    p = make_phoneme("a")
    reg = Register([p])
    assert reg.subset(10) is reg


def test_register_info():
    reg = Register()
    reg.info = {"key": "value"}
    assert reg.info["key"] == "value"


def test_labels_lengths():
    assert len(LABELS_C) == 9
    assert len(LABELS_V) == 6
