from alparc.phonecodes import phonecodes
from alparc import generate
import pandas as pd

# adapt to what your file looks like
# here we use a CELEX corpus (which we are not allowed to re-distribute)
from alparc.phonecodes import phonecodes
import csv
import pandas as pd
import os
from alparc.io import CORPUS_DEFAULT_PATH_DEU_SPECIAL


syllables_corpus_path = os.path.join(CORPUS_DEFAULT_PATH_DEU_SPECIAL, "orig", "syll.txt")

with open(syllables_corpus_path, "r", encoding='utf-8') as csv_file:
    fdata = list(csv.reader(csv_file, delimiter='\t'))

syllables_dict = {}

for syll_stats in fdata[1:]:
    syll_ipa = phonecodes.xsampa2ipa(syll_stats[1], language="deu")
    info = {"freq": int(syll_stats[2]), "prob": float(syll_stats[3])}
    syllables_dict[syll_ipa] = info  # will overwrite if already present

df = pd.DataFrame.from_dict(syllables_dict, orient="index")

df = df.drop_duplicates()

# for future reference
df.to_csv("results/syllables.csv")

generate(syllable_corpus="results/syllables.csv")
