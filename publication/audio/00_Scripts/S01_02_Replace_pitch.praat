#############################
##### Trials w/ prosody #####
#############################

# clear
clearinfo

# project directory
dir$ = "/data/u_titone_thesis/PhD_Leipzig/01_Projects/01_Artificial_Lexicon/01_Stimuli/"

#################
### Lexicon A ###
#################

# directories
input$ = dir$ + "04_Streams/00_Audios/00_Lexicon_A/00_Exposure/"
output$ = dir$ + "04_Streams/00_Audios/00_Lexicon_A/00_Exposure/"

# get file info
Create Strings as file list... list 'input$'/*.wav
number = Get number of strings
clearinfo

# loop
for i from 1 to number

	# read file
	select Strings list
	soundfile$ = Get string... i
	name$ = replace$ (soundfile$, ".wav", "", 1)
	fullfile$ = input$ + soundfile$
	Read from file... 'fullfile$'
	To Manipulation: 0.01, 75, 600
	
	#########################
	### Change pitch tier ###
	#########################
	
	# read prosody
	Read from file: dir$ + "02_Prosody/02_Sounds/pitch_contour_long.wav"
	
	# extract pitch tier
	To Manipulation: 0.01, 75, 600
	Extract pitch tier
	Stylize: 5, "Hz"
	Interpolate quadratically: 5, "Hz"
	
	# replace pitch tier
	selectObject: "Manipulation " + name$
	plusObject: "PitchTier pitch_contour_long"
	Replace pitch tier
	selectObject: "Manipulation " + name$
	Get resynthesis (overlap-add)
	name$ = replace$ (name$, "Not_P", "Yes_P", 1) + ".wav"
	
	###########################
	### Save processed file ###
	###########################
	
	# save output
	# Save as WAV file... 'output$'/'name$'

endfor

#################
### Lexicon B ###
#################

# directories
input$ = dir$ + "04_Streams/00_Audios/01_Lexicon_B/00_Exposure/"
output$ = dir$ + "04_Streams/00_Audios/01_Lexicon_B/00_Exposure/"

# get file info
Create Strings as file list... list 'input$'/*.wav
number = Get number of strings
clearinfo

# loop
for i from 1 to number

	# read file
	select Strings list
	soundfile$ = Get string... i
	name$ = replace$ (soundfile$, ".wav", "", 1)
	fullfile$ = input$ + soundfile$
	Read from file... 'fullfile$'
	To Manipulation: 0.01, 75, 600
	
	#########################
	### Change pitch tier ###
	#########################
	
	# read prosody
	Read from file: dir$ + "02_Prosody/02_Sounds/pitch_contour_long.wav"
	
	# extract pitch tier
	To Manipulation: 0.01, 75, 600
	Extract pitch tier
	Stylize: 5, "Hz"
	Interpolate quadratically: 5, "Hz"
	
	# replace pitch tier
	selectObject: "Manipulation " + name$
	plusObject: "PitchTier pitch_contour_long"
	Replace pitch tier
	selectObject: "Manipulation " + name$
	Get resynthesis (overlap-add)
	name$ = replace$ (name$, "Not_P", "Yes_P", 1) + ".wav"
	
	###########################
	### Save processed file ###
	###########################
	
	# save output
	# Save as WAV file... 'output$'/'name$'

endfor
