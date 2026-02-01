"""
D&D 5e Core - Condition Parser
Parse condition effects from monster actions and magic items
"""
from typing import Optional, Dict, Any, List
import re

from ..combat.condition import (
    Condition,
    create_restrained_condition,
    create_poisoned_condition,
    create_frightened_condition,
    create_grappled_condition,
    create_paralyzed_condition,
    create_stunned_condition,
    create_prone_condition,
    create_blinded_condition,
    create_charmed_condition,
    create_incapacitated_condition
)
from ..abilities import AbilityType


class ConditionParser:
    """
    Parser for extracting condition effects from monster descriptions.

    This class analyzes monster action descriptions to identify and create
    Condition objects that can be applied to characters.
    """

    # Mapping of condition keywords to their creation functions
    CONDITION_CREATORS = {
        'restrained': create_restrained_condition,
        'grappled': create_grappled_condition,
        'poisoned': create_poisoned_condition,
        'paralyzed': create_paralyzed_condition,
        'stunned': create_stunned_condition,
        'frightened': create_frightened_condition,
        'prone': create_prone_condition,
        'blinded': create_blinded_condition,
        'charmed': create_charmed_condition,
        'incapacitated': create_incapacitated_condition,
    }

    # Regex patterns for extracting DC and ability type
    DC_PATTERN = re.compile(r'DC\s*(\d+)\s*(\w+)', re.IGNORECASE)
    SAVE_PATTERN = re.compile(r'(\w+)\s+saving\s+throw', re.IGNORECASE)

    @classmethod
    def parse_condition_from_description(
        cls,
        description: str,
        monster: Optional[Any] = None
    ) -> List[Condition]:
        """
        Parse condition effects from action description.

        Args:
            description: Action description text
            monster: The monster applying the condition (optional)

        Returns:
            List of Condition objects found in description
        """
        conditions = []
        desc_lower = description.lower()

        # Extract DC information
        dc_match = cls.DC_PATTERN.search(description)
        dc_value = int(dc_match.group(1)) if dc_match else None
        dc_type_str = dc_match.group(2).lower() if dc_match else None

        # Map DC type string to AbilityType
        dc_type = cls._parse_ability_type(dc_type_str) if dc_type_str else None

        # If no DC in format "DC XX", try "XXX saving throw"
        if dc_type is None:
            save_match = cls.SAVE_PATTERN.search(description)
            if save_match:
                dc_type = cls._parse_ability_type(save_match.group(1))

        # Check for each condition keyword
        for condition_name, creator_func in cls.CONDITION_CREATORS.items():
            if condition_name in desc_lower:
                # Create condition with appropriate parameters
                try:
                    if condition_name in ['restrained', 'grappled', 'frightened', 'charmed']:
                        # These conditions reference the source creature
                        condition = creator_func(
                            creature=monster,
                            dc_type=dc_type,
                            dc_value=dc_value
                        )
                    elif condition_name in ['poisoned', 'paralyzed', 'stunned', 'blinded']:
                        # These don't need creature reference
                        condition = creator_func(
                            dc_type=dc_type,
                            dc_value=dc_value
                        )
                    elif condition_name in ['prone', 'incapacitated']:
                        # These don't need DC or creature
                        condition = creator_func()
                    else:
                        continue

                    conditions.append(condition)
                except Exception as e:
                    # If creation fails, skip this condition
                    print(f"Warning: Failed to create {condition_name} condition: {e}")
                    continue

        return conditions

    @classmethod
    def _parse_ability_type(cls, ability_str: str) -> Optional[AbilityType]:
        """
        Parse ability type from string.

        Args:
            ability_str: Ability name (e.g., "strength", "str", "dexterity")

        Returns:
            AbilityType or None
        """
        if not ability_str:
            return None

        ability_lower = ability_str.lower().strip()

        # Map common variations
        ability_map = {
            'str': AbilityType.STR,
            'strength': AbilityType.STR,
            'dex': AbilityType.DEX,
            'dexterity': AbilityType.DEX,
            'con': AbilityType.CON,
            'constitution': AbilityType.CON,
            'int': AbilityType.INT,
            'intelligence': AbilityType.INT,
            'wis': AbilityType.WIS,
            'wisdom': AbilityType.WIS,
            'cha': AbilityType.CHA,
            'charisma': AbilityType.CHA,
        }

        return ability_map.get(ability_lower)

    @classmethod
    def parse_dc_from_action_data(cls, action_data: Dict[str, Any]) -> tuple:
        """
        Extract DC type and value from action data.

        Args:
            action_data: Dictionary containing action data

        Returns:
            Tuple of (dc_type: AbilityType, dc_value: int)
        """
        dc_type = None
        dc_value = None

        # Check for dc field
        if 'dc' in action_data:
            dc_info = action_data['dc']
            if isinstance(dc_info, dict):
                if 'dc_type' in dc_info:
                    dc_type = cls._parse_ability_type(dc_info['dc_type']['index'])
                if 'dc_value' in dc_info:
                    dc_value = dc_info['dc_value']

        # Fallback to description parsing
        if (dc_type is None or dc_value is None) and 'desc' in action_data:
            desc_conditions = cls.parse_condition_from_description(action_data['desc'])
            if desc_conditions:
                # Use DC from first condition found
                first_condition = desc_conditions[0]
                dc_type = first_condition.dc_type or dc_type
                dc_value = first_condition.dc_value or dc_value

        return dc_type, dc_value

    @classmethod
    def extract_conditions_from_action(
        cls,
        action_data: Dict[str, Any],
        monster: Optional[Any] = None
    ) -> List[Condition]:
        """
        Extract all conditions from an action's data.

        Args:
            action_data: Dictionary containing action data (from JSON)
            monster: The monster using this action

        Returns:
            List of Condition objects
        """
        conditions = []

        # Parse from description
        if 'desc' in action_data:
            conditions.extend(
                cls.parse_condition_from_description(
                    action_data['desc'],
                    monster
                )
            )

        # Update DC if we have more specific information
        dc_type, dc_value = cls.parse_dc_from_action_data(action_data)

        for condition in conditions:
            if dc_type and not condition.dc_type:
                condition.dc_type = dc_type
            if dc_value and not condition.dc_value:
                condition.dc_value = dc_value

        return conditions


def parse_magic_item_conditions(item_description: str) -> List[Condition]:
    """
    Parse conditions from magic item description.

    Args:
        item_description: Magic item description text

    Returns:
        List of Condition objects that the item can apply
    """
    return ConditionParser.parse_condition_from_description(item_description)
