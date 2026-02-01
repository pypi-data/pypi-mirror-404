"""
D&D 5e Core - Magic Item Factory
Comprehensive collection of magic items, potions, rings, wands, and wondrous items
Merged from magic_item_factory.py and predefined_magic_items.py
"""
from typing import Optional

from .magic_item import MagicItem, MagicItemAction, MagicItemRarity, MagicItemType
from ..combat.condition_parser import ConditionParser
from .equipment import Cost, EquipmentCategory
from .potion import HealingPotion, SpeedPotion, StrengthPotion, SimplePotion


def create_magic_item_with_conditions(
    name: str,
    description: str,
    rarity: MagicItemRarity,
    item_type: MagicItemType,
    action_name: str = None,
    action_description: str = "",
    damage_dice: str = None,
    damage_type: str = None,
    save_dc: int = None,
    save_ability: str = None,
    uses_per_day: int = None,
    recharge: str = None,
    requires_attunement: bool = False,
    ac_bonus: int = 0,
    weight: float = 0.0,
    cost: int = 0
) -> MagicItem:
    """
    Create a magic item with automatic condition parsing.

    Args:
        name: Item name
        description: Item description
        rarity: Item rarity
        item_type: Type of magic item
        action_name: Name of the action (if item has active ability)
        action_description: Description of the action (parsed for conditions)
        damage_dice: Damage dice (e.g., "3d6")
        damage_type: Type of damage
        save_dc: Saving throw DC
        save_ability: Ability for saving throw
        uses_per_day: Limited uses per day
        recharge: When item recharges ("dawn", "short rest", "long rest")
        requires_attunement: Whether item requires attunement
        ac_bonus: AC bonus provided
        weight: Item weight
        cost: Item cost in gp

    Returns:
        MagicItem with parsed conditions
    """
    # Parse conditions from description
    conditions = ConditionParser.parse_condition_from_description(
        action_description if action_description else description
    )

    # Create action if applicable
    actions = []
    if action_name:
        action_type = "attack" if damage_dice else "utility"

        action = MagicItemAction(
            name=action_name,
            description=action_description,
            action_type=action_type,
            damage_dice=damage_dice,
            damage_type=damage_type,
            save_dc=save_dc,
            save_ability=save_ability,
            uses_per_day=uses_per_day,
            recharge=recharge,
            conditions=conditions
        )
        actions.append(action)

    # Create the magic item
    return MagicItem(
        index=name.lower().replace(" ", "-"),
        name=name,
        desc=[description] if isinstance(description, str) else description,
        weight=weight,
        cost=Cost(quantity=cost, unit='gp'),
        category=EquipmentCategory(
            index=item_type.value,
            name=item_type.value.title(),
            url=f"/api/equipment-categories/{item_type.value}"
        ),
        rarity=rarity,
        item_type=item_type,
        requires_attunement=requires_attunement,
        ac_bonus=ac_bonus,
        actions=actions,
        equipped=False
    )


# Pre-built magic items with conditions

def create_wand_of_paralysis() -> MagicItem:
    """Create a Wand of Paralysis that can paralyze targets"""
    return create_magic_item_with_conditions(
        name="Wand of Paralysis",
        description="This wand can paralyze a creature for 1 minute.",
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WAND,
        action_name="Paralyze",
        action_description="Target must make a DC 15 Constitution saving throw or be paralyzed for 1 minute. "
                          "The target can repeat the saving throw at the end of each of its turns.",
        save_dc=15,
        save_ability="con",
        uses_per_day=3,
        recharge="dawn",
        requires_attunement=True,
        weight=1.0,
        cost=5000
    )


def create_staff_of_entanglement() -> MagicItem:
    """Create a Staff that restrains creatures"""
    return create_magic_item_with_conditions(
        name="Staff of Entanglement",
        description="This staff can entangle and restrain foes.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.STAFF,
        action_name="Entangle",
        action_description="Target must make a DC 13 Strength saving throw or be restrained by magical vines. "
                          "The target can use its action to make a DC 13 Strength check to break free.",
        save_dc=13,
        save_ability="str",
        uses_per_day=5,
        recharge="dawn",
        requires_attunement=False,
        weight=4.0,
        cost=500
    )


