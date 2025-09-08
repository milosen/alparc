from alparc.phonecodes import phonecodes
from alparc import generate
import pandas as pd

# adapt to what your file looks like
df = pd.read_csv("corpus/orig/EFS.CD", delimiter="\\", names=["Syllable", "freq"], usecols=[0, 3])

# phonecodes provides conversion routines to get the ipa phonemes
df["Syllable"] = df["Syllable"].apply(lambda x: phonecodes.disc2ipa(x, L="eng"))

# ALPARC expects these columns
df = df.set_index("Syllable").rename_axis(index=None)
df["prob"] = df["freq"]/df.sum()["freq"]

df = df.drop_duplicates()

# for future reference
df.to_csv("corpus/syllables.csv")

generate(syllables="corpus/syllables.csv")
