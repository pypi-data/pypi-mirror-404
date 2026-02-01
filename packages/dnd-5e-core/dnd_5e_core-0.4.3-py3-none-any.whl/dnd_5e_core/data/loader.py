"""
D&D 5e Core - Data Loader
Functions to load D&D 5e data from local JSON files and return entity objects

This module provides functions to load game data (monsters, spells, weapons, armor)
from local JSON files and convert them into proper entity objects (Monster, Spell, etc.)
instead of raw dictionaries.

Example:
    >>> from dnd_5e_core.data import load_monster, load_spell
    >>>
    >>> # Load a monster object
    >>> goblin = load_monster("goblin")
    >>> print(f"{goblin.name} - CR {goblin.challenge_rating}")
    >>>
    >>> # Load a spell object
    >>> fireball = load_spell("fireball")
    >>> print(f"{fireball.name} - Level {fireball.level}")
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.monster import Monster
    from ..spells.spell import Spell
    from ..equipment.weapon import Weapon
    from ..equipment.armor import Armor


# Default data directory (can be overridden)
_DATA_DIR = None


def set_data_directory(path: str):
    """
    Set the data directory path.

    Args:
        path: Path to the data directory containing JSON files
    """
    global _DATA_DIR
    _DATA_DIR = Path(path)


def get_data_directory() -> Path:
    """
    Get the data directory path.

    Returns:
        Path to data directory
    """
    global _DATA_DIR

    if _DATA_DIR is None:
        # Data is always in dnd_5e_core/data (next to this file)
        current_file = Path(__file__)
        _DATA_DIR = current_file.parent

        if not _DATA_DIR.exists() or not _DATA_DIR.is_dir():
            raise FileNotFoundError(
                f"Data directory not found at {_DATA_DIR}. Please use set_data_directory() to specify the path."
            )

    return _DATA_DIR


def load_json_file(category: str, index: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON file from the data directory.

    Args:
        category: Category (e.g., "monsters", "spells", "weapons")
        index: Item index/name (e.g., "goblin", "fireball")

    Returns:
        Dict with data or None on error
    """
    try:
        data_dir = get_data_directory()
        file_path = data_dir / category / f"{index}.json"

        if not file_path.exists():
            # Silently return None for files not found (e.g., magic items in equipment collection)
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data
    except Exception as e:
        # Only print error if DEBUG mode is enabled
        if os.getenv('DEBUG'):
            print(f"Error loading {category}/{index}: {e}")
        return None


def list_json_files(category: str) -> List[str]:
    """
    List all JSON files in a category.

    Args:
        category: Category (e.g., "monsters", "spells")

    Returns:
        List of indices (without .json extension)
    """
    try:
        data_dir = get_data_directory()
        category_dir = data_dir / category

        if not category_dir.exists():
            return []

        return [
            f.stem for f in category_dir.glob("*.json")
            if f.is_file()
        ]
    except Exception as e:
        print(f"Error listing {category}: {e}")
        return []


# ===== Helper Functions to Create Objects from JSON Data =====

