"""
D&D 5e Core - Serialization System
Save and load game data to/from JSON files
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Type, TypeVar, Optional
from datetime import datetime
from enum import Enum

T = TypeVar('T')


class DndJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for D&D 5e objects.
    Handles dataclasses, enums, and other custom types.
    """

    def default(self, obj):
        """Convert special types to JSON-serializable format"""

        # Handle dataclasses
        if is_dataclass(obj):
            return asdict(obj)

        # Handle enums
        if isinstance(obj, Enum):
            return obj.value

        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle Path objects
        if isinstance(obj, Path):
            return str(obj)

        # Handle sets
        if isinstance(obj, set):
            return list(obj)

        # Try default serialization
        try:
            return super().default(obj)
        except TypeError:
            # For objects with __dict__, try to serialize that
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            # Last resort: convert to string
            return str(obj)


def to_json(obj: Any, indent: int = 2) -> str:
    """
    Convert an object to JSON string.

    Args:
        obj: Object to serialize
        indent: Indentation level for pretty printing

    Returns:
        JSON string
    """
    return json.dumps(obj, cls=DndJSONEncoder, indent=indent)


def from_json(json_str: str, target_type: Optional[Type[T]] = None) -> T:
    """
    Parse JSON string to Python object.

    Args:
        json_str: JSON string to parse
        target_type: Optional type to cast to

    Returns:
        Parsed object
    """
    data = json.loads(json_str)

    if target_type and is_dataclass(target_type):
        # Try to reconstruct dataclass
        return target_type(**data)

    return data


def save_to_file(obj: Any, file_path: Path, indent: int = 2):
    """
    Save an object to a JSON file.

    Args:
        obj: Object to save
        file_path: Path to save to
        indent: Indentation for pretty printing
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, cls=DndJSONEncoder, indent=indent)


def load_from_file(file_path: Path, target_type: Optional[Type[T]] = None) -> T:
    """
    Load an object from a JSON file.

    Args:
        file_path: Path to load from
        target_type: Optional type to cast to

    Returns:
        Loaded object
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if target_type and is_dataclass(target_type):
        return target_type(**data)

    return data


def serialize_character(character: 'Character') -> Dict[str, Any]:
    """
    Serialize a Character object to a dictionary.

    Args:
        character: Character to serialize

    Returns:
        Dictionary representation
    """
    from ..entities.character import Character

    if not isinstance(character, Character):
        raise TypeError("Expected Character object")

    # Convert to dict using custom encoder
    char_dict = json.loads(to_json(character))

    # Add metadata
    char_dict['_serialized_at'] = datetime.now().isoformat()
    char_dict['_type'] = 'Character'

    return char_dict


def deserialize_character(data: Dict[str, Any]) -> 'Character':
    """
    Deserialize a Character object from a dictionary.

    Args:
        data: Dictionary representation

    Returns:
        Character object
    """
    from ..entities.character import Character

    # Remove metadata
    data = {k: v for k, v in data.items() if not k.startswith('_')}

    # Reconstruct character
    # Note: This is simplified - full implementation would need to
    # reconstruct nested objects like abilities, class_type, etc.
    return Character(**data)


def serialize_monster(monster: 'Monster') -> Dict[str, Any]:
    """
    Serialize a Monster object to a dictionary.

    Args:
        monster: Monster to serialize

    Returns:
        Dictionary representation
    """
    from ..entities.monster import Monster

    if not isinstance(monster, Monster):
        raise TypeError("Expected Monster object")

    monster_dict = json.loads(to_json(monster))
    monster_dict['_serialized_at'] = datetime.now().isoformat()
    monster_dict['_type'] = 'Monster'

    return monster_dict


def deserialize_monster(data: Dict[str, Any]) -> 'Monster':
    """
    Deserialize a Monster object from a dictionary.

    Args:
        data: Dictionary representation

    Returns:
        Monster object
    """
    from ..entities.monster import Monster

    data = {k: v for k, v in data.items() if not k.startswith('_')}
    return Monster(**data)


def save_character(character: 'Character', file_path: Path):
    """
    Save a character to a file.

    Args:
        character: Character to save
        file_path: Path to save to
    """
    char_data = serialize_character(character)
    save_to_file(char_data, file_path)


def load_character(file_path: Path) -> 'Character':
    """
    Load a character from a file.

    Args:
        file_path: Path to load from

    Returns:
        Character object
    """
    data = load_from_file(file_path)
    return deserialize_character(data)


def save_party(characters: list['Character'], file_path: Path):
    """
    Save a party of characters to a file.

    Args:
        characters: List of characters
        file_path: Path to save to
    """
    party_data = {
        'characters': [serialize_character(char) for char in characters],
        'party_size': len(characters),
        'saved_at': datetime.now().isoformat()
    }
    save_to_file(party_data, file_path)


def load_party(file_path: Path) -> list['Character']:
    """
    Load a party of characters from a file.

    Args:
        file_path: Path to load from

    Returns:
        List of Character objects
    """
    data = load_from_file(file_path)
    return [deserialize_character(char_data) for char_data in data['characters']]


def create_backup(file_path: Path) -> Path:
    """
    Create a backup of a file.

    Args:
        file_path: File to backup

    Returns:
        Path to backup file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".{timestamp}.backup")

    # Copy file content
    backup_path.write_bytes(file_path.read_bytes())

    return backup_path

