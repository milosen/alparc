#!/bin/bash

# additional settings
arpac generate-streams --common.name "default_3words_no_rnd" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 3 --syllable.syllable_alpha 0.05 --stream.tp-modes word_structured position_controlled
arpac generate-streams --common.name "default_5words_no_rnd" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 5 --syllable.syllable_alpha 0.05 --stream.tp-modes word_structured position_controlled
arpac generate-streams --common.name "default_2syllables_no_rnd" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 2 --syllable.syllable_alpha 0.05 --stream.tp-modes word_structured position_controlled
arpac generate-streams --common.name "default_4syllables_no_rnd" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 4 --syllable.syllable_alpha 0.05 --stream.tp-modes word_structured position_controlled
