"""
D&D 5e Core - Collection Loader
Functions to load D&D 5e API collection indexes from local JSON files
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


# Default collections directory
_COLLECTIONS_DIR = None


def set_collections_directory(path: str):
    """
    Set the collections directory path.

    Args:
        path: Path to the collections directory containing JSON files
    """
    global _COLLECTIONS_DIR
    _COLLECTIONS_DIR = Path(path)


def get_collections_directory() -> Path:
    """
    Get the collections directory path.

    Returns:
        Path to collections directory
    """
    global _COLLECTIONS_DIR

    if _COLLECTIONS_DIR is None:
        # Try to find collections directory automatically
        current_file = Path(__file__)

        # Try common locations
        possible_paths = [
            # If collections is inside the dnd_5e_core/data package (preferred for distribution)
            current_file.parent / "collections",
            # If collections is in the dnd-5e-core package project root (for dev)
            current_file.parent.parent.parent / "collections",
            # If used from DnD-5th-Edition-API project (fallback)
            current_file.parent.parent.parent.parent.parent / "DnD-5th-Edition-API" / "collections",
            # If collections is in current working directory
            Path.cwd() / "collections",
        ]

        for path in possible_paths:
            if path.exists() and path.is_dir():
                _COLLECTIONS_DIR = path
                break
        else:
            raise FileNotFoundError(
                f"Collections directory not found. Tried: {possible_paths}\n"
                f"Use set_collections_directory() to specify the location."
            )

    return _COLLECTIONS_DIR


def load_collection(collection_name: str, collections_path: Optional[str] = None, validate: bool = False, schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a collection index file.

    Args:
        collection_name: Name of the collection (e.g., 'monsters', 'spells')
        collections_path: Optional custom path to collections directory
        validate: If True, validate the loaded JSON against the collections schema (requires `jsonschema`)
        schema_path: Optional explicit path to a JSON Schema file. If not provided, the package `schemas/collections_schema.json` is used when available.

    Returns:
        Dictionary with 'count' and 'results' keys

    Raises:
        FileNotFoundError: If collection file doesn't exist
        RuntimeError: If validate=True but jsonschema is not installed
        ValueError: If validation fails
    """
    if collections_path:
        collections_dir = Path(collections_path)
    else:
        collections_dir = get_collections_directory()

    file_path = collections_dir / f"{collection_name}.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Collection file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Optional validation step
    if validate:
        try:
            import jsonschema
        except Exception:
            raise RuntimeError("jsonschema is required to validate collections; install it with `pip install jsonschema`")

        # Determine schema location
        if schema_path:
            schema_file = Path(schema_path)
        else:
            # Default schema lives in the package 'schemas' directory next to project root
            schema_file = Path(__file__).parent.parent / "schemas" / "collections_schema.json"

        if not schema_file.exists():
            raise FileNotFoundError(f"Collections schema not found: {schema_file}")

        with open(schema_file, "r", encoding="utf-8") as sf:
            schema = json.load(sf)

        try:
            jsonschema.validate(instance=data, schema=schema)
        except Exception as exc:
            # Re-raise as ValueError with the original message for callers
            raise ValueError(f"Collection validation failed for {file_path}: {exc}")

    return data


def populate(collection_name: str, key_name: str = "results",
             with_url: bool = False, collection_path: Optional[str] = None) -> List:
    """
    Load and extract data from a collection file.

    This function maintains compatibility with the original populate() function
    from DnD-5th-Edition-API.

    Args:
        collection_name: Name of the collection file (without .json extension)
        key_name: Key to extract from the JSON (default: 'results')
        with_url: If True, return tuples of (index, url), otherwise just indexes
        collection_path: Optional custom path to collections directory

    Returns:
        List of indexes or (index, url) tuples

    Example:
        >>> monsters = populate('monsters', 'results')
        >>> ['aboleth', 'goblin', ...]
        >>>
        >>> monsters_with_urls = populate('monsters', 'results', with_url=True)
        >>> [('aboleth', '/api/monsters/aboleth'), ...]
    """
    data = load_collection(collection_name, collection_path)

    collection_json_list = data.get(key_name, [])

    if with_url:
        data_list = [(json_data['index'], json_data['url'])
                     for json_data in collection_json_list]
    else:
        data_list = [json_data['index'] for json_data in collection_json_list]

    return data_list


