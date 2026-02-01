"""
D&D 5e Core - Combat Module
Contains all combat-related classes and systems
"""

from .damage import Damage
from .condition import (
    Condition, ConditionType,
    create_restrained_condition, create_poisoned_condition,
    create_frightened_condition, create_grappled_condition,
    create_paralyzed_condition, create_stunned_condition,
    create_prone_condition, create_blinded_condition,
    create_charmed_condition, create_incapacitated_condition
)
from .condition_parser import ConditionParser, parse_magic_item_conditions
from .action import ActionType, Action
from .special_ability import AreaOfEffect, SpecialAbility
from .combat_system import CombatSystem, execute_combat_turn
# Re-export RangeType from equipment for convenience
from ..equipment import RangeType

__all__ = [
    'Damage',
    'Condition', 'ConditionType',
    'create_restrained_condition', 'create_poisoned_condition',
    'create_frightened_condition', 'create_grappled_condition',
    'create_paralyzed_condition', 'create_stunned_condition',
    'create_prone_condition', 'create_blinded_condition',
    'create_charmed_condition', 'create_incapacitated_condition',
    'ConditionParser', 'parse_magic_item_conditions',
    'ActionType', 'Action',
    'AreaOfEffect', 'SpecialAbility',
    'CombatSystem', 'execute_combat_turn',
    'RangeType',  # Re-exported from equipment
]

