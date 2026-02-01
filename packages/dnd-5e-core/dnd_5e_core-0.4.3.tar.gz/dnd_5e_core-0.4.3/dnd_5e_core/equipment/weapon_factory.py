"""
D&D 5e Core - Weapon Factory
Factory functions for creating special and magical weapons
"""
from typing import Optional

from .weapon import WeaponData, CategoryType, RangeType, DamageType, WeaponProperty, WeaponRange, WeaponThrowRange
from .equipment import Cost, EquipmentCategory
from ..mechanics.dice import DamageDice


def create_damage_type(index: str, name: str) -> DamageType:
    """Create a damage type"""
    return DamageType(index=index, name=name, desc=f"{name} damage")


def create_weapon_property(index: str, name: str, desc: str = "") -> WeaponProperty:
    """Create a weapon property"""
    return WeaponProperty(index=index, name=name, desc=desc or f"{name} property")


def create_weapon_category(category_type: str = "simple-weapons") -> EquipmentCategory:
    """Create weapon equipment category"""
    return EquipmentCategory(
        index=category_type,
        name=category_type.replace("-", " ").title(),
        url=f"/api/equipment-categories/{category_type}"
    )


# ============================================================================
# MAGICAL WEAPONS - GENERIC ENHANCEMENTS
# ============================================================================

def create_weapon_plus_1(base_weapon: WeaponData) -> WeaponData:
    """+1 weapon (Uncommon)"""
    enhanced = base_weapon.__class__(**base_weapon.__dict__)
    enhanced.name = f"{base_weapon.name} +1"
    enhanced.index = f"{base_weapon.index}-plus-1"
    enhanced.is_magic = True
    enhanced.cost = Cost(quantity=base_weapon.cost.quantity * 10, unit="gp")
    return enhanced


def create_weapon_plus_2(base_weapon: WeaponData) -> WeaponData:
    """+2 weapon (Rare)"""
    enhanced = base_weapon.__class__(**base_weapon.__dict__)
    enhanced.name = f"{base_weapon.name} +2"
    enhanced.index = f"{base_weapon.index}-plus-2"
    enhanced.is_magic = True
    enhanced.cost = Cost(quantity=base_weapon.cost.quantity * 50, unit="gp")
    return enhanced


def create_weapon_plus_3(base_weapon: WeaponData) -> WeaponData:
    """+3 weapon (Very Rare)"""
    enhanced = base_weapon.__class__(**base_weapon.__dict__)
    enhanced.name = f"{base_weapon.name} +3"
    enhanced.index = f"{base_weapon.index}-plus-3"
    enhanced.is_magic = True
    enhanced.cost = Cost(quantity=base_weapon.cost.quantity * 100, unit="gp")
    return enhanced


# ============================================================================
# LEGENDARY NAMED WEAPONS
# ============================================================================

