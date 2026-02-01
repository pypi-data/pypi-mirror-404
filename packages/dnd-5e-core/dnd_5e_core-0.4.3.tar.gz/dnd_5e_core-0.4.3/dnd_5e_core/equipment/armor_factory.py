"""
D&D 5e Core - Armor Factory
Factory functions for creating special and magical armors
"""
from typing import Optional

from .armor import ArmorData
from .equipment import Cost, EquipmentCategory


def create_armor_category(category_type: str = "armor") -> EquipmentCategory:
    """Create armor equipment category"""
    return EquipmentCategory(
        index=category_type,
        name=category_type.replace("-", " ").title(),
        url=f"/api/equipment-categories/{category_type}"
    )


# ============================================================================
# MAGICAL ARMORS
# ============================================================================

def create_armor_of_invulnerability() -> ArmorData:
    """Armor of Invulnerability (Legendary)
    While wearing this armor, you have resistance to nonmagical damage.
    You can use an action to make yourself immune to nonmagical damage for 10 minutes.
    """
    return ArmorData(
        index="armor-of-invulnerability",
        name="Armor of Invulnerability",
        cost=Cost(quantity=50000, unit="gp"),
        weight=65,
        desc=["Legendary plate armor. Resistance to nonmagical damage. Can activate immunity for 10 minutes once per day."],
        category=create_armor_category("heavy-armor"),
        armor_class={"base": 18, "dex_bonus": False, "max_bonus": 0},
        str_minimum=15,
        stealth_disadvantage=True,
        equipped=False
    )


def create_demon_armor() -> ArmorData:
    """Demon Armor (Very Rare, cursed)
    While wearing this armor, you gain +1 AC. You are vulnerable to damage from holy sources.
    The armor is cursed and cannot be removed once worn.
    """
    return ArmorData(
        index="demon-armor",
        name="Demon Armor",
        cost=Cost(quantity=25000, unit="gp"),
        weight=65,
        desc=["Very Rare cursed plate armor. +1 AC but vulnerability to radiant damage. Cursed."],
        category=create_armor_category("heavy-armor"),
        armor_class={"base": 19, "dex_bonus": False, "max_bonus": 0},
        str_minimum=15,
        stealth_disadvantage=True,
        equipped=False
    )


def create_dragon_scale_mail(dragon_type: str = "red") -> ArmorData:
    """Dragon Scale Mail (Very Rare)
    +1 AC, advantage on saving throws against Frightful Presence and breath weapons,
    resistance to one damage type based on dragon.
    """
    dragon_resistances = {
        "black": "acid",
        "blue": "lightning",
        "brass": "fire",
        "bronze": "lightning",
        "copper": "acid",
        "gold": "fire",
        "green": "poison",
        "red": "fire",
        "silver": "cold",
        "white": "cold"
    }

    resistance = dragon_resistances.get(dragon_type.lower(), "fire")

    return ArmorData(
        index=f"{dragon_type}-dragon-scale-mail",
        name=f"{dragon_type.title()} Dragon Scale Mail",
        cost=Cost(quantity=20000, unit="gp"),
        weight=45,
        desc=[f"Very Rare scale mail. +1 AC, advantage on saves vs dragon fear and breath, resistance to {resistance} damage."],
        category=create_armor_category("medium-armor"),
        armor_class={"base": 15, "dex_bonus": True, "max_bonus": 2},
        str_minimum=0,
        stealth_disadvantage=True,
        equipped=False
    )


def create_dwarven_plate() -> ArmorData:
    """Dwarven Plate (Very Rare)
    +2 AC. While wearing this armor, you gain a +2 bonus to AC.
    """
    return ArmorData(
        index="dwarven-plate",
        name="Dwarven Plate",
        cost=Cost(quantity=15000, unit="gp"),
        weight=65,
        desc=["Very Rare plate armor. +2 AC bonus."],
        category=create_armor_category("heavy-armor"),
        armor_class={"base": 20, "dex_bonus": False, "max_bonus": 0},
        str_minimum=15,
        stealth_disadvantage=True,
        equipped=False
    )


