"""
D&D 5e Core - Spells Module
Contains all spellcasting-related classes
"""

from .spell import Spell
from .spellcaster import SpellCaster
from .spell_slots import (
    SpellSlots,
    get_spell_slots_by_level
)
from .cantrips import (
    is_cantrip,
    get_cantrip_damage_scaling,
    get_cantrip_damage,
    filter_cantrips,
    get_cantrips_known_by_level,
    DAMAGE_CANTRIPS,
    UTILITY_CANTRIPS
)

__all__ = [
    'Spell',
    'SpellCaster',
    'SpellSlots',
    'get_spell_slots_by_level',
    'is_cantrip',
    'get_cantrip_damage_scaling',
    'get_cantrip_damage',
    'filter_cantrips',
    'get_cantrips_known_by_level',
    'DAMAGE_CANTRIPS',
    'UTILITY_CANTRIPS',
]

