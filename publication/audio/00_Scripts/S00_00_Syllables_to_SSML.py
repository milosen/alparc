#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#%%#################################################################################################
############################################## README ##############################################
####################################################################################################

"""
This script extracts a subset of CV syllables from a German corpus based on frequency statistics:
(1) German syllables and statistics are extracted from a corpus of conversational German (BAStat)
(2) Phonological features of German phonemes are extracted from a binary matrix (binary_features)
(3) Consonant-Vowel (CV) syllables with long vowel length are selected from the list of syllables
(4) Syllables with uniform log-proability of occurrence are selected from the subset of syllables
(5) Selected CV syllables are written in IPA style to separate files for text-to-speech synthesis

@author: titone
"""

# PROJECT DIRECTORY
project_dir = '/data/u_titone_thesis/PhD_Leipzig/01_Projects/01_Artificial_Lexicon/'
stimuli_dir = project_dir + '01_Stimuli/'

#%%#################################################################################################
############################################## IMPORT ##############################################
####################################################################################################

# IMPORT MODULES
import csv
import pickle
import phonecodes
import numpy as np
from scipy import stats
from matplotlib import pyplot as plt

#%%#################################################################################################
########################################### CV SYLLABLES ###########################################
####################################################################################################

# READ SYLLABLES, FREQUENCIES AND PROBABILITIES FROM CORPUS AND CONVERT SYLLABLES TO IPA
indir = stimuli_dir + '00_Corpus/'
fname = indir + 'syll.txt'
fdata = list(csv.reader(open(fname, "r"), delimiter = '\t'))
sylls = [phonecodes.xsampa2ipa(i[1], 'deu') for i in fdata[1:]]
freqs = [int(i[2]) for i in fdata[1:]]
probs = [float(i[3]) for i in fdata[1:]]

# READ MATRIX OF BINARY FEATURES FOR ALL IPA PHONEMES
fname = indir + 'binary_features.csv'
fdata = list(csv.reader(open(fname, "r")))
labls = fdata[0][1:]
phons = [i[0] for i in fdata[1:]]
numbs = [i[1:] for i in fdata[1:]]
cnsnt = [phons[i] for i in range(len(phons)) if numbs[i][labls.index('cons')] == '+']
longV = [phons[i] for i in range(len(phons)) if numbs[i][labls.index('long')] == '+' 
                                             and phons[i] not in cnsnt]

# SELECT CONSONANT-VOWEL SYLLABLES WITH LONG VOWEL LENGTH
cvidx = [i for i in range(len(sylls)) if sylls[i].startswith(tuple(cnsnt))
         and sylls[i].endswith(tuple(longV)) and len(sylls[i]) == 3]
cvsyl = [sylls[i] for i in cvidx]
cvfrq = [freqs[i] for i in cvidx]
cvprb = [probs[i] for i in cvidx]

# SELECT CV SYLLABLES WITH UNIFORM LOG-PROBABILITY OF OCCURRENCE IN THE CORPUS
CVidx = [i for i in range(len(cvfrq)) 
         if stats.uniform.sf(abs(stats.zscore(np.log(cvfrq))))[i] > 0.05]
CVsyl = [cvsyl[i] for i in CVidx]
CVfrq = [cvfrq[i] for i in CVidx]
CVprb = [cvprb[i] for i in CVidx]

# # SAVE SUBSET OF CV SYLLABLES FOR THE NEXT STEP
# opdir = stimuli_dir + '01_Syllables/00_CV/'
# fname = opdir + 'syllables.pickle'
# with open(fname, 'wb') as f:
#     pickle.dump(CVsyl, f, pickle.HIGHEST_PROTOCOL)

# # SAVE EACH SYLLABLE TO A TEXT FILE FOR THE SPEECH SYNTHESIZER
# opdir = stimuli_dir + '01_Syllables/01_Tags/'
# c = [i[0] for i in CVsyl]
# v = [i[1] for i in CVsyl]
# c = ' '.join(c).replace('ʃ','sch').replace('ɡ','g').replace('ç','ch').replace('ʒ','dsch').split()
# v = ' '.join(v).replace('ɛ','ä').replace('ø','ö').replace('y','ü').split()
# t = [c[i] + v[i] for i in range(len(CVsyl))]
# for iSyll in range(len(CVsyl)):
#     i_Txt = t[iSyll]
#     i_IPA = CVsyl[iSyll]
#     toSyn = '<phoneme alphabet="ipa" ph=' + '"' + i_IPA + '"' + '>' + i_Txt + '</phoneme>'
#     fname = opdir + str(i_IPA[0:2]) + '.txt'
#     with open(fname, 'w') as f:
#         f.write(toSyn + "\n")
#         w = csv.writer(f)
