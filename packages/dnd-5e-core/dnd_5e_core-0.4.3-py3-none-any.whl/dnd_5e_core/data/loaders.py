"""
D&D 5e Core - Character and Monster Loading
Provides utilities to load characters and monsters from the D&D 5e API
"""
from typing import List, Optional
from random import choice, randint
import requests


API_BASE_URL = "https://www.dnd5eapi.co/api"


def populate(collection_name: str, key_name: str = "results") -> List[str]:
    """
    Get a list of items from a collection in the D&D 5e API.

    Args:
        collection_name: Name of the collection (e.g., "monsters", "spells")
        key_name: Key to extract from response (default: "results")

    Returns:
        List of item indices
    """
    try:
        response = requests.get(f"{API_BASE_URL}/{collection_name}")
        response.raise_for_status()
        data = response.json()

        if key_name in data:
            return [item['index'] for item in data[key_name]]
        return []
    except Exception as e:
        print(f"Error loading {collection_name}: {e}")
        return []


def request_monster(index: str):
    """
    Load a monster from the D&D 5e API.

    Args:
        index: Monster index (e.g., "goblin", "adult-red-dragon")

    Returns:
        Monster instance or None if not found
    """
    try:
        # Import here to avoid circular dependencies
        from .loader import load_monster
        return load_monster(index)
    except Exception as e:
        print(f"Error loading monster {index}: {e}")
        return None


def load_monsters_database():
    """
    Load all available monsters from the D&D 5e API.

    Returns:
        List of Monster instances
    """
    print("Loading monsters database...")
    monster_indices = populate("monsters", "results")
    monsters = []

    for index in monster_indices:
        monster = request_monster(index)
        if monster:
            monsters.append(monster)

    print(f"Loaded {len(monsters)} monsters")
    return monsters


