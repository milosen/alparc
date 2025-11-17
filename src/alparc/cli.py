import collections
from dataclasses import dataclass, field
import datetime
from functools import partial
import itertools
import logging.config
import math
from typing import List, Optional, Literal, Dict, Tuple, Union
import logging
import os
import tyro
import yaml
import json

from tqdm import tqdm

from alparc.core.stream import make_streams
from alparc.eval import to_lexicon
from alparc.io import load_phonemes, read_phoneme_corpus, read_syllables_corpus
from alparc.types.base_types import Register, RegisterType
from alparc.types.phoneme import TypePhonemeFeatureLabels
from alparc.types.syllable import LABELS_C, LABELS_V, Syllable
from alparc.types.word import WordType, Word
from alparc.types.lexicon import LexiconType
from alparc.types.stream import StreamType, Stream
from alparc.controls.common import get_oscillation_patterns

from alparc.core.lexicon import make_lexicon_generator, make_lexicons
from alparc.core.word import make_words
from alparc.core.syllable import make_syllables

from alparc.controls.common import *
from alparc import *


@dataclass
class CommonArgs:
    """"""
    lang: Literal["deu", "eng"] = DEFAULT_COMMON_LANG
    """The reference language to use (mainly for corpora)"""
    log_dir: Union[str, os.PathLike] = DEFAULT_COMMON_LOG_DIR
    """The base directory to safe logs and results to"""
    name: Optional[str] = DEFAULT_COMMON_NAME
    """Name of the experiment or dataset (to name the subdirectory)"""
    log_console: bool = DEFAULT_COMMON_LOG_CONSOLE
    """Log to console"""
    progress_bars: bool = DEFAULT_COMMON_PROGRESS_BARS
    """Show progress bars in console"""
    lexicon: Optional[List[str]] = DEFAULT_COMMON_LEXICON
    """Start with this given lexicon."""

@dataclass
class SyllableArgs:
    phoneme_pattern: str = DEFAULT_SYLLABLE_PHONEME_PATTERN
    """Phoneme pattern to use for syllable generation."""
    unigram_control: bool = DEFAULT_SYLLABLE_UNIGRAM_CONTROL
    """Control for phoneme frequency of use in the syllable compared to the reference language"""
    unigram_alpha: Optional[float] = DEFAULT_SYLLABLE_UNIGRAM_ALPHA
    """Threshold for phoneme frequency of use in the syllable"""
    syllable_control: bool = DEFAULT_SYLLABLE_SYLLABLE_CONTROL
    """Control for syllable frequency of use in the syllable compared to the reference language"""
    syllable_alpha: Optional[float] = DEFAULT_SYLLABLE_SYLLABLE_ALPHA
    """Threshold for syllable frequency of use in the syllable"""
    syllables_path: Optional[str] = DEFAULT_SYLLABLE_SYLLABLES_PATH
    """Path to syllable corpus csv file"""
    export_ssml: bool = DEFAULT_SYLLABLE_EXPORT_SSML
    """Export syllables to SSML format, e.g. for audio generation"""
    consonant_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: DEFAULT_SYLLABLE_CONSONANT_FEATURES)
    """Consonant features to use for controls in syllable generation"""
    vowel_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: DEFAULT_SYLLABLE_VOWEL_FEATURES)
    """Vowel features to use for controls in syllable generation"""

@dataclass
class WordArgs:
    n_words: int = DEFAULT_WORD_N_WORDS
    """Number of words to generate"""
    n_syllables_per_word: Literal[2, 3, 4] = DEFAULT_WORD_N_SYLLABLES_PER_WORD
    """Number of syllables per word"""
    bigram_control: bool = DEFAULT_WORD_BIGRAM_CONTROL
    """Control for bigram frequency of use in the word compared to the reference language"""
    bigram_alpha: Optional[float] = DEFAULT_WORD_BIGRAM_ALPHA
    """Threshold for bigram frequency of use in the word"""
    trigram_control: bool = DEFAULT_WORD_TRIGRAM_CONTROL
    """Control for trigram frequency of use in the word compared to the reference language"""
    trigram_alpha: Optional[float] = DEFAULT_WORD_TRIGRAM_ALPHA
    """Threshold for trigram frequency of use in the word"""
    positional_control: bool = DEFAULT_WORD_POSITIONAL_CONTROL
    """Control for positional frequency of use of a phoneme in the word compared to the reference language"""
    positional_control_position: Optional[int] = DEFAULT_WORD_POSITIONAL_CONTROL_POSITION
    """Position of the phoneme in the word (0 = first, 1 = second, ...). If None, all positions are controlled"""
    position_alpha: int = DEFAULT_WORD_POSITION_ALPHA
    """Threshold for positional frequency of use of a phoneme in the word"""
    phonotactic_control: bool = DEFAULT_WORD_PHONOTACTIC_CONTROL
    """Control for phonotactic feature repetition of the phonemes in the word"""
    n_look_back: int = DEFAULT_WORD_N_LOOK_BACK
    """Number of phonemes to look back for phonotactic control"""
    max_tries: int = DEFAULT_WORD_MAX_TRIES
    """Maximum number of tries to generate the word register with the given constraints"""

