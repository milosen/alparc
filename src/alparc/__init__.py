import datetime
from functools import partial
import logging
import os
from typing import Optional, Tuple, Union, List

from tqdm import tqdm
import yaml

from alparc.types.elements import LABELS_V
from .io import load_phonemes, load_syllables, load_words, load_lexicons, load_streams, export_speech_synthesizer, read_phoneme_corpus

from .controls.common import set_seed

from .types.base_types import Register, RegisterType, Element
from .types.phoneme import Phoneme, PhonemeType
from .types.syllable import LABELS_C, Syllable, SyllableType
from .types.word import Word, WordType
from .types.lexicon import Lexicon, LexiconType
from .types.stream import Stream, StreamType

from .core.syllable import make_syllables
from .core.word import make_words
from .core.lexicon import make_lexicons
from .core.stream import make_streams

from .eval import to_lexicon, to_stream, to_word

# ================================================================
# Common Defaults
# ================================================================
DEFAULT_COMMON_LANG = "deu"
DEFAULT_COMMON_LOG_DIR = "results"
DEFAULT_COMMON_NAME = None
DEFAULT_COMMON_LOG_CONSOLE = True
DEFAULT_COMMON_PROGRESS_BARS = True
DEFAULT_COMMON_LEXICON = None
_OBJECT_DUMP = "_alrpac"

# ================================================================
# Syllable Defaults
# ================================================================
DEFAULT_SYLLABLE_PHONEME_PATTERN = "cV"
DEFAULT_SYLLABLE_UNIGRAM_CONTROL = True
DEFAULT_SYLLABLE_UNIGRAM_ALPHA = None
DEFAULT_SYLLABLE_SYLLABLE_CONTROL = True
DEFAULT_SYLLABLE_SYLLABLE_ALPHA = None
DEFAULT_SYLLABLE_SYLLABLES_PATH = None
DEFAULT_SYLLABLE_EXPORT_SSML = False
DEFAULT_SYLLABLE_CONSONANT_FEATURES = LABELS_C
DEFAULT_SYLLABLE_VOWEL_FEATURES = LABELS_V

# ================================================================
# Word Defaults
# ================================================================
DEFAULT_WORD_N_WORDS = 10000
DEFAULT_WORD_N_SYLLABLES_PER_WORD = 3
DEFAULT_WORD_BIGRAM_CONTROL = True
DEFAULT_WORD_BIGRAM_ALPHA = None
DEFAULT_WORD_TRIGRAM_CONTROL = True
DEFAULT_WORD_TRIGRAM_ALPHA = None
DEFAULT_WORD_POSITIONAL_CONTROL = True
DEFAULT_WORD_POSITIONAL_CONTROL_POSITION = None
DEFAULT_WORD_POSITION_ALPHA = 0
DEFAULT_WORD_PHONOTACTIC_CONTROL = True
DEFAULT_WORD_N_LOOK_BACK = 2
DEFAULT_WORD_MAX_TRIES = 100000

# ================================================================
# Lexicon Defaults
# ================================================================
DEFAULT_LEXICON_N_LEXICONS = 2
DEFAULT_LEXICON_N_WORDS_PER_LEXICON = 4
DEFAULT_LEXICON_UNIQUE_WORDS = False
DEFAULT_LEXICON_BINARY_FEATURE_CONTROL = True
DEFAULT_LEXICON_LAG_OF_INTEREST = 1
DEFAULT_LEXICON_MAX_OVERLAP = 1
DEFAULT_LEXICON_MAX_WORD_MATRIX = 200
DEFAULT_LEXICON_CONTROL_FEATURES = DEFAULT_SYLLABLE_CONSONANT_FEATURES + DEFAULT_SYLLABLE_VOWEL_FEATURES

# ================================================================
# Stream Defaults
# ================================================================
DEFAULT_STREAM_REPETITIONS = 15
DEFAULT_STREAM_MAX_RHYTHMICITY = None
DEFAULT_STREAM_N_STREAMS_PER_LEXICON = 2
DEFAULT_STREAM_MAX_TRIES_RANDOMIZE = 10
DEFAULT_STREAM_TP_MODES = ["random", "word_structured", "position_controlled"]
DEFAULT_STREAM_REQUIRE_ALL_TP_MODES = True

# ================================================================
# DIAGNOSE Defaults
# ================================================================
DEFAULT_DIAGNOSE_SPLIT_REGISTERS = False
DEFAULT_DIAGNOSE_GENERATE_STREAMS = False
DEFAULT_DIAGNOSE_PHONEME_PATTERN = "cv"


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
        return results


def read_lexicon(words: Union[str, List[str]]):
    return Lexicon(word for word in words)