def _create_monster_from_data(index: str, data: Dict[str, Any]) -> Optional['Monster']:
    """
    Create a Monster object from JSON data.

    Args:
        index: Monster index
        data: Monster JSON data

    Returns:
        Monster object
    """
    from ..entities.monster import Monster
    from ..abilities.abilities import Abilities
    from ..classes.proficiency import Proficiency, ProfType
    from ..combat.action import Action, ActionType
    from ..combat.damage import Damage
    from ..equipment.weapon import DamageType
    from ..mechanics.dice import DamageDice
    from ..spells.spell import Spell
    from ..spells.spellcaster import SpellCaster
    from ..combat.special_ability import SpecialAbility, AreaOfEffect
    from ..combat.condition_parser import ConditionParser

    # Abilities
    abilities = Abilities(
        str=data.get('strength', 10),
        dex=data.get('dexterity', 10),
        con=data.get('constitution', 10),
        int=data.get('intelligence', 10),
        wis=data.get('wisdom', 10),
        cha=data.get('charisma', 10)
    )

    # Proficiencies
    proficiencies: List[Proficiency] = []
    if 'proficiencies' in data:
        for prof_data in data['proficiencies']:
            prof_index = prof_data['proficiency']['index']
            prof_name = prof_data['proficiency'].get('name', prof_index)

            # Déterminer le type de proficiency
            prof_type = None
            if 'skill' in prof_index:
                prof_type = ProfType.SKILL
            elif 'saving-throw' in prof_index:
                prof_type = ProfType.ST
            elif 'weapon' in prof_index or prof_index in ['simple-weapons', 'martial-weapons']:
                prof_type = ProfType.WEAPON
            elif 'armor' in prof_index or prof_index in ['light-armor', 'medium-armor', 'heavy-armor', 'shields']:
                prof_type = ProfType.ARMOR
            else:
                prof_type = ProfType.OTHER

            prof = Proficiency(
                index=prof_index,
                name=prof_name,
                type=prof_type,
                ref=None,  # Pas de référence spécifique pour les monstres
                value=prof_data.get('value', 0)
            )
            proficiencies.append(prof)

    # Special abilities & Spellcasting
    special_abilities: List[SpecialAbility] = []
    spell_caster: Optional[SpellCaster] = None

    if "special_abilities" in data:
        for special_ability in data['special_abilities']:
            action_name: str = special_ability['name']

            # Spellcasting
            if special_ability['name'] == 'Spellcasting':
                ability: dict = special_ability['spellcasting']
                caster_level = ability['level']
                dc_type = ability['ability']['index']
                dc_value = ability['dc']
                ability_modifier = ability['modifier']
                slots = [s for s in ability['slots'].values()]
                spells: List[Spell] = []

                for spell_dict in ability['spells']:
                    spell_index_name: str = spell_dict['url'].split('/')[3]
                    spell = load_spell(spell_index_name)
                    if spell is not None:
                        spells.append(spell)

                if spells:
                    spell_caster = SpellCaster(
                        level=caster_level,
                        spell_slots=slots,
                        learned_spells=spells,
                        dc_type=dc_type,
                        dc_value=dc_value + ability_modifier,
                        ability_modifier=ability_modifier
                    )

            # Special abilities with damage
            elif 'damage' in special_ability:
                damages: List[Damage] = []
                for damage in special_ability['damage']:
                    if "damage_type" in damage:
                        damage_type = DamageType(
                            index=damage['damage_type']['index'],
                            name=damage['damage_type'].get('name', damage['damage_type']['index']),
                            desc=f"{damage['damage_type']['index']} damage"
                        )

                        damage_dice_str = damage['damage_dice']
                        if '+' in damage_dice_str:
                            dice_part, bonus = damage_dice_str.split('+')
                            dd = DamageDice(dice_part.strip(), int(bonus))
                        elif '-' in damage_dice_str:
                            dice_part, bonus = damage_dice_str.split('-')
                            dd = DamageDice(dice_part.strip(), -int(bonus))
                        else:
                            dd = DamageDice(damage_dice_str)

                        damages.append(Damage(type=damage_type, dd=dd))

                # Extract DC info
                dc_type = None
                dc_value = None
                dc_success = None
                if 'dc' in special_ability:
                    dc_type = special_ability['dc']['dc_type']['index']
                    dc_value = special_ability['dc']['dc_value']
                    dc_success = special_ability['dc'].get('success_type')

                # Area of effect
                area_of_effect: Optional[AreaOfEffect] = None
                if 'area_of_effect' in special_ability:
                    aoe_data = special_ability['area_of_effect']
                    area_of_effect = AreaOfEffect(
                        type=aoe_data.get('type', 'sphere'),
                        size=aoe_data.get('size', 15)
                    )

                if damages:
                    special_abilities.append(SpecialAbility(
                        name=action_name,
                        desc=special_ability.get('desc', ''),
                        damages=damages,
                        dc_type=dc_type,
                        dc_value=dc_value,
                        dc_success=dc_success,
                        recharge_on_roll=None,
                        area_of_effect=area_of_effect
                    ))

    # Actions
    actions: List[Action] = []

    if "actions" in data:
        for action in data['actions']:
            # Skip Multiattack for now (will handle separately)
            if action['name'] != 'Multiattack':
                if "damage" in action:
                    normal_range = long_range = 5
                    is_melee_attack = re.search("Melee.*Attack", action.get('desc', ''))
                    is_ranged_attack = re.search("Ranged.*Attack", action.get('desc', ''))

                    # Extract range for ranged attacks
                    if is_ranged_attack:
                        range_pattern = r"range\s+(\d+)/(\d+)\s*ft\."
                        match = re.search(range_pattern, action.get('desc', ''))
                        if match:
                            normal_range = int(match.group(1))
                            long_range = int(match.group(2))
                        else:
                            normal_range = 5
                            long_range = None

                    damages: List[Damage] = []
                    for damage in action['damage']:
                        if "damage_type" in damage:
                            damage_type = DamageType(
                                index=damage['damage_type']['index'],
                                name=damage['damage_type'].get('name', damage['damage_type']['index']),
                                desc=f"{damage['damage_type']['index']} damage"
                            )
                            dd = DamageDice(damage['damage_dice'])
                            damages.append(Damage(type=damage_type, dd=dd))

                    if damages:
                        action_type = ActionType.MIXED if is_melee_attack and is_ranged_attack else ActionType.MELEE if is_melee_attack else ActionType.RANGED

                        # Parse conditions from action description
                        conditions = ConditionParser.extract_conditions_from_action(action, None)

                        actions.append(Action(
                            name=action['name'],
                            desc=action.get('desc', ''),
                            type=action_type,
                            normal_range=normal_range,
                            long_range=long_range,
                            attack_bonus=action.get('attack_bonus'),
                            multi_attack=None,
                            damages=damages,
                            effects=conditions if conditions else None
                        ))

            # Handle special abilities with DC
            elif 'dc' in action:
                if 'damage' in action:
                    damages: List[Damage] = []
                    for damage in action['damage']:
                        if "damage_type" in damage:
                            damage_type = DamageType(
                                index=damage['damage_type']['index'],
                                name=damage['damage_type'].get('name', damage['damage_type']['index']),
                                desc=f"{damage['damage_type']['index']} damage"
                            )
                            dd = DamageDice(damage['damage_dice'])
                            damages.append(Damage(type=damage_type, dd=dd))

                    dc_type = action['dc']['dc_type']['index']
                    dc_value = action['dc']['dc_value']
                    dc_success = action['dc'].get('success_type')

                    # Extract recharge info
                    recharge_on_roll = None
                    if 'usage' in action and 'dice' in action['usage']:
                        recharge_on_roll = action['usage']['min_value']

                    if damages:
                        special_abilities.append(SpecialAbility(
                            name=action['name'],
                            desc=action.get('desc', ''),
                            damages=damages,
                            dc_type=dc_type,
                            dc_value=dc_value,
                            dc_success=dc_success,
                            recharge_on_roll=recharge_on_roll,
                            area_of_effect=None
                        ))

        # Handle Multiattack
        for action in data['actions']:
            if action['name'] == 'Multiattack' and 'options' in action:
                multi_attack: List[Action] = []
                choose_count = action['options']['choose']

                for action_dict in action['options']['from'][0]:
                    try:
                        count = int(action_dict['count'])
                        action_match = next((a for a in actions if a.name == action_dict['name']), None)
                        if action_match and action_match.type in {ActionType.MELEE, ActionType.RANGED}:
                            multi_attack.extend([action_match] * count)
                    except (ValueError, KeyError):
                        if os.getenv('DEBUG'):
                            print(f"Invalid count option for {index}: {action_dict.get('name')}")

                if multi_attack:
                    actions.append(Action(
                        name=action['name'],
                        desc=action.get('desc', ''),
                        type=ActionType.MELEE,
                        attack_bonus=0,  # Multiattack uses the sub-actions' bonuses
                        multi_attack=multi_attack,
                        damages=None
                    ))

    # Speed
    speed_data = data.get('speed', {})
    speed_str = speed_data.get('fly') or speed_data.get('walk') or '30 ft.'
    speed = int(speed_str.split()[0])

    # Source (extended monsters have this field)
    source = data.get('source', None)

    # Create Monster
    return Monster(
        index=index,
        name=data['name'],
        abilities=abilities,
        proficiencies=proficiencies,
        armor_class=data.get('armor_class', 10),
        hit_points=data.get('hit_points', 1),
        hit_dice=data.get('hit_dice', '1d8'),
        xp=data.get('xp', 0),
        speed=speed,
        challenge_rating=parse_challenge_rating(data.get('challenge_rating', 0)),
        actions=actions,
        sc=spell_caster,
        sa=special_abilities if special_abilities else None,
        source=source
    )