def create_flame_tongue() -> WeaponData:
    """Flame Tongue (Rare)
    +2d6 fire damage when activated.
    """
    return WeaponData(
        index="flame-tongue",
        name="Flame Tongue",
        cost=Cost(quantity=5000, unit="gp"),
        weight=3,
        desc=["Rare longsword. Can ignite to deal +2d6 fire damage."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        bonus_damage={"fire": "2d6"},  # +2d6 fire damage
        equipped=False
    )


def create_frost_brand() -> WeaponData:
    """Frost Brand (Very Rare)
    +1d6 cold damage, resistance to fire damage, extinguishes flames.
    """
    return WeaponData(
        index="frost-brand",
        name="Frost Brand",
        cost=Cost(quantity=20000, unit="gp"),
        weight=3,
        desc=["Very Rare longsword. +1d6 cold damage, fire resistance."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        bonus_damage={"cold": "1d6"},  # +1d6 cold damage
        resistances_granted=["fire"],  # Grants fire resistance
        equipped=False
    )


def create_holy_avenger() -> WeaponData:
    """Holy Avenger (Legendary)
    +3 longsword, +2d10 radiant damage to fiends and undead.
    """
    return WeaponData(
        index="holy-avenger",
        name="Holy Avenger",
        cost=Cost(quantity=165000, unit="gp"),
        weight=3,
        desc=["Legendary longsword. +3, +2d10 radiant vs fiends/undead."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=3,  # +3 to attack rolls
        damage_bonus=3,  # +3 to damage rolls
        creature_type_damage={"fiend": "2d10", "undead": "2d10"},  # +2d10 radiant vs fiends/undead
        equipped=False
    )


def create_vorpal_sword() -> WeaponData:
    """Vorpal Sword (Legendary)
    +3 weapon, can decapitate on a 20.
    """
    return WeaponData(
        index="vorpal-sword",
        name="Vorpal Sword",
        cost=Cost(quantity=75000, unit="gp"),
        weight=3,
        desc=["Legendary longsword. +3, can decapitate on critical hit."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=3,  # +3 to attack rolls
        damage_bonus=3,  # +3 to damage rolls
        special_properties=["decapitate on natural 20"],
        equipped=False
    )


def create_sun_blade() -> WeaponData:
    """Sun Blade (Rare)
    +2 longsword (finesse, versatile), +1d8 radiant to undead, emits sunlight.
    """
    return WeaponData(
        index="sun-blade",
        name="Sun Blade",
        cost=Cost(quantity=12000, unit="gp"),
        weight=3,
        desc=["Rare longsword. +2, finesse, +1d8 radiant vs undead, emits sunlight."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("finesse", "Finesse"),
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("radiant", "Radiant"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=2,  # +2 to attack rolls
        damage_bonus=2,  # +2 to damage rolls
        creature_type_damage={"undead": "1d8"},  # +1d8 radiant vs undead
        special_properties=["emits sunlight"],
        equipped=False
    )


def create_sword_of_sharpness() -> WeaponData:
    """Sword of Sharpness (Very Rare)
    +3 to damage rolls, can maximize damage or sever limb on 20.
    """
    return WeaponData(
        index="sword-of-sharpness",
        name="Sword of Sharpness",
        cost=Cost(quantity=25000, unit="gp"),
        weight=3,
        desc=["Very Rare longsword. +3 to damage, can sever limbs."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        damage_bonus=3,  # +3 to damage rolls
        special_properties=["maximize damage or sever limb on natural 20"],
        equipped=False
    )


def create_nine_lives_stealer() -> WeaponData:
    """Nine Lives Stealer (Very Rare)
    +2 longsword, can instantly slay creatures (9 charges).
    """
    return WeaponData(
        index="nine-lives-stealer",
        name="Nine Lives Stealer",
        cost=Cost(quantity=20000, unit="gp"),
        weight=3,
        desc=["Very Rare longsword. +2, can instantly slay (9 charges)."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=2,  # +2 to attack rolls
        damage_bonus=2,  # +2 to damage rolls
        special_properties=["can instantly slay (9 charges)"],
        equipped=False
    )


def create_oathbow() -> WeaponData:
    """Oathbow (Very Rare)
    +3d6 damage to sworn enemy, advantage on attack rolls.
    """
    return WeaponData(
        index="oathbow",
        name="Oathbow",
        cost=Cost(quantity=25000, unit="gp"),
        weight=2,
        desc=["Very Rare longbow. +3d6 vs sworn enemy, advantage on attacks."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("ammunition", "Ammunition"),
            create_weapon_property("heavy", "Heavy"),
            create_weapon_property("two-handed", "Two-Handed"),
        ],
        damage_type=create_damage_type("piercing", "Piercing"),
        range_type=RangeType.RANGED,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        weapon_range=WeaponRange(normal=150, long=600),
        is_magic=True,
        special_properties=["3d6 vs sworn enemy", "advantage on attacks vs sworn enemy"],
        equipped=False
    )


def create_giant_slayer() -> WeaponData:
    """Giant Slayer (Rare)
    +1 weapon, +2d6 damage vs giants.
    """
    return WeaponData(
        index="giant-slayer",
        name="Giant Slayer",
        cost=Cost(quantity=7000, unit="gp"),
        weight=3,
        desc=["Rare longsword. +1, deals +2d6 damage to giants."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,
        damage_bonus=1,
        creature_type_damage={"giant": "2d6"},  # +2d6 vs giants
        equipped=False
    )


def create_dragon_slayer() -> WeaponData:
    """Dragon Slayer (Rare)
    +1 weapon, +3d6 damage vs dragons.
    """
    return WeaponData(
        index="dragon-slayer",
        name="Dragon Slayer",
        cost=Cost(quantity=8000, unit="gp"),
        weight=3,
        desc=["Rare longsword. +1, deals +3d6 damage to dragons."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,
        damage_bonus=1,
        creature_type_damage={"dragon": "3d6"},  # +3d6 vs dragons
        equipped=False
    )


def create_defender() -> WeaponData:
    """Defender (Legendary)
    +3 weapon, can transfer bonus to AC.
    """
    return WeaponData(
        index="defender",
        name="Defender",
        cost=Cost(quantity=48000, unit="gp"),
        weight=3,
        desc=["Legendary longsword. +3, can transfer bonus to AC."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=3,  # +3 to attack rolls (can transfer to AC)
        damage_bonus=3,  # +3 to damage rolls (can transfer to AC)
        special_properties=["can transfer up to +3 bonus to AC"],
        equipped=False
    )


def create_luck_blade() -> WeaponData:
    """Luck Blade (Legendary)
    +1 weapon, grants luck, can grant wishes (1d4-1 wishes).
    """
    return WeaponData(
        index="luck-blade",
        name="Luck Blade",
        cost=Cost(quantity=125000, unit="gp"),
        weight=3,
        desc=["Legendary longsword. +1, grants luck, may have wishes."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,  # +1 to attack rolls
        damage_bonus=1,  # +1 to damage rolls
        special_properties=["grants luck (+1 to saves)", "may have 1d4-1 wishes"],
        equipped=False
    )


def create_hammer_of_thunderbolts() -> WeaponData:
    """Hammer of Thunderbolts (Legendary)
    +1 warhammer, Strength 20, +4d6 damage to giants when attuned.
    """
    return WeaponData(
        index="hammer-of-thunderbolts",
        name="Hammer of Thunderbolts",
        cost=Cost(quantity=60000, unit="gp"),
        weight=5,
        desc=["Legendary warhammer. Sets Strength to 20, +4d6 vs giants."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("bludgeoning", "Bludgeoning"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,  # +1 to attack rolls
        damage_bonus=1,  # +1 to damage rolls
        creature_type_damage={"giant": "4d6"},  # +4d6 vs giants when attuned
        special_properties=["sets Strength to 20 when attuned"],
        equipped=False
    )


def create_dwarven_thrower() -> WeaponData:
    """Dwarven Thrower (Very Rare)
    +3 warhammer, returns when thrown, +1d8 vs giants.
    """
    return WeaponData(
        index="dwarven-thrower",
        name="Dwarven Thrower",
        cost=Cost(quantity=18000, unit="gp"),
        weight=2,
        desc=["Very Rare warhammer. +3, returns when thrown, +1d8 vs giants."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("thrown", "Thrown"),
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("bludgeoning", "Bludgeoning"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d8"),
        damage_dice_two_handed=DamageDice("1d10"),
        throw_range=WeaponThrowRange(normal=20, long=60),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=3,  # +3 to attack rolls
        damage_bonus=3,  # +3 to damage rolls
        creature_type_damage={"giant": "1d8"},  # +1d8 vs giants
        special_properties=["returns when thrown"],
        equipped=False
    )


def create_javelin_of_lightning() -> WeaponData:
    """Javelin of Lightning (Uncommon)
    Transforms into a lightning bolt (4d6 damage, DC 13 DEX save).
    """
    return WeaponData(
        index="javelin-of-lightning",
        name="Javelin of Lightning",
        cost=Cost(quantity=1500, unit="gp"),
        weight=2,
        desc=["Uncommon javelin. Can transform into lightning bolt (4d6, DC 13 DEX)."],
        category=create_weapon_category("simple-weapons"),
        properties=[
            create_weapon_property("thrown", "Thrown"),
        ],
        damage_type=create_damage_type("piercing", "Piercing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.SIMPLE,
        damage_dice=DamageDice("1d6"),
        throw_range=WeaponThrowRange(normal=30, long=120),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        special_properties=["transforms into lightning bolt", "4d6 lightning damage in line", "DC 13 DEX save for half"],
        equipped=False
    )


def create_trident_of_fish_command() -> WeaponData:
    """Trident of Fish Command (Uncommon)
    +1 trident, can control fish and aquatic beasts.
    """
    return WeaponData(
        index="trident-of-fish-command",
        name="Trident of Fish Command",
        cost=Cost(quantity=800, unit="gp"),
        weight=4,
        desc=["Uncommon trident. +1, can dominate fish/aquatic beasts."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("thrown", "Thrown"),
            create_weapon_property("versatile", "Versatile"),
        ],
        damage_type=create_damage_type("piercing", "Piercing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d6"),
        damage_dice_two_handed=DamageDice("1d8"),
        throw_range=WeaponThrowRange(normal=20, long=60),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,  # +1 to attack rolls
        damage_bonus=1,  # +1 to damage rolls
        special_properties=["can dominate fish and aquatic beasts (DC 15 WIS)"],
        equipped=False
    )


def create_scimitar_of_speed() -> WeaponData:
    """Scimitar of Speed (Very Rare)
    +2 scimitar, can make one extra attack as bonus action.
    """
    return WeaponData(
        index="scimitar-of-speed",
        name="Scimitar of Speed",
        cost=Cost(quantity=12000, unit="gp"),
        weight=3,
        desc=["Very Rare scimitar. +2, can attack as bonus action."],
        category=create_weapon_category("martial-weapons"),
        properties=[
            create_weapon_property("finesse", "Finesse"),
            create_weapon_property("light", "Light"),
        ],
        damage_type=create_damage_type("slashing", "Slashing"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.MARTIAL,
        damage_dice=DamageDice("1d6"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=2,  # +2 to attack rolls
        damage_bonus=2,  # +2 to damage rolls
        special_properties=["can make one extra attack as bonus action"],
        equipped=False
    )


def create_mace_of_disruption() -> WeaponData:
    """Mace of Disruption (Rare)
    +2 mace, extra 2d6 radiant to fiends/undead, can destroy undead.
    """
    return WeaponData(
        index="mace-of-disruption",
        name="Mace of Disruption",
        cost=Cost(quantity=7000, unit="gp"),
        weight=4,
        desc=["Rare mace. +2, 2d6 radiant vs fiends/undead, can destroy undead."],
        category=create_weapon_category("simple-weapons"),
        properties=[],
        damage_type=create_damage_type("bludgeoning", "Bludgeoning"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.SIMPLE,
        damage_dice=DamageDice("1d6"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=2,  # +2 to attack rolls
        damage_bonus=2,  # +2 to damage rolls
        creature_type_damage={"fiend": "2d6", "undead": "2d6"},  # +2d6 radiant vs fiends/undead
        special_properties=["can destroy undead (DC 15 WIS save)"],
        equipped=False
    )


def create_mace_of_smiting() -> WeaponData:
    """Mace of Smiting (Rare)
    +1 mace, +2d6 damage to constructs, can destroy them.
    """
    return WeaponData(
        index="mace-of-smiting",
        name="Mace of Smiting",
        cost=Cost(quantity=7000, unit="gp"),
        weight=4,
        desc=["Rare mace. +1, +2d6 vs constructs, can destroy them."],
        category=create_weapon_category("simple-weapons"),
        properties=[],
        damage_type=create_damage_type("bludgeoning", "Bludgeoning"),
        range_type=RangeType.MELEE,
        category_type=CategoryType.SIMPLE,
        damage_dice=DamageDice("1d6"),
        weapon_range=WeaponRange(normal=5, long=None),
        is_magic=True,
        attack_bonus=1,  # +1 to attack rolls
        damage_bonus=1,  # +1 to damage rolls
        creature_type_damage={"construct": "2d6"},  # +2d6 vs constructs
        special_properties=["can destroy constructs on critical hit"],
        equipped=False
    )


# ============================================================================
# REGISTRY
# ============================================================================

SPECIAL_WEAPONS = {
    "flame-tongue": create_flame_tongue,
    "frost-brand": create_frost_brand,
    "holy-avenger": create_holy_avenger,
    "vorpal-sword": create_vorpal_sword,
    "sun-blade": create_sun_blade,
    "sword-of-sharpness": create_sword_of_sharpness,
    "nine-lives-stealer": create_nine_lives_stealer,
    "oathbow": create_oathbow,
    "giant-slayer": create_giant_slayer,
    "dragon-slayer": create_dragon_slayer,
    "defender": create_defender,
    "luck-blade": create_luck_blade,
    "hammer-of-thunderbolts": create_hammer_of_thunderbolts,
    "dwarven-thrower": create_dwarven_thrower,
    "javelin-of-lightning": create_javelin_of_lightning,
    "trident-of-fish-command": create_trident_of_fish_command,
    "scimitar-of-speed": create_scimitar_of_speed,
    "mace-of-disruption": create_mace_of_disruption,
    "mace-of-smiting": create_mace_of_smiting,
}


def get_special_weapon(index: str) -> Optional[WeaponData]:
    """Get a special weapon by index"""
    factory = SPECIAL_WEAPONS.get(index)
    if factory:
        return factory()
    return None


__all__ = [
    'create_weapon_plus_1',
    'create_weapon_plus_2',
    'create_weapon_plus_3',
    'create_flame_tongue',
    'create_frost_brand',
    'create_holy_avenger',
    'create_vorpal_sword',
    'create_sun_blade',
    'create_sword_of_sharpness',
    'create_nine_lives_stealer',
    'create_oathbow',
    'create_giant_slayer',
    'create_dragon_slayer',
    'create_defender',
    'create_luck_blade',
    'create_hammer_of_thunderbolts',
    'create_dwarven_thrower',
    'create_javelin_of_lightning',
    'create_trident_of_fish_command',
    'create_scimitar_of_speed',
    'create_mace_of_disruption',
    'create_mace_of_smiting',
    'SPECIAL_WEAPONS',
    'get_special_weapon',
]
