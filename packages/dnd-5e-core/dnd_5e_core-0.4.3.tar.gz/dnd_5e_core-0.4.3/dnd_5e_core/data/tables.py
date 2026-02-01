"""
D&D 5e Core - Table Loading
Provides utilities to load CSV tables for game mechanics
"""
import csv
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from .loader import get_data_directory, load_json_file


def load_table(filename: str) -> List[List[str]]:
    """
    Load a CSV table from the tables directory.

    Args:
        filename: Name of the CSV file (with or without extension)

    Returns:
        List of rows, where each row is a list of values
    """
    if not filename.endswith('.csv'):
        filename += '.csv'

    table_file = get_data_directory() / 'tables' / filename

    if not table_file.exists():
        return []

    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        # Skip header
        next(csv_reader, None)
        return list(csv_reader)


def load_height_weight_table() -> List[Dict[str, str]]:
    """
    Load the height and weight table for character generation.

    Returns:
        List of dictionaries with race height/weight modifiers
        Example: [
            {
                'Race': 'Human',
                'Base Height': "4'8\"",
                'Height Modifier': '2d10',
                'Base Weight': '110 lb.',
                'Weight Modifier': '2d4'
            },
            ...
        ]
    """
    headers = ['Race', 'Base Height', 'Height Modifier', 'Base Weight', 'Weight Modifier']
    table_file = get_data_directory() / 'tables' / 'Height and Weight-Height and Weight.csv'

    if not table_file.exists():
        return []

    result = []
    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            result.append({header: row.get(header, '') for header in headers})

    return result


def load_xp_levels_table() -> Dict[int, int]:
    """
    Load XP requirements for each level.

    Returns:
        Dictionary mapping level to XP required
        Example: {1: 0, 2: 300, 3: 900, ..., 20: 355000}
    """
    table_file = get_data_directory() / 'tables' / 'XP Levels-XP Levels.csv'

    if not table_file.exists():
        return {}

    xp_levels = {}
    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        # Skip header
        next(csv_reader, None)
        for row in csv_reader:
            if len(row) >= 2:
                try:
                    level = int(row[0])
                    xp = int(row[1])
                    xp_levels[level] = xp
                except ValueError:
                    continue

    return xp_levels


def load_spell_slots_table(class_name: str) -> Tuple[Dict[int, List[int]], List[int], List[int]]:
    """
    Load spell slots table for a spellcasting class.

    Args:
        class_name: Name of the class (e.g., 'wizard', 'cleric', 'bard')

    Returns:
        Tuple of (spell_slots_by_level, cantrips_known, spells_known)
        - spell_slots_by_level: {level: [slot1, slot2, ..., slot9]}
        - cantrips_known: list of cantrips known at each level [level1, level2, ...]
        - spells_known: list of spells known at each level (empty if class uses prepared spells)
    """
    spell_slots = {}
    cantrips = []
    spells = []

    # Try to load from class_levels JSON files
    for level in range(1, 21):
        level_data = load_json_file('class_levels', f'{class_name}-{level}')
        if level_data and 'spellcasting' in level_data:
            spellcasting = level_data['spellcasting']

            # Get spell slots for each level (1-9)
            slots = []
            for i in range(1, 10):
                slot_key = f'spell_slots_level_{i}'
                slots.append(spellcasting.get(slot_key, 0))
            spell_slots[level] = slots

            # Get cantrips known
            cantrips.append(spellcasting.get('cantrips_known', 0))

            # Get spells known (for classes like Bard, Sorcerer)
            spells.append(spellcasting.get('spells_known', 0))

    return spell_slots, cantrips, spells


def load_encounter_difficulty_table() -> List[Dict[str, str]]:
    """
    Load encounter difficulty thresholds by character level.

    Returns:
        List of dictionaries with difficulty thresholds
        Example: [
            {'Level': '1', 'Easy': '25', 'Medium': '50', 'Hard': '75', 'Deadly': '100'},
            ...
        ]
    """
    table_file = get_data_directory() / 'tables' / 'Encounter_Difficulty.csv'

    if not table_file.exists():
        return []

    result = []
    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            result.append(dict(row))

    return result


def load_encounter_levels_table() -> List[Dict[str, str]]:
    """
    Load encounter levels table (monster challenge ratings by dungeon level).

    Returns:
        List of dictionaries with encounter levels
    """
    table_file = get_data_directory() / 'tables' / 'Encounter_Levels.csv'

    if not table_file.exists():
        return []

    result = []
    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            result.append(dict(row))

    return result


def load_encounter_gold_table() -> List[Dict[str, str]]:
    """
    Load encounter gold/treasure table.

    Returns:
        List of dictionaries with gold values by level
    """
    table_file = get_data_directory() / 'tables' / 'Encounter_Gold.csv'

    if not table_file.exists():
        return []

    result = []
    with open(table_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        for row in csv_reader:
            result.append(dict(row))

    return result


def load_combat_table(monster_vs_class: bool = True) -> List[List[str]]:
    """
    Load combat encounter table (monster vs class balance).

    Args:
        monster_vs_class: If True, load "Monster vs class" table

    Returns:
        List of rows from the combat table
    """
    filename = 'Combat (Monster vs Class)-Monster vs class.csv' if monster_vs_class else 'Combat.csv'
    return load_table(filename)


def load_magic_item_table(item_type: str) -> List[List[str]]:
    """
    Load magic item table by type.

    Args:
        item_type: Type of magic item ('Armor', 'Potions', 'Rings', 'Scrolls',
                   'Swords', 'Wands or staffs', 'Misc. Magic', 'Misc. Weapons')

    Returns:
        List of rows from the magic item table
    """
    # Map item types to filenames
    table_files = {
        'armor': 'Armor-Armor.csv',
        'potions': 'Potions-Potions.csv',
        'rings': 'Rings-Rings.csv',
        'scrolls': 'Scrolls-Scrolls.csv',
        'swords': 'Swords-Swords.csv',
        'wands': 'Wands or staffs-Wands or staffs.csv',
        'misc-magic': 'Misc. Magic-Misc. Magic.csv',
        'misc-weapons': 'Misc. Weapons-Misc. Weapons.csv'
    }

    filename = table_files.get(item_type.lower(), f'{item_type}.csv')
    return load_table(filename)


def load_class_spell_table(class_name: str) -> List[List[str]]:
    """
    Load spell list table for a specific class.

    Args:
        class_name: Name of the class ('Bard', 'Cleric', 'Druid', 'Paladin', 'Sorcerer', 'Wizard')

    Returns:
        List of rows from the class spell table
    """
    filename = f'{class_name.capitalize()}-{class_name.capitalize()}.csv'
    return load_table(filename)
