"""
D&D 5e Core - Condition System
Conditions that can affect creatures in combat
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..abilities import AbilityType
    from ..entities import Monster, Character


class ConditionType(Enum):
    """
    Standard D&D 5e conditions that can affect creatures

    Reference: https://www.dndbeyond.com/sources/basic-rules/appendix-a-conditions
    """
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"
    EXHAUSTION = "exhaustion"


@dataclass
class Condition:
    """
    A condition that affects a creature.

    Conditions can impose various effects on creatures, such as:
    - Disadvantage on ability checks or attack rolls
    - Advantage for attackers
    - Movement restrictions
    - Automatic saving throws

    Some conditions require saving throws to resist or escape.
    """
    index: str  # Unique identifier (e.g., "restrained", "poisoned")
    name: str = ""
    desc: str = ""
    dc_type: Optional['AbilityType'] = None  # Ability used for saving throw
    dc_value: Optional[int] = None  # DC for saving throw
    creature: Optional['Monster'] = None  # Creature that applied the condition (for grapple, etc.)
    duration: Optional[int] = None  # Duration in rounds (None = until saved)

    def __copy__(self):
        from copy import copy
        return Condition(
            index=self.index,
            name=self.name,
            desc=self.desc,
            dc_type=copy(self.dc_type) if self.dc_type else None,
            dc_value=self.dc_value,
            creature=self.creature,
            duration=self.duration
        )

    def __repr__(self):
        if self.dc_type and self.dc_value:
            return f"{self.name} (DC {self.dc_value} {self.dc_type.value})"
        return self.name

    def apply_to_character(self, character: 'Character') -> None:
        """
        Apply this condition to a character.

        Args:
            character: The character to apply the condition to
        """
        if character.conditions is None:
            character.conditions = []

        # Don't add duplicate conditions
        if not any(c.index == self.index for c in character.conditions):
            character.conditions.append(self)

    def apply_to_monster(self, monster: 'Monster') -> None:
        """
        Apply this condition to a monster.

        Args:
            monster: The monster to apply the condition to
        """
        if not hasattr(monster, 'conditions') or monster.conditions is None:
            monster.conditions = []

        # Don't add duplicate conditions
        if not any(c.index == self.index for c in monster.conditions):
            monster.conditions.append(self)

    def attempt_save(self, creature) -> bool:
        """
        Attempt a saving throw to resist or escape this condition.

        Args:
            creature: The creature attempting the save (Character or Monster)

        Returns:
            True if the save is successful, False otherwise
        """
        if not self.dc_type or not self.dc_value:
            return False

        from random import randint

        # Get ability modifier
        ability_mod = 0
        if hasattr(creature, 'abilities'):
            # Utiliser get_modifier() pour obtenir le modificateur
            ability_mod = creature.abilities.get_modifier(self.dc_type.value)

        # Roll saving throw (d20)
        roll = randint(1, 20) + ability_mod

        # Success if roll meets or exceeds DC
        success = roll >= self.dc_value

        # If successful, remove condition
        if success and hasattr(creature, 'conditions') and creature.conditions:
            creature.conditions = [c for c in creature.conditions if c.index != self.index]

        return success

    def remove_from_character(self, character: 'Character') -> None:
        """
        Remove this condition from a character.

        Args:
            character: The character to remove the condition from
        """
        if character.conditions:
            character.conditions = [c for c in character.conditions if c.index != self.index]

    def remove_from_monster(self, monster: 'Monster') -> None:
        """
        Remove this condition from a monster.

        Args:
            monster: The monster to remove the condition from
        """
        if hasattr(monster, 'conditions') and monster.conditions:
            monster.conditions = [c for c in monster.conditions if c.index != self.index]


# ============================================================================
# Helper functions to create common conditions
# ============================================================================

def create_restrained_condition(
    creature: Optional['Monster'] = None,
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Restrained condition.

    A restrained creature's speed becomes 0, and it can't benefit from any bonus to its speed.
    Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage.
    The creature has disadvantage on Dexterity saving throws.
    """
    from ..abilities import AbilityType

    return Condition(
        index="restrained",
        name="Restrained",
        desc="Speed is 0, attacks have disadvantage, attacks against have advantage, DEX saves have disadvantage",
        dc_type=dc_type or AbilityType.STR,
        dc_value=dc_value,
        creature=creature
    )


