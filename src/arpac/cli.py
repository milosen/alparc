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

from arpac.core.stream import make_streams
from arpac.eval import to_lexicon
from arpac.io import load_phonemes, read_phoneme_corpus, read_syllables_corpus
from arpac.types.base_types import Register, RegisterType
from arpac.types.phoneme import TypePhonemeFeatureLabels
from arpac.types.syllable import LABELS_C, LABELS_V, Syllable
from arpac.types.word import WordType, Word
from arpac.types.lexicon import LexiconType
from arpac.types.stream import StreamType, Stream
from arpac.controls.common import get_oscillation_patterns

from arpac.core.lexicon import make_lexicon_generator, make_lexicons
from arpac.core.word import make_words
from arpac.core.syllable import make_syllables

from arpac.controls.common import *

_OBJECT_DUMP = "_arpac"

def setup_log_dir(results_base_dir: str, name="unknown"):
    results_dir = f"{name}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    results_path = os.path.join(os.path.normpath(results_base_dir), results_dir)
    os.makedirs(results_path, exist_ok=True)
    os.makedirs(os.path.join(results_path, _OBJECT_DUMP), exist_ok=True)
    return results_path


def setup_logging(log_dir: Optional[str] = None, log_console: bool = True, name: str = "unnamed_command") -> Tuple[logging.Logger, str]:
    log_path = setup_log_dir(log_dir, name=name)
    logging.basicConfig(filename=os.path.join(log_path, "debug.log"), 
                        encoding='utf-8', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if log_console:
        logger.addHandler(logging.StreamHandler())
    return logger, log_path


def write_stream_summary(streams: Register, save_path: str, logger: logging.Logger):
    with open(os.path.join(save_path, "streams.yml"), 'w') as file:
        results = {"streams": {}, "info": {}}
        results["streams"] = [{
                "stream_full": "|".join([syllable.id for syllable in stream]),
                "lexicon": stream.info["lexicon"],
                "lexicon_info": stream.info["lexicon_info"],
                "rhythmicity_indexes": stream.info["rhythmicity_indexes"],
                "stream_tp_mode": stream.info["stream_tp_mode"],
                "n_syllables_per_word": stream.info["n_syllables_per_word"] if "n_syllables_per_word" in stream.info.keys() else None,
                "n_look_back": stream.info["n_look_back"] if "n_look_back" in stream.info.keys() else None,
                "phonotactic_control": stream.info["phonotactic_control"] if "phonotactic_control" in stream.info.keys() else None,
                "syllables_info": stream.info["syllables_info"] if "syllables_info" in stream.info.keys() else None,
        } for stream in streams]
        for stream in streams:
            logger.info(f"- {stream.id}")
        results["info"] = streams.info
        yaml.dump(results, file, encoding="utf-8")

@dataclass
class CommonArgs:
    """"""
    lang: Literal["deu", "eng"] = "deu"
    """The reference language to use (mainly for corpora)"""
    log_dir: Union[str, os.PathLike] = "results"
    """The base directory to safe logs and results to"""
    name: Optional[str] = None
    """Name of the experiment or dataset (to name the subdirectory)"""
    log_console: bool = True
    """Log to console"""
    progress_bars: bool = True
    """Show progress bars in console"""

@dataclass
class SyllableArgs:
    phoneme_pattern: str = "cV"
    """Phoneme pattern to use for syllable generation."""
    unigram_control: bool = True
    """Control for phoneme frequency of use in the syllable compared to the reference language"""
    unigram_alpha: Optional[float] = None
    """Threshold for phoneme frequency of use in the syllable"""
    syllable_control: bool = True
    """Control for syllable frequency of use in the syllable compared to the reference language"""
    syllable_alpha: Optional[float] = None
    """Threshold for syllable frequency of use in the syllable"""
    export_ssml: bool = False
    """Export syllables to SSML format, e.g. for audio generation"""
    consonant_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: LABELS_C)
    """Consonant features to use for controls in syllable generation"""
    vowel_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: LABELS_V)
    """Vowel features to use for controls in syllable generation"""

@dataclass
class WordArgs:
    n_words: int = 10000
    """Number of words to generate"""
    n_syllables_per_word: Literal[2, 3, 4] = 3
    """Number of syllables per word"""
    bigram_control: bool = True
    """Control for bigram frequency of use in the word compared to the reference language"""
    bigram_alpha: Optional[float] = None
    """Threshold for bigram frequency of use in the word"""
    trigram_control: bool = True
    """Control for trigram frequency of use in the word compared to the reference language"""
    trigram_alpha: Optional[float] = None
    """Threshold for trigram frequency of use in the word"""
    positional_control: bool = True
    """Control for positional frequency of use of a phoneme in the word compared to the reference language"""
    positional_control_position: Optional[int] = None
    """Position of the phoneme in the word (0 = first, 1 = second, ...). If None, all positions are controlled"""
    position_alpha: int = 0
    """Threshold for positional frequency of use of a phoneme in the word"""
    phonotactic_control: bool = True
    """Control for phonotactic feature repetition of the phonemes in the word"""
    n_look_back: int = 2
    """Number of phonemes to look back for phonotactic control"""
    max_tries: int = 100000
    """Maximum number of tries to generate the word register with the given constraints"""