def create_elven_chain() -> ArmorData:
    """Elven Chain (Rare)
    +1 AC, can be worn under normal clothes, no disadvantage on Stealth.
    """
    return ArmorData(
        index="elven-chain",
        name="Elven Chain",
        cost=Cost(quantity=5000, unit="gp"),
        weight=20,
        desc=["Rare chain shirt. +1 AC, can be worn under clothes, no stealth disadvantage."],
        category=create_armor_category("medium-armor"),
        armor_class={"base": 14, "dex_bonus": True, "max_bonus": 2},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_glamoured_studded_leather() -> ArmorData:
    """Glamoured Studded Leather (Rare)
    +1 AC, can change appearance as a bonus action.
    """
    return ArmorData(
        index="glamoured-studded-leather",
        name="Glamoured Studded Leather",
        cost=Cost(quantity=3000, unit="gp"),
        weight=13,
        desc=["Rare studded leather. +1 AC, can change appearance as bonus action."],
        category=create_armor_category("light-armor"),
        armor_class={"base": 13, "dex_bonus": True, "max_bonus": 99},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_mithral_armor(armor_type: str = "chain-shirt") -> ArmorData:
    """Mithral Armor (Uncommon)
    No disadvantage on Stealth, no Strength requirement.
    """
    armor_configs = {
        "chain-shirt": {"base": 13, "weight": 10, "category": "medium-armor"},
        "breastplate": {"base": 14, "weight": 10, "category": "medium-armor"},
        "half-plate": {"base": 15, "weight": 20, "category": "medium-armor"},
        "ring-mail": {"base": 14, "weight": 20, "category": "heavy-armor"},
        "chain-mail": {"base": 16, "weight": 27, "category": "heavy-armor"},
        "splint": {"base": 17, "weight": 30, "category": "heavy-armor"},
        "plate": {"base": 18, "weight": 32, "category": "heavy-armor"}
    }

    config = armor_configs.get(armor_type, armor_configs["chain-shirt"])

    return ArmorData(
        index=f"mithral-{armor_type}",
        name=f"Mithral {armor_type.replace('-', ' ').title()}",
        cost=Cost(quantity=800, unit="gp"),
        weight=config["weight"],
        desc=[f"Uncommon {armor_type}. Made of mithral, no stealth disadvantage, no Strength requirement."],
        category=create_armor_category(config["category"]),
        armor_class={"base": config["base"], "dex_bonus": True if "medium" in config["category"] or "light" in config["category"] else False, "max_bonus": 2 if "medium" in config["category"] else 0},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_adamantine_armor(armor_type: str = "chain-shirt") -> ArmorData:
    """Adamantine Armor (Uncommon)
    Any critical hit against you becomes a normal hit.
    """
    armor_configs = {
        "chain-shirt": {"base": 13, "weight": 20, "category": "medium-armor", "cost": 400},
        "breastplate": {"base": 14, "weight": 20, "category": "medium-armor", "cost": 400},
        "half-plate": {"base": 15, "weight": 40, "category": "medium-armor", "cost": 750},
        "ring-mail": {"base": 14, "weight": 40, "category": "heavy-armor", "cost": 100},
        "chain-mail": {"base": 16, "weight": 55, "category": "heavy-armor", "cost": 200},
        "splint": {"base": 17, "weight": 60, "category": "heavy-armor", "cost": 200},
        "plate": {"base": 18, "weight": 65, "category": "heavy-armor", "cost": 500}
    }

    config = armor_configs.get(armor_type, armor_configs["chain-shirt"])
    is_heavy = "heavy" in config["category"]

    return ArmorData(
        index=f"adamantine-{armor_type}",
        name=f"Adamantine {armor_type.replace('-', ' ').title()}",
        cost=Cost(quantity=config["cost"], unit="gp"),
        weight=config["weight"],
        desc=[f"Uncommon {armor_type}. Critical hits against you become normal hits."],
        category=create_armor_category(config["category"]),
        armor_class={"base": config["base"], "dex_bonus": not is_heavy, "max_bonus": 2 if not is_heavy else 0},
        str_minimum=13 if is_heavy else 0,
        stealth_disadvantage=is_heavy,
        equipped=False
    )


def create_armor_of_resistance(damage_type: str = "fire") -> ArmorData:
    """Armor of Resistance (Rare)
    Resistance to one type of damage while wearing this armor.
    """
    return ArmorData(
        index=f"armor-of-{damage_type}-resistance",
        name=f"Armor of {damage_type.title()} Resistance",
        cost=Cost(quantity=6000, unit="gp"),
        weight=65,
        desc=[f"Rare plate armor. Resistance to {damage_type} damage."],
        category=create_armor_category("heavy-armor"),
        armor_class={"base": 18, "dex_bonus": False, "max_bonus": 0},
        str_minimum=15,
        stealth_disadvantage=True,
        damage_resistances=[damage_type],  # ✅ Add resistance
        equipped=False
    )


def create_plate_armor_of_etherealness() -> ArmorData:
    """Plate Armor of Etherealness (Legendary)
    Can use an action to speak the command word and cast Etherealness on yourself.
    """
    return ArmorData(
        index="plate-armor-of-etherealness",
        name="Plate Armor of Etherealness",
        cost=Cost(quantity=48000, unit="gp"),
        weight=65,
        desc=["Legendary plate armor. Can cast Etherealness on yourself once per day."],
        category=create_armor_category("heavy-armor"),
        armor_class={"base": 18, "dex_bonus": False, "max_bonus": 0},
        str_minimum=15,
        stealth_disadvantage=True,
        equipped=False
    )


# ============================================================================
# MAGICAL SHIELDS
# ============================================================================

def create_animated_shield() -> ArmorData:
    """Animated Shield (Very Rare)
    As a bonus action, you can speak the command word to animate the shield.
    It hovers in your space and grants +2 AC while animated.
    """
    return ArmorData(
        index="animated-shield",
        name="Animated Shield",
        cost=Cost(quantity=6000, unit="gp"),
        weight=6,
        desc=["Very Rare shield. Can animate to grant +2 AC without using your hands."],
        category=create_armor_category("shield"),
        armor_class={"base": 2, "dex_bonus": False, "max_bonus": 0},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_arrow_catching_shield() -> ArmorData:
    """Arrow-Catching Shield (Rare)
    +2 bonus to AC against ranged attacks.
    """
    return ArmorData(
        index="arrow-catching-shield",
        name="Arrow-Catching Shield",
        cost=Cost(quantity=6000, unit="gp"),
        weight=6,
        desc=["Rare shield. +2 AC (total +4) against ranged attacks."],
        category=create_armor_category("shield"),
        armor_class={"base": 2, "dex_bonus": False, "max_bonus": 0},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_shield_of_missile_attraction() -> ArmorData:
    """Shield of Missile Attraction (Rare, cursed)
    Ranged weapon attacks against you have advantage, and you take an extra 1d6 damage from them.
    """
    return ArmorData(
        index="shield-of-missile-attraction",
        name="Shield of Missile Attraction",
        cost=Cost(quantity=1000, unit="gp"),
        weight=6,
        desc=["Rare cursed shield. Attracts ranged attacks (disadvantage for wearer)."],
        category=create_armor_category("shield"),
        armor_class={"base": 2, "dex_bonus": False, "max_bonus": 0},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


def create_spellguard_shield() -> ArmorData:
    """Spellguard Shield (Very Rare)
    +2 AC and advantage on saving throws against spells and magical effects.
    """
    return ArmorData(
        index="spellguard-shield",
        name="Spellguard Shield",
        cost=Cost(quantity=50000, unit="gp"),
        weight=6,
        desc=["Very Rare shield. +2 AC and advantage on saves against spells."],
        category=create_armor_category("shield"),
        armor_class={"base": 2, "dex_bonus": False, "max_bonus": 0},
        str_minimum=0,
        stealth_disadvantage=False,
        equipped=False
    )


# ============================================================================
# REGISTRY
# ============================================================================

SPECIAL_ARMORS = {
    "armor-of-invulnerability": create_armor_of_invulnerability,
    "demon-armor": create_demon_armor,
    "dragon-scale-mail": lambda: create_dragon_scale_mail("red"),
    "dwarven-plate": create_dwarven_plate,
    "elven-chain": create_elven_chain,
    "glamoured-studded-leather": create_glamoured_studded_leather,
    "mithral-chain-shirt": lambda: create_mithral_armor("chain-shirt"),
    "mithral-plate": lambda: create_mithral_armor("plate"),
    "adamantine-plate": lambda: create_adamantine_armor("plate"),
    "armor-of-fire-resistance": lambda: create_armor_of_resistance("fire"),
    "armor-of-cold-resistance": lambda: create_armor_of_resistance("cold"),
    "plate-armor-of-etherealness": create_plate_armor_of_etherealness,
    "animated-shield": create_animated_shield,
    "arrow-catching-shield": create_arrow_catching_shield,
    "shield-of-missile-attraction": create_shield_of_missile_attraction,
    "spellguard-shield": create_spellguard_shield,
}


def get_special_armor(index: str) -> Optional[ArmorData]:
    """Get a special armor by index"""
    factory = SPECIAL_ARMORS.get(index)
    if factory:
        return factory()
    return None


__all__ = [
    'create_armor_of_invulnerability',
    'create_demon_armor',
    'create_dragon_scale_mail',
    'create_dwarven_plate',
    'create_elven_chain',
    'create_glamoured_studded_leather',
    'create_mithral_armor',
    'create_adamantine_armor',
    'create_armor_of_resistance',
    'create_plate_armor_of_etherealness',
    'create_animated_shield',
    'create_arrow_catching_shield',
    'create_shield_of_missile_attraction',
    'create_spellguard_shield',
    'SPECIAL_ARMORS',
    'get_special_armor',
]
