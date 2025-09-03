from alparc import generate
# Example usage for generating streams from scratch
# This will generate a set of streams with the default parameters.
# check out the documentation for more options, or run `help(generate)`.
streams, report = generate()
# Example usage for generating streams starting with a custom lexicon
# This will generate a set of streams based on the provided lexicon.
# The lexicon should be a list of words. Phonemes in the lexicon should be separated by an underscore _ and syllables should be separated by vertical bars |.
streams, report = generate(words=["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"], is_lexicon=True)
# Example usage for generating streams from words
streams, report = generate(words=["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"], is_lexicon=False)
