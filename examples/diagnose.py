from alparc import diagnose
# Example usage
stimuli, report = diagnose(stimuli=["k_a|t_a|l_a|n_a", "m_a|r_a|s_a|p_a"], is_lexicon=False)
stimuli, report = diagnose(stimuli="k_a|t_a|l_a|n_a|m_a|r_a|s_a|p_a")