def create_ring_of_blinding() -> MagicItem:
    """Create a Ring that can blind targets"""
    return create_magic_item_with_conditions(
        name="Ring of Blinding",
        description="This ring can emit a flash of light to blind enemies.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.RING,
        action_name="Blinding Flash",
        action_description="Target must make a DC 14 Constitution saving throw or be blinded for 1 minute.",
        save_dc=14,
        save_ability="con",
        uses_per_day=2,
        recharge="long rest",
        requires_attunement=True,
        weight=0.1,
        cost=800
    )


def create_cloak_of_fear() -> MagicItem:
    """Create a Cloak that frightens enemies"""
    return create_magic_item_with_conditions(
        name="Cloak of Fear",
        description="This cloak can instill fear in nearby creatures.",
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        action_name="Aura of Terror",
        action_description="Creatures within 30 feet must make a DC 15 Wisdom saving throw or be frightened "
                          "for 1 minute. A frightened creature can repeat the saving throw at the end of each turn.",
        save_dc=15,
        save_ability="wis",
        uses_per_day=1,
        recharge="long rest",
        requires_attunement=True,
        weight=1.0,
        cost=3000
    )


def create_poisoned_dagger() -> MagicItem:
    """Create a magical dagger that poisons on hit"""
    return create_magic_item_with_conditions(
        name="Poisoned Dagger +1",
        description="This magical dagger is coated with a potent poison.",
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WEAPON,
        action_name="Poison Strike",
        action_description="On hit, target takes 2d8 poison damage and must make a DC 13 Constitution saving throw "
                          "or be poisoned for 1 hour.",
        damage_dice="2d8",
        damage_type="poison",
        save_dc=13,
        save_ability="con",
        uses_per_day=3,
        recharge="dawn",
        requires_attunement=False,
        weight=1.0,
        cost=1000
    )


# ============================================================================
# PREDEFINED MAGIC ITEMS FROM STANDARD D&D 5E
# ============================================================================

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