def create_poisoned_condition(
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Poisoned condition.

    A poisoned creature has disadvantage on attack rolls and ability checks.
    """
    from ..abilities import AbilityType

    return Condition(
        index="poisoned",
        name="Poisoned",
        desc="Disadvantage on attack rolls and ability checks",
        dc_type=dc_type or AbilityType.CON,
        dc_value=dc_value
    )


def create_frightened_condition(
    creature: Optional['Monster'] = None,
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Frightened condition.

    A frightened creature has disadvantage on ability checks and attack rolls while
    the source of its fear is within line of sight. The creature can't willingly
    move closer to the source of its fear.
    """
    from ..abilities import AbilityType

    return Condition(
        index="frightened",
        name="Frightened",
        desc="Disadvantage on ability checks and attacks while source is visible, can't move closer",
        dc_type=dc_type or AbilityType.WIS,
        dc_value=dc_value,
        creature=creature
    )


def create_grappled_condition(
    creature: Optional['Monster'] = None,
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Grappled condition.

    A grappled creature's speed becomes 0, and it can't benefit from any bonus to its speed.
    The condition ends if the grappler is incapacitated or if an effect removes the grappled
    creature from the reach of the grappler.
    """
    from ..abilities import AbilityType

    return Condition(
        index="grappled",
        name="Grappled",
        desc="Speed is 0",
        dc_type=dc_type or AbilityType.STR,
        dc_value=dc_value,
        creature=creature
    )


def create_paralyzed_condition(
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Paralyzed condition.

    A paralyzed creature is incapacitated and can't move or speak.
    The creature automatically fails Strength and Dexterity saving throws.
    Attack rolls against the creature have advantage.
    Any attack that hits the creature is a critical hit if the attacker is within 5 feet.
    """
    from ..abilities import AbilityType

    return Condition(
        index="paralyzed",
        name="Paralyzed",
        desc="Incapacitated, can't move or speak, auto-fail STR/DEX saves, attacks have advantage, melee hits are crits",
        dc_type=dc_type or AbilityType.CON,
        dc_value=dc_value
    )


def create_stunned_condition(
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Stunned condition.

    A stunned creature is incapacitated, can't move, and can speak only falteringly.
    The creature automatically fails Strength and Dexterity saving throws.
    Attack rolls against the creature have advantage.
    """
    from ..abilities import AbilityType

    return Condition(
        index="stunned",
        name="Stunned",
        desc="Incapacitated, can't move, auto-fail STR/DEX saves, attacks against have advantage",
        dc_type=dc_type or AbilityType.CON,
        dc_value=dc_value
    )


def create_prone_condition() -> Condition:
    """
    Create a Prone condition.

    A prone creature's only movement option is to crawl, unless it stands up.
    The creature has disadvantage on attack rolls.
    An attack roll against the creature has advantage if the attacker is within 5 feet,
    otherwise disadvantage.
    """
    return Condition(
        index="prone",
        name="Prone",
        desc="Must crawl or stand up, disadvantage on attacks, melee attacks against have advantage, ranged have disadvantage",
        dc_type=None,
        dc_value=None
    )


def create_blinded_condition(
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Blinded condition.

    A blinded creature can't see and automatically fails any ability check that requires sight.
    Attack rolls against the creature have advantage, and the creature's attack rolls have disadvantage.
    """
    from ..abilities import AbilityType

    return Condition(
        index="blinded",
        name="Blinded",
        desc="Can't see, auto-fail sight checks, attacks have disadvantage, attacks against have advantage",
        dc_type=dc_type or AbilityType.CON,
        dc_value=dc_value
    )


def create_charmed_condition(
    creature: Optional['Monster'] = None,
    dc_type: Optional['AbilityType'] = None,
    dc_value: Optional[int] = None
) -> Condition:
    """
    Create a Charmed condition.

    A charmed creature can't attack the charmer or target the charmer with harmful
    abilities or magical effects. The charmer has advantage on any ability check to
    interact socially with the creature.
    """
    from ..abilities import AbilityType

    return Condition(
        index="charmed",
        name="Charmed",
        desc="Can't attack or harm charmer, charmer has advantage on social checks",
        dc_type=dc_type or AbilityType.WIS,
        dc_value=dc_value,
        creature=creature
    )


def create_incapacitated_condition() -> Condition:
    """
    Create an Incapacitated condition.

    An incapacitated creature can't take actions or reactions.
    """
    return Condition(
        index="incapacitated",
        name="Incapacitated",
        desc="Can't take actions or reactions",
        dc_type=None,
        dc_value=None
    )


def create_unconscious_condition() -> Condition:
    """
    Create an Unconscious condition.

    An unconscious creature is incapacitated, can't move or speak, and is unaware
    of its surroundings. The creature drops whatever it's holding and falls prone.
    The creature automatically fails Strength and Dexterity saving throws.
    Attack rolls against the creature have advantage.
    Any attack that hits the creature is a critical hit if the attacker is within 5 feet.
    """
    return Condition(
        index="unconscious",
        name="Unconscious",
        desc="Incapacitated, can't move or speak, unaware, drops items, falls prone, auto-fail STR/DEX saves, attacks have advantage, melee hits are crits",
        dc_type=None,
        dc_value=None
    )
