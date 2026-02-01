"""
D&D 5e Core - Spell Slots System
Manages spell slots for spellcasters
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SpellSlots:
    """
    Tracks available and used spell slots for each spell level.

    In D&D 5e, spell slots are consumed when casting spells and
    recover after a long rest.
    """
    # Maximum slots per level (0-9, where 0 is cantrips which don't use slots)
    max_slots: List[int] = field(default_factory=lambda: [0] * 10)

    # Currently available slots per level
    current_slots: List[int] = field(default_factory=lambda: [0] * 10)

    def __post_init__(self):
        """Initialize current slots to max slots if not provided"""
        if all(slot == 0 for slot in self.current_slots):
            self.current_slots = self.max_slots.copy()

    def has_slot(self, level: int) -> bool:
        """Check if a spell slot is available for the given level"""
        if level == 0:  # Cantrips don't use slots
            return True
        if level < 0 or level >= len(self.current_slots):
            return False
        return self.current_slots[level] > 0

    def use_slot(self, level: int) -> bool:
        """
        Use a spell slot of the given level.
        Returns True if successful, False if no slot available.
        """
        if level == 0:  # Cantrips don't use slots
            return True
        if not self.has_slot(level):
            return False
        self.current_slots[level] -= 1
        return True

    def restore_slot(self, level: int) -> bool:
        """
        Restore one spell slot of the given level.
        Returns True if successful, False if already at max.
        """
        if level <= 0 or level >= len(self.current_slots):
            return False
        if self.current_slots[level] >= self.max_slots[level]:
            return False
        self.current_slots[level] += 1
        return True

    def long_rest(self):
        """Restore all spell slots (simulates a long rest)"""
        self.current_slots = self.max_slots.copy()

    def __repr__(self):
        slots_str = ", ".join(
            f"L{i}: {curr}/{max_val}"
            for i, (curr, max_val) in enumerate(zip(self.current_slots, self.max_slots))
            if max_val > 0
        )
        return f"SpellSlots({slots_str})"


def get_spell_slots_by_level(caster_level: int, caster_class: str = "full") -> List[int]:
    """
    Get the spell slots available for a given caster level.

    Args:
        caster_level: The character's level
        caster_class: Type of caster ("full", "half", "third")

    Returns:
        List of spell slots for each spell level [0-9]
    """
    # Standard spell slot progression for full casters (Wizard, Cleric, etc.)
    FULL_CASTER_SLOTS = {
        1: [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
        2: [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [0, 4, 2, 0, 0, 0, 0, 0, 0, 0],
        4: [0, 4, 3, 0, 0, 0, 0, 0, 0, 0],
        5: [0, 4, 3, 2, 0, 0, 0, 0, 0, 0],
        6: [0, 4, 3, 3, 0, 0, 0, 0, 0, 0],
        7: [0, 4, 3, 3, 1, 0, 0, 0, 0, 0],
        8: [0, 4, 3, 3, 2, 0, 0, 0, 0, 0],
        9: [0, 4, 3, 3, 3, 1, 0, 0, 0, 0],
        10: [0, 4, 3, 3, 3, 2, 0, 0, 0, 0],
        11: [0, 4, 3, 3, 3, 2, 1, 0, 0, 0],
        12: [0, 4, 3, 3, 3, 2, 1, 0, 0, 0],
        13: [0, 4, 3, 3, 3, 2, 1, 1, 0, 0],
        14: [0, 4, 3, 3, 3, 2, 1, 1, 0, 0],
        15: [0, 4, 3, 3, 3, 2, 1, 1, 1, 0],
        16: [0, 4, 3, 3, 3, 2, 1, 1, 1, 0],
        17: [0, 4, 3, 3, 3, 2, 1, 1, 1, 1],
        18: [0, 4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [0, 4, 3, 3, 3, 3, 2, 1, 1, 1],
        20: [0, 4, 3, 3, 3, 3, 2, 2, 1, 1],
    }

    if caster_class == "full":
        return FULL_CASTER_SLOTS.get(caster_level, [0] * 10)
    elif caster_class == "half":
        # Half casters (Paladin, Ranger) progress at half the rate
        effective_level = caster_level // 2
        return FULL_CASTER_SLOTS.get(effective_level, [0] * 10)
    elif caster_class == "third":
        # Third casters (Eldritch Knight, Arcane Trickster) progress at 1/3 rate
        effective_level = caster_level // 3
        return FULL_CASTER_SLOTS.get(effective_level, [0] * 10)
    else:
        return [0] * 10