def create_belt_of_giant_strength(giant_type: str = "hill") -> MagicItem:
    """Belt of Giant Strength: Sets Strength to specific value"""
    strength_values = {
        "hill": (21, 5000),
        "stone": (23, 10000),
        "frost": (23, 10000),
        "fire": (25, 20000),
        "cloud": (27, 50000),
        "storm": (29, 100000)
    }

    strength, cost = strength_values.get(giant_type, strength_values["hill"])

    return MagicItem(
        index=f"belt-of-{giant_type}-giant-strength",
        name=f"Belt of {giant_type.title()} Giant Strength",
        cost=Cost(quantity=cost, unit="gp"),
        weight=1,
        desc=[f"Your Strength score is {strength} while you wear this belt."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE if strength <= 23 else MagicItemRarity.VERY_RARE if strength <= 25 else MagicItemRarity.LEGENDARY,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ability_bonuses={"str": strength - 10}
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
        ability_bonuses={"con": 9}
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
        recharge=None
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


def create_boots_of_speed() -> MagicItem:
    """Boots of Speed: Double speed for 10 minutes"""
    return MagicItem(
        index="boots-of-speed",
        name="Boots of Speed",
        cost=Cost(quantity=4000, unit="gp"),
        weight=1,
        desc=["As a bonus action, you can click the heels together to double your walking speed and make opportunity attacks against you have disadvantage."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True
    )


def create_boots_of_levitation() -> MagicItem:
    """Boots of Levitation: Levitate at will"""
    return MagicItem(
        index="boots-of-levitation",
        name="Boots of Levitation",
        cost=Cost(quantity=4000, unit="gp"),
        weight=1,
        desc=["While you wear these boots, you can cast levitate on yourself at will."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True
    )


def create_cloak_of_elvenkind() -> MagicItem:
    """Cloak of Elvenkind: Advantage on Stealth checks"""
    return MagicItem(
        index="cloak-of-elvenkind",
        name="Cloak of Elvenkind",
        cost=Cost(quantity=5000, unit="gp"),
        weight=1,
        desc=["While you wear this cloak with its hood up, Wisdom (Perception) checks made to see you have disadvantage, and you have advantage on Dexterity (Stealth) checks."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True
    )


def create_gauntlets_of_ogre_power() -> MagicItem:
    """Gauntlets of Ogre Power: Strength becomes 19"""
    return MagicItem(
        index="gauntlets-of-ogre-power",
        name="Gauntlets of Ogre Power",
        cost=Cost(quantity=2000, unit="gp"),
        weight=2,
        desc=["Your Strength score is 19 while you wear these gauntlets."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ability_bonuses={"str": 9}
    )


def create_headband_of_intellect() -> MagicItem:
    """Headband of Intellect: Intelligence becomes 19"""
    return MagicItem(
        index="headband-of-intellect",
        name="Headband of Intellect",
        cost=Cost(quantity=2000, unit="gp"),
        weight=0,
        desc=["Your Intelligence score is 19 while you wear this headband."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=True,
        ability_bonuses={"int": 9}
    )


def create_periapt_of_health() -> MagicItem:
    """Periapt of Health: Immunity to disease"""
    return MagicItem(
        index="periapt-of-health",
        name="Periapt of Health",
        cost=Cost(quantity=5000, unit="gp"),
        weight=0,
        desc=["You are immune to contracting any disease while you wear this pendant."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=False
    )


def create_periapt_of_proof_against_poison() -> MagicItem:
    """Periapt of Proof Against Poison: Immunity to poison"""
    return MagicItem(
        index="periapt-of-proof-against-poison",
        name="Periapt of Proof Against Poison",
        cost=Cost(quantity=5000, unit="gp"),
        weight=0,
        desc=["This delicate silver chain has a brilliant-cut black gem pendant. While you wear it, poisons have no effect on you. You are immune to the poisoned condition and have immunity to poison damage."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=False
    )


def create_ring_of_free_action() -> MagicItem:
    """Ring of Free Action: Cannot be paralyzed or restrained"""
    return MagicItem(
        index="ring-of-free-action",
        name="Ring of Free Action",
        cost=Cost(quantity=20000, unit="gp"),
        weight=0,
        desc=["While you wear this ring, difficult terrain doesn't cost you extra movement. In addition, magic can neither reduce your speed nor cause you to be paralyzed or restrained."],
        category=EquipmentCategory(index="ring", name="Ring", url="/api/equipment-categories/ring"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.RING,
        requires_attunement=True
    )


def create_ring_of_regeneration() -> MagicItem:
    """Ring of Regeneration: Regain 1d6 HP every 10 minutes"""
    return MagicItem(
        index="ring-of-regeneration",
        name="Ring of Regeneration",
        cost=Cost(quantity=30000, unit="gp"),
        weight=0,
        desc=["While wearing this ring, you regain 1d6 hit points every 10 minutes, provided that you have at least 1 hit point."],
        category=EquipmentCategory(index="ring", name="Ring", url="/api/equipment-categories/ring"),
        equipped=False,
        rarity=MagicItemRarity.VERY_RARE,
        item_type=MagicItemType.RING,
        requires_attunement=True
    )


def create_ring_of_spell_storing() -> MagicItem:
    """Ring of Spell Storing: Store up to 5 levels of spells"""
    return MagicItem(
        index="ring-of-spell-storing",
        name="Ring of Spell Storing",
        cost=Cost(quantity=24000, unit="gp"),
        weight=0,
        desc=["This ring stores spells cast into it, holding them until the attuned wearer uses them."],
        category=EquipmentCategory(index="ring", name="Ring", url="/api/equipment-categories/ring"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.RING,
        requires_attunement=True
    )


def create_wand_of_fireballs() -> MagicItem:
    """Wand of Fireballs: Cast Fireball (7 charges)"""
    fireball = MagicItemAction(
        name="Fireball",
        description="Cast fireball (8d6 fire damage, 20-foot radius)",
        action_type="attack",
        damage_dice="8d6",
        damage_type="fire",
        range=150,
        area_of_effect="sphere",
        save_dc=15,
        save_ability="dex",
        uses_per_day=7,
        recharge="dawn"
    )

    return MagicItem(
        index="wand-of-fireballs",
        name="Wand of Fireballs",
        cost=Cost(quantity=8000, unit="gp"),
        weight=1,
        desc=["This wand has 7 charges. While holding it, you can use an action to expend 1 or more of its charges to cast fireball."],
        category=EquipmentCategory(index="wand", name="Wand", url="/api/equipment-categories/wand"),
        equipped=False,
        rarity=MagicItemRarity.RARE,
        item_type=MagicItemType.WAND,
        requires_attunement=True,
        actions=[fireball]
    )


def create_bag_of_holding() -> MagicItem:
    """Bag of Holding: 500 lbs capacity, 64 cubic feet"""
    return MagicItem(
        index="bag-of-holding",
        name="Bag of Holding",
        cost=Cost(quantity=4000, unit="gp"),
        weight=15,
        desc=["This bag has an interior space considerably larger than its outside dimensions. The bag can hold up to 500 pounds, not exceeding a volume of 64 cubic feet."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=False
    )


def create_rope_of_climbing() -> MagicItem:
    """Rope of Climbing: 60 feet of magical rope"""
    return MagicItem(
        index="rope-of-climbing",
        name="Rope of Climbing",
        cost=Cost(quantity=2000, unit="gp"),
        weight=3,
        desc=["This 60-foot length of silk rope weighs 3 pounds and can hold up to 3,000 pounds. You can command the rope to knot, unknot, coil, or anchor itself."],
        category=EquipmentCategory(index="wondrous-items", name="Wondrous Item", url="/api/equipment-categories/wondrous-items"),
        equipped=False,
        rarity=MagicItemRarity.UNCOMMON,
        item_type=MagicItemType.WONDROUS,
        requires_attunement=False
    )


# ============================================================================
# POTIONS
# ============================================================================

def create_potion_of_healing() -> HealingPotion:
    """Potion of Healing: Restore 2d4+2 HP"""
    return HealingPotion(
        name="Potion of Healing",
        rarity=MagicItemRarity.COMMON,
        hit_dice="2d4",
        bonus=2,
        min_cost=40,
        max_cost=60,
        min_level=1
    )


def create_potion_of_greater_healing() -> HealingPotion:
    """Potion of Greater Healing: Restore 4d4+4 HP"""
    return HealingPotion(
        name="Potion of Greater Healing",
        rarity=MagicItemRarity.UNCOMMON,
        hit_dice="4d4",
        bonus=4,
        min_cost=120,
        max_cost=180,
        min_level=1
    )


def create_potion_of_superior_healing() -> HealingPotion:
    """Potion of Superior Healing: Restore 8d4+8 HP"""
    return HealingPotion(
        name="Potion of Superior Healing",
        rarity=MagicItemRarity.RARE,
        hit_dice="8d4",
        bonus=8,
        min_cost=400,
        max_cost=500,
        min_level=1
    )


def create_potion_of_supreme_healing() -> HealingPotion:
    """Potion of Supreme Healing: Restore 10d4+20 HP"""
    return HealingPotion(
        name="Potion of Supreme Healing",
        rarity=MagicItemRarity.VERY_RARE,
        hit_dice="10d4",
        bonus=20,
        min_cost=1200,
        max_cost=1500,
        min_level=1
    )


def create_antitoxin() -> SimplePotion:
    """Antitoxin: Advantage on saving throws against poison for 1 hour"""
    return SimplePotion(
        name="Antitoxin",
        rarity=MagicItemRarity.COMMON,
        min_cost=40,
        max_cost=60,
        description="Advantage on saving throws against poison for 1 hour",
        duration=3600
    )


def create_potion_of_poison() -> SimplePotion:
    """Potion of Poison: 3d6 poison damage, DC 13 CON save"""
    return SimplePotion(
        name="Potion of Poison",
        rarity=MagicItemRarity.UNCOMMON,
        min_cost=80,
        max_cost=120,
        description="3d6 poison damage, DC 13 CON save (half on success)",
        duration=None
    )


def create_potion_of_speed() -> SpeedPotion:
    """Potion of Speed: Haste effect for 1 minute"""
    return SpeedPotion(
        name="Potion of Speed",
        rarity=MagicItemRarity.VERY_RARE,
        min_cost=350,
        max_cost=450,
        duration=60,
        min_level=1
    )


def create_potion_of_invisibility() -> SimplePotion:
    """Potion of Invisibility: Invisible for 1 hour"""
    return SimplePotion(
        name="Potion of Invisibility",
        rarity=MagicItemRarity.VERY_RARE,
        min_cost=160,
        max_cost=200,
        description="Become invisible for 1 hour (effect ends early if you attack or cast a spell)",
        duration=3600
    )


def create_potion_of_flying() -> SimplePotion:
    """Potion of Flying: Fly for 1 hour"""
    return SimplePotion(
        name="Potion of Flying",
        rarity=MagicItemRarity.VERY_RARE,
        min_cost=450,
        max_cost=550,
        description="Gain flying speed equal to walking speed for 1 hour",
        duration=3600
    )


def create_potion_of_giant_strength(giant_type: str = "hill") -> StrengthPotion:
    """Potion of Giant Strength: Sets Strength for 1 hour"""
    strength_values = {
        "hill": (21, 200),
        "stone": (23, 300),
        "frost": (23, 300),
        "fire": (25, 500),
        "cloud": (27, 1000),
        "storm": (29, 2000)
    }

    strength, _cost = strength_values.get(giant_type, strength_values["hill"])

    return StrengthPotion(
        name=f"Potion of {giant_type.title()} Giant Strength",
        rarity=MagicItemRarity.UNCOMMON if strength <= 21 else MagicItemRarity.RARE if strength <= 25 else MagicItemRarity.VERY_RARE,
        min_cost= _cost if ' _cost' in locals() else 200,
        max_cost= _cost if ' _cost' in locals() else 300,
        value=strength,
        duration=3600,
        min_level=1
    )


def create_elixir_of_health() -> SimplePotion:
    """Elixir of Health: Cures any disease and poisoned condition"""
    return SimplePotion(
        name="Elixir of Health",
        rarity=MagicItemRarity.RARE,
        min_cost=100,
        max_cost=140,
        description="Cures disease and removes blinded, deafened, paralyzed, and poisoned conditions",
        duration=None
    )


def create_oil_of_slipperiness() -> SimplePotion:
    """Oil of Slipperiness: Freedom of movement effect"""
    return SimplePotion(
        name="Oil of Slipperiness",
        rarity=MagicItemRarity.UNCOMMON,
        min_cost=420,
        max_cost=520,
        description="Grants Freedom of Movement for 8 hours",
        duration=8*3600
    )


# ============================================================================
# REGISTRY OF ALL MAGIC ITEMS
# ============================================================================

MAGIC_ITEMS_REGISTRY = {
    # Condition-based items
    "wand-of-paralysis": create_wand_of_paralysis,
    "staff-of-entanglement": create_staff_of_entanglement,
    "ring-of-blinding": create_ring_of_blinding,
    "cloak-of-fear": create_cloak_of_fear,
    "poisoned-dagger": create_poisoned_dagger,

    # Standard magic items
    "ring-of-protection": create_ring_of_protection,
    "cloak-of-protection": create_cloak_of_protection,
    "wand-of-magic-missiles": create_wand_of_magic_missiles,
    "staff-of-healing": create_staff_of_healing,
    "belt-of-giant-strength": lambda: create_belt_of_giant_strength("hill"),
    "belt-of-hill-giant-strength": lambda: create_belt_of_giant_strength("hill"),
    "belt-of-stone-giant-strength": lambda: create_belt_of_giant_strength("stone"),
    "belt-of-frost-giant-strength": lambda: create_belt_of_giant_strength("frost"),
    "belt-of-fire-giant-strength": lambda: create_belt_of_giant_strength("fire"),
    "belt-of-cloud-giant-strength": lambda: create_belt_of_giant_strength("cloud"),
    "belt-of-storm-giant-strength": lambda: create_belt_of_giant_strength("storm"),
    "amulet-of-health": create_amulet_of_health,
    "bracers-of-defense": create_bracers_of_defense,
    "necklace-of-fireballs": create_necklace_of_fireballs,
    "boots-of-speed": create_boots_of_speed,
    "boots-of-levitation": create_boots_of_levitation,
    "cloak-of-elvenkind": create_cloak_of_elvenkind,
    "gauntlets-of-ogre-power": create_gauntlets_of_ogre_power,
    "headband-of-intellect": create_headband_of_intellect,
    "periapt-of-health": create_periapt_of_health,
    "periapt-of-proof-against-poison": create_periapt_of_proof_against_poison,
    "ring-of-free-action": create_ring_of_free_action,
    "ring-of-regeneration": create_ring_of_regeneration,
    "ring-of-spell-storing": create_ring_of_spell_storing,
    "wand-of-fireballs": create_wand_of_fireballs,
    "bag-of-holding": create_bag_of_holding,
    "rope-of-climbing": create_rope_of_climbing,

    # Potions
    "potion-of-healing": create_potion_of_healing,
    "potion-of-greater-healing": create_potion_of_greater_healing,
    "potion-of-superior-healing": create_potion_of_superior_healing,
    "potion-of-supreme-healing": create_potion_of_supreme_healing,
    "antitoxin": create_antitoxin,
    "potion-of-poison": create_potion_of_poison,
    "potion-of-speed": create_potion_of_speed,
    "potion-of-invisibility": create_potion_of_invisibility,
    "potion-of-flying": create_potion_of_flying,
    "potion-of-hill-giant-strength": lambda: create_potion_of_giant_strength("hill"),
    "potion-of-stone-giant-strength": lambda: create_potion_of_giant_strength("stone"),
    "potion-of-frost-giant-strength": lambda: create_potion_of_giant_strength("frost"),
    "potion-of-fire-giant-strength": lambda: create_potion_of_giant_strength("fire"),
    "potion-of-cloud-giant-strength": lambda: create_potion_of_giant_strength("cloud"),
    "potion-of-storm-giant-strength": lambda: create_potion_of_giant_strength("storm"),
    "elixir-of-health": create_elixir_of_health,
    "oil-of-slipperiness": create_oil_of_slipperiness,
}


def get_magic_item(index: str) -> Optional[MagicItem]:
    """
    Get a magic item by index from the registry.

    Args:
        index: Magic item index

    Returns:
        MagicItem instance or None if not found
    """
    factory = MAGIC_ITEMS_REGISTRY.get(index)
    if factory:
        return factory()
    return None


# Alias for compatibility
PREDEFINED_ITEMS = MAGIC_ITEMS_REGISTRY


__all__ = [
    'create_magic_item_with_conditions',
    'create_wand_of_paralysis',
    'create_staff_of_entanglement',
    'create_ring_of_blinding',
    'create_cloak_of_fear',
    'create_poisoned_dagger',
    'create_ring_of_protection',
    'create_cloak_of_protection',
    'create_wand_of_magic_missiles',
    'create_staff_of_healing',
    'create_belt_of_giant_strength',
    'create_amulet_of_health',
    'create_bracers_of_defense',
    'create_necklace_of_fireballs',
    'create_boots_of_speed',
    'create_boots_of_levitation',
    'create_cloak_of_elvenkind',
    'create_gauntlets_of_ogre_power',
    'create_headband_of_intellect',
    'create_periapt_of_health',
    'create_periapt_of_proof_against_poison',
    'create_ring_of_free_action',
    'create_ring_of_regeneration',
    'create_ring_of_spell_storing',
    'create_wand_of_fireballs',
    'create_bag_of_holding',
    'create_rope_of_climbing',
    'create_potion_of_healing',
    'create_potion_of_greater_healing',
    'create_potion_of_superior_healing',
    'create_potion_of_supreme_healing',
    'create_antitoxin',
    'create_potion_of_poison',
    'create_potion_of_speed',
    'create_potion_of_invisibility',
    'create_potion_of_flying',
    'create_potion_of_giant_strength',
    'create_elixir_of_health',
    'create_oil_of_slipperiness',
    'MAGIC_ITEMS_REGISTRY',
    'PREDEFINED_ITEMS',
    'get_magic_item',
]