def diagnose(
        lexicon: List[str], 
        log_dir: Union[str, os.PathLike] = DEFAULT_COMMON_LOG_DIR,
        export_ssml: bool = DEFAULT_SYLLABLE_EXPORT_SSML,
        split_registers: bool = DEFAULT_DIAGNOSE_SPLIT_REGISTERS,
        generate_streams: bool = DEFAULT_DIAGNOSE_GENERATE_STREAMS,
        phoneme_pattern: str = DEFAULT_DIAGNOSE_PHONEME_PATTERN,
        log_console: bool = True, 
        logger=None
    ):
    f"""Load and diagnose a custom lexicon.

    Args:
        lexicon (List[str]): The lexicon should be a list of words. Phonemes in the lexicon should be separated by an underscore _ and syllables by vertical bars |. Example: ["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"]
        export_ssml (bool): Export syllables to SSML format, e.g. for audio generation.
        split_registers (bool): Derive phoneme and syllable registers from the lexicon.
        generate_streams (bool): Generate streams from the parsed lexicons.
        phoneme_pattern (str): Phoneme pattern to assume for syllable parsing
        log_dir (Union[str, os.PathLike], optional): _description_. Defaults to {DEFAULT_COMMON_LOG_DIR}.
        log_console (bool, optional): _description_. Defaults to True.
        logger (_type_, optional): _description_. Defaults to None.

    Returns:
        lexicon: ALPARC-type Lexicon
        report: Summary of the diagnostics
    """
    if logger is None:
        with open(os.path.join(log_dir, "config.yml"), "w") as file:
            yaml.dump({
                "lexicon": lexicon, 
                "log_dir": log_dir,
                "export_ssml": export_ssml,
                "split_registers": split_registers,
                "generate_streams": generate_streams,
                "phoneme_pattern": phoneme_pattern,
                "log_console": log_console,
            }, file, encoding="utf-8")

        logger, log_dir = setup_logging(log_dir, log_console, name="diagnose_lexicon")

    lexicon = [[syll.split("_") for syll in word.split("|")] for word in lexicon]
    lexicon = to_lexicon(lexicon, syllable_type=None)
    save_path = os.path.join(log_dir, _OBJECT_DUMP, "lexicon.json")

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

    if split_registers or generate_streams:
        logger.warning("Automatic generation from diagnosed lexicons not supported yet. Please use `generate_streams`")
    
    return lexicon, summary


def generate_streams(
    lexicons,
    max_rhythmicity = DEFAULT_STREAM_MAX_RHYTHMICITY,
    repetitions = DEFAULT_STREAM_REPETITIONS,
    max_tries_randomize = DEFAULT_STREAM_MAX_TRIES_RANDOMIZE,
    tp_modes = DEFAULT_STREAM_TP_MODES,
    require_all_tp_modes = DEFAULT_STREAM_REQUIRE_ALL_TP_MODES,
    n_streams_per_lexicon = DEFAULT_STREAM_N_STREAMS_PER_LEXICON,
    # log
    logger=None,
    log_dir: str = DEFAULT_COMMON_LOG_DIR,
):
    logger.info(f"Generate Streams: ...") 
    streams = Register() 
    for _ in tqdm(range(n_streams_per_lexicon)): 
        for stream in make_streams(
            lexicons, 
            max_rhythmicity=max_rhythmicity, 
            stream_length=repetitions, 
            max_tries_randomize=max_tries_randomize, 
            tp_modes=tp_modes, 
            require_all_tp_modes=require_all_tp_modes
        ): 
            streams.append(stream) 
        logger.info(f"Streams: ") 
        streams.save(os.path.join(log_dir, _OBJECT_DUMP, f"streams.json")) 
    
    report = write_stream_summary(streams, save_path=log_dir, logger=logger) 
    return streams, report


# ---------------------------------------------------------------------
# FULL PIPELINE
# ---------------------------------------------------------------------

