"""
D&D 5e Core - Challenge Rating System
Determines monster difficulty and encounter balance
"""
from __future__ import annotations

from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ChallengeRating:
    """
    Represents a monster's Challenge Rating.

    CR determines the difficulty of a monster and the XP it grants.
    """
    value: float

    @property
    def xp(self) -> int:
        """Get XP value for this CR"""
        from .experience import get_cr_xp
        return get_cr_xp(self.value)

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on CR"""
        if self.value < 0.5:
            return 2
        elif self.value < 5:
            return 2
        elif self.value < 9:
            return 3
        elif self.value < 13:
            return 4
        elif self.value < 17:
            return 5
        elif self.value < 21:
            return 6
        elif self.value < 25:
            return 7
        elif self.value < 29:
            return 8
        else:
            return 9

    def __repr__(self):
        if self.value < 1:
            return f"CR {self.value} ({self.xp} XP)"
        return f"CR {int(self.value)} ({self.xp} XP)"

    def __eq__(self, other):
        if isinstance(other, (int, float)):
            return self.value == other
        return self.value == other.value

    def __lt__(self, other):
        if isinstance(other, (int, float)):
            return self.value < other
        return self.value < other.value

    def __le__(self, other):
        if isinstance(other, (int, float)):
            return self.value <= other
        return self.value <= other.value

    def __gt__(self, other):
        if isinstance(other, (int, float)):
            return self.value > other
        return self.value > other.value

    def __ge__(self, other):
        if isinstance(other, (int, float)):
            return self.value >= other
        return self.value >= other.value


class EncounterDifficulty:
    """Difficulty levels for encounters"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    DEADLY = "deadly"


def get_xp_thresholds_for_level(character_level: int) -> dict[str, int]:
    """
    Get XP thresholds for encounter difficulty at a given level.

    Args:
        character_level: Character level (1-20)

    Returns:
        Dictionary with easy, medium, hard, and deadly XP thresholds
    """
    # XP thresholds per character level from DMG p.82
    THRESHOLDS = {
        1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
        2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
        3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
        4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
        5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
        6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
        7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
        8: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
        9: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
        10: {"easy": 600, "medium": 1200, "hard": 1900, "deadly": 2800},
        11: {"easy": 800, "medium": 1600, "hard": 2400, "deadly": 3600},
        12: {"easy": 1000, "medium": 2000, "hard": 3000, "deadly": 4500},
        13: {"easy": 1100, "medium": 2200, "hard": 3400, "deadly": 5100},
        14: {"easy": 1250, "medium": 2500, "hard": 3800, "deadly": 5700},
        15: {"easy": 1400, "medium": 2800, "hard": 4300, "deadly": 6400},
        16: {"easy": 1600, "medium": 3200, "hard": 4800, "deadly": 7200},
        17: {"easy": 2000, "medium": 3900, "hard": 5900, "deadly": 8800},
        18: {"easy": 2100, "medium": 4200, "hard": 6300, "deadly": 9500},
        19: {"easy": 2400, "medium": 4900, "hard": 7300, "deadly": 10900},
        20: {"easy": 2800, "medium": 5700, "hard": 8500, "deadly": 12700},
    }

    return THRESHOLDS.get(character_level, THRESHOLDS[1])


def calculate_encounter_difficulty(
    party_levels: List[int],
    monster_crs: List[float]
) -> Tuple[int, str]:
    """
    Calculate encounter difficulty for a party.

    Args:
        party_levels: List of character levels
        monster_crs: List of monster challenge ratings

    Returns:
        Tuple of (adjusted_xp, difficulty_string)
    """
    from .experience import get_cr_xp

    # Calculate total XP
    total_xp = sum(get_cr_xp(cr) for cr in monster_crs)

    # Apply multiplier based on number of monsters (DMG p.82)
    num_monsters = len(monster_crs)
    if num_monsters == 1:
        multiplier = 1.0
    elif num_monsters == 2:
        multiplier = 1.5
    elif num_monsters <= 6:
        multiplier = 2.0
    elif num_monsters <= 10:
        multiplier = 2.5
    elif num_monsters <= 14:
        multiplier = 3.0
    else:
        multiplier = 4.0

    # Adjust for party size (fewer than 3 or more than 5 characters)
    party_size = len(party_levels)
    if party_size < 3:
        multiplier *= 1.5
    elif party_size > 5:
        multiplier *= 0.5

    adjusted_xp = int(total_xp * multiplier)

    # Determine difficulty
    total_thresholds = {
        "easy": 0,
        "medium": 0,
        "hard": 0,
        "deadly": 0
    }

    for level in party_levels:
        thresholds = get_xp_thresholds_for_level(level)
        for key in total_thresholds:
            total_thresholds[key] += thresholds[key]

    # Determine difficulty tier
    if adjusted_xp < total_thresholds["easy"]:
        difficulty = "trivial"
    elif adjusted_xp < total_thresholds["medium"]:
        difficulty = "easy"
    elif adjusted_xp < total_thresholds["hard"]:
        difficulty = "medium"
    elif adjusted_xp < total_thresholds["deadly"]:
        difficulty = "hard"
    else:
        difficulty = "deadly"

    return adjusted_xp, difficulty


def get_appropriate_cr_range(party_level: int) -> Tuple[float, float]:
    """
    Get an appropriate CR range for a party of a given average level.

    Args:
        party_level: Average party level

    Returns:
        Tuple of (min_cr, max_cr) for balanced encounters
    """
    # General guideline: CR should be within ±3 of party level
    min_cr = max(0, party_level - 3)
    max_cr = party_level + 3

    return (min_cr, max_cr)

