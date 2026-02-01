"""
D&D 5e Core - Armor System
Armor classes for D&D 5e
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, TYPE_CHECKING, List

from .equipment import Equipment, Cost, EquipmentCategory


@dataclass
class ArmorData(Equipment):
    armor_class: dict
    str_minimum: int
    stealth_disadvantage: bool

    # Magic armor bonuses
    armor_bonus: int = 0  # +1/+2/+3 to AC

    # Damage resistances (e.g., Armor of Resistance: fire)
    damage_resistances: List[str] = field(default_factory=list)  # ["fire", "cold", "lightning"]

    # Damage immunities (e.g., Armor of Invulnerability)
    damage_immunities: List[str] = field(default_factory=list)  # ["poison", "necrotic"]

    # Condition immunities (e.g., Periapt of Proof against Poison)
    condition_immunities: List[str] = field(default_factory=list)  # ["poisoned", "charmed"]

    # Saving throw bonus (e.g., Cloak of Protection: +1)
    saving_throw_bonus: int = 0

    # Special properties
    special_properties: List[str] = field(default_factory=list)  # ["immune to critical hits"]

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        """Compare armors by their unique index when possible to avoid AttributeError
        when older objects without all fields are compared. Return NotImplemented for unknown types."""
        if other is None:
            return False
        if isinstance(other, ArmorData):
            return getattr(self, 'index', None) == getattr(other, 'index', None)
        # Fallback: compare by index attribute if present on other
        if hasattr(other, 'index'):
            return getattr(self, 'index', None) == getattr(other, 'index', None)
        return NotImplemented


# Alias for compatibility
Armor = ArmorData