def generate(
    # common
    lang: Optional[str] = DEFAULT_COMMON_LANG,
    progress_bars: bool = DEFAULT_COMMON_PROGRESS_BARS,
    lexicon: List[str] = DEFAULT_COMMON_LEXICON,
    
    # phoneme + syllable
    syllable_unigram_control: bool = DEFAULT_SYLLABLE_UNIGRAM_CONTROL,
    syllable_unigram_alpha: Optional[float] = DEFAULT_SYLLABLE_UNIGRAM_ALPHA,
    syllable_phoneme_pattern: str = DEFAULT_SYLLABLE_PHONEME_PATTERN,
    syllable_control: bool = DEFAULT_SYLLABLE_SYLLABLE_CONTROL,
    syllable_alpha: Optional[float] = DEFAULT_SYLLABLE_SYLLABLE_ALPHA,
    syllable_consonant_features: Optional[list] = DEFAULT_SYLLABLE_CONSONANT_FEATURES,
    syllable_vowel_features: Optional[list] = DEFAULT_SYLLABLE_VOWEL_FEATURES,
    syllable_export_ssml: bool = DEFAULT_SYLLABLE_EXPORT_SSML,
    syllable_corpus: str = None,

    # word generation
    word_n_syllables_per_word: int = DEFAULT_WORD_N_SYLLABLES_PER_WORD,
    word_bigram_control: bool = DEFAULT_WORD_BIGRAM_CONTROL,
    word_bigram_alpha: Optional[float] = DEFAULT_WORD_BIGRAM_ALPHA,
    word_trigram_control: bool = DEFAULT_WORD_TRIGRAM_CONTROL,
    word_trigram_alpha: Optional[float] = DEFAULT_WORD_TRIGRAM_ALPHA,
    word_positional_control: bool = DEFAULT_WORD_POSITIONAL_CONTROL,
    word_positional_control_position: Optional[int] = DEFAULT_WORD_POSITIONAL_CONTROL_POSITION,
    word_position_alpha: Optional[float] = DEFAULT_WORD_POSITION_ALPHA,
    word_phonotactic_control: bool = DEFAULT_WORD_PHONOTACTIC_CONTROL,
    word_n_look_back: int = DEFAULT_WORD_N_LOOK_BACK,
    word_n_words: int = DEFAULT_WORD_N_WORDS,
    word_max_tries: int = DEFAULT_WORD_MAX_TRIES,

    # lexicon-level
    lexicon_n_lexicons: int = DEFAULT_LEXICON_N_LEXICONS,
    lexicon_n_words_per_lexicon: int = DEFAULT_LEXICON_N_WORDS_PER_LEXICON,
    lexicon_binary_feature_control: bool = DEFAULT_LEXICON_BINARY_FEATURE_CONTROL,
    lexicon_max_overlap: float = DEFAULT_LEXICON_MAX_OVERLAP,
    lexicon_lag_of_interest: Optional[int] = DEFAULT_LEXICON_LAG_OF_INTEREST,
    lexicon_max_word_matrix: Optional[int] = DEFAULT_LEXICON_MAX_WORD_MATRIX,
    lexicon_unique_words: bool = DEFAULT_LEXICON_UNIQUE_WORDS,
    lexicon_control_features: Optional[list] = DEFAULT_LEXICON_CONTROL_FEATURES,

    # stream-level
    stream_max_rhythmicity = DEFAULT_STREAM_MAX_RHYTHMICITY,
    stream_repetitions = DEFAULT_STREAM_REPETITIONS,
    stream_max_tries_randomize = DEFAULT_STREAM_MAX_TRIES_RANDOMIZE,
    stream_tp_modes = DEFAULT_STREAM_TP_MODES,
    stream_require_all_tp_modes = DEFAULT_STREAM_REQUIRE_ALL_TP_MODES,
    stream_n_streams_per_lexicon = DEFAULT_STREAM_N_STREAMS_PER_LEXICON,

    # log
    log_dir: str = DEFAULT_COMMON_LOG_DIR,
    log_console: bool = True,
):
    """
    Run the full lexicon-generation pipeline:
    phonemes → syllables → pseudo-words → lexicons.

    All intermediate objects are logged and saved to disk.

    Parameters
    ----------
    lang : str, optional
        Language code used for phoneme and syllable patterns.
    progress_bars : bool
        Whether progress bars should render during word/lexicon construction.

    unigram_control : bool
        Whether to filter phonemes by unimodal distribution.
    unigram_alpha : float, optional
        Threshold for unigram phoneme filtering.

    phoneme_pattern : str
        Pattern describing syllable structure (e.g., cV, cVc).
    syllable_control : bool
        Whether to apply corpus-based syllable control.
    syllable_alpha : float, optional
        Threshold for syllable-level feature control.
    consonant_features, vowel_features : list, optional
        Feature lists for constrained syllable generation.
    export_ssml : bool
        Whether to export SSML files for speech synthesis.

    n_syllables_per_word : int
        Number of syllables in each pseudo-word.
    bigram_control, trigram_control : bool
        Whether to enforce bigram/trigram distributions.
    bigram_alpha, trigram_alpha : float, optional
        Threshold for n-gram controls.
    positional_control : bool
        Whether to condition syllable choice on position.
    positional_control_position : int, optional
        Target position for the positional constraint.
    position_alpha : float, optional
        Threshold for positional control.
    phonotactic_control : bool
        Enforce phonotactic rules.
    n_look_back : int
        Look-back window for phonotactic control.
    n_words : int
        Number of pseudo-words to generate.
    max_tries : int
        Maximum failed attempts allowed when generating words.

    n_lexicons : int
        Number of lexicons to generate.
    n_words_per_lexicon : int
        Words per lexicon.
    binary_feature_control : bool
        If true, control binary features across lexicons.
    max_overlap : float
        Maximum inter-lexicon word-feature overlap count.
    lag_of_interest : int, optional
        Shift for computing feature-vector correlation.
    max_word_matrix : int, optional
        Maximum allowed size of the word-feature matrix.
    unique_words : bool
        Enforce unique words within each lexicon.
    control_features : list, optional
        Optional feature list to loosen lexicon construction.

    logger : logging.Logger, optional
        Optional logger for reporting progress.
    log_dir : str
        Directory where all intermediate results are stored.

    Returns
    -------
    list[Lexicon]
        Generated lexicons.
    """

    logger, log_dir = setup_logging(log_dir, log_console, name="generate_streams")
    dump_dir = os.path.join(log_dir, _OBJECT_DUMP)

    if lexicon is not None:
        lexicon, _ = diagnose(lexicon, logger=logger, log_dir=log_dir)
        lexicons = [lexicon] 
        return generate_streams(
            lexicons, 
            max_rhythmicity=stream_max_rhythmicity,
            repetitions=stream_repetitions,
            max_tries_randomize=stream_max_tries_randomize,
            tp_modes=stream_tp_modes,
            require_all_tp_modes=stream_require_all_tp_modes,
            n_streams_per_lexicon=stream_n_streams_per_lexicon, 
            logger=logger, 
            log_dir=log_dir
        )

    # ----------------------------------------------------------
    # PHONEMES
    # ----------------------------------------------------------
    phonemes = load_phonemes(lang=lang if syllable_unigram_control else None)

    if syllable_unigram_alpha is not None:
        phonemes = phonemes.filter(lambda u: u.info["p_unif"] > syllable_unigram_alpha)

    if logger:
        logger.info(f"Generated Phonemes: {phonemes}")

    # ----------------------------------------------------------
    # SYLLABLES
    # ----------------------------------------------------------
    syllables = make_syllables(
        phonemes=phonemes,
        phoneme_pattern=syllable_phoneme_pattern,
        syllable_control=syllable_control,
        syllable_alpha=syllable_alpha,
        lang=lang,
        consonant_features=syllable_consonant_features,
        vowel_features=syllable_vowel_features,
        syllables_path=syllable_corpus,
    )

    if logger:
        logger.info(f"Generated Syllables: {syllables}")

    syllables.save(os.path.join(dump_dir, "syllables.json"))

    if syllable_export_ssml:
        from alparc.io import export_speech_synthesizer
        export_speech_synthesizer(syllables, syllables_dir=os.path.join(log_dir, "ssml"))

    # ----------------------------------------------------------
    # WORDS
    # ----------------------------------------------------------
    if logger:
        logger.info("Generating Pseudo-Words...")

    pseudo_words = make_words(
        syllables=syllables,
        num_syllables=word_n_syllables_per_word,
        bigram_control=word_bigram_control,
        bigram_alpha=word_bigram_alpha,
        trigram_control=word_trigram_control,
        trigram_alpha=word_trigram_alpha,
        positional_control=word_positional_control,
        positional_control_position=word_positional_control_position,
        position_alpha=word_position_alpha,
        phonotactic_control=word_phonotactic_control,
        n_look_back=word_n_look_back,
        n_words=word_n_words,
        max_tries=word_max_tries,
        progress_bar=progress_bars,
        lang=lang,
    )

    if not pseudo_words:
        logger.warn("No valid words found.")
        return Stream(), {}

    if logger:
        logger.info(f"Generated Pseudo-Words: {pseudo_words}")

    pseudo_words.save(os.path.join(dump_dir, "pseudo_words.json"))

    if logger:
        logger.info("Generating Lexicons...")

    lexicons = make_lexicons(
        pseudo_words,
        n_lexicons=lexicon_n_lexicons,
        n_words=lexicon_n_words_per_lexicon,
        binary_feature_control=lexicon_binary_feature_control,
        max_overlap=lexicon_max_overlap,
        lag_of_interest=lexicon_lag_of_interest,
        max_word_matrix=lexicon_max_word_matrix,
        unique_words=lexicon_unique_words,
        control_features=lexicon_control_features,
        progress_bar=progress_bars,
    )

    if logger:
        logger.info(f"Generated Lexicons: {[str(lx) for lx in lexicons]}")

    for i, lex in enumerate(lexicons):
        lex.save(os.path.join(dump_dir, f"lexicon_{i}.json"))

    return generate_streams(
            lexicons, 
            max_rhythmicity=stream_max_rhythmicity,
            repetitions=stream_repetitions,
            max_tries_randomize=stream_max_tries_randomize,
            tp_modes=stream_tp_modes,
            require_all_tp_modes=stream_require_all_tp_modes,
            n_streams_per_lexicon=stream_n_streams_per_lexicon, 
            logger=logger, 
            log_dir=log_dir
        )
