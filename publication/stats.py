import glob
import pandas as pd
from alparc import load_streams

all_streams = [
    ("ALPARC-DEU", load_streams(glob.glob("results/default_german_*")[-1] + "/_arpac/streams.json")), 
    ("ALPARC-DEU-3w", load_streams(glob.glob("results/default_3words_no_rnd_*")[-1] + "/_arpac/streams.json")),
    ("ALPARC-DEU-5w", load_streams(glob.glob("results/default_5words_no_rnd_*")[-1] + "/_arpac/streams.json")), 
    ("ALPARC-DEU-2s", load_streams(glob.glob("results/default_2syllables_no_rnd_*")[-1] + "/_arpac/streams.json")),
    ("ALPARC-DEU-4s", load_streams(glob.glob("results/default_4syllables_no_rnd_*")[-1] + "/_arpac/streams.json")),
    ("ALPARC-ENG", load_streams(glob.glob("results/default_english_*")[-1] + "/_arpac/streams.json")), 
    ("ALPARC-RND", load_streams(glob.glob("results/random_german_*")[-1] + "/_arpac/streams.json")),
    ("ALPARC-RND", load_streams(glob.glob("results/random_english_*")[-1] + "/_arpac/streams.json")),
    ("BENCHMARK", load_streams(glob.glob("results/literature_streams_*")[-1] + "/_arpac/streams.json")), 
]

data = {"Control": [], "Lexicon": [], "Cumulative feature overlap": [], "Feature": [], "PRI": [], "Stream TP mode": [], "Stream": []}

mode_to_mode = {  # TP-uniform position-random; TP-uniform position-fixed and TP-structured
    "random": "TP-uniform position-random",
    "word_structured": "TP-structured",
    "position_controlled": "TP-uniform position-fixed"
}

for control, streams in all_streams:
    for stream in streams:
        for k, v in stream.info["rhythmicity_indexes"].items():
            data["Feature"].append(k)
            data["PRI"].append(v)
            data["Control"].append(control)
            data["Lexicon"].append(str(stream.info["lexicon"]))
            data["Stream TP mode"].append(mode_to_mode[stream.info["stream_tp_mode"]])
            data["Stream"].append("|".join(syll.id for syll in stream))
            data["Cumulative feature overlap"].append(stream.info["lexicon_info"]["cumulative_feature_repetitiveness"])
        data["Feature"].append("max")
        data["PRI"].append(max(stream.info["rhythmicity_indexes"].values()))
        data["Control"].append(control)
        data["Lexicon"].append(str(stream.info["lexicon"]))
        data["Stream TP mode"].append(mode_to_mode[stream.info["stream_tp_mode"]])
        data["Stream"].append("|".join(syll.id for syll in stream))
        data["Cumulative feature overlap"].append(stream.info["lexicon_info"]["cumulative_feature_repetitiveness"])

df = pd.DataFrame(data)

df.Control = df.Control.astype("category")
df.Control = df.Control.cat.set_categories([
    "ALPARC-DEU", 
    "ALPARC-DEU-3w",
    "ALPARC-DEU-5w", 
    "ALPARC-DEU-2s",
    "ALPARC-DEU-4s",
    "ALPARC-ENG", 
    "ALPARC-RND",
    "BENCHMARK",
])

df = df.sort_values(["Control", "Lexicon", "Stream TP mode"]).reset_index(drop=True)

import os
os.makedirs("results/", exist_ok=True)
df.to_csv("results/analysis_full_dataset.csv")

df_lexicons = df[["Control", "Lexicon"]].drop_duplicates().reset_index(drop=True)
df_lexicons.to_csv("results/analysis_all_lexicons.csv")

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
from pingouin import ttest
import itertools

tp_modes = ["TP-uniform position-random", "TP-uniform position-fixed", "TP-structured"]
dfs = []

for i, tp_mode in enumerate(tp_modes):
    for one, two in itertools.combinations([
    "ALPARC-DEU",
    "ALPARC-ENG", 
    "ALPARC-RND",
    "BENCHMARK"], 2):
        df2 = df[(df["Stream TP mode"] == tp_mode) & (df["Feature"] == "max")]
        cat1 = df2[df2['Control'] == one]["PRI"]
        cat2 = df2[df2['Control'] == two]["PRI"]
        print(tp_mode, one, two)
        this = ttest(list(cat1), list(cat2), alternative="two-sided")
        this.index = pd.MultiIndex.from_tuples([(tp_mode, f"{one} vs. {two}")], names=["Stream TP mode", "Controls"])
        dfs.append(this)

ttest_df = pd.concat(dfs).rename({"dof": "df"}, axis=1)

ttest_df.to_csv("results/table_1.csv", index=True)