def _create_spell_from_data(index: str, data: Dict[str, Any]) -> Optional['Spell']:
    """
    Create a Spell object from JSON data.

    Args:
        index: Spell index
        data: Spell JSON data

    Returns:
        Spell object
    """
    from ..spells.spell import Spell
    from ..equipment.weapon import DamageType
    from ..combat.special_ability import AreaOfEffect

    # Damage (if applicable)
    damage_type = None
    damage_at_slot_level = None
    damage_at_character_level = None

    if 'damage' in data:
        if 'damage_type' in data['damage']:
            damage_type = DamageType(
                index=data['damage']['damage_type']['index'],
                name=data['damage']['damage_type'].get('name', data['damage']['damage_type']['index']),
                desc=f"{data['damage']['damage_type']['index']} damage"
            )

        if 'damage_at_slot_level' in data['damage']:
            damage_at_slot_level = data['damage']['damage_at_slot_level']

        if 'damage_at_character_level' in data['damage']:
            damage_at_character_level = data['damage']['damage_at_character_level']

    # Healing
    heal_at_slot_level = None
    if 'heal_at_slot_level' in data:
        heal_at_slot_level = data['heal_at_slot_level']

    # DC info
    dc_type = None
    dc_success = None
    if 'dc' in data:
        dc_type = data['dc']['dc_type']['index']
        dc_success = data['dc'].get('dc_success')

    # Area of effect
    area_of_effect = None
    if 'area_of_effect' in data:
        aoe_data = data['area_of_effect']
        area_of_effect = AreaOfEffect(
            type=aoe_data.get('type', 'sphere'),
            size=aoe_data.get('size', 15)
        )

    # Range
    range_value = data.get('range', 'Self')
    if isinstance(range_value, str):
        # Extract number from strings like "120 feet" or "Self"
        import re
        match = re.search(r'(\d+)', range_value)
        range_ft = int(match.group(1)) if match else 0
    else:
        range_ft = int(range_value)

    # 🆕 Parse defensive/buff spell properties
    duration = data.get('duration')
    concentration = data.get('concentration', 'False').lower() == 'true'

    # Parse description for defensive bonuses
    desc_text = ' '.join(data.get('desc', [])).lower()
    ac_bonus = None
    saving_throw_bonus = None

    # Check for AC bonuses (Shield +5, Shield of Faith +2, Mage Armor sets AC)
    if '+5 bonus to ac' in desc_text:
        ac_bonus = 5
    elif '+2 bonus to ac' in desc_text:
        ac_bonus = 2
    elif '+1 bonus to ac' in desc_text:
        ac_bonus = 1
    elif 'base ac becomes 13' in desc_text:  # Mage Armor
        ac_bonus = 3  # Simplified: ~average bonus

    # Check for saving throw bonuses
    if 'bonus to saving throw' in desc_text:
        if '+2' in desc_text:
            saving_throw_bonus = 2
        elif '+1' in desc_text:
            saving_throw_bonus = 1

    return Spell(
        index=index,
        name=data['name'],
        desc='\n'.join(data.get('desc', [])),
        level=data.get('level', 0),
        allowed_classes=[c['index'] for c in data.get('classes', [])],
        heal_at_slot_level=heal_at_slot_level,
        damage_type=damage_type,
        damage_at_slot_level=damage_at_slot_level,
        damage_at_character_level=damage_at_character_level,
        dc_type=dc_type,
        dc_success=dc_success,
        range=range_ft,
        area_of_effect=area_of_effect,
        school=data.get('school', {}).get('index', 'evocation'),
        duration=duration,
        concentration=concentration,
        ac_bonus=ac_bonus,
        saving_throw_bonus=saving_throw_bonus
    )


