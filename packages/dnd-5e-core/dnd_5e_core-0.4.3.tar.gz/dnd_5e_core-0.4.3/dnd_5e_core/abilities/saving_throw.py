"""
D&D 5e Core - Saving Throws System
Saving throw mechanics for ability checks
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import randint
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .abilities import Abilities


class SavingThrowType(Enum):
    """Types of saving throws corresponding to ability scores"""
    STRENGTH = "str"
    DEXTERITY = "dex"
    CONSTITUTION = "con"
    INTELLIGENCE = "int"
    WISDOM = "wis"
    CHARISMA = "cha"

    @property
    def ability_name(self) -> str:
        """Get the full ability name"""
        return self.name.title()


@dataclass
class SavingThrow:
    """
    Represents a saving throw check.

    Saving throws are used to resist spells, traps, poison, and other hazards.
    Characters add their ability modifier and proficiency bonus (if proficient).
    """
    saving_throw_type: SavingThrowType
    dc: int  # Difficulty Class
    proficient: bool = False
    advantage: bool = False
    disadvantage: bool = False

    def roll(
        self,
        abilities: 'Abilities',
        proficiency_bonus: int
    ) -> tuple[int, bool]:
        """
        Make a saving throw roll.

        Args:
            abilities: Character's ability scores
            proficiency_bonus: Character's proficiency bonus

        Returns:
            Tuple of (total_roll, success)
        """
        # Get ability modifier
        ability_value = getattr(abilities, self.saving_throw_type.value)
        ability_modifier = (ability_value - 10) // 2

        # Add proficiency if proficient
        if self.proficient:
            ability_modifier += proficiency_bonus

        # Roll d20 with advantage/disadvantage
        if self.advantage and not self.disadvantage:
            roll = max(randint(1, 20), randint(1, 20))
        elif self.disadvantage and not self.advantage:
            roll = min(randint(1, 20), randint(1, 20))
        else:
            roll = randint(1, 20)

        # Natural 1 always fails, natural 20 always succeeds
        if roll == 1:
            return (roll + ability_modifier, False)
        elif roll == 20:
            return (roll + ability_modifier, True)

        # Calculate total and check against DC
        total = roll + ability_modifier
        success = total >= self.dc

        return (total, success)

    def __repr__(self):
        adv_str = " (Adv)" if self.advantage else " (Dis)" if self.disadvantage else ""
        prof_str = " [Proficient]" if self.proficient else ""
        return f"{self.saving_throw_type.ability_name} Save DC {self.dc}{adv_str}{prof_str}"


def make_saving_throw(
    dc: int,
    ability_type: str,
    abilities: 'Abilities',
    proficiency_bonus: int,
    proficiencies: Optional[list[str]] = None,
    advantage: bool = False,
    disadvantage: bool = False
) -> tuple[int, bool]:
    """
    Convenience function to make a saving throw.

    Args:
        dc: Difficulty class
        ability_type: Which ability to use (str, dex, con, int, wis, cha)
        abilities: Character's abilities
        proficiency_bonus: Character's proficiency bonus
        proficiencies: List of proficient saving throws
        advantage: Roll with advantage
        disadvantage: Roll with disadvantage

    Returns:
        Tuple of (total_roll, success)
    """
    # Convert ability_type string to enum
    saving_throw_type = SavingThrowType(ability_type.lower())

    # Check if proficient
    proficient = False
    if proficiencies:
        proficient = ability_type.lower() in [p.lower() for p in proficiencies]

    # Create and roll saving throw
    saving_throw = SavingThrow(
        saving_throw_type=saving_throw_type,
        dc=dc,
        proficient=proficient,
        advantage=advantage,
        disadvantage=disadvantage
    )

    return saving_throw.roll(abilities, proficiency_bonus)

