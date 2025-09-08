from alparc import generate

# Example usage for generating streams starting with a custom lexicon
# This will generate a set of streams based on the provided lexicon.
# The lexicon should be a list of words. Phonemes in the lexicon should be separated by an underscore _ and syllables should be separated by vertical bars |.
streams, report = generate(lexicon=[
    'f_oː|ɡ_uː|r_iː', 'ɡ_eː|z_iː|m_aː', 'l_iː|v_aː|k_uː', 'ʃ_aː|h_ɛː|p_iː'
])