def _create_race_from_data(index: str, data: Dict[str, Any]) -> Optional['Race']:
    """
    Create a Race object from JSON data.

    Args:
        index: Race index
        data: Race JSON data

    Returns:
        Race object
    """
    from ..races.race import Race
    from ..races.language import Language
    from ..races.trait import Trait
    from ..classes.proficiency import Proficiency, ProfType

    # Ability bonuses
    ability_bonuses = {}
    for bonus in data.get('ability_bonuses', []):
        # Skip if not a dict
        if not isinstance(bonus, dict):
            continue
        # Also check nested structure
        if 'ability_score' in bonus and isinstance(bonus['ability_score'], dict):
            ability_bonuses[bonus['ability_score']['index']] = bonus['bonus']

    # Languages
    languages = []
    for lang_data in data.get('languages', []):
        # Skip if not a dict
        if not isinstance(lang_data, dict):
            continue

        language = Language(
            index=lang_data.get('index', ''),
            name=lang_data.get('name', ''),
            desc=lang_data.get('desc', ''),
            type=lang_data.get('type', 'Standard'),
            typical_speakers=lang_data.get('typical_speakers', []),
            script=lang_data.get('script', '')
        )
        languages.append(language)

    # Traits
    traits = []
    for trait_data in data.get('traits', []):
        # Skip if not a dict
        if not isinstance(trait_data, dict):
            continue

        # Trait desc peut être une liste dans le JSON
        desc_value = trait_data.get('desc', [])
        if isinstance(desc_value, list):
            desc_str = '\n'.join(desc_value)
        else:
            desc_str = str(desc_value)

        trait = Trait(
            index=trait_data.get('index', ''),
            name=trait_data.get('name', ''),
            desc=desc_str
        )
        traits.append(trait)

    # Starting proficiencies
    proficiencies = []
    for prof_data in data.get('starting_proficiencies', []):
        # Skip if not a dict
        if not isinstance(prof_data, dict):
            continue

        prof_index = prof_data.get('index', '')
        prof_name = prof_data.get('name', prof_index)

        # Déterminer le type
        if 'skill' in prof_index:
            prof_type = ProfType.SKILL
        elif 'weapon' in prof_index or prof_index in ['simple-weapons', 'martial-weapons']:
            prof_type = ProfType.WEAPON
        elif 'armor' in prof_index or prof_index in ['light-armor', 'medium-armor', 'heavy-armor', 'shields']:
            prof_type = ProfType.ARMOR
        elif 'tool' in prof_index:
            prof_type = ProfType.TOOLS
        else:
            prof_type = ProfType.OTHER

        prof = Proficiency(
            index=prof_index,
            name=prof_name,
            type=prof_type,
            ref=None
        )
        proficiencies.append(prof)

    # Proficiency options
    proficiency_options = []
    if 'starting_proficiency_options' in data:
        for option_data in data['starting_proficiency_options']:
            # Handle case where option_data might be a string or non-dict
            if not isinstance(option_data, dict):
                continue

            choose = option_data.get('choose', 1)
            from_list = []

            for prof_data in option_data.get('from', []):
                # Also check if prof_data is a dict
                if not isinstance(prof_data, dict):
                    continue

                prof_index = prof_data.get('index', '')
                prof_name = prof_data.get('name', prof_index)

                if 'skill' in prof_index:
                    prof_type = ProfType.SKILL
                else:
                    prof_type = ProfType.OTHER

                prof = Proficiency(
                    index=prof_index,
                    name=prof_name,
                    type=prof_type,
                    ref=None
                )
                from_list.append(prof)

            if from_list:  # Only add if we have proficiencies
                proficiency_options.append((choose, from_list))

    return Race(
        index=index,
        name=data['name'],
        speed=data.get('speed', 30),
        ability_bonuses=ability_bonuses,
        alignment=data.get('alignment', ''),
        age=data.get('age', ''),
        size=data.get('size', 'Medium'),
        size_description=data.get('size_description', ''),
        starting_proficiencies=proficiencies,
        starting_proficiency_options=proficiency_options,
        languages=languages,
        language_desc=data.get('language_desc', ''),
        traits=traits,
        subraces=[]  # Les subraces sont chargées séparément
    )


def _create_class_from_data(index: str, data: Dict[str, Any]) -> Optional['ClassType']:
    """
    Create a ClassType object from JSON data.

    Args:
        index: Class index
        data: Class JSON data

    Returns:
        ClassType object
    """
    from ..classes.class_type import ClassType
    from ..classes.proficiency import Proficiency, ProfType
    from ..abilities.abilities import AbilityType
    from ..equipment.equipment import Inventory

    # Proficiencies
    proficiencies = []
    for prof_data in data.get('proficiencies', []):
        prof_index = prof_data.get('index', '')
        prof_name = prof_data.get('name', prof_index)

        # Déterminer le type
        if 'skill' in prof_index:
            prof_type = ProfType.SKILL
        elif 'saving-throw' in prof_index:
            prof_type = ProfType.ST
        elif 'weapon' in prof_index or prof_index in ['simple-weapons', 'martial-weapons']:
            prof_type = ProfType.WEAPON
        elif 'armor' in prof_index or prof_index in ['light-armor', 'medium-armor', 'heavy-armor', 'shields']:
            prof_type = ProfType.ARMOR
        elif 'tool' in prof_index:
            prof_type = ProfType.TOOLS
        else:
            prof_type = ProfType.OTHER

        prof = Proficiency(
            index=prof_index,
            name=prof_name,
            type=prof_type,
            ref=None
        )
        proficiencies.append(prof)

    # Proficiency choices
    proficiency_choices = []
    if 'proficiency_choices' in data:
        for choice_data in data['proficiency_choices']:
            choose = choice_data.get('choose', 1)
            from_list = []

            for prof_data in choice_data.get('from', []):
                prof_index = prof_data.get('index', '')
                prof_name = prof_data.get('name', prof_index)

                if 'skill' in prof_index:
                    prof_type = ProfType.SKILL
                else:
                    prof_type = ProfType.OTHER

                prof = Proficiency(
                    index=prof_index,
                    name=prof_name,
                    type=prof_type,
                    ref=None
                )
                from_list.append(prof)

            proficiency_choices.append((choose, from_list))

    # Saving throws
    saving_throws = []
    for st_data in data.get('saving_throws', []):
        ability_index = st_data.get('index', '').replace('saving-throw-', '').upper()
        if ability_index in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            saving_throws.append(AbilityType[ability_index])

    # Spellcasting info
    spellcasting_data = data.get('spellcasting', {})
    can_cast = spellcasting_data != {} and spellcasting_data is not None
    spellcasting_level = spellcasting_data.get('level', 0) if can_cast else 0
    spellcasting_ability = spellcasting_data.get('spellcasting_ability', {}).get('index', '') if can_cast else ''

    # Spell slots
    spell_slots = {}
    if can_cast and 'spell_slots_level_1' in data:
        for i in range(1, 10):
            key = f'spell_slots_level_{i}'
            if key in data:
                spell_slots[i] = data[key]

    # Spells known
    spells_known = []
    cantrips_known = []

    return ClassType(
        index=index,
        name=data['name'],
        hit_die=data.get('hit_die', 8),
        proficiency_choices=proficiency_choices,
        proficiencies=proficiencies,
        saving_throws=saving_throws,
        starting_equipment=[],  # Simplified pour l'instant
        starting_equipment_options=[],
        class_levels=[],
        multi_classing=[],
        subclasses=[sc.get('index', '') for sc in data.get('subclasses', [])],
        spellcasting_level=spellcasting_level,
        spellcasting_ability=spellcasting_ability,
        can_cast=can_cast,
        spell_slots=spell_slots,
        spells_known=spells_known,
        cantrips_known=cantrips_known
    )


