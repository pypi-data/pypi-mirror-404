"""
D&D 5e Core - Predefined Magic Items

⚠️ DEPRECATED: This module has been merged into magic_item_factory.py
All functions are still available but will be removed in a future version.
Please import from magic_item_factory instead:

    from dnd_5e_core.equipment import create_ring_of_protection  # Still works
    from dnd_5e_core.equipment.magic_item_factory import create_ring_of_protection  # Recommended

Common magic items ready to use in combat and adventures
"""
import warnings

warnings.warn(
    "predefined_magic_items module is deprecated and has been merged into magic_item_factory. "
    "Import from magic_item_factory instead.",
    DeprecationWarning,
    stacklevel=2
)

from .magic_item import (
    MagicItem, MagicItemRarity, MagicItemType,
    MagicItemAction
)
from .equipment import Cost, EquipmentCategory


def create_ring_of_protection() -> MagicItem:
    """Ring of Protection: +1 AC and saving throws"""
    return MagicItem(
        index="ring-of-protection",
        name="Ring of Protection",
        cost=Cost(quantity=1000, unit="gp"),
        weight=0,
        desc=["You gain a +1 bonus to AC and saving throws while wearing this ring."],
        category=EquipmentCategory(index="ring", name="Ring", url="/api/equipment-categories/ring"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.RING,
        requires_attunement=True,
        ac_bonus=1,
        saving_throw_bonus=1
    )


def create_cloak_of_protection() -> MagicItem:
    """Cloak of Protection: +1 AC and saving throws"""
    return MagicItem(
        index="cloak-of-protection",
        name="Cloak of Protection",
        cost=Cost(quantity=800, unit="gp"),
        weight=1,
        desc=["You gain a +1 bonus to AC and saving throws while wearing this cloak."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ac_bonus=1,
        saving_throw_bonus=1
    )


def create_wand_of_magic_missiles() -> MagicItem:
    """Wand of Magic Missiles: Cast Magic Missile"""
    action = MagicItemAction(
        name="Magic Missile",
        description="Fire 3 darts that automatically hit for 1d4+1 force damage each",
        action_type="attack",
        damage_dice="1d4+1",
        damage_type="force",
        range=120,
        uses_per_day=7,
        recharge="dawn"
    )

    return MagicItem(
        index="wand-of-magic-missiles",
        name="Wand of Magic Missiles",
        cost=Cost(quantity=2000, unit="gp"),
        weight=1,
        desc=["This wand has 7 charges. You can use an action to expend 1 or more charges to cast magic missile."],
        category=EquipmentCategory(index="wand", name="Wand", url="/api/equipment-categories/wand"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WAND,
        requires_attunement=False,
        actions=[action]
    )


def create_staff_of_healing() -> MagicItem:
    """Staff of Healing: Cast healing spells"""
    cure_wounds = MagicItemAction(
        name="Cure Wounds",
        description="Heal 1d8+3 HP",
        action_type="healing",
        healing_dice="1d8+3",
        range=5,
        uses_per_day=10,
        recharge="dawn"
    )

    return MagicItem(
        index="staff-of-healing",
        name="Staff of Healing",
        cost=Cost(quantity=3000, unit="gp"),
        weight=4,
        desc=["This staff has 10 charges and can cast healing spells."],
        category=EquipmentCategory(index="staff", name="Staff", url="/api/equipment-categories/staff"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.STAFF,
        requires_attunement=True,
        actions=[cure_wounds]
    )


def create_belt_of_giant_strength() -> MagicItem:
    """Belt of Giant Strength: Sets Strength to 21"""
    return MagicItem(
        index="belt-of-giant-strength-hill",
        name="Belt of Hill Giant Strength",
        cost=Cost(quantity=5000, unit="gp"),
        weight=1,
        desc=["Your Strength score is 21 while you wear this belt."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ability_bonuses={"str": 6}  # Assuming base 15, +6 = 21
    )


def create_amulet_of_health() -> MagicItem:
    """Amulet of Health: Sets Constitution to 19"""
    return MagicItem(
        index="amulet-of-health",
        name="Amulet of Health",
        cost=Cost(quantity=4000, unit="gp"),
        weight=0,
        desc=["Your Constitution score is 19 while you wear this amulet."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ability_bonuses={"con": 5}  # Assuming base 14, +5 = 19
    )


def create_bracers_of_defense() -> MagicItem:
    """Bracers of Defense: +2 AC when not wearing armor"""
    return MagicItem(
        index="bracers-of-defense",
        name="Bracers of Defense",
        cost=Cost(quantity=1500, unit="gp"),
        weight=1,
        desc=["You gain a +2 bonus to AC while you wear these bracers and aren't wearing armor."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ac_bonus=2
    )


def create_necklace_of_fireballs() -> MagicItem:
    """Necklace of Fireballs: Detachable beads that explode"""
    fireball_bead = MagicItemAction(
        name="Fireball Bead",
        description="Throw a bead that explodes for 6d6 fire damage in 20-foot radius",
        action_type="attack",
        damage_dice="6d6",
        damage_type="fire",
        range=60,
        area_of_effect="sphere",
        save_dc=15,
        save_ability="dex",
        uses_per_day=6,
        recharge=None  # Single use beads
    )

    return MagicItem(
        index="necklace-of-fireballs",
        name="Necklace of Fireballs",
        cost=Cost(quantity=2000, unit="gp"),
        weight=1,
        desc=["This necklace has 6 beads. You can detach and throw a bead as an action."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=False,
        actions=[fireball_bead]
    )


# Registry of predefined magic items
PREDEFINED_MAGIC_ITEMS = {
    "ring-of-protection": create_ring_of_protection,
    "cloak-of-protection": create_cloak_of_protection,
    "wand-of-magic-missiles": create_wand_of_magic_missiles,
    "staff-of-healing": create_staff_of_healing,
    "belt-of-giant-strength": create_belt_of_giant_strength,
    "amulet-of-health": create_amulet_of_health,
    "bracers-of-defense": create_bracers_of_defense,
    "necklace-of-fireballs": create_necklace_of_fireballs,
}


def get_magic_item(index: str) -> MagicItem:
    """
    Get a predefined magic item by index.

    Args:
        index: Magic item index

    Returns:
        MagicItem instance

    Raises:
        KeyError: If magic item not found
    """
    if index not in PREDEFINED_MAGIC_ITEMS:
        raise KeyError(f"Magic item '{index}' not found in predefined items")

    return PREDEFINED_MAGIC_ITEMS[index]()


__all__ = [
    'create_ring_of_protection',
    'create_cloak_of_protection',
    'create_wand_of_magic_missiles',
    'create_staff_of_healing',
    'create_belt_of_giant_strength',
    'create_amulet_of_health',
    'create_bracers_of_defense',
    'create_necklace_of_fireballs',
    'PREDEFINED_MAGIC_ITEMS',
    'get_magic_item',
]

