"""
D&D 5e Core - Classes Module
Contains character class and proficiency systems
"""

from .proficiency import ProfType, Proficiency
from .class_type import ClassType, Feature, Level, BackGround
from .multiclass import (
    MulticlassRequirements,
    MULTICLASS_PREREQUISITES,
    can_multiclass_into,
    can_multiclass_from,
    calculate_spell_slots_multiclass,
    get_multiclass_proficiencies,
    calculate_hit_points_multiclass
)

__all__ = [
    'ProfType',
    'Proficiency',
    'ClassType',
    'Feature',
    'Level',
    'BackGround',
    'MulticlassRequirements',
    'MULTICLASS_PREREQUISITES',
    'can_multiclass_into',
    'can_multiclass_from',
    'calculate_spell_slots_multiclass',
    'get_multiclass_proficiencies',
    'calculate_hit_points_multiclass',
]