# ===== Loader Functions =====

def load_monster(index: str) -> Optional['Monster']:
    """
    Load monster data from local JSON file and return a Monster object.

    Args:
        index: Monster index (e.g., "goblin", "ancient-red-dragon")

    Returns:
        Monster object or None
    """
    # Try loading from official monsters first
    data = load_json_file("monsters/official", index)
    is_extended = False

    # Try loading from extended monsters
    if data is None:
        data = load_json_file("monsters/extended", index)
        is_extended = True if data else False

    # If not found, try loading from bestiary-sublist-data.json
    if data is None:
        try:
            data_dir = get_data_directory()
            bestiary_file = data_dir / "monsters" / "bestiary-sublist-data.json"

            if bestiary_file.exists():
                with open(bestiary_file, 'r', encoding='utf-8') as f:
                    bestiary_data = json.load(f)

                # Search for the monster in the bestiary data
                for monster_data in bestiary_data:
                    if monster_data.get('index') == index:
                        data = monster_data
                        break
        except Exception as e:
            if os.getenv('DEBUG'):
                print(f"Error loading monster from bestiary: {e}")

    # Finally, try old-style loading from monsters/ directly
    if data is None:
        data = load_json_file("monsters", index)

    if data is None:
        return None

    # Normalize extended monster format if needed
    if is_extended or (data.get('source') and 'abilities' in data and isinstance(data['abilities'], dict)):
        from .extended_monster_parser import normalize_extended_monster_data
        data = normalize_extended_monster_data(data)

    return _create_monster_from_data(index, data)


def load_spell(index: str) -> Optional['Spell']:
    """
    Load spell data from local JSON file and return a Spell object.

    Args:
        index: Spell index (e.g., "fireball", "magic-missile")

    Returns:
        Spell object or None
    """
    data = load_json_file("spells", index)
    if data is None:
        return None

    return _create_spell_from_data(index, data)


def load_weapon(index: str) -> Optional['Weapon']:
    """
    Load weapon data from local JSON file and return a Weapon object.

    Args:
        index: Weapon index (e.g., "longsword", "dagger")

    Returns:
        Weapon object or None
    """
    data = load_json_file("equipment", index)
    if data is None or data.get('equipment_category', {}).get('index') != 'weapon':
        # Try weapons collection
        data = load_json_file("weapons", index)
        if data is None:
            return None

    from ..equipment.weapon import Weapon, DamageType, WeaponProperty, WeaponRange, RangeType, CategoryType
    from ..equipment.equipment import Cost, EquipmentCategory
    from ..mechanics.dice import DamageDice

    # Damage type
    damage_type = DamageType(
        index='slashing',
        name='Slashing',
        desc='slashing damage'
    )
    if 'damage' in data and 'damage_type' in data['damage']:
        damage_type = DamageType(
            index=data['damage']['damage_type']['index'],
            name=data['damage']['damage_type'].get('name', data['damage']['damage_type']['index']),
            desc=f"{data['damage']['damage_type']['index']} damage"
        )

    # Range
    weapon_range = None
    if 'range' in data:
        normal_range = data['range'].get('normal', 5)
        long_range = data['range'].get('long')
        weapon_range = WeaponRange(normal=normal_range, long=long_range)

    # Properties
    properties = []
    for prop_data in data.get('properties', []):
        prop = WeaponProperty(
            index=prop_data.get('index', ''),
            name=prop_data.get('name', prop_data.get('index', '')),
            desc=prop_data.get('desc', '')
        )
        properties.append(prop)

    # Range type and category type
    weapon_range_str = data.get('weapon_range', 'Melee')
    range_type = RangeType.RANGED if weapon_range_str == 'Ranged' else RangeType.MELEE

    weapon_category_str = data.get('weapon_category', 'Simple')
    category_type = CategoryType.MARTIAL if weapon_category_str == 'Martial' else CategoryType.SIMPLE

    # Damage dice
    damage_dice = DamageDice(data.get('damage', {}).get('damage_dice', '1d4'))

    # Two-handed damage (if versatile)
    damage_dice_two_handed = None
    if '2h_damage' in data:
        damage_dice_two_handed = DamageDice(data['2h_damage'].get('damage_dice', '1d4'))

    return Weapon(
        index=index,
        name=data['name'],
        desc=data.get('desc') if isinstance(data.get('desc'), list) else None,
        category=EquipmentCategory(
            index=data.get('equipment_category', {}).get('index', 'weapon'),
            name=data.get('equipment_category', {}).get('name', 'Weapon'),
            url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/weapon')
        ),
        cost=Cost(
            quantity=data.get('cost', {}).get('quantity', 0),
            unit=data.get('cost', {}).get('unit', 'gp')
        ),
        weight=data.get('weight', 0),
        equipped=False,
        properties=properties,
        damage_type=damage_type,
        range_type=range_type,
        category_type=category_type,
        damage_dice=damage_dice,
        damage_dice_two_handed=damage_dice_two_handed,
        weapon_range=weapon_range
    )


