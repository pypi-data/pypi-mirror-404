"""
D&D 5e Core - Name Generation
Provides utilities to load character names by race from CSV files
"""
import csv
from typing import Dict, List
from pathlib import Path
from .loader import get_data_directory


def load_names(race_index: str) -> Dict[str, List[str]]:
    """
    Load names for a specific race from CSV file.

    Args:
        race_index: Race index (e.g., 'dwarf', 'elf', 'human', 'tiefling')

    Returns:
        Dictionary with gender as key and list of names as value
        Example: {'male': ['Thorin', 'Balin'], 'female': ['Dís', 'Frerin']}
    """
    names_dict = {}
    names_file = get_data_directory() / 'names' / f'{race_index}.csv'

    if not names_file.exists():
        return names_dict

    with open(names_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if len(row) >= 2:
                gender, name = row[0], row[1]
                if gender not in names_dict:
                    names_dict[gender] = []
                names_dict[gender].append(name)

    return names_dict


def load_human_names() -> Dict[str, Dict[str, List[str]]]:
    """
    Load human names organized by ethnic group and gender from CSV file.

    Returns:
        Nested dictionary: {ethnic: {gender: [names]}}
        Example: {
            'calishite': {'male': ['Aseir', 'Bardeid'], 'female': ['Atala', 'Ceidil']},
            'chondathan': {'male': ['Darvin', 'Dorn'], 'female': ['Arveene', 'Esvele']}
        }
    """
    names_dict = {}
    names_file = get_data_directory() / 'names' / 'human.csv'

    if not names_file.exists():
        return names_dict

    with open(names_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if len(row) >= 3:
                ethnic, gender, name = row[0], row[1], row[2]
                if ethnic not in names_dict:
                    names_dict[ethnic] = {}
                if gender not in names_dict[ethnic]:
                    names_dict[ethnic][gender] = []
                names_dict[ethnic][gender].append(name)

    return names_dict


def load_clan_names(race_index: str) -> List[str]:
    """
    Load clan/family names for races that have them (dwarf, dragonborn, gnome).

    Args:
        race_index: Race index (e.g., 'dwarf', 'dragonborn', 'gnome')

    Returns:
        List of clan/family names
    """
    clan_names = []

    # Try different file naming patterns
    patterns = [
        f'clan_names-{race_index}.csv',
        f'clan_name-{race_index}.csv',
        f'family_name-{race_index}.csv'
    ]

    for pattern in patterns:
        clan_file = get_data_directory() / 'names' / pattern
        if clan_file.exists():
            with open(clan_file, newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    if row:  # Skip empty rows
                        clan_names.append(row[0])
            break

    return clan_names


def load_virtue_names(race_index: str = 'tiefling') -> List[str]:
    """
    Load virtue names for tieflings.

    Args:
        race_index: Race index (default: 'tiefling')

    Returns:
        List of virtue names
    """
    virtue_names = []
    virtue_file = get_data_directory() / 'names' / f'virtue_name-{race_index}.csv'

    if not virtue_file.exists():
        return virtue_names

    with open(virtue_file, newline='', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if row:  # Skip empty rows
                virtue_names.append(row[0])

    return virtue_names
