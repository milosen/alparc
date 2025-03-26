#!/bin/bash
arpac generate-streams --common.name "no_corpus" --common.lang eng --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 \
                       --syllable.no-unigram-control --syllable.no-syllable-control  --word.no-phonotactic-control --word.no-positional-control
arpac generate-streams --common.name "default_5words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 5
arpac generate-streams --common.name "default_6words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 6
arpac generate-streams --common.name "default_8words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 8
arpac generate-streams --common.name "default_2syllables" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 2
arpac generate-streams --common.name "default_4syllables" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 4

#arpac generate-streams --lexicon.binary-feature-control --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10  --syllable.syllable_alpha 0.05 --common.name "default_german"
#arpac generate-streams --lexicon.binary-feature-control --common.lang eng --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --common.name "default_english"
#arpac generate-streams --lexicon.binary-feature-control --common.name "no_corpus" --common.lang eng --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 \
#                       --syllable.no-unigram-control --syllable.no-syllable-control  --word.no-phonotactic-control --word.no-positional-control
#arpac generate-streams --lexicon.binary-feature-control --common.name "default_5words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 5
#arpac generate-streams --lexicon.binary-feature-control --common.name "default_6words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 6
#arpac generate-streams --lexicon.binary-feature-control --common.name "default_8words" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --lexicon.n-words-per-lexicon 8
#arpac generate-streams --lexicon.binary-feature-control --common.name "default_2syllables" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 2
#arpac generate-streams --lexicon.binary-feature-control --common.name "default_4syllables" --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --word.n-syllables-per-word 4