def load_armor(index: str) -> Optional['Armor']:
    """
    Load armor data from local JSON file and return an Armor object.

    Args:
        index: Armor index (e.g., "plate-armor", "chain-mail")

    Returns:
        Armor object or None
    """
    data = load_json_file("equipment", index)
    if data is None or data.get('equipment_category', {}).get('index') != 'armor':
        # Try armors collection
        data = load_json_file("armors", index)
        if data is None:
            return None

    from ..equipment.armor import Armor
    from ..equipment.equipment import Cost, EquipmentCategory

    # AC info
    armor_class = data.get('armor_class', {'base': 10})

    # Strength requirement
    str_minimum = data.get('str_minimum', 0)

    # Stealth disadvantage
    stealth_disadvantage = data.get('stealth_disadvantage', False)

    return Armor(
        index=index,
        name=data['name'],
        desc=data.get('desc') if isinstance(data.get('desc'), list) else None,
        category=EquipmentCategory(
            index=data.get('equipment_category', {}).get('index', 'armor'),
            name=data.get('equipment_category', {}).get('name', 'Armor'),
            url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/armor')
        ),
        cost=Cost(
            quantity=data.get('cost', {}).get('quantity', 0),
            unit=data.get('cost', {}).get('unit', 'gp')
        ),
        weight=data.get('weight', 0),
        equipped=False,
        armor_class=armor_class,
        str_minimum=str_minimum,
        stealth_disadvantage=stealth_disadvantage
    )


def load_magic_item(index: str) -> Optional['MagicItem']:
    """
    Load magic item data from local JSON file.

    Args:
        index: Magic item index (e.g., "bag-of-holding", "flame-tongue")

    Returns:
        MagicItem object or None
    """
    # Load from local JSON file in dnd_5e_core/data/magic-items
    data = load_json_file("magic-items", index)

    if data is None:
        return None

    # Create MagicItem
    from ..equipment.magic_item import MagicItem, MagicItemRarity, MagicItemType
    from ..equipment.equipment import Cost, EquipmentCategory

    # Parse rarity
    rarity = MagicItemRarity.COMMON
    if 'rarity' in data:
        rarity_str = data['rarity'].get('name', 'common').lower()
        try:
            rarity = MagicItemRarity(rarity_str)
        except ValueError:
            rarity = MagicItemRarity.COMMON

    # Parse type
    item_type = MagicItemType.WONDROUS
    category_idx = data.get('equipment_category', {}).get('index', 'wondrous-items')
    if 'weapon' in category_idx:
        item_type = MagicItemType.WEAPON
    elif 'armor' in category_idx:
        item_type = MagicItemType.ARMOR
    elif 'potion' in category_idx:
        item_type = MagicItemType.POTION
    elif 'ring' in category_idx:
        item_type = MagicItemType.RING
    elif 'wand' in category_idx:
        item_type = MagicItemType.WAND
    elif 'staff' in category_idx or 'rod' in category_idx:
        item_type = MagicItemType.STAFF

    # Create basic magic item
    return MagicItem(
        index=index,
        name=data['name'],
        cost=Cost(quantity=0, unit='gp'),  # Magic items don't have standard costs
        weight=data.get('weight', 0),
        desc=data.get('desc', []),
        category=EquipmentCategory(
            index=category_idx,
            name=data.get('equipment_category', {}).get('name', 'Magic Items'),
            url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/magic-items')
        ),
        equipped=False,
        rarity=rarity,
        requires_attunement=data.get('requires_attunement', False),
        item_type=item_type,
        effects=[],  # TODO: Parse effects from description
        actions=[]   # TODO: Parse actions from description
    )


def list_magic_items() -> List[str]:
    """
    Get list of all available magic items from local JSON files.

    Returns:
        List of magic item indices
    """
    # Load from local JSON files in dnd_5e_core/data/magic-items
    return list_json_files("magic-items")


def load_race(index: str) -> Optional['Race']:
    """
    Load race data from local JSON file and return a Race object.

    Args:
        index: Race index (e.g., "elf", "dwarf", "human")

    Returns:
        Race object or None
    """
    data = load_json_file("races", index)
    if data is None:
        return None

    return _create_race_from_data(index, data)


def load_class(index: str) -> Optional['ClassType']:
    """
    Load class data from local JSON file and return a ClassType object.

    Args:
        index: Class index (e.g., "fighter", "wizard", "rogue")

    Returns:
        ClassType object or None
    """
    data = load_json_file("classes", index)
    if data is None:
        return None

    return _create_class_from_data(index, data)


def load_equipment(index: str):
    """
    Load equipment data from local JSON file and return appropriate object.

    Returns Weapon, Armor, or Equipment object depending on equipment category.

    Args:
        index: Equipment index

    Returns:
        Weapon, Armor, or Equipment object, or None
    """
    data = load_json_file("equipment", index)
    if data is None:
        return None

    # Déterminer le type d'équipement
    category = data.get('equipment_category', {}).get('index', '')

    if category == 'weapon':
        return load_weapon(index)
    elif category == 'armor':
        return load_armor(index)
    else:
        # Pour les autres équipements, retourner un objet Equipment basique
        from ..equipment.equipment import Equipment, Cost, EquipmentCategory

        return Equipment(
            index=index,
            name=data['name'],
            cost=Cost(
                quantity=data.get('cost', {}).get('quantity', 0),
                unit=data.get('cost', {}).get('unit', 'gp')
            ),
            weight=data.get('weight', 0),
            desc=data.get('desc') if isinstance(data.get('desc'), list) else None,
            category=EquipmentCategory(
                index=data.get('equipment_category', {}).get('index', 'adventuring-gear'),
                name=data.get('equipment_category', {}).get('name', 'Adventuring Gear'),
                url=data.get('equipment_category', {}).get('url', '/api/equipment-categories/adventuring-gear')
            ),
            equipped=False
        )