def simple_character_generator(
    level: int = 1,
    race_name: Optional[str] = None,
    class_name: Optional[str] = None,
    name: Optional[str] = None,
    apply_class_abilities: bool = True,
    apply_racial_traits: bool = True,
    strict_class_prereqs: bool = True,
    max_attempts: int = 10,
):
    """
    Generate a simple character with basic attributes.

    This is a simplified version that doesn't require loading full collections.
    For more advanced character generation, use the full API.

    Args:
        level: Character level (default: 1)
        race_name: Race name (optional, random if not provided)
        class_name: Class name (optional, random if not provided)
        name: Character name (optional, random if not provided)
        apply_class_abilities: Automatically apply class abilities (default: True)
        apply_racial_traits: Automatically apply racial traits (default: True)

    Returns:
        Character instance
    """
    # Import here to avoid circular dependencies
    from ..entities import Character
    from ..races import Race
    from ..classes import ClassType
    from ..abilities import Abilities

    # Default races
    if not race_name:
        race_name = choice(["human", "elf", "dwarf", "halfling"])

    # Generate abilities
    def roll_ability():
        rolls = sorted([randint(1, 6) for _ in range(4)])
        return sum(rolls[1:])  # Drop lowest

    strength = roll_ability()
    dexterity = roll_ability()
    constitution = roll_ability()
    intelligence = roll_ability()
    wisdom = roll_ability()
    charisma = roll_ability()

    abilities = Abilities(strength, dexterity, constitution, intelligence, wisdom, charisma)

    mod = lambda x: (x - 10) // 2
    ability_modifiers = Abilities(
        mod(strength), mod(dexterity), mod(constitution),
        mod(intelligence), mod(wisdom), mod(charisma)
    )

    # Generate name
    if not name:
        prefixes = ["Ara", "Eld", "Gim", "Tho", "Bil", "Fro"]
        suffixes = ["dor", "rin", "li", "rgrim", "bo", "do"]
        name = choice(prefixes) + choice(suffixes)

    # Default classes
    # Validate class prerequisites: do not allow classes that abilities don't satisfy.
    # If the user provided a class_name explicitly, ensure abilities meet that class' minimums.
    from ..classes.multiclass import can_multiclass_into

    # Candidate classes to choose from when randomizing
    candidate_classes = [
        "barbarian", "bard", "cleric", "druid", "fighter", "monk",
        "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"
    ]

    if class_name:
        ok, reason = can_multiclass_into(class_name, abilities)
        if not ok:
            if not strict_class_prereqs:
                # Attempt to reroll abilities up to max_attempts to satisfy the explicit class
                attempts = 0
                while attempts < max_attempts and not ok:
                    attempts += 1
                    strength = roll_ability()
                    dexterity = roll_ability()
                    constitution = roll_ability()
                    intelligence = roll_ability()
                    wisdom = roll_ability()
                    charisma = roll_ability()

                    abilities = Abilities(strength, dexterity, constitution, intelligence, wisdom, charisma)
                    ability_modifiers = Abilities(
                        mod(strength), mod(dexterity), mod(constitution),
                        mod(intelligence), mod(wisdom), mod(charisma)
                    )

                    ok, reason = can_multiclass_into(class_name, abilities)

                if not ok:
                    raise ValueError(
                        f"After {max_attempts} attempts, abilities do not meet minimum requirements for class '{class_name}': {reason}"
                    )
            else:
                # Explicit class requested but abilities don't match requirements
                raise ValueError(f"Abilities do not meet minimum requirements for class '{class_name}': {reason}")
    else:
        # Try up to N times to generate abilities that allow at least one class
        attempts = 0
        max_attempts = 10
        valid_choice = None

        while attempts < max_attempts:
            valid_candidates = [c for c in candidate_classes if can_multiclass_into(c, abilities)[0]]
            if valid_candidates:
                valid_choice = choice(valid_candidates)
                break

            # Reroll abilities and modifiers
            attempts += 1
            strength = roll_ability()
            dexterity = roll_ability()
            constitution = roll_ability()
            intelligence = roll_ability()
            wisdom = roll_ability()
            charisma = roll_ability()

            abilities = Abilities(strength, dexterity, constitution, intelligence, wisdom, charisma)
            ability_modifiers = Abilities(
                mod(strength), mod(dexterity), mod(constitution),
                mod(intelligence), mod(wisdom), mod(charisma)
            )

        if valid_choice:
            class_name = valid_choice
        else:
            # Failed to produce a valid set after retries; raise to avoid assigning invalid class
            raise RuntimeError(
                f"Could not generate abilities satisfying any class prerequisites after {max_attempts} attempts"
            )

    # Create simple race
    race = Race(
        index=race_name,
        name=race_name.capitalize(),
        speed=30,
        ability_bonuses={},
        alignment="Any",
        age="Varies",
        size="Medium",
        size_description="Medium size",
        starting_proficiencies=[],
        starting_proficiency_options=[],
        languages=[],
        language_desc="Common",
        traits=[],
        subraces=[]
    )

    # Create simple class with correct spellcasting info
    hit_dice = {
        "barbarian": 12, "fighter": 10, "paladin": 10, "ranger": 10,
        "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8, "warlock": 8,
        "sorcerer": 6, "wizard": 6
    }

    # Define all spellcasting classes with their primary ability and caster type
    spellcasting_classes = {
        "bard": ("cha", 1),        # Full caster, Charisma
        "cleric": ("wis", 1),      # Full caster, Wisdom
        "druid": ("wis", 1),       # Full caster, Wisdom
        "sorcerer": ("cha", 1),    # Full caster, Charisma
        "wizard": ("int", 1),      # Full caster, Intelligence
        "paladin": ("cha", 2),     # Half caster, Charisma
        "ranger": ("wis", 2),      # Half caster, Wisdom
        "warlock": ("cha", 1),     # Pact caster, Charisma
    }

    is_caster = class_name in spellcasting_classes
    spellcasting_ability = spellcasting_classes[class_name][0] if is_caster else ""
    spellcasting_level = spellcasting_classes[class_name][1] if is_caster else 0

    class_type = ClassType(
        index=class_name,
        name=class_name.capitalize(),
        hit_die=hit_dice.get(class_name, 8),
        proficiency_choices=[],
        proficiencies=[],
        saving_throws=[],
        starting_equipment=[],
        starting_equipment_options=[],
        class_levels=[],
        multi_classing=[],
        subclasses=[],
        spellcasting_level=spellcasting_level,
        spellcasting_ability=spellcasting_ability,
        can_cast=is_caster,
        spell_slots={},
        spells_known=[],
        cantrips_known=[]
    )


    # Calculate HP
    hit_points = class_type.hit_die + ability_modifiers.con
    for _ in range(level - 1):
        hit_points += randint(1, class_type.hit_die) + ability_modifiers.con

    # Create SpellCaster for spellcasting classes with actual spell loading
    spell_caster = None
    if class_type.can_cast:
        from ..spells.spellcaster import SpellCaster
        from .collections import load_all_spells
        from random import sample

        # Load all spells
        try:
            all_spells = load_all_spells()
            if not all_spells:
                print(f"⚠️  Warning: No spells loaded (load_all_spells returned empty list)")
        except Exception as e:
            import traceback
            print(f"⚠️  Warning: Could not load spells: {e}")
            print("Full traceback:")
            traceback.print_exc()
            all_spells = []

        # Filter learnable spells (same logic as get_spell_caster in main.py)
        learnable_spells = [
            s for s in all_spells
            if class_type.index in s.allowed_classes
            and s.level <= level
            and (s.damage_type or s.heal_at_slot_level)
        ]

        learned_spells = []  # Initialize to empty list
        if learnable_spells:
            # Separate cantrips and slot spells
            cantrips_spells = [s for s in learnable_spells if s.level == 0]
            slot_spells = [s for s in learnable_spells if s.level > 0]

            # Determine number of cantrips (simplified)
            n_cantrips = min(len(cantrips_spells), 3 if level < 4 else 4 if level < 10 else 5)

            # Determine number of spells known (simplified)
            n_slot_spells = min(len(slot_spells), level + 1)

            # Select random spells
            if cantrips_spells and n_cantrips > 0:
                learned_spells += sample(cantrips_spells, min(n_cantrips, len(cantrips_spells)))
            if slot_spells and n_slot_spells > 0:
                learned_spells += sample(slot_spells, min(n_slot_spells, len(slot_spells)))

        # Calculate spell slots using progression data if available
        spell_slots = [0] * 10  # Index 0 unused, 1-9 are spell levels

        try:
            from .progression_loader import get_spell_slots_for_level
            spell_slots = get_spell_slots_for_level(class_type.index, level)
        except Exception:
            # Fallback to hardcoded values if progression data not available
            if class_type.spellcasting_level == 1:  # Full caster
                if level >= 1: spell_slots[1] = 2 if level == 1 else 3 if level == 2 else 4
                if level >= 3: spell_slots[2] = 2 if level == 3 else 3
                if level >= 5: spell_slots[3] = 2 if level == 5 else 3
                if level >= 7: spell_slots[4] = 1 if level == 7 else 2 if level == 8 else 3
                if level >= 9: spell_slots[5] = 1 if level == 9 else 2
                if level >= 11: spell_slots[6] = 1
                if level >= 13: spell_slots[7] = 1
                if level >= 15: spell_slots[8] = 1
                if level >= 17: spell_slots[9] = 1
            elif class_type.spellcasting_level == 2:  # Half caster (Paladin, Ranger)
                # Half casters get slots as if they were half their level (rounded down)
                effective_level = level // 2
                if effective_level >= 1: spell_slots[1] = 2 if effective_level == 1 else 3 if effective_level == 2 else 4
                if effective_level >= 3: spell_slots[2] = 2 if effective_level == 3 else 3
                if effective_level >= 5: spell_slots[3] = 2 if effective_level == 5 else 3
                if effective_level >= 7: spell_slots[4] = 1 if effective_level == 7 else 2 if effective_level == 8 else 3
                if effective_level >= 9: spell_slots[5] = 1 if effective_level == 9 else 2

        # Calculate DC and ability modifier
        ability_modifier = getattr(ability_modifiers, class_type.spellcasting_ability, 0)
        proficiency_bonus = 2 + ((level - 1) // 4)  # +2 at 1-4, +3 at 5-8, +4 at 9-12, etc.
        dc_value = 8 + proficiency_bonus + ability_modifier

        spell_caster = SpellCaster(
            level=level,
            spell_slots=spell_slots,
            learned_spells=learned_spells,
            dc_type=class_type.spellcasting_ability,
            dc_value=dc_value,
            ability_modifier=ability_modifier
        )

    character = Character(
        race=race,
        subrace=None,
        class_type=class_type,
        proficiencies=[],
        abilities=abilities,
        ability_modifiers=ability_modifiers,
        gender=choice(["male", "female"]),
        name=name,
        ethnic=None,
        height=66 + randint(-6, 6),
        weight=150 + randint(-30, 30),
        inventory=[None] * 20,
        hit_points=hit_points,
        max_hit_points=hit_points,
        xp=0,
        level=level,
        age=18 * 52 + randint(0, 299),
        gold=90 + randint(0, 99),
        sc=spell_caster,
        conditions=[],
        speed=race.speed,
        haste_timer=0,
        hasted=False,
        st_advantages=[]
    )

    # 🆕 PHASE 1: Apply Class Abilities automatically
    if apply_class_abilities:
        from ..mechanics.class_abilities import ClassAbilities

        # Store class abilities manager
        character.class_abilities_manager = class_name

        # Apply automatic benefits based on class and level
        if class_name == "fighter" and level >= 5:
            # Extra Attack at level 5
            # Use multi_attack_bonus to add extra attacks
            if level >= 20:
                character.multi_attack_bonus = 3  # 4 total attacks
            elif level >= 11:
                character.multi_attack_bonus = 2  # 3 total attacks
            else:
                character.multi_attack_bonus = 1  # 2 total attacks

        elif class_name == "barbarian":
            # Initialize rage system
            character.rage_active = False
            character.rage_uses_left = ClassAbilities._get_rage_uses(level)
            character.rage_damage_bonus = 0
            # Barbarians also get Extra Attack at level 5
            if level >= 5:
                character.multi_attack_bonus = 1  # 2 total attacks

        elif class_name == "rogue" and level >= 1:
            # Sneak Attack damage
            character.sneak_attack_dice = (level + 1) // 2

        elif class_name == "monk" and level >= 1:
            # Ki points
            character.ki_points = level
            character.ki_points_max = level
            # Monks get Extra Attack at level 5
            if level >= 5:
                character.multi_attack_bonus = 1  # 2 total attacks

        elif class_name == "paladin" and level >= 1:
            # Lay on Hands pool
            character.lay_on_hands_pool = level * 5
            # Paladins get Extra Attack at level 5
            if level >= 5:
                character.multi_attack_bonus = 1  # 2 total attacks

        elif class_name == "ranger" and level >= 5:
            # Rangers get Extra Attack at level 5
            character.multi_attack_bonus = 1  # 2 total attacks

        # Store reference to know abilities are applied
        character.has_class_abilities = True

    # 🆕 PHASE 1: Apply Racial Traits automatically
    if apply_racial_traits:
        from ..mechanics.racial_traits import RacialTraits

        # Store racial traits manager
        character.racial_traits_manager = race_name

        # Apply automatic benefits based on race
        if race_name in ["elf", "half-elf"]:
            RacialTraits.apply_darkvision(character, 60)
            RacialTraits.apply_fey_ancestry(character)
            if race_name == "elf":
                RacialTraits.apply_trance(character)
                RacialTraits.apply_keen_senses(character)

        elif race_name == "dwarf":
            RacialTraits.apply_darkvision(character, 60)
            RacialTraits.apply_dwarven_resilience(character)
            RacialTraits.apply_stonecunning(character)
            RacialTraits.apply_dwarven_toughness(character)

        elif race_name == "halfling":
            RacialTraits.apply_lucky(character)
            RacialTraits.apply_brave(character)
            RacialTraits.apply_halfling_nimbleness(character)

        elif race_name == "gnome":
            RacialTraits.apply_darkvision(character, 60)
            RacialTraits.apply_gnome_cunning(character)

        elif race_name == "half-orc":
            RacialTraits.apply_darkvision(character, 60)
            RacialTraits.apply_relentless_endurance(character)
            RacialTraits.apply_savage_attacks(character)

        elif race_name == "tiefling":
            RacialTraits.apply_darkvision(character, 60)
            RacialTraits.apply_hellish_resistance(character)

        elif race_name == "dragonborn":
            # Breath weapon will be applied dynamically
            character.breath_weapon_uses = 1

        # Store reference to know traits are applied
        character.has_racial_traits = True

    return character


def level_up_character(character, new_level: int = None, verbose: bool = True):
    """
    Fait passer un personnage au niveau supérieur en appliquant tous les bénéfices

    Args:
        character: Instance de Character
        new_level: Nouveau niveau (si None, level+1)
        verbose: Afficher les messages

    Returns:
        Character modifié
    """
    if new_level is None:
        new_level = character.level + 1

    if new_level <= character.level:
        if verbose:
            print(f"⚠️  Le personnage est déjà niveau {character.level}")
        return character

    if new_level > 20:
        if verbose:
            print(f"⚠️  Niveau maximum atteint (20)")
        return character

    try:
        from .progression_loader import apply_level_up_benefits

        if verbose:
            print(f"\n🎉 {character.name} passe du niveau {character.level} au niveau {new_level}!")

        # Appliquer les bénéfices
        character.level = new_level
        apply_level_up_benefits(character, new_level)

    except Exception as e:
        if verbose:
            print(f"⚠️  Impossible d'utiliser le système de progression: {e}")
            print(f"   Utilisation du système de base...")

        # Fallback: Augmentation basique
        from random import randint

        hp_gain = randint(1, character.class_type.hit_die) + character.abilities.get_modifier('con')
        hp_gain = max(1, hp_gain)

        character.level = new_level
        character.max_hit_points += hp_gain
        character.hit_points += hp_gain

        if verbose:
            print(f"   ❤️  HP: +{hp_gain} ({character.max_hit_points} total)")

    return character


__all__ = [
    'populate',
    'request_monster',
    'load_monsters_database',
    'simple_character_generator',
    'level_up_character',
]
