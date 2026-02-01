"""
dnd-5e-core
===========

A complete Python package implementing D&D 5th Edition core rules and mechanics.

This package contains all game logic for D&D 5e and is UI-agnostic.
Use it with pygame, ncurses, web, or any other interface.

Quick Start
-----------

    from dnd_5e_core.entities import Sprite
    from dnd_5e_core.equipment import HealingPotion, PotionRarity
    from dnd_5e_core.mechanics import DamageDice
    from dnd_5e_core.abilities import Abilities, AbilityType

    # Create abilities
    abilities = Abilities(str=16, dex=14, con=13, int=12, wis=10, cha=8)

    # Roll damage
    damage = DamageDice("2d6+3")
    result = damage.roll()

    # Create a healing potion
    potion = HealingPotion(
        id=1,
        name="Potion of Healing",
        rarity=PotionRarity.COMMON,
        hit_dice="2d4",
        bonus=2,
        min_cost=50,
        max_cost=50
    )

Modules
-------
- entities: Sprite, Monster, Character
- equipment: Weapons, Armor, Potions
- spells: Spell, SpellCaster
- combat: Actions, Damage, Conditions
- races: Races and Subraces
- classes: Character classes and proficiencies
- abilities: The six core abilities
- mechanics: Dice rolling, XP, CR
- data: API loaders and serialization
"""

__version__ = '0.4.3'
__author__ = 'D&D Development Team'

# Import key classes for convenience
from .entities import Sprite, Monster, Character
from .equipment import (
    Cost, Equipment,
    HealingPotion, SpeedPotion, StrengthPotion, PotionRarity,
    Weapon, Armor
)
from .mechanics import DamageDice
from .mechanics.class_abilities import ClassAbilities
from .mechanics.racial_traits import RacialTraits
from .abilities import Abilities, AbilityType
from .races import Language, Trait, SubRace, Race
from .classes import ProfType, Proficiency, ClassType
from .combat import Damage, Condition, ActionType, Action, SpecialAbility
from .spells import Spell, SpellCaster
from .data import load_monster, load_spell, load_weapon, load_armor
from .ui import Color, color, cprint

# Agent integration helpers
from .agent import init_for_agent, serialize_for_agent, AgentContext

__all__ = [
    # Version
    '__version__',
    # Entities
    'Sprite', 'Monster', 'Character',
    # Equipment
    'Cost', 'Equipment',
    'HealingPotion', 'SpeedPotion', 'StrengthPotion', 'PotionRarity',
    'Weapon', 'Armor',
    # Mechanics
    'DamageDice',
    # Abilities
    'Abilities', 'AbilityType',
    # Races
    'Language', 'Trait', 'SubRace', 'Race',
    # Classes
    'ProfType', 'Proficiency', 'ClassType',
    # Combat
    'Damage', 'Condition', 'ActionType', 'Action', 'SpecialAbility',
    # Spells
    'Spell', 'SpellCaster',
    # Data loaders
    'load_monster', 'load_spell', 'load_weapon', 'load_armor',
    # UI helpers
    'Color', 'color', 'cprint',
    # Agent helpers
    'init_for_agent', 'serialize_for_agent', 'AgentContext',
]

# Additional exports available via submodules
# from dnd_5e_core.mechanics import (experience, level_up, challenge_rating)
# from dnd_5e_core.abilities import (skill, saving_throw)
# from dnd_5e_core.spells import (spell_slots, cantrips)
# from dnd_5e_core.classes import multiclass
# from dnd_5e_core.utils import (helpers, constants)
# from dnd_5e_core.data import (api_client, serialization)
# from dnd_5e_core.equipment import inventory