def list_monsters() -> List[str]:
    """
    Get list of all available monsters from local files.

    Returns:
        List of monster indices
    """
    return list_json_files("monsters")


def list_spells() -> List[str]:
    """
    Get list of all available spells from local files.

    Returns:
        List of spell indices
    """
    return list_json_files("spells")


def list_equipment() -> List[str]:
    """
    Get list of all available equipment from local files.

    Returns:
        List of equipment indices
    """
    return list_json_files("equipment")


def list_weapons() -> List[str]:
    """
    Get list of all available weapons from local files.

    Returns:
        List of weapon indices
    """
    return list_json_files("weapons")


def list_armors() -> List[str]:
    """
    Get list of all available armors from local files.

    Returns:
        List of armor indices
    """
    return list_json_files("armors")


def list_races() -> List[str]:
    """
    Get list of all available races from local files.

    Returns:
        List of race indices
    """
    return list_json_files("races")


def list_classes() -> List[str]:
    """
    Get list of all available classes from local files.

    Returns:
        List of class indices
    """
    return list_json_files("classes")


def load_damage_type(index: str) -> Optional['DamageType']:
    """
    Load damage type data from local JSON file.

    Args:
        index: Damage type index (e.g., "fire", "slashing", "poison")

    Returns:
        DamageType object or None
    """
    data = load_json_file("damage-types", index)
    if data is None:
        return None

    from ..equipment.weapon import DamageType
    return DamageType(
        index=data['index'],
        name=data['name'],
        desc='\n'.join(data.get('desc', [])) if isinstance(data.get('desc'), list) else data.get('desc', '')
    )


def load_condition(index: str) -> Optional['Condition']:
    """
    Load condition data from local JSON file.

    Args:
        index: Condition index (e.g., "blinded", "poisoned", "stunned")

    Returns:
        Condition object or None
    """
    data = load_json_file("conditions", index)
    if data is None:
        return None

    from ..combat.condition import Condition
    return Condition(
        index=data['index'],
        name=data['name'],
        desc='\n'.join(data.get('desc', [])) if isinstance(data.get('desc'), list) else data.get('desc', '')
    )


def load_trait(index: str) -> Optional['Trait']:
    """
    Load trait data from local JSON file.

    Args:
        index: Trait index (e.g., "darkvision", "fey-ancestry")

    Returns:
        Trait object or None
    """
    data = load_json_file("traits", index)
    if data is None:
        return None

    from ..races.trait import Trait
    return Trait(
        index=data['index'],
        name=data['name'],
        desc='\n'.join(data.get('desc', [])) if isinstance(data.get('desc'), list) else data.get('desc', '')
    )


def load_subrace(index: str) -> Optional['SubRace']:
    """
    Load subrace data from local JSON file.

    Args:
        index: Subrace index (e.g., "high-elf", "hill-dwarf")

    Returns:
        SubRace object or None
    """
    data = load_json_file("subraces", index)
    if data is None:
        return None

    from ..races.subrace import SubRace
    from ..classes.proficiency import Proficiency, ProfType

    # Parse ability bonuses
    ability_bonuses = {}
    for bonus in data.get('ability_bonuses', []):
        if isinstance(bonus, dict) and 'ability_score' in bonus:
            ability_bonuses[bonus['ability_score']['index']] = bonus['bonus']

    # Load starting proficiencies
    starting_proficiencies = []
    for prof_data in data.get('starting_proficiencies', []):
        if isinstance(prof_data, dict):
            prof_index = prof_data.get('index', '')
            prof_name = prof_data.get('name', prof_index)

            # Determine type
            if 'skill' in prof_index:
                prof_type = ProfType.SKILL
            elif 'weapon' in prof_index:
                prof_type = ProfType.WEAPON
            elif 'armor' in prof_index:
                prof_type = ProfType.ARMOR
            else:
                prof_type = ProfType.OTHER

            prof = Proficiency(
                index=prof_index,
                name=prof_name,
                type=prof_type,
                ref=None
            )
            starting_proficiencies.append(prof)

    # Load racial traits
    racial_traits = []
    for trait_data in data.get('racial_traits', []):
        if isinstance(trait_data, dict):
            trait = load_trait(trait_data.get('index', ''))
            if trait:
                racial_traits.append(trait)

    return SubRace(
        index=data['index'],
        name=data['name'],
        desc=data.get('desc', ''),
        ability_bonuses=ability_bonuses,
        starting_proficiencies=starting_proficiencies,
        racial_traits=racial_traits
    )


def load_language(index: str) -> Optional['Language']:
    """
    Load language data from local JSON file.

    Args:
        index: Language index (e.g., "common", "elvish", "dwarvish")

    Returns:
        Language object or None
    """
    data = load_json_file("languages", index)
    if data is None:
        return None

    from ..races.language import Language
    return Language(
        index=data['index'],
        name=data['name'],
        desc=data.get('desc', ''),
        type=data.get('type', ''),
        typical_speakers=data.get('typical_speakers', []),
        script=data.get('script', '')
    )


