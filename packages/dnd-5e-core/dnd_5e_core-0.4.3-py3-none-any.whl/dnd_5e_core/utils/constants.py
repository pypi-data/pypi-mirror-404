"""
D&D 5e Core - Game Constants
Common constants used throughout D&D 5e
"""
from __future__ import annotations

# Ability Scores
ABILITY_SCORE_MIN = 1
ABILITY_SCORE_MAX = 20
ABILITY_SCORE_MAX_WITH_MAGIC = 30

# Character Levels
MIN_LEVEL = 1
MAX_LEVEL = 20

# Dice
DICE_TYPES = [4, 6, 8, 10, 12, 20, 100]

# Movement
BASE_SPEED_HUMAN = 30  # feet
BASE_SPEED_DWARF = 25  # feet
BASE_SPEED_ELF = 30  # feet
BASE_SPEED_HALFLING = 25  # feet

# Combat
ATTACK_ROLL_CRITICAL_SUCCESS = 20
ATTACK_ROLL_CRITICAL_FAILURE = 1
BASE_SPELL_SAVE_DC = 8

# Conditions
CONDITIONS = [
    "blinded",
    "charmed",
    "deafened",
    "exhaustion",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
]

# Damage Types
DAMAGE_TYPES = [
    "acid",
    "bludgeoning",
    "cold",
    "fire",
    "force",
    "lightning",
    "necrotic",
    "piercing",
    "poison",
    "psychic",
    "radiant",
    "slashing",
    "thunder",
]

# Spell Schools
SPELL_SCHOOLS = [
    "abjuration",
    "conjuration",
    "divination",
    "enchantment",
    "evocation",
    "illusion",
    "necromancy",
    "transmutation",
]

# Armor Classes
ARMOR_CLASS_UNARMORED = 10
ARMOR_CLASS_MAX_DEX_MEDIUM = 2
ARMOR_CLASS_MAX_DEX_HEAVY = 0
SHIELD_AC_BONUS = 2

# Ranges
MELEE_RANGE = 5  # feet
SHORT_RANGE_THROWN = 20  # feet
LONG_RANGE_THROWN = 60  # feet
TOUCH_RANGE = 0  # feet (touch spells)

# Proficiency
PROFICIENCY_BONUS_BY_LEVEL = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

# Rests
SHORT_REST_HOURS = 1
LONG_REST_HOURS = 8

# Currency (in copper pieces)
COPPER_TO_SILVER = 10
SILVER_TO_ELECTRUM = 2
ELECTRUM_TO_GOLD = 2
GOLD_TO_PLATINUM = 10

# Or more simply:
CP_VALUE = 1
SP_VALUE = 10
EP_VALUE = 50
GP_VALUE = 100
PP_VALUE = 1000

# Sizes
CREATURE_SIZES = {
    "tiny": {"space": 2.5, "weight_multiplier": 1},
    "small": {"space": 5, "weight_multiplier": 1},
    "medium": {"space": 5, "weight_multiplier": 1},
    "large": {"space": 10, "weight_multiplier": 2},
    "huge": {"space": 15, "weight_multiplier": 4},
    "gargantuan": {"space": 20, "weight_multiplier": 8},
}

# Skills
SKILLS = [
    "acrobatics",
    "animal-handling",
    "arcana",
    "athletics",
    "deception",
    "history",
    "insight",
    "intimidation",
    "investigation",
    "medicine",
    "nature",
    "perception",
    "performance",
    "persuasion",
    "religion",
    "sleight-of-hand",
    "stealth",
    "survival",
]

# Languages
STANDARD_LANGUAGES = [
    "common",
    "dwarvish",
    "elvish",
    "giant",
    "gnomish",
    "goblin",
    "halfling",
    "orc",
]

EXOTIC_LANGUAGES = [
    "abyssal",
    "celestial",
    "draconic",
    "deep-speech",
    "infernal",
    "primordial",
    "sylvan",
    "undercommon",
]

# Equipment Categories
EQUIPMENT_CATEGORIES = [
    "armor",
    "weapon",
    "adventuring-gear",
    "tools",
    "mounts-and-vehicles",
    "trade-goods",
]

# Weapon Properties
WEAPON_PROPERTIES = [
    "ammunition",
    "finesse",
    "heavy",
    "light",
    "loading",
    "range",
    "reach",
    "special",
    "thrown",
    "two-handed",
    "versatile",
]

# Armor Types
ARMOR_TYPES = {
    "light": ["padded", "leather", "studded-leather"],
    "medium": ["hide", "chain-shirt", "scale-mail", "breastplate", "half-plate"],
    "heavy": ["ring-mail", "chain-mail", "splint", "plate"],
    "shield": ["shield"],
}

# Classes
CLASSES = [
    "barbarian",
    "bard",
    "cleric",
    "druid",
    "fighter",
    "monk",
    "paladin",
    "ranger",
    "rogue",
    "sorcerer",
    "warlock",
    "wizard",
]

# Races
RACES = [
    "dragonborn",
    "dwarf",
    "elf",
    "gnome",
    "half-elf",
    "half-orc",
    "halfling",
    "human",
    "tiefling",
]

# Alignments
ALIGNMENTS = [
    "lawful-good",
    "neutral-good",
    "chaotic-good",
    "lawful-neutral",
    "true-neutral",
    "chaotic-neutral",
    "lawful-evil",
    "neutral-evil",
    "chaotic-evil",
]

# Adventure difficulty multipliers (for treasure/rewards)
DIFFICULTY_MULTIPLIERS = {
    "easy": 0.5,
    "medium": 1.0,
    "hard": 1.5,
    "deadly": 2.0,
}

