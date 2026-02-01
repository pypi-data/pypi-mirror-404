"""
D&D 5e Core - Level Up System
Handles character advancement and level progression
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, List, Tuple

if TYPE_CHECKING:
    from ..entities.character import Character
    from ..spells.spell import Spell
    from ..classes.class_type import ClassType


@dataclass
class LevelUpResult:
    """
    Result of a level up operation.
    Contains information about what changed.
    """
    success: bool
    new_level: int
    hp_gained: int
    new_max_hp: int
    ability_score_improvement: bool = False
    new_spells: List['Spell'] = None
    messages: List[str] = None

    def __post_init__(self):
        if self.new_spells is None:
            self.new_spells = []
        if self.messages is None:
            self.messages = []


def calculate_hp_gain(class_type: 'ClassType', constitution_modifier: int, take_average: bool = True) -> int:
    """
    Calculate HP gained on level up.

    Args:
        class_type: Character's class
        constitution_modifier: Constitution ability modifier
        take_average: If True, take average; if False, roll hit die

    Returns:
        HP to add
    """
    from random import randint

    hit_die = class_type.hit_die

    if take_average:
        # Take average (rounded up)
        hp_gain = (hit_die // 2) + 1
    else:
        # Roll the hit die
        hp_gain = randint(1, hit_die)

    # Add constitution modifier (minimum 1 HP per level)
    hp_gain += constitution_modifier
    return max(1, hp_gain)


def can_level_up(character: 'Character') -> bool:
    """
    Check if character has enough XP to level up.

    Args:
        character: Character to check

    Returns:
        True if character can level up
    """
    from .experience import should_level_up
    return should_level_up(character.xp, character.level)


def get_ability_score_improvement_levels() -> List[int]:
    """
    Get the levels at which ability score improvements are granted.
    Standard for most classes: 4, 8, 12, 16, 19
    Fighters get additional at: 6, 14
    Rogues get additional at: 10

    Returns:
        List of levels
    """
    return [4, 8, 12, 16, 19]


def is_ability_score_improvement_level(level: int, class_name: Optional[str] = None) -> bool:
    """
    Check if a level grants an ability score improvement.

    Args:
        level: Character level
        class_name: Class name (for Fighter/Rogue special cases)

    Returns:
        True if this level grants an ASI
    """
    base_levels = get_ability_score_improvement_levels()

    if level in base_levels:
        return True

    # Fighter gets extra ASI at 6 and 14
    if class_name and class_name.lower() == "fighter":
        if level in [6, 14]:
            return True

    # Rogue gets extra ASI at 10
    if class_name and class_name.lower() == "rogue":
        if level == 10:
            return True

    return False


def get_spells_learned_at_level(
    new_level: int,
    class_type: 'ClassType'
) -> int:
    """
    Get number of new spells learned at this level.

    Args:
        new_level: New character level
        class_type: Character's class

    Returns:
        Number of new spells to learn
    """
    if not class_type.can_cast:
        return 0

    # Check spells_known table if it exists
    if hasattr(class_type, 'spells_known') and class_type.spells_known:
        if new_level <= len(class_type.spells_known):
            current_spells = class_type.spells_known[new_level - 1]
            if new_level > 1:
                previous_spells = class_type.spells_known[new_level - 2]
                return current_spells - previous_spells
            return current_spells

    # Default: learn 2 new spells per level for prepared casters
    # (Wizards get 2 per level, others prepare based on ability mod + level)
    return 2 if new_level > 1 else 0


def perform_level_up(
    character: 'Character',
    available_spells: Optional[List['Spell']] = None,
    take_average_hp: bool = True
) -> LevelUpResult:
    """
    Perform a level up for a character.

    Args:
        character: Character to level up
        available_spells: Spells available to learn (for spellcasters)
        take_average_hp: If True, take average HP; if False, roll

    Returns:
        LevelUpResult with details of the level up
    """
    from .experience import should_level_up

    # Check if can level up
    if not should_level_up(character.xp, character.level):
        return LevelUpResult(
            success=False,
            new_level=character.level,
            hp_gained=0,
            new_max_hp=character.max_hit_points,
            messages=["Not enough XP to level up"]
        )

    if character.level >= 20:
        return LevelUpResult(
            success=False,
            new_level=20,
            hp_gained=0,
            new_max_hp=character.max_hit_points,
            messages=["Already at maximum level (20)"]
        )

    messages = []
    new_level = character.level + 1

    # Calculate HP gain
    con_mod = character.ability_modifiers.con
    hp_gain = calculate_hp_gain(character.class_type, con_mod, take_average_hp)
    new_max_hp = character.max_hit_points + hp_gain

    messages.append(f"Level up! Now level {new_level}")
    messages.append(f"Gained {hp_gain} HP (Total: {new_max_hp})")

    # Check for ability score improvement
    asi = is_ability_score_improvement_level(new_level, character.class_type.index)
    if asi:
        messages.append("You can increase ability scores or choose a feat!")

    # Handle spell learning
    new_spells = []
    if character.class_type.can_cast and available_spells:
        spells_to_learn = get_spells_learned_at_level(new_level, character.class_type)
        if spells_to_learn > 0:
            messages.append(f"You can learn {spells_to_learn} new spell(s)")
            # Note: Actual spell selection should be done by the UI/game logic

    # Update character (caller should handle this)
    # character.level = new_level
    # character.max_hit_points = new_max_hp
    # character.hit_points = new_max_hp  # Full heal on level up

    return LevelUpResult(
        success=True,
        new_level=new_level,
        hp_gained=hp_gain,
        new_max_hp=new_max_hp,
        ability_score_improvement=asi,
        new_spells=new_spells,
        messages=messages
    )