@dataclass
class LexiconArgs:
    n_lexicons: int = DEFAULT_LEXICON_N_LEXICONS
    """Number of lexicons to generate"""
    n_words_per_lexicon: Literal[3, 4, 5] = DEFAULT_LEXICON_N_WORDS_PER_LEXICON
    """Number of words per lexicon"""
    unique_words: bool = DEFAULT_LEXICON_UNIQUE_WORDS
    """Check uniqueness of words across all lexicons"""
    binary_feature_control: bool = DEFAULT_LEXICON_BINARY_FEATURE_CONTROL
    """Control for binary feature repetition between words in the lexicon. 
    See 'lag_of_interest', 'max_overlap', and 'max_word_matrix'."""
    lag_of_interest: int = DEFAULT_LEXICON_LAG_OF_INTEREST
    """Binary feature frequency in words"""
    max_overlap: int = DEFAULT_LEXICON_MAX_OVERLAP
    """Maximum number of overlapping features between words in the lexicon"""
    max_word_matrix: int = DEFAULT_LEXICON_MAX_WORD_MATRIX
    """Maximum number of words to use to create pairwise feature overlaps (Will be sub-sampled if necessary)"""
    control_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: DEFAULT_LEXICON_CONTROL_FEATURES)
    """If controlled, which binary features to include in binary feature control"""

@dataclass
class StreamArgs:
    repetitions: int = DEFAULT_STREAM_REPETITIONS
    """Number of repetitions of the lexicon contents to create a full stream"""
    max_rhythmicity: Optional[float] = DEFAULT_STREAM_MAX_RHYTHMICITY
    """Threshold for maximum rhythmicity index of features in the stream. If None, rhythmicity control is still applied, but no threshold"""
    n_streams_per_lexicon: int = DEFAULT_STREAM_N_STREAMS_PER_LEXICON
    """Number of streams to generate per lexicon"""
    max_tries_randomize: int = DEFAULT_STREAM_MAX_TRIES_RANDOMIZE
    """Maximum number of tries to randomize the stream (only if max_rhythmicity is used)"""
    tp_modes: List[Literal["random", "word_structured", "position_controlled"]] = field(default_factory=lambda: DEFAULT_STREAM_TP_MODES)
    """Rules to use for the syllable randomization. If None, all patterns are used"""
    require_all_tp_modes: bool = DEFAULT_STREAM_REQUIRE_ALL_TP_MODES
    """If True, all tp_modes are required to return a valid stream for a given lexicon, otherwise the stream will be dropped"""

@dataclass
class Generate:
    """Generate a dataset of streams from a phenome database and language-specific phoneme, syllable and n-gram corpora"""
    common: CommonArgs = field(default_factory=lambda: CommonArgs())
    syllable: SyllableArgs = field(default_factory=lambda: SyllableArgs())
    word: WordArgs = field(default_factory=lambda: WordArgs())
    lexicon: LexiconArgs = field(default_factory=lambda: LexiconArgs())
    stream: StreamArgs = field(default_factory=lambda: StreamArgs())

