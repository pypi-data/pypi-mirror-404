"""
D&D 5e Core - Experience System
Experience points and level progression
"""
from __future__ import annotations

from typing import Optional


# XP thresholds for each level (1-20)
XP_LEVELS = [
    0,      # Level 1
    300,    # Level 2
    900,    # Level 3
    2700,   # Level 4
    6500,   # Level 5
    14000,  # Level 6
    23000,  # Level 7
    34000,  # Level 8
    48000,  # Level 9
    64000,  # Level 10
    85000,  # Level 11
    100000, # Level 12
    120000, # Level 13
    140000, # Level 14
    165000, # Level 15
    195000, # Level 16
    225000, # Level 17
    265000, # Level 18
    305000, # Level 19
    355000, # Level 20
]


def get_level_from_xp(xp: int) -> int:
    """
    Determine character level based on experience points.

    Args:
        xp: Total experience points

    Returns:
        Character level (1-20)
    """
    for level in range(len(XP_LEVELS) - 1, 0, -1):
        if xp >= XP_LEVELS[level]:
            return level + 1
    return 1


def get_xp_for_level(level: int) -> int:
    """
    Get the XP required to reach a specific level.

    Args:
        level: Target level (1-20)

    Returns:
        XP required for that level
    """
    if level < 1:
        return 0
    if level > 20:
        return XP_LEVELS[-1]
    return XP_LEVELS[level - 1]


def get_xp_to_next_level(current_xp: int, current_level: int) -> int:
    """
    Calculate XP needed to reach the next level.

    Args:
        current_xp: Current experience points
        current_level: Current character level

    Returns:
        XP needed for next level
    """
    if current_level >= 20:
        return 0
    next_level_xp = get_xp_for_level(current_level + 1)
    return next_level_xp - current_xp


def should_level_up(current_xp: int, current_level: int) -> bool:
    """
    Check if character has enough XP to level up.

    Args:
        current_xp: Current experience points
        current_level: Current character level

    Returns:
        True if character can level up
    """
    if current_level >= 20:
        return False
    return current_xp >= get_xp_for_level(current_level + 1)


def calculate_proficiency_bonus(level: int) -> int:
    """
    Calculate proficiency bonus based on character level.

    Proficiency bonus increases every 4 levels:
    - Levels 1-4: +2
    - Levels 5-8: +3
    - Levels 9-12: +4
    - Levels 13-16: +5
    - Levels 17-20: +6

    Args:
        level: Character level

    Returns:
        Proficiency bonus
    """
    if level < 1:
        return 0
    return 2 + (level - 1) // 4


def get_cr_xp(challenge_rating: float) -> int:
    """
    Get XP reward for defeating a monster of a given CR.

    Args:
        challenge_rating: Monster's challenge rating

    Returns:
        XP value
    """
    CR_XP_VALUES = {
        0: 10,
        0.125: 25,
        0.25: 50,
        0.5: 100,
        1: 200,
        2: 450,
        3: 700,
        4: 1100,
        5: 1800,
        6: 2300,
        7: 2900,
        8: 3900,
        9: 5000,
        10: 5900,
        11: 7200,
        12: 8400,
        13: 10000,
        14: 11500,
        15: 13000,
        16: 15000,
        17: 18000,
        18: 20000,
        19: 22000,
        20: 25000,
        21: 33000,
        22: 41000,
        23: 50000,
        24: 62000,
        25: 75000,
        26: 90000,
        27: 105000,
        28: 120000,
        29: 135000,
        30: 155000,
    }
    return CR_XP_VALUES.get(challenge_rating, 0)

