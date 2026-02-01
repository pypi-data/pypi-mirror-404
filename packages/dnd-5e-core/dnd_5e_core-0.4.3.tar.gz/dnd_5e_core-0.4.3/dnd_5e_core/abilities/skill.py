"""
D&D 5e Core - Skills System
Character skills and their ability score associations
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .abilities import AbilityType


class SkillType(Enum):
    """All skills in D&D 5e and their associated ability scores"""
    ACROBATICS = ("acrobatics", "dex")
    ANIMAL_HANDLING = ("animal-handling", "wis")
    ARCANA = ("arcana", "int")
    ATHLETICS = ("athletics", "str")
    DECEPTION = ("deception", "cha")
    HISTORY = ("history", "int")
    INSIGHT = ("insight", "wis")
    INTIMIDATION = ("intimidation", "cha")
    INVESTIGATION = ("investigation", "int")
    MEDICINE = ("medicine", "wis")
    NATURE = ("nature", "int")
    PERCEPTION = ("perception", "wis")
    PERFORMANCE = ("performance", "cha")
    PERSUASION = ("persuasion", "cha")
    RELIGION = ("religion", "int")
    SLEIGHT_OF_HAND = ("sleight-of-hand", "dex")
    STEALTH = ("stealth", "dex")
    SURVIVAL = ("survival", "wis")

    def __init__(self, index: str, ability: str):
        self.index = index
        self.ability = ability

    @property
    def skill_name(self) -> str:
        """Human-readable skill name"""
        return self.name.replace("_", " ").title()


@dataclass
class Skill:
    """
    Represents a character's proficiency in a skill.

    Skills allow characters to perform specific tasks and use their
    ability modifiers + proficiency bonus if proficient.
    """
    skill_type: SkillType
    proficient: bool = False
    expertise: bool = False  # Double proficiency bonus

    @property
    def name(self) -> str:
        """Human-readable skill name"""
        return self.skill_type.skill_name

    @property
    def ability_score(self) -> str:
        """Associated ability score (str, dex, con, int, wis, cha)"""
        return self.skill_type.ability

    def get_modifier(self, ability_modifier: int, proficiency_bonus: int) -> int:
        """
        Calculate the skill modifier.

        Args:
            ability_modifier: The modifier from the associated ability score
            proficiency_bonus: Character's proficiency bonus

        Returns:
            Total skill modifier
        """
        modifier = ability_modifier
        if self.proficient:
            if self.expertise:
                modifier += proficiency_bonus * 2
            else:
                modifier += proficiency_bonus
        return modifier

    def __repr__(self):
        prof = "E" if self.expertise else "P" if self.proficient else "-"
        return f"{self.name} ({self.ability_score.upper()}) [{prof}]"


def get_all_skills() -> list[Skill]:
    """Get a list of all skills with no proficiencies"""
    return [Skill(skill_type=skill_type) for skill_type in SkillType]

