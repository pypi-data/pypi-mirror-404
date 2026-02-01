"""
D&D 5e Core - Multiclassing System
Rules and calculations for multiclass characters
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .class_type import ClassType
    from ..abilities.abilities import Abilities


@dataclass
class MulticlassRequirements:
    """Ability score requirements for multiclassing"""
    class_name: str
    required_abilities: Dict[str, int]  # e.g., {"str": 13, "dex": 13}


# Multiclass ability score requirements (PHB p.163)
MULTICLASS_PREREQUISITES = {
    "barbarian": {"str": 13},
    "bard": {"cha": 13},
    "cleric": {"wis": 13},
    "druid": {"wis": 13},
    "fighter": {"str": 13, "dex": 13},  # Either STR or DEX
    "monk": {"dex": 13, "wis": 13},
    "paladin": {"str": 13, "cha": 13},
    "ranger": {"dex": 13, "wis": 13},
    "rogue": {"dex": 13},
    "sorcerer": {"cha": 13},
    "warlock": {"cha": 13},
    "wizard": {"int": 13},
}


def can_multiclass_into(
    class_name: str,
    abilities: 'Abilities'
) -> Tuple[bool, str]:
    """
    Check if a character can multiclass into a class.

    Args:
        class_name: Class to multiclass into
        abilities: Character's abilities

    Returns:
        Tuple of (can_multiclass, reason)
    """
    class_lower = class_name.lower()

    if class_lower not in MULTICLASS_PREREQUISITES:
        return (False, f"Unknown class: {class_name}")

    requirements = MULTICLASS_PREREQUISITES[class_lower]

    # Special case for Fighter: needs STR 13 OR DEX 13
    if class_lower == "fighter":
        if abilities.str >= 13 or abilities.dex >= 13:
            return (True, "")
        return (False, "Requires Strength 13 or Dexterity 13")

    # Check all requirements
    for ability, required_score in requirements.items():
        actual_score = getattr(abilities, ability)
        if actual_score < required_score:
            return (False, f"Requires {ability.upper()} {required_score}")

    return (True, "")


def can_multiclass_from(
    class_name: str,
    abilities: 'Abilities'
) -> Tuple[bool, str]:
    """
    Check if a character can multiclass out of their current class.
    Same requirements as multiclassing into it.

    Args:
        class_name: Current class
        abilities: Character's abilities

    Returns:
        Tuple of (can_multiclass, reason)
    """
    return can_multiclass_into(class_name, abilities)


def calculate_spell_slots_multiclass(
    class_levels: Dict[str, int]
) -> List[int]:
    """
    Calculate spell slots for multiclass spellcasters.

    Uses the multiclass spellcaster rules from PHB p.164.
    Different classes contribute differently to spell slot progression.

    Args:
        class_levels: Dictionary of class names to levels
            e.g., {"wizard": 3, "cleric": 2}

    Returns:
        List of spell slots for each level [0-9]
    """
    # Full casters: Bard, Cleric, Druid, Sorcerer, Wizard
    full_casters = ["bard", "cleric", "druid", "sorcerer", "wizard"]

    # Half casters: Paladin, Ranger
    half_casters = ["paladin", "ranger"]

    # Third casters: Eldritch Knight (Fighter), Arcane Trickster (Rogue)
    # Note: These are subclasses, not full classes
    third_casters = ["eldritch-knight", "arcane-trickster"]

    # Calculate effective spellcaster level
    effective_level = 0

    for class_name, level in class_levels.items():
        class_lower = class_name.lower()

        if class_lower in full_casters:
            effective_level += level
        elif class_lower in half_casters:
            effective_level += level // 2
        elif class_lower in third_casters:
            effective_level += level // 3
        elif class_lower == "warlock":
            # Warlock uses Pact Magic, doesn't combine with other classes
            # Handle separately if needed
            pass

    # Get spell slots for effective caster level
    from ..spells.spell_slots import get_spell_slots_by_level
    return get_spell_slots_by_level(effective_level, "full")


def get_multiclass_proficiencies(class_name: str) -> Dict[str, List[str]]:
    """
    Get proficiencies gained when multiclassing into a class.

    Multiclass proficiencies are more limited than starting proficiencies.

    Args:
        class_name: Class being multiclassed into

    Returns:
        Dictionary with armor, weapon, tool, and skill proficiencies
    """
    multiclass_profs = {
        "barbarian": {
            "armor": ["light", "medium", "shields"],
            "weapons": ["simple", "martial"],
            "tools": [],
            "skills": 1  # Choose 1 from class list
        },
        "bard": {
            "armor": ["light"],
            "weapons": ["simple", "hand-crossbows", "longswords", "rapiers", "shortswords"],
            "tools": ["one-musical-instrument"],
            "skills": 1
        },
        "cleric": {
            "armor": ["light", "medium", "shields"],
            "weapons": ["simple"],
            "tools": [],
            "skills": 0
        },
        "druid": {
            "armor": ["light", "medium", "shields"],
            "weapons": ["clubs", "daggers", "darts", "javelins", "maces", "quarterstaffs",
                       "scimitars", "sickles", "slings", "spears"],
            "tools": ["herbalism-kit"],
            "skills": 0
        },
        "fighter": {
            "armor": ["light", "medium", "heavy", "shields"],
            "weapons": ["simple", "martial"],
            "tools": [],
            "skills": 0
        },
        "monk": {
            "armor": [],
            "weapons": ["simple", "shortswords"],
            "tools": [],
            "skills": 0
        },
        "paladin": {
            "armor": ["light", "medium", "heavy", "shields"],
            "weapons": ["simple", "martial"],
            "tools": [],
            "skills": 0
        },
        "ranger": {
            "armor": ["light", "medium", "shields"],
            "weapons": ["simple", "martial"],
            "tools": [],
            "skills": 1
        },
        "rogue": {
            "armor": ["light"],
            "weapons": ["simple", "hand-crossbows", "longswords", "rapiers", "shortswords"],
            "tools": ["thieves-tools"],
            "skills": 1
        },
        "sorcerer": {
            "armor": [],
            "weapons": [],
            "tools": [],
            "skills": 0
        },
        "warlock": {
            "armor": ["light"],
            "weapons": ["simple"],
            "tools": [],
            "skills": 0
        },
        "wizard": {
            "armor": [],
            "weapons": [],
            "tools": [],
            "skills": 0
        },
    }

    return multiclass_profs.get(class_name.lower(), {
        "armor": [],
        "weapons": [],
        "tools": [],
        "skills": 0
    })


def calculate_hit_points_multiclass(
    class_levels: Dict[str, int],
    class_hit_dice: Dict[str, int],
    constitution_modifier: int,
    take_average: bool = True
) -> int:
    """
    Calculate hit points for a multiclass character.

    Args:
        class_levels: Dictionary of class names to levels
        class_hit_dice: Dictionary of class names to hit die size
        constitution_modifier: Constitution modifier
        take_average: If True, use average; if False, roll

    Returns:
        Total hit points
    """
    from random import randint

    total_hp = 0
    first_class = True

    for class_name, level in class_levels.items():
        hit_die = class_hit_dice.get(class_name, 8)

        for _ in range(level):
            if first_class:
                # First level: max hit die
                total_hp += hit_die
                first_class = False
            else:
                # Subsequent levels
                if take_average:
                    total_hp += (hit_die // 2) + 1
                else:
                    total_hp += randint(1, hit_die)

            # Add constitution modifier each level (minimum 1)
            total_hp += max(1, constitution_modifier)

    return total_hp

