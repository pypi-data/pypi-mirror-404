"""
D&D 5e Core - Mechanics Module
Contains dice rolling and other game mechanics
"""

from .dice import DamageDice
from .experience import (
    XP_LEVELS,
    get_level_from_xp,
    get_xp_for_level,
    get_xp_to_next_level,
    should_level_up,
    calculate_proficiency_bonus,
    get_cr_xp
)
from .level_up import (
    LevelUpResult,
    calculate_hp_gain,
    can_level_up,
    get_ability_score_improvement_levels,
    is_ability_score_improvement_level,
    perform_level_up
)
from .challenge_rating import (
    ChallengeRating,
    EncounterDifficulty,
    get_xp_thresholds_for_level,
    calculate_encounter_difficulty,
    get_appropriate_cr_range
)
from .encounter_builder import (
    ENCOUNTER_TABLE,
    generate_encounter_distribution,
    select_monsters_by_encounter_table,
    get_encounter_info
)
from .gold_rewards import (
    ENCOUNTER_GOLD_TABLE,
    get_encounter_gold,
    calculate_treasure_hoard
)

__all__ = [
    'DamageDice',
    'XP_LEVELS',
    'get_level_from_xp',
    'get_xp_for_level',
    'get_xp_to_next_level',
    'should_level_up',
    'calculate_proficiency_bonus',
    'get_cr_xp',
    'LevelUpResult',
    'calculate_hp_gain',
    'can_level_up',
    'get_ability_score_improvement_levels',
    'is_ability_score_improvement_level',
    'perform_level_up',
    'ChallengeRating',
    'EncounterDifficulty',
    'get_xp_thresholds_for_level',
    'calculate_encounter_difficulty',
    'get_appropriate_cr_range',
    'ENCOUNTER_TABLE',
    'generate_encounter_distribution',
    'select_monsters_by_encounter_table',
    'get_encounter_info',
    'ENCOUNTER_GOLD_TABLE',
    'get_encounter_gold',
    'calculate_treasure_hoard',
]

