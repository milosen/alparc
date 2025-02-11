import logging
from arpac.register_builders import PhonemeRegisterBuilder
from arpac.registers import PhonemeRegister
from arpac.io import BINARY_FEATURES_DEFAULT_PATH

def test_load_feature_dataset():
    corpus = PhonemeRegisterBuilder().add_features_dataset().build()
    assert isinstance(corpus, PhonemeRegister), f"Is actually {type(corpus)}"

def test_print():
    dataset = PhonemeRegisterBuilder().add_features_dataset().build()
    logging.info(dataset)

def test_language_validation():
    corpus = PhonemeRegisterBuilder().add_phoneme_corpus(lang="deu").build()
    logging.info(corpus)