def load_proficiency(index: str) -> Optional['Proficiency']:
    """
    Load proficiency data from local JSON file.

    Args:
        index: Proficiency index (e.g., "skill-perception", "armor-light")

    Returns:
        Proficiency object or None
    """
    data = load_json_file("proficiencies", index)
    if data is None:
        return None

    from ..classes.proficiency import Proficiency, ProfType
    from ..abilities.abilities import AbilityType

    # Parse type
    prof_type_str = data.get('type', 'other')
    try:
        prof_type = ProfType(prof_type_str)
    except ValueError:
        prof_type = ProfType.OTHER

    # Parse reference (if available)
    ref = None
    if 'reference' in data:
        ref_url = data['reference'].get('url', '')
        if ref_url:
            parts = ref_url.split('/')
            if len(parts) >= 4:
                category = parts[2]
                ref_index = parts[3]

                if category == 'equipment':
                    ref = load_equipment(ref_index)
                elif category == 'equipment-categories':
                    ref = load_equipment_category(ref_index)
                elif category == 'ability-scores':
                    try:
                        ref = AbilityType(ref_index.upper())
                    except ValueError:
                        pass

    # Parse classes and races
    classes = [c['index'] for c in data.get('classes', []) if isinstance(c, dict)]
    races = [r['index'] for r in data.get('races', []) if isinstance(r, dict)]

    return Proficiency(
        index=data['index'],
        name=data['name'],
        type=prof_type,
        ref=ref,
        classes=classes,
        races=races
    )


def load_weapon_property(index: str) -> Optional['WeaponProperty']:
    """
    Load weapon property data from local JSON file.

    Args:
        index: Weapon property index (e.g., "finesse", "versatile", "two-handed")

    Returns:
        WeaponProperty object or None
    """
    data = load_json_file("weapon-properties", index)
    if data is None:
        return None

    from ..equipment.weapon import WeaponProperty
    return WeaponProperty(
        index=data['index'],
        name=data['name'],
        desc='\n'.join(data.get('desc', [])) if isinstance(data.get('desc'), list) else data.get('desc', '')
    )


def load_equipment_category(index: str) -> Optional['EquipmentCategory']:
    """
    Load equipment category data from local JSON file.

    Args:
        index: Equipment category index (e.g., "weapon", "armor", "adventuring-gear")

    Returns:
        EquipmentCategory object or None
    """
    data = load_json_file("equipment-categories", index)
    if data is None:
        return None

    from ..equipment.equipment import EquipmentCategory
    return EquipmentCategory(
        index=data['index'],
        name=data['name'],
        url=data.get('url', f'/api/equipment-categories/{index}')
    )


def list_damage_types() -> List[str]:
    """
    Get list of all available damage types from local files.

    Returns:
        List of damage type indices
    """
    return list_json_files("damage-types")


def list_conditions() -> List[str]:
    """
    Get list of all available conditions from local files.

    Returns:
        List of condition indices
    """
    return list_json_files("conditions")


def list_traits() -> List[str]:
    """
    Get list of all available traits from local files.

    Returns:
        List of trait indices
    """
    return list_json_files("traits")


def list_subraces() -> List[str]:
    """
    Get list of all available subraces from local files.

    Returns:
        List of subrace indices
    """
    return list_json_files("subraces")


def list_languages() -> List[str]:
    """
    Get list of all available languages from local files.

    Returns:
        List of language indices
    """
    return list_json_files("languages")


def list_proficiencies() -> List[str]:
    """
    Get list of all available proficiencies from local files.

    Returns:
        List of proficiency indices
    """
    return list_json_files("proficiencies")


def list_weapon_properties() -> List[str]:
    """
    Get list of all available weapon properties from local files.

    Returns:
        List of weapon property indices
    """
    return list_json_files("weapon-properties")


def list_equipment_categories() -> List[str]:
    """
    Get list of all available equipment categories from local files.

    Returns:
        List of equipment category indices
    """
    return list_json_files("equipment-categories")


def clear_cache():
    """
    Note: No cache needed when using local files.
    This function is kept for API compatibility.
    """
    print("No cache to clear (using local JSON files)")



# ===== Helper Functions =====

def parse_dice_notation(dice_str: str) -> tuple[int, int, int]:
    """
    Parse D&D dice notation.

    Args:
        dice_str: Dice string (e.g., "2d6+3", "1d8")

    Returns:
        Tuple of (dice_count, dice_sides, bonus)
    """
    import re

    # Match pattern like "2d6+3" or "1d8-2"
    match = re.match(r'(\d+)d(\d+)([+\-]\d+)?', dice_str)
    if match:
        dice_count = int(match.group(1))
        dice_sides = int(match.group(2))
        bonus = int(match.group(3)) if match.group(3) else 0
        return dice_count, dice_sides, bonus

    return 1, 6, 0  # Default


def parse_challenge_rating(cr_value: Any) -> float:
    """
    Parse challenge rating value.

    Args:
        cr_value: CR value (can be float, int, or fraction string)

    Returns:
        Float CR value
    """
    if isinstance(cr_value, (int, float)):
        return float(cr_value)

    if isinstance(cr_value, str):
        if '/' in cr_value:
            # Fraction like "1/2", "1/4"
            num, denom = cr_value.split('/')
            return float(num) / float(denom)
        return float(cr_value)

    return 0.0


# ===== Example Usage =====

if __name__ == "__main__":
    # Note: Data directory is auto-detected from dnd-5e-core/data
    # No need to call set_data_directory() unless you have a custom location

    # Example: Load goblin
    goblin_data = load_monster("goblin")
    if goblin_data:
        print(f"Loaded: {goblin_data.name}")
        print(f"CR: {goblin_data.challenge_rating}")
        print(f"HP: {goblin_data.hit_points}")

    # Example: List all monsters
    monsters = list_monsters()
    print(f"\nTotal monsters available: {len(monsters)}")
    print(f"First 5: {monsters[:5]}")

    # Example: Load fireball spell
    fireball_data = load_spell("fireball")
    if fireball_data:
        print(f"\nLoaded spell: {fireball_data.name}")
        print(f"Level: {fireball_data.level}")
