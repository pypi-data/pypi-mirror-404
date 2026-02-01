"""
D&D 5e Core - Equipment Module
Contains all equipment classes (weapons, armor, potions, magic items, etc.)
"""

from .equipment import Cost, EquipmentCategory, Equipment, Inventory
from .potion import PotionRarity, Potion, HealingPotion, SpeedPotion, StrengthPotion
from .weapon import (
    CategoryType, RangeType, DamageType,
    WeaponProperty, WeaponRange, WeaponThrowRange, Weapon
)
from .armor import Armor
from .magic_item import (
    MagicItem, MagicItemRarity, MagicItemType,
    MagicItemEffect, MagicItemAction, create_magic_item_from_data
)

# Import from merged magic_item_factory (includes predefined_magic_items)
from .magic_item_factory import (
    create_magic_item_with_conditions,
    create_wand_of_paralysis, create_staff_of_entanglement,
    create_ring_of_blinding, create_cloak_of_fear,
    create_poisoned_dagger,
    create_ring_of_protection, create_cloak_of_protection,
    create_wand_of_magic_missiles, create_staff_of_healing,
    create_belt_of_giant_strength, create_amulet_of_health,
    create_bracers_of_defense, create_necklace_of_fireballs,
    create_boots_of_speed, create_boots_of_levitation,
    create_cloak_of_elvenkind, create_gauntlets_of_ogre_power,
    create_headband_of_intellect, create_periapt_of_health,
    create_periapt_of_proof_against_poison,
    create_ring_of_free_action, create_ring_of_regeneration,
    create_ring_of_spell_storing, create_wand_of_fireballs,
    create_bag_of_holding, create_rope_of_climbing,
    create_potion_of_healing, create_potion_of_greater_healing,
    create_potion_of_superior_healing, create_potion_of_supreme_healing,
    create_antitoxin, create_potion_of_poison,
    create_potion_of_speed, create_potion_of_invisibility,
    create_potion_of_flying, create_potion_of_giant_strength,
    create_elixir_of_health, create_oil_of_slipperiness,
    get_magic_item, MAGIC_ITEMS_REGISTRY
)

# Import armor factory
from .armor_factory import (
    create_armor_of_invulnerability, create_demon_armor,
    create_dragon_scale_mail, create_dwarven_plate,
    create_elven_chain, create_glamoured_studded_leather,
    create_mithral_armor, create_adamantine_armor,
    create_armor_of_resistance, create_plate_armor_of_etherealness,
    create_animated_shield, create_arrow_catching_shield,
    create_shield_of_missile_attraction, create_spellguard_shield,
    get_special_armor, SPECIAL_ARMORS
)

# Import weapon factory
from .weapon_factory import (
    create_weapon_plus_1, create_weapon_plus_2, create_weapon_plus_3,
    create_flame_tongue, create_frost_brand, create_holy_avenger,
    create_vorpal_sword, create_sun_blade, create_sword_of_sharpness,
    create_nine_lives_stealer, create_oathbow, create_giant_slayer,
    create_dragon_slayer, create_defender, create_luck_blade,
    create_hammer_of_thunderbolts, create_dwarven_thrower,
    create_javelin_of_lightning, create_trident_of_fish_command,
    create_scimitar_of_speed, create_mace_of_disruption,
    create_mace_of_smiting, get_special_weapon, SPECIAL_WEAPONS
)

__all__ = [
    # Base equipment
    'Cost', 'EquipmentCategory', 'Equipment', 'Inventory',
    # Potions
    'PotionRarity', 'Potion', 'HealingPotion', 'SpeedPotion', 'StrengthPotion',
    # Weapon types
    'CategoryType', 'RangeType', 'DamageType',
    'WeaponProperty', 'WeaponRange', 'WeaponThrowRange', 'Weapon',
    # Armor
    'Armor',
    # Magic Items
    'MagicItem', 'MagicItemRarity', 'MagicItemType',
    'MagicItemEffect', 'MagicItemAction', 'create_magic_item_from_data',

    # Magic Item Factory (merged with predefined)
    'create_magic_item_with_conditions',
    'create_wand_of_paralysis', 'create_staff_of_entanglement',
    'create_ring_of_blinding', 'create_cloak_of_fear',
    'create_poisoned_dagger',
    'create_ring_of_protection', 'create_cloak_of_protection',
    'create_wand_of_magic_missiles', 'create_staff_of_healing',
    'create_belt_of_giant_strength', 'create_amulet_of_health',
    'create_bracers_of_defense', 'create_necklace_of_fireballs',
    'create_boots_of_speed', 'create_boots_of_levitation',
    'create_cloak_of_elvenkind', 'create_gauntlets_of_ogre_power',
    'create_headband_of_intellect', 'create_periapt_of_health',
    'create_periapt_of_proof_against_poison',
    'create_ring_of_free_action', 'create_ring_of_regeneration',
    'create_ring_of_spell_storing', 'create_wand_of_fireballs',
    'create_bag_of_holding', 'create_rope_of_climbing',
    'create_potion_of_healing', 'create_potion_of_greater_healing',
    'create_potion_of_superior_healing', 'create_potion_of_supreme_healing',
    'create_antitoxin', 'create_potion_of_poison',
    'create_potion_of_speed', 'create_potion_of_invisibility',
    'create_potion_of_flying', 'create_potion_of_giant_strength',
    'create_elixir_of_health', 'create_oil_of_slipperiness',
    'get_magic_item', 'MAGIC_ITEMS_REGISTRY',

    # Armor Factory
    'create_armor_of_invulnerability', 'create_demon_armor',
    'create_dragon_scale_mail', 'create_dwarven_plate',
    'create_elven_chain', 'create_glamoured_studded_leather',
    'create_mithral_armor', 'create_adamantine_armor',
    'create_armor_of_resistance', 'create_plate_armor_of_etherealness',
    'create_animated_shield', 'create_arrow_catching_shield',
    'create_shield_of_missile_attraction', 'create_spellguard_shield',
    'get_special_armor', 'SPECIAL_ARMORS',

    # Weapon Factory
    'create_weapon_plus_1', 'create_weapon_plus_2', 'create_weapon_plus_3',
    'create_flame_tongue', 'create_frost_brand', 'create_holy_avenger',
    'create_vorpal_sword', 'create_sun_blade', 'create_sword_of_sharpness',
    'create_nine_lives_stealer', 'create_oathbow', 'create_giant_slayer',
    'create_dragon_slayer', 'create_defender', 'create_luck_blade',
    'create_hammer_of_thunderbolts', 'create_dwarven_thrower',
    'create_javelin_of_lightning', 'create_trident_of_fish_command',
    'create_scimitar_of_speed', 'create_mace_of_disruption',
    'create_mace_of_smiting', 'get_special_weapon', 'SPECIAL_WEAPONS',
]

