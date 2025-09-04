from typing import Union, List
from .io import load_phonemes, load_syllables, load_words, load_lexicons, load_streams, export_speech_synthesizer

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

from .cli import generate_stream_dataset, evaluate_lexicons, Generate, Diagnose, CommonArgs, WordArgs, StreamArgs, LexiconArgs, SyllableArgs

DEFAULT_GENERATE_ARGS = Generate(
    common=CommonArgs(),
    syllable=SyllableArgs(),
    word=WordArgs(),
    lexicon=LexiconArgs(),
    stream=StreamArgs()
)

def segmentation(obj: Union[str, List[str]], is_lexicon):
    if isinstance(obj, list) and is_lexicon:
        return Lexicon()

def generate(args: Generate = DEFAULT_GENERATE_ARGS, words=None, is_lexicon=True):
    
    generate_stream_dataset(args)


def diagnose(args: Diagnose):
    evaluate_lexicons(args)
