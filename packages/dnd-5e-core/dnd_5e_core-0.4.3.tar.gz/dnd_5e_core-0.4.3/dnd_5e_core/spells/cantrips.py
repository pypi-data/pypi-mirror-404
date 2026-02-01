"""
D&D 5e Core - Cantrips System
Level 0 spells that can be cast at will
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .spell import Spell


def is_cantrip(spell: 'Spell') -> bool:
    """
    Check if a spell is a cantrip.

    Args:
        spell: Spell to check

    Returns:
        True if spell is a cantrip (level 0)
    """
    return spell.level == 0


def get_cantrip_damage_scaling(character_level: int, base_dice: str) -> str:
    """
    Calculate cantrip damage scaling based on character level.

    Most damage cantrips increase in power at levels 5, 11, and 17.

    Args:
        character_level: Character's total level
        base_dice: Base damage dice (e.g., "1d10")

    Returns:
        Scaled damage dice (e.g., "2d10" at level 5)
    """
    if "d" not in base_dice:
        return base_dice

    # Extract dice count and type
    parts = base_dice.split("d")
    if len(parts) != 2:
        return base_dice

    try:
        base_count = int(parts[0])
        dice_type = parts[1]
    except ValueError:
        return base_dice

    # Scale based on character level
    if character_level >= 17:
        multiplier = 4
    elif character_level >= 11:
        multiplier = 3
    elif character_level >= 5:
        multiplier = 2
    else:
        multiplier = 1

    scaled_count = base_count * multiplier
    return f"{scaled_count}d{dice_type}"


# Common cantrips and their properties
DAMAGE_CANTRIPS = {
    "acid-splash": {"damage_type": "acid", "base_damage": "1d6", "save": "dex"},
    "chill-touch": {"damage_type": "necrotic", "base_damage": "1d8", "attack": True},
    "eldritch-blast": {"damage_type": "force", "base_damage": "1d10", "attack": True},
    "fire-bolt": {"damage_type": "fire", "base_damage": "1d10", "attack": True},
    "poison-spray": {"damage_type": "poison", "base_damage": "1d12", "save": "con"},
    "ray-of-frost": {"damage_type": "cold", "base_damage": "1d8", "attack": True},
    "sacred-flame": {"damage_type": "radiant", "base_damage": "1d8", "save": "dex"},
    "shocking-grasp": {"damage_type": "lightning", "base_damage": "1d8", "attack": True},
    "thorn-whip": {"damage_type": "piercing", "base_damage": "1d6", "attack": True},
    "toll-the-dead": {"damage_type": "necrotic", "base_damage": "1d8", "save": "wis"},  # 1d12 if damaged
}

UTILITY_CANTRIPS = [
    "blade-ward",
    "dancing-lights",
    "druidcraft",
    "friends",
    "guidance",
    "light",
    "mage-hand",
    "mending",
    "message",
    "minor-illusion",
    "prestidigitation",
    "produce-flame",
    "resistance",
    "shillelagh",
    "spare-the-dying",
    "thaumaturgy",
    "true-strike",
    "vicious-mockery",
]


def get_cantrip_damage(
    cantrip_name: str,
    character_level: int,
    ability_modifier: int = 0
) -> tuple[str, str]:
    """
    Get scaled damage for a damage cantrip.

    Args:
        cantrip_name: Name/index of the cantrip
        character_level: Character's level for scaling
        ability_modifier: Spellcasting ability modifier (some add this to damage)

    Returns:
        Tuple of (damage_dice, damage_type)
    """
    if cantrip_name not in DAMAGE_CANTRIPS:
        return ("0", "")

    cantrip = DAMAGE_CANTRIPS[cantrip_name]
    base_damage = cantrip["base_damage"]
    scaled_damage = get_cantrip_damage_scaling(character_level, base_damage)

    return (scaled_damage, cantrip["damage_type"])


def filter_cantrips(spells: List['Spell']) -> List['Spell']:
    """
    Filter a list of spells to only cantrips.

    Args:
        spells: List of spells

    Returns:
        List containing only cantrips
    """
    return [spell for spell in spells if is_cantrip(spell)]


def get_cantrips_known_by_level(class_name: str, level: int) -> int:
    """
    Get number of cantrips known at a given level for a class.

    Args:
        class_name: Class name/index
        level: Character level

    Returns:
        Number of cantrips known
    """
    # Cantrips known progression for full casters
    CANTRIPS_KNOWN = {
        "bard": {1: 2, 4: 3, 10: 4},
        "cleric": {1: 3, 4: 4, 10: 5},
        "druid": {1: 2, 4: 3, 10: 4},
        "sorcerer": {1: 4, 4: 5, 10: 6},
        "warlock": {1: 2, 4: 3, 10: 4},
        "wizard": {1: 3, 4: 4, 10: 5},
    }

    class_lower = class_name.lower()
    if class_lower not in CANTRIPS_KNOWN:
        return 0

    progression = CANTRIPS_KNOWN[class_lower]

    # Find the highest level threshold the character has reached
    cantrips = 0
    for threshold in sorted(progression.keys()):
        if level >= threshold:
            cantrips = progression[threshold]

    return cantrips

