"""
D&D 5e Core - Inventory System
Represents inventory items with quantity
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .equipment import Equipment, EquipmentCategory


@dataclass
class Inventory:
    """
    Represents an inventory slot containing equipment and quantity.
    Used for starting equipment and equipment options.
    """
    quantity: str
    equipment: Union['Equipment', 'EquipmentCategory']

    def __repr__(self):
        return f"{self.quantity} {self.equipment.index}"