@dataclass
class Diagnose:
    """Diagnose a lexicon by checking its phonotactic, acoustic and rhythmic properties"""
    lexicons: str
    """Lexicon string(s) consisting of words and syllables. Multiple lexicons should be separated by ' '.
    Syllables should be separated by '|' and words by '||'. Example: pi|ɾu|ta||ba|ɡo|li||to|ku|da||ɡu|haɪ|bo"""
    common: CommonArgs = field(default_factory=lambda: CommonArgs())
    stream: StreamArgs = field(default_factory=lambda: StreamArgs())
    export_ssml: bool = DEFAULT_SYLLABLE_EXPORT_SSML
    """Export syllables to SSML format, e.g. for audio generation"""
    split_registers: bool = DEFAULT_DIAGNOSE_SPLIT_REGISTERS
    """Derive phoneme and syllable registers from the lexicon"""
    generate_streams: bool = DEFAULT_DIAGNOSE_GENERATE_STREAMS
    """Generate streams from the parsed lexicons"""
    phoneme_pattern: str = DEFAULT_DIAGNOSE_PHONEME_PATTERN
    """Phoneme pattern to assume for syllable parsing"""

def generate_stream_dataset(args: Generate) -> Tuple[Register, Dict]:
    logger, log_dir = setup_logging(args.common.log_dir, args.common.log_console, name=args.common.name or "generate_streams")
    
    with open(os.path.join(log_dir, "config.yml"), "w") as file:
        yaml.dump(vars(args), file, encoding="utf-8")

    phonemes = load_phonemes(lang=(args.common.lang if args.syllable.unigram_control else None))
    if args.syllable.unigram_alpha is not None:
        phonemes = phonemes.filter(lambda unigram: unigram.info["p_unif"] > args.syllable.unigram_alpha)
    logger.info(f"Generate Phonemes: {phonemes}")

    syllables = make_syllables(
        phonemes=phonemes, 
        phoneme_pattern=args.syllable.phoneme_pattern,
        syllable_control=args.syllable.syllable_control,
        syllables_path=args.syllable.syllables_path,
        syllable_alpha=args.syllable.syllable_alpha,
        lang=args.common.lang,
        consonant_features=args.syllable.consonant_features,
        vowel_features=args.syllable.vowel_features,
    )
    logger.info(f"Generate Syllables: {syllables}")

    syllables.save(os.path.join(log_dir, _OBJECT_DUMP, "syllables.json"))

    if args.syllable.export_ssml:
        from alparc.io import export_speech_synthesizer
        export_speech_synthesizer(syllables, syllables_dir=os.path.join(log_dir, "ssml"))

    logger.info(f"Generate Pseudo-Words: ...")
    pseudo_words = make_words(
        syllables=syllables,
        num_syllables=args.word.n_syllables_per_word,
        bigram_control=args.word.bigram_control,
        bigram_alpha=args.word.bigram_alpha,
        trigram_control=args.word.trigram_control,
        trigram_alpha=args.word.trigram_alpha,
        positional_control=args.word.positional_control,
        positional_control_position=args.word.positional_control_position,
        position_alpha=args.word.position_alpha,
        phonotactic_control=args.word.phonotactic_control,
        n_look_back=args.word.n_look_back,
        n_words=args.word.n_words,
        max_tries=args.word.max_tries,
        progress_bar=args.common.progress_bars,
        lang=args.common.lang,
    )
    logger.info(f"Pseudo-Words: {pseudo_words}")

    pseudo_words.save(os.path.join(log_dir, _OBJECT_DUMP, "pseudo_words.json"))

    logger.info(f"Generate Lexicons: ...")
    lexicons = make_lexicons(
        pseudo_words, 
        n_lexicons=args.lexicon.n_lexicons, 
        n_words=args.lexicon.n_words_per_lexicon,
        max_overlap=args.lexicon.max_overlap,
        lag_of_interest=args.lexicon.lag_of_interest,
        max_word_matrix=args.lexicon.max_word_matrix,
        unique_words=args.lexicon.unique_words,
        control_features=args.lexicon.control_features,
        progress_bar=args.common.progress_bars,
        binary_feature_control=args.lexicon.binary_feature_control,
    )
    logger.info(f"Lexicons: {[str(l) for l in lexicons]}")

    for i, lexicon in enumerate(lexicons):
        lexicon.save(os.path.join(log_dir, _OBJECT_DUMP, f"lexicon_{i}.json"))

    logger.info(f"Generate Streams: ...")
    streams = Register()
    for _ in tqdm(range(args.stream.n_streams_per_lexicon)):
        for stream in make_streams(
            lexicons,
            max_rhythmicity=args.stream.max_rhythmicity,
            stream_length=args.stream.repetitions,
            max_tries_randomize=args.stream.max_tries_randomize,
            tp_modes=args.stream.tp_modes,
            require_all_tp_modes=args.stream.require_all_tp_modes
        ):
            streams.append(stream)
    
    logger.info(f"Streams: ")
    streams.save(os.path.join(log_dir, _OBJECT_DUMP, f"streams.json"))
    report = write_stream_summary(streams, save_path=log_dir, logger=logger)
    return streams, report

