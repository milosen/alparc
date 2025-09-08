from functools import partial
import os
from typing import Optional, Union, List

from tqdm import tqdm
import yaml
from .io import load_phonemes, load_syllables, load_words, load_lexicons, load_streams, export_speech_synthesizer, read_phoneme_corpus

from .controls.common import set_seed

from .types.base_types import Register, RegisterType, Element
from .types.phoneme import Phoneme, PhonemeType
from .types.syllable import Syllable, SyllableType
from .types.word import Word, WordType
from .types.lexicon import Lexicon, LexiconType
from .types.stream import Stream, StreamType

from .core.syllable import make_syllables
from .core.word import make_words
from .core.lexicon import make_lexicons
from .core.stream import make_streams

from .eval import to_lexicon, to_stream, to_word

from .cli import _OBJECT_DUMP, generate_stream_dataset, evaluate_lexicons, Generate, Diagnose, CommonArgs, WordArgs, StreamArgs, LexiconArgs, SyllableArgs, setup_logging, write_stream_summary

def read_lexicon(words: Union[str, List[str]]):
    return Lexicon(word for word in words)

def generate_lexicons(generate_args, logger, log_dir):
    phonemes = load_phonemes(lang=(generate_args.common.lang if generate_args.syllable.unigram_control else None))
    if generate_args.syllable.unigram_alpha is not None:
        phonemes = phonemes.filter(lambda unigram: unigram.info["p_unif"] > generate_args.syllable.unigram_alpha)

    logger.info(f"Generate Phonemes: {phonemes}")

    syllables = make_syllables(
        phonemes=phonemes, 
        phoneme_pattern=generate_args.syllable.phoneme_pattern,
        syllable_control=generate_args.syllable.syllable_control,
        syllable_alpha=generate_args.syllable.syllable_alpha,
        lang=generate_args.common.lang,
        consonant_features=generate_args.syllable.consonant_features,
        vowel_features=generate_args.syllable.vowel_features,
    )
    logger.info(f"Generate Syllables: {syllables}")

    syllables.save(os.path.join(log_dir, _OBJECT_DUMP, "syllables.json"))

    if generate_args.syllable.export_ssml:
        from alparc.io import export_speech_synthesizer
        export_speech_synthesizer(syllables, syllables_dir=os.path.join(log_dir, "ssml"))

    logger.info(f"Generate Pseudo-Words: ...")
    pseudo_words = make_words(
        syllables=syllables,
        num_syllables=generate_args.word.n_syllables_per_word,
        bigram_control=generate_args.word.bigram_control,
        bigram_alpha=generate_args.word.bigram_alpha,
        trigram_control=generate_args.word.trigram_control,
        trigram_alpha=generate_args.word.trigram_alpha,
        positional_control=generate_args.word.positional_control,
        positional_control_position=generate_args.word.positional_control_position,
        position_alpha=generate_args.word.position_alpha,
        phonotactic_control=generate_args.word.phonotactic_control,
        n_look_back=generate_args.word.n_look_back,
        n_words=generate_args.word.n_words,
        max_tries=generate_args.word.max_tries,
        progress_bar=generate_args.common.progress_bars,
        lang=generate_args.common.lang,
    )
    logger.info(f"Pseudo-Words: {pseudo_words}")

    pseudo_words.save(os.path.join(log_dir, _OBJECT_DUMP, "pseudo_words.json"))

    logger.info(f"Generate Lexicons: ...")
    lexicons = make_lexicons(
        pseudo_words, 
        n_lexicons=generate_args.lexicon.n_lexicons, 
        n_words=generate_args.lexicon.n_words_per_lexicon,
        max_overlap=generate_args.lexicon.max_overlap,
        lag_of_interest=generate_args.lexicon.lag_of_interest,
        max_word_matrix=generate_args.lexicon.max_word_matrix,
        unique_words=generate_args.lexicon.unique_words,
        control_features=generate_args.lexicon.control_features,
        progress_bar=generate_args.common.progress_bars,
        binary_feature_control=generate_args.lexicon.binary_feature_control,
    )
    logger.info(f"Lexicons: {[str(l) for l in lexicons]}")

    for i, lexicon in enumerate(lexicons):
        lexicon.save(os.path.join(log_dir, _OBJECT_DUMP, f"lexicon_{i}.json"))
    
    return lexicons

def diagnose(lexicon, diagnose_args: Diagnose = Diagnose(" "), log=None):
    if log is not None:
        logger, log_dir = log
    else:
        logger, log_dir = setup_logging(diagnose_args.common.log_dir, diagnose_args.common.log_console, name="diagnose_lexicon")

        with open(os.path.join(log_dir, "config.yml"), "w") as file:
            yaml.dump(vars(diagnose_args), file, encoding="utf-8")

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
    
    return lexicon, summary


def generate(
    lexicon: Optional[List[str]] = None,
    syllables: Optional[str] = None,
    generate_args: Generate = Generate(), 
):
    # overwrite here for easier access
    generate_args.common.lexicon = lexicon
    generate_args.syllable.syllables_path = syllables

    if generate_args.syllable.syllables_path is not None:
        print("Generate with custom syllable corpus: ", generate_args.syllable.syllables_path)
        generate_args.syllable.unigram_control = False
        generate_args.word.positional_control = False

    logger, log_dir = setup_logging(generate_args.common.log_dir, generate_args.common.log_console, name="generate_streams")
    
    with open(os.path.join(log_dir, "config.yml"), "w") as file:
        yaml.dump(vars(generate_args), file, encoding="utf-8")

    if generate_args.common.lexicon is None:
        lexicons = generate_lexicons(generate_args=generate_args, log_dir=log_dir, logger=logger)
    else:
        lexicon, _ = diagnose(lexicon, log=(logger, log_dir))
        lexicons = [lexicon]

    logger.info(f"Generate Streams: ...")
    streams = Register()
    for _ in tqdm(range(generate_args.stream.n_streams_per_lexicon)):
        for stream in make_streams(
            lexicons,
            max_rhythmicity=generate_args.stream.max_rhythmicity,
            stream_length=generate_args.stream.repetitions,
            max_tries_randomize=generate_args.stream.max_tries_randomize,
            tp_modes=generate_args.stream.tp_modes,
            require_all_tp_modes=generate_args.stream.require_all_tp_modes
        ):
            streams.append(stream)
    
    logger.info(f"Streams: ")
    streams.save(os.path.join(log_dir, _OBJECT_DUMP, f"streams.json"))
    report = write_stream_summary(streams, save_path=log_dir, logger=logger)
    return streams, report
