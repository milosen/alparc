#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#%%#################################################################################################
############################################## README ##############################################
####################################################################################################

"""
Created on Tue Sep 20 14:49:36 2022

(1) Read stimuli constructed with the algorithm (Titone, Milosevic & Meyer 2024)
(2) Concatenated audio syllables to make streams according to "best_lexicon.txt"

@author: titone
"""

# PROJECT DIRECTORY
project_dir = '/data/u_titone_thesis/PhD_Leipzig/01_Projects/01_Artificial_Lexicon/'

#%%#################################################################################################
############################################## IMPORT ##############################################
####################################################################################################

# IMPORT MODULES
import csv
import wave
import pickle
import itertools
import numpy as np

#%%#################################################################################################
############################################## TRIALS ##############################################
####################################################################################################

# IMPORT STREAMS FROM TITONE, MILOSEVIC & MEYER (2024) ARC PACKAGE
indir = project_dir + '01_Stimuli/02_Lexicons/'
fname = indir + 'best_lexicon.txt'
fdata = list(csv.reader(open(fname, "r")))
lexicon_words = fdata[0][0].split(": ")[1].split("|")
lexicon_sylls = [list(map(''.join, zip(*[iter(i)]*nPoss))) for i in lexicon_words]
TP_posrdm_arc = fdata[2][0].split(": ")[1].split("|")
TP_struct_arc = fdata[7][0].split(": ")[1].split("|")
TP_posfix_arc = fdata[12][0].split(": ")[1].split("|")
TP_stream_arc = [TP_struct_arc, TP_posfix_arc, TP_posrdm_arc]
TP_fnames_arc = ['TP_struct_ARC', 'TP_posfix_ARC', 'TP_posrdm_ARC']

#%%#################################################################################################
######################################### TRIALS SYNTHESIS #########################################
####################################################################################################

# CONCATENATE SYLLABLES INTO AUDITORY STREAMS
opdir = project_dir + '01_Stimuli/03_Streams/'
indir = project_dir + '01_Stimuli/01_Syllables/06_Sounds/'
for iStrm in range(len(TP_stream_arc)):
    trial = TP_stream_arc[iStrm]
    f_out = opdir + TP_fnames_arc[iStrm] + '.wav'
    fdata = []
    for iSyll in trial:
        sname = iSyll.replace('ː', '.wav')
        fname = indir + sname
        audio = wave.open(fname, 'rb')
        fdata.append([audio.getparams(), audio.readframes(audio.getnframes())])
        audio.close()
    sfile = wave.open(f_out, 'wb')
    sfile.setparams(fdata[0][0])
    for i in range(len(fdata)):
        sfile.writeframes(fdata[i][1])
    sfile.close()