def evaluate_lexicons(args: Diagnose):
    logger, log_dir = setup_logging(args.common.log_dir, args.common.log_console, name=args.common.name or "evaluate_lexicon")

    with open(os.path.join(log_dir, "config.yml"), "w") as file:
        yaml.dump(vars(args), file, encoding="utf-8")

    lexicons = [[w.split("|") for w in l.split("||")] for l in args.lexicons.split(" ")]
    lexicons = list(map(partial(to_lexicon, syllable_type=args.phoneme_pattern), lexicons))
    save_path = os.path.join(log_dir, _OBJECT_DUMP, "lexicon.json")
    for lexicon in lexicons:
            logger.info(f"Read Lexicon: {lexicon}")
            lexicon.save(save_path)
            logger.info(f"Lexicon object saved to file: {save_path}")
            save_path = os.path.join(log_dir, "lexicon.yml")
            with open(save_path, 'w') as file:
                summary = {}
                summary["lexicon"] = "|".join(word.id for word in lexicon)
                summary["info"] = lexicon.info
                yaml.dump(summary, file, encoding="utf-8")
            logger.info(f"Lexicon summary saved to file: {save_path}")

    if args.generate_streams:
        logger.info(f"Generate Streams: ...")
        streams = Register()
        for _ in tqdm(range(args.stream.n_streams_per_lexicon)):
            for stream in make_streams(
                lexicons,
                max_rhythmicity=args.stream.max_rhythmicity,
                stream_length=args.stream.repetitions,
                max_tries_randomize=args.stream.max_tries_randomize,
                tp_modes=args.stream.tp_modes,
                require_all_tp_modes=args.stream.require_all_tp_modes
            ):
                streams.append(stream)
        
        logger.info(f"Streams: ")
        streams.save(os.path.join(log_dir, _OBJECT_DUMP, f"streams.json"))
        write_stream_summary(streams, save_path=log_dir, logger=logger)

    if args.split_registers:
        for lexicon in lexicons:
            syllables = lexicon.flatten()
            syllables.save(os.path.join(log_dir, _OBJECT_DUMP, "syllables.json"))
            logger.info(f"Syllables object saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'syllables.json')}")

            syllables_with_corpus_stats = syllables.intersection(read_syllables_corpus(lang=args.common.lang))
            syllables_with_corpus_stats.save(os.path.join(log_dir, _OBJECT_DUMP, "syllables_with_corpus_stats.json"))
            logger.info(f"Syllables object with corpus stats saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'syllables_with_corpus_stats.json')}")

            if args.export_ssml:
                from alparc.io import export_speech_synthesizer
                export_speech_synthesizer(syllables, syllables_dir=os.path.join(log_dir, "ssml"))

            phonemes = syllables.flatten()
            phonemes.save(os.path.join(log_dir, _OBJECT_DUMP, "phonemes.json"))
            logger.info(f"Phonemes object saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'phonemes.json')}")

            if args.common.lang == "deu":
                corpus_phonemes = read_phoneme_corpus(lang=args.common.lang)
                phonemes_with_german_corpus_stats = phonemes.intersection(corpus_phonemes)
                phonemes_with_german_corpus_stats.save(os.path.join(log_dir, _OBJECT_DUMP, "phonemes_with_german_corpus_stats.json"))
                logger.info(f"Phonemes object with corpus stats saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'phonemes_with_german_corpus_stats.json')}")


def cli():
    args = tyro.cli(Union[Generate, Diagnose], prog="alparc", description="The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control")
    if isinstance(args, Generate):
        generate_stream_dataset(args)
    if isinstance(args, Diagnose):
        evaluate_lexicons(args)