def get_collection_count(collection_name: str, collection_path: Optional[str] = None) -> int:
    """
    Get the count of items in a collection.

    Args:
        collection_name: Name of the collection
        collection_path: Optional custom path to collections directory

    Returns:
        Number of items in the collection
    """
    data = load_collection(collection_name, collection_path)
    return data.get('count', 0)


def get_collection_item(collection_name: str, index: str,
                        collection_path: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get a specific item from a collection by its index.

    Args:
        collection_name: Name of the collection
        index: Index/slug of the item to find
        collection_path: Optional custom path to collections directory

    Returns:
        Dictionary with 'index', 'name', and 'url' keys, or None if not found
    """
    data = load_collection(collection_name, collection_path)
    results = data.get('results', [])

    for item in results:
        if item['index'] == index:
            return item

    return None


def list_all_collections(collections_path: Optional[str] = None) -> List[str]:
    """
    List all available collection files.

    Args:
        collections_path: Optional custom path to collections directory

    Returns:
        List of collection names (without .json extension)
    """
    if collections_path:
        collections_dir = Path(collections_path)
    else:
        collections_dir = get_collections_directory()

    collection_files = sorted(collections_dir.glob("*.json"))
    return [f.stem for f in collection_files if f.name != "README.md"]


# Convenience functions for common collections (return indexes)

def get_monsters_list(with_url: bool = False) -> List:
    """
    Get list of all monster indexes.

    Args:
        with_url: If True, return tuples of (index, url)

    Returns:
        List of monster indexes or (index, url) tuples
    """
    return populate('monsters', 'results', with_url=with_url)


def get_spells_list(with_url: bool = False) -> List:
    """
    Get list of all spell indexes.

    Args:
        with_url: If True, return tuples of (index, url)

    Returns:
        List of spell indexes or (index, url) tuples
    """
    return populate('spells', 'results', with_url=with_url)


def get_classes_list(with_url: bool = False) -> List:
    """Get list of all class indexes."""
    return populate('classes', 'results', with_url=with_url)


def get_races_list(with_url: bool = False) -> List:
    """Get list of all race indexes."""
    return populate('races', 'results', with_url=with_url)


def get_equipment_list(with_url: bool = False) -> List:
    """Get list of all equipment indexes."""
    return populate('equipment', 'results', with_url=with_url)


def get_weapons_list(with_url: bool = False) -> List:
    """Get list of all weapon indexes."""
    return populate('weapons', 'results', with_url=with_url)


def get_armors_list(with_url: bool = False) -> List:
    """Get list of all armor indexes."""
    return populate('armors', 'results', with_url=with_url)


def get_magic_items_list(with_url: bool = False) -> List:
    """Get list of all magic item indexes."""
    return populate('magic-items', 'results', with_url=with_url)


# ===== Object Loading Functions =====
# These functions return actual Monster, Spell, etc. objects instead of indexes

def load_all_monsters() -> List:
    """
    Load all monsters as Monster objects.

    Returns:
        List of Monster objects

    Example:
        >>> monsters = load_all_monsters()
        >>> for monster in monsters:
        ...     print(f"{monster.name} - CR {monster.challenge_rating}")
    """
    from .loader import load_monster

    monster_indexes = get_monsters_list()
    monsters = []

    for index in monster_indexes:
        monster = load_monster(index)
        if monster:
            monsters.append(monster)

    return monsters


def load_all_spells() -> List:
    """
    Load all spells as Spell objects.

    Returns:
        List of Spell objects

    Example:
        >>> spells = load_all_spells()
        >>> for spell in spells:
        ...     print(f"{spell.name} - Level {spell.level}")
    """
    from .loader import load_spell

    spell_indexes = get_spells_list()
    spells = []

    for index in spell_indexes:
        spell = load_spell(index)
        if spell:
            spells.append(spell)

    return spells


def load_all_weapons() -> List:
    """
    Load all weapons as Weapon objects.

    Returns:
        List of Weapon objects

    Example:
        >>> weapons = load_all_weapons()
        >>> for weapon in weapons:
        ...     print(f"{weapon.name} - {weapon.damage_dice}")
    """
    from .loader import load_weapon

    weapon_indexes = get_weapons_list()
    weapons = []

    for index in weapon_indexes:
        weapon = load_weapon(index)
        if weapon:
            weapons.append(weapon)

    return weapons


def load_all_armors() -> List:
    """
    Load all armors as Armor objects.

    Returns:
        List of Armor objects

    Example:
        >>> armors = load_all_armors()
        >>> for armor in armors:
        ...     print(f"{armor.name} - AC {armor.armor_class}")
    """
    from .loader import load_armor

    armor_indexes = get_armors_list()
    armors = []

    for index in armor_indexes:
        armor = load_armor(index)
        if armor:
            armors.append(armor)

    return armors


def filter_monsters(min_cr: float = None, max_cr: float = None,
                    name_contains: str = None) -> List:
    """
    Filter monsters by criteria.

    Args:
        min_cr: Minimum challenge rating
        max_cr: Maximum challenge rating
        name_contains: Filter by name (case-insensitive)

    Returns:
        List of Monster objects matching criteria

    Example:
        >>> # Get all CR 1-5 dragons
        >>> dragons = filter_monsters(min_cr=1, max_cr=5, name_contains="dragon")
    """
    monsters = load_all_monsters()

    if min_cr is not None:
        monsters = [m for m in monsters if m.challenge_rating >= min_cr]

    if max_cr is not None:
        monsters = [m for m in monsters if m.challenge_rating <= max_cr]

    if name_contains is not None:
        name_lower = name_contains.lower()
        monsters = [m for m in monsters if name_lower in m.name.lower()]

    return monsters


def filter_spells(level: int = None, school: str = None,
                  class_name: str = None) -> List:
    """
    Filter spells by criteria.

    Args:
        level: Spell level (0-9, where 0 is cantrip)
        school: School of magic (e.g., "evocation", "abjuration")
        class_name: Class that can cast (e.g., "wizard", "cleric")

    Returns:
        List of Spell objects matching criteria

    Example:
        >>> # Get all wizard cantrips
        >>> cantrips = filter_spells(level=0, class_name="wizard")
    """
    spells = load_all_spells()

    if level is not None:
        spells = [s for s in spells if s.level == level]

    if school is not None:
        school_lower = school.lower()
        spells = [s for s in spells if s.school.lower() == school_lower]

    if class_name is not None:
        class_lower = class_name.lower()
        spells = [s for s in spells if class_lower in s.allowed_classes]

    return spells


if __name__ == "__main__":
    # Example usage - Collections (indexes)
    print("=" * 60)
    print("COLLECTIONS - List of Indexes")
    print("=" * 60)

    print("\nAvailable collections:")
    for collection in list_all_collections():
        count = get_collection_count(collection)
        print(f"  - {collection}: {count} items")

    print("\nExample: First 5 monster indexes:")
    monster_indexes = get_monsters_list()
    for index in monster_indexes[:5]:
        print(f"  - {index}")

    # Example usage - Object Loading
    print("\n" + "=" * 60)
    print("OBJECT LOADING - Monster Objects")
    print("=" * 60)

    print("\nLoading first 5 monsters as objects:")
    monsters = load_all_monsters()[:5]
    for monster in monsters:
        print(f"  - {monster.name}: CR {monster.challenge_rating}, HP {monster.hit_points}")

    print("\n" + "=" * 60)
    print("FILTERING - Search by Criteria")
    print("=" * 60)

    print("\nGoblins and Orcs (CR 0-1):")
    low_cr_monsters = filter_monsters(max_cr=1, name_contains="")
    for monster in low_cr_monsters[:5]:
        print(f"  - {monster.name}: CR {monster.challenge_rating}")

    print("\nWizard Cantrips:")
    wizard_cantrips = filter_spells(level=0, class_name="wizard")
    for spell in wizard_cantrips[:5]:
        print(f"  - {spell.name} ({spell.school})")

