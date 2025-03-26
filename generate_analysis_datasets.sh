#!/bin/bash

arpac generate-streams --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10  --syllable.syllable_alpha 0.05 --common.name "default_german"
arpac generate-streams --common.lang eng --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --common.name "default_english"

arpac generate-streams --lexicon.no-binary-feature-control --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10  --syllable.syllable_alpha 0.05 --common.name "random_german"
arpac generate-streams --lexicon.no-binary-feature-control --common.lang eng --lexicon.n-lexicons 21 --stream.n-streams-per-lexicon 10 --common.name "random_english"

arpac evaluate-lexicons --stream.n-streams-per-lexicon 10 --common.name literature_streams --lexicons \
"pi|ɾu|ta||ba|ɡo|li||to|ku|da||ɡu|ki|bo \
pa|be|la||di|ne|ka||lu|fa|ri||xi|so|du \
ma|xu|pe||xe|ro|ɡa||de|mu|si||fo|le|ti \
pu|ke|mi||ra|fi|nu||bi|na|po||me|do|xi \
no|ni|xe||bu|lo|te||re|mo|fu||ko|tu|sa \
mi|lo|de||da|le|bu||no|ru|pa||ka|te|xi \
ne|do|li||ri|fo|nu||ba|to|ɡu||ki|ra|pu \
ɡo|na|be||mu|di|la||ro|ni|xe||pi|ku|sa \
fu|bi|re||xe|tu|si||ta|fi|ko||ke|ma|po \
ti|fa|xu||so|du|xi||me|lu|bo||ɡa|ni|pe \
mi|po|la||za|bɛ|tu||ʁo|ki|sɛ||nu|ɡa|di \
dɛ|mʊ|ri||sɛ|ni|ɡɛ||ræ|ku|səʊ||pi|lɛ|ru \
ki|fəʊ|bu||lu|fɑ|ɡi||pæ|beɪ|lɑ||tɑ|ɡəʊ|fʊ \
bi|du|pɛ||məʊ|bɑ|li||rɛ|ɡæ|tʊ||sæ|tɛ|kəʊ \
bəʊ|dɑ|mɛ||fi|nəʊ|pɑ||ɡʊ|rɑ|təʊ||ləʊ|kæ|neɪ \
fɛ|si|nɑ||kɛ|su|dəʊ||mæ|pʊ|di||ti|mi|nu \
tu|pi|ɹoʊ||ɡoʊ|la|bu||pa|doʊ|ti||bi|da|ku \
meɪ|lu|ɡi||ɹa|fi|nu||pu|keɪ|mi||toʊ|na|poʊ \
ɡoʊ|la|tu||da|ɹoʊ|pi||ti|bu|doʊ||pa|bi|ku \
poʊ|fi|mu||noʊ|vu|ka||vi|koʊ|ɡa||ba|fu|ɡi \
ma|nu|toʊ||ni|moʊ|lu||voʊ|ɹi|fa||li|du|ɹa"
