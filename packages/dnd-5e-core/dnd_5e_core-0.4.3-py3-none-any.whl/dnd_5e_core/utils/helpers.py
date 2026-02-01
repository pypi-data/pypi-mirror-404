"""
D&D 5e Core - Helper Functions
Utility functions for common D&D calculations
"""
from __future__ import annotations

from random import randint, choice
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..mechanics.dice import DamageDice


def roll_dice(dice_notation: str) -> int:
    """
    Roll dice from standard notation (e.g., "2d6", "1d20+5").

    Args:
        dice_notation: Dice string like "2d6", "1d20+3", "3d8-2"

    Returns:
        Result of the roll
    """
    from ..mechanics.dice import DamageDice

    dice = DamageDice(dice=dice_notation)
    return dice.roll()


def roll_with_advantage() -> int:
    """Roll d20 with advantage (take higher of two rolls)"""
    return max(randint(1, 20), randint(1, 20))


def roll_with_disadvantage() -> int:
    """Roll d20 with disadvantage (take lower of two rolls)"""
    return min(randint(1, 20), randint(1, 20))


def calculate_modifier(ability_score: int) -> int:
    """
    Calculate ability modifier from ability score.

    Args:
        ability_score: Ability score value (typically 1-20, can go higher)

    Returns:
        Ability modifier
    """
    return (ability_score - 10) // 2


def calculate_ac(
    base_ac: int,
    dex_modifier: int,
    max_dex_bonus: Optional[int] = None,
    bonus: int = 0
) -> int:
    """
    Calculate Armor Class.

    Args:
        base_ac: Base AC from armor
        dex_modifier: Dexterity modifier
        max_dex_bonus: Maximum dexterity bonus allowed (for medium/heavy armor)
        bonus: Additional AC bonus (shield, magic items, etc.)

    Returns:
        Total AC
    """
    if max_dex_bonus is not None:
        dex_modifier = min(dex_modifier, max_dex_bonus)

    return base_ac + dex_modifier + bonus


def calculate_attack_bonus(
    ability_modifier: int,
    proficiency_bonus: int,
    is_proficient: bool = True,
    magic_bonus: int = 0
) -> int:
    """
    Calculate attack bonus.

    Args:
        ability_modifier: Relevant ability modifier (STR or DEX)
        proficiency_bonus: Character's proficiency bonus
        is_proficient: Whether proficient with the weapon
        magic_bonus: Bonus from magic weapons

    Returns:
        Total attack bonus
    """
    bonus = ability_modifier + magic_bonus
    if is_proficient:
        bonus += proficiency_bonus
    return bonus


def calculate_save_dc(
    base_dc: int,
    ability_modifier: int,
    proficiency_bonus: int
) -> int:
    """
    Calculate spell save DC or special ability DC.

    Formula: 8 + proficiency bonus + ability modifier

    Args:
        base_dc: Base DC (usually 8)
        ability_modifier: Spellcasting ability modifier
        proficiency_bonus: Proficiency bonus

    Returns:
        Save DC
    """
    return base_dc + proficiency_bonus + ability_modifier


def is_critical_hit(attack_roll: int, critical_range: int = 20) -> bool:
    """
    Check if an attack roll is a critical hit.

    Args:
        attack_roll: The d20 roll result
        critical_range: Minimum roll for a critical (usually 20, some features lower it)

    Returns:
        True if critical hit
    """
    return attack_roll >= critical_range


def is_critical_fail(attack_roll: int) -> bool:
    """Check if an attack roll is a critical failure (natural 1)"""
    return attack_roll == 1


def apply_resistance(damage: int) -> int:
    """Apply damage resistance (half damage, rounded down)"""
    return damage // 2


def apply_vulnerability(damage: int) -> int:
    """Apply damage vulnerability (double damage)"""
    return damage * 2


def calculate_spell_attack_bonus(
    spellcasting_modifier: int,
    proficiency_bonus: int,
    magic_bonus: int = 0
) -> int:
    """
    Calculate spell attack bonus.

    Args:
        spellcasting_modifier: Spellcasting ability modifier
        proficiency_bonus: Proficiency bonus
        magic_bonus: Bonus from magic items

    Returns:
        Spell attack bonus
    """
    return spellcasting_modifier + proficiency_bonus + magic_bonus


def get_random_ability_scores(method: str = "standard") -> List[int]:
    """
    Generate random ability scores.

    Args:
        method: Generation method
            - "standard": Roll 4d6, drop lowest
            - "classic": Roll 3d6 straight
            - "heroic": Roll 2d6+6

    Returns:
        List of 6 ability scores
    """
    scores = []

    for _ in range(6):
        if method == "standard":
            # Roll 4d6, drop lowest
            rolls = [randint(1, 6) for _ in range(4)]
            rolls.remove(min(rolls))
            score = sum(rolls)
        elif method == "classic":
            # Roll 3d6
            score = sum(randint(1, 6) for _ in range(3))
        elif method == "heroic":
            # Roll 2d6+6
            score = randint(1, 6) + randint(1, 6) + 6
        else:
            # Default to standard
            rolls = [randint(1, 6) for _ in range(4)]
            rolls.remove(min(rolls))
            score = sum(rolls)

        scores.append(score)

    return scores


def get_standard_array() -> List[int]:
    """Get the standard ability score array: [15, 14, 13, 12, 10, 8]"""
    return [15, 14, 13, 12, 10, 8]


def calculate_carrying_capacity(strength_score: int) -> int:
    """
    Calculate carrying capacity in pounds.

    Args:
        strength_score: Strength ability score

    Returns:
        Carrying capacity in pounds
    """
    return strength_score * 15


def calculate_jump_distance(strength_score: int, running_start: bool = False) -> Tuple[int, int]:
    """
    Calculate jump distances.

    Args:
        strength_score: Strength ability score
        running_start: Whether character has a running start

    Returns:
        Tuple of (long_jump_feet, high_jump_feet)
    """
    if running_start:
        long_jump = strength_score
        high_jump = 3 + calculate_modifier(strength_score)
    else:
        long_jump = strength_score // 2
        high_jump = (3 + calculate_modifier(strength_score)) // 2

    return (long_jump, max(0, high_jump))


def format_modifier(modifier: int) -> str:
    """
    Format ability modifier with sign.

    Args:
        modifier: Ability modifier

    Returns:
        Formatted string like "+3" or "-2"
    """
    if modifier >= 0:
        return f"+{modifier}"
    return str(modifier)


def format_dice(dice: 'DamageDice') -> str:
    """
    Format damage dice for display.

    Args:
        dice: DamageDice object

    Returns:
        Formatted string like "2d6+3"
    """
    if dice.bonus >= 0:
        return f"{dice.dice}+{dice.bonus}"
    return f"{dice.dice}{dice.bonus}"