@dataclass
class LexiconArgs:
    n_lexicons: int = 2
    """Number of lexicons to generate"""
    n_words_per_lexicon: Literal[3, 4, 5] = 4
    """Number of words per lexicon"""
    unique_words: bool = False
    """Check uniqueness of words across all lexicons"""
    binary_feature_control: bool = True
    """Control for binary feature repetition between words in the lexicon. 
    See 'lag_of_interest', 'max_overlap', and 'max_word_matrix'."""
    lag_of_interest: int = 1
    """Binary feature frequency in words"""
    max_overlap: int = 1
    """Maximum number of overlapping features between words in the lexicon"""
    max_word_matrix: int = 200
    """Maximum number of words to use to create pairwise feature overlaps (Will be sub-sampled if necessary)"""
    control_features: List[TypePhonemeFeatureLabels] = field(default_factory=lambda: LABELS_C + LABELS_V)
    """If controlled, which binary features to include in binary feature control"""

@dataclass
class StreamArgs:
    repetitions: int = 15
    """Number of repetitions of the lexicon contents to create a full stream"""
    max_rhythmicity: Optional[float] = None
    """Threshold for maximum rhythmicity index of features in the stream. If None, rhythmicity control is still applied, but no threshold"""
    n_streams_per_lexicon: int = 2
    """Number of streams to generate per lexicon"""
    max_tries_randomize: int = 10
    """Maximum number of tries to randomize the stream (only if max_rhythmicity is used)"""
    tp_modes: List[Literal["random", "word_structured", "position_controlled"]] = field(default_factory=lambda: ["random", "word_structured", "position_controlled"])
    """Rules to use for the syllable randomization. If None, all patterns are used"""
    require_all_tp_modes: bool = True
    """If True, all tp_modes are required to return a valid stream for a given lexicon, otherwise the stream will be dropped"""

@dataclass
class Generate:
    """Generate a dataset of streams from a phenome database and language-specific phoneme, syllable and n-gram corpora"""
    common: CommonArgs
    syllable: SyllableArgs
    word: WordArgs
    lexicon: LexiconArgs
    stream: StreamArgs

def generate_stream_dataset(args: Generate) -> RegisterType:
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
        syllable_alpha=args.syllable.syllable_alpha,
        lang=args.common.lang,
        consonant_features=args.syllable.consonant_features,
        vowel_features=args.syllable.vowel_features,
    )
    logger.info(f"Generate Syllables: {syllables}")

    syllables.save(os.path.join(log_dir, _OBJECT_DUMP, "syllables.json"))

    if args.syllable.export_ssml:
        from arpac.io import export_speech_synthesizer
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
    write_stream_summary(streams, save_path=log_dir, logger=logger)


def write_lexicon_summary(lexicon: Register, save_path: str, logger: logging.Logger):
    with open(os.path.join(save_path, "lexicons.yml"), 'w') as file:
        results = {}
        results["lexicon"] = "|".join(word.id for word in lexicon)
        results["info"] = lexicon.info
        yaml.dump(results, file, encoding="utf-8")


@dataclass
class Diagnose:
    """Diagnose a lexicon by checking its phonotactic, acoustic and rhythmic properties"""
    lexicons: str
    """Lexicon string(s) consisting of words and syllables. Multiple lexicons should be separated by ' '.
    Syllables should be separated by '|' and words by '||'. Example: pi|ɾu|ta||ba|ɡo|li||to|ku|da||ɡu|haɪ|bo"""
    common: CommonArgs
    stream: StreamArgs
    export_ssml: bool = True
    """Export syllables to SSML format, e.g. for audio generation"""
    split_registers: bool = False
    """Derive phoneme and syllable registers from the lexicon"""
    generate_streams: bool = True
    """Generate streams from the parsed lexicons"""
    phoneme_pattern: str = "cv"
    """Phoneme pattern to assume for syllable parsing"""

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
                from arpac.io import export_speech_synthesizer
                export_speech_synthesizer(syllables, syllables_dir=os.path.join(log_dir, "ssml"))

            phonemes = syllables.flatten()
            phonemes.save(os.path.join(log_dir, _OBJECT_DUMP, "phonemes.json"))
            logger.info(f"Phonemes object saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'phonemes.json')}")

            if args.common.lang == "deu":
                corpus_phonemes = read_phoneme_corpus(lang=args.common.lang)
                phonemes_with_german_corpus_stats = phonemes.intersection(corpus_phonemes)
                phonemes_with_german_corpus_stats.save(os.path.join(log_dir, _OBJECT_DUMP, "phonemes_with_german_corpus_stats.json"))
                logger.info(f"Phonemes object with corpus stats saved to file: {os.path.join(log_dir, _OBJECT_DUMP, 'phonemes_with_german_corpus_stats.json')}")


@dataclass
class EvaluateStream:
    stream: str
    """Stream string consisting of syllables, separated by '|'. 
    Example: pi|ɾu|ta|ba|ɡo|li|to|li|to|ku|ɾu|ta|ba|ɡo|li|to|ku|da|ɡu|ki|bo"""


def cli():
    args = tyro.cli(Union[Generate, Diagnose], prog="alparc", description="The ALPARC Toolbox: Artificial Languages with Phonological and Acoustic Rhythmicity Control")
    if isinstance(args, Generate):
        generate_stream_dataset(args)
    if isinstance(args, Diagnose):
        evaluate_lexicons(args)
