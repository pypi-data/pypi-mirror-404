"""
D&D 5e Core - Data Module
Data loading from local JSON files
"""

from .loader import (
    set_data_directory, get_data_directory,
    load_monster, load_spell, load_weapon, load_armor, load_magic_item,
    load_race, load_class, load_equipment,
    # NEW: Additional loaders
    load_damage_type, load_condition, load_trait, load_subrace,
    load_language, load_proficiency, load_weapon_property, load_equipment_category,
    # List functions
    list_monsters, list_spells, list_equipment, list_weapons, list_armors,
    list_races, list_classes,
    # NEW: Additional list functions
    list_damage_types, list_conditions, list_traits, list_subraces,
    list_languages, list_proficiencies, list_weapon_properties, list_equipment_categories,
    # Utilities
    clear_cache, parse_dice_notation, parse_challenge_rating
)

from .collections import (
    set_collections_directory, get_collections_directory,
    load_collection, populate, get_collection_count, get_collection_item,
    list_all_collections,
    get_monsters_list, get_spells_list, get_classes_list, get_races_list,
    get_equipment_list, get_weapons_list, get_armors_list, get_magic_items_list,
    # Object loading functions
    load_all_monsters, load_all_spells, load_all_weapons, load_all_armors,
    filter_monsters, filter_spells
)

# NEW: Names module
from .names import (
    load_names, load_human_names, load_clan_names, load_virtue_names
)

# NEW: Tables module
from .tables import (
    load_table, load_height_weight_table, load_xp_levels_table,
    load_spell_slots_table, load_encounter_difficulty_table,
    load_encounter_levels_table, load_encounter_gold_table,
    load_combat_table, load_magic_item_table, load_class_spell_table
)

__all__ = [
    # Data loader functions (individual objects)
    'set_data_directory', 'get_data_directory',
    'load_monster', 'load_spell', 'load_weapon', 'load_armor', 'load_magic_item',
    'load_race', 'load_class', 'load_equipment',
    # NEW loaders
    'load_damage_type', 'load_condition', 'load_trait', 'load_subrace',
    'load_language', 'load_proficiency', 'load_weapon_property', 'load_equipment_category',
    # List functions
    'list_monsters', 'list_spells', 'list_equipment', 'list_weapons', 'list_armors',
    'list_races', 'list_classes',
    # NEW list functions
    'list_damage_types', 'list_conditions', 'list_traits', 'list_subraces',
    'list_languages', 'list_proficiencies', 'list_weapon_properties', 'list_equipment_categories',
    # Utilities
    'clear_cache', 'parse_dice_notation', 'parse_challenge_rating',
    # Collections functions (indexes)
    'set_collections_directory', 'get_collections_directory',
    'load_collection', 'populate', 'get_collection_count', 'get_collection_item',
    'list_all_collections',
    'get_monsters_list', 'get_spells_list', 'get_classes_list', 'get_races_list',
    'get_equipment_list', 'get_weapons_list', 'get_armors_list', 'get_magic_items_list',
    # Object loading functions (bulk)
    'load_all_monsters', 'load_all_spells', 'load_all_weapons', 'load_all_armors',
    'filter_monsters', 'filter_spells',
    # NEW: Names functions
    'load_names', 'load_human_names', 'load_clan_names', 'load_virtue_names',
    # NEW: Tables functions
    'load_table', 'load_height_weight_table', 'load_xp_levels_table',
    'load_spell_slots_table', 'load_encounter_difficulty_table',
    'load_encounter_levels_table', 'load_encounter_gold_table',
    'load_combat_table', 'load_magic_item_table', 'load_class_spell_table'
]

