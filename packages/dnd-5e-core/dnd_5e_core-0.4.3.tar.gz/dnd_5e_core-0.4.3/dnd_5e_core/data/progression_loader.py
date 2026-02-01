"""
Loader pour les données de progression de classes
"""
import json
from pathlib import Path
from typing import Optional, Dict
from ..mechanics.class_progression import (
    ClassProgression,
    create_class_progression_from_api
)


# Cache pour éviter de recharger les mêmes données
_progression_cache: Dict[str, ClassProgression] = {}


def load_class_progression(class_index: str) -> Optional[ClassProgression]:
    """
    Charge la progression complète d'une classe

    Args:
        class_index: Index de la classe (ex: 'wizard', 'fighter')

    Returns:
        ClassProgression ou None si non trouvé
    """
    # Vérifier le cache
    if class_index in _progression_cache:
        return _progression_cache[class_index]

    # Charger depuis le fichier JSON
    data_file = Path(__file__).parent.parent / "data" / "class_levels" / f"{class_index}_levels.json"

    if not data_file.exists():
        print(f"⚠️  Fichier non trouvé: {data_file}")
        return None

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)

        progression = create_class_progression_from_api(class_index, api_data)

        # Mettre en cache
        _progression_cache[class_index] = progression

        return progression

    except Exception as e:
        print(f"❌ Erreur lors du chargement de {class_index}: {e}")
        return None


def get_spell_slots_for_level(class_index: str, level: int) -> list:
    """
    Récupère les slots de sorts pour une classe à un niveau donné

    Args:
        class_index: Index de la classe
        level: Niveau du personnage

    Returns:
        Liste des slots de sorts [0, lvl1, lvl2, ..., lvl9]
    """
    progression = load_class_progression(class_index)

    if not progression:
        return [0] * 10

    spellcasting = progression.get_spellcasting(level)

    if not spellcasting:
        return [0] * 10

    return spellcasting.spell_slots


def get_prof_bonus_for_level(level: int) -> int:
    """
    Calcule le bonus de maîtrise pour un niveau donné

    Standard D&D 5e: +2 au niveau 1-4, +3 au 5-8, +4 au 9-12, +5 au 13-16, +6 au 17-20
    """
    if level < 5:
        return 2
    elif level < 9:
        return 3
    elif level < 13:
        return 4
    elif level < 17:
        return 5
    else:
        return 6


def get_features_at_level(class_index: str, level: int) -> list:
    """
    Récupère toutes les features obtenues à un niveau spécifique

    Args:
        class_index: Index de la classe
        level: Niveau du personnage

    Returns:
        Liste des features
    """
    progression = load_class_progression(class_index)

    if not progression:
        return []

    level_data = progression.get_level(level)

    if not level_data:
        return []

    return level_data.features


def get_class_specific_value(class_index: str, level: int, key: str, default=None):
    """
    Récupère une valeur spécifique à la classe pour un niveau

    Exemples:
    - Barbarian: rage_count, rage_damage_bonus
    - Monk: ki_points, martial_arts_dice
    - Rogue: sneak_attack_dice

    Args:
        class_index: Index de la classe
        level: Niveau du personnage
        key: Clé de la valeur recherchée
        default: Valeur par défaut si non trouvée

    Returns:
        Valeur ou default
    """
    progression = load_class_progression(class_index)

    if not progression:
        return default

    return progression.get_class_specific(level, key) or default


# =============================================================================
# FONCTIONS UTILITAIRES POUR L'INTÉGRATION AVEC Character
# =============================================================================

def apply_level_up_benefits(character, new_level: int):
    """
    Applique tous les bénéfices d'un passage de niveau

    Args:
        character: Instance de Character
        new_level: Nouveau niveau atteint
    """
    class_index = character.class_type.index

    # Charger la progression
    progression = load_class_progression(class_index)

    if not progression:
        print(f"⚠️  Pas de données de progression pour {class_index}")
        return

    level_data = progression.get_level(new_level)

    if not level_data:
        print(f"⚠️  Pas de données pour le niveau {new_level}")
        return

    # 1. Augmenter les HP
    from random import randint
    hp_gain = randint(1, progression.hit_die) + character.abilities.get_modifier('con')
    hp_gain = max(1, hp_gain)  # Minimum 1 HP
    character.max_hit_points += hp_gain
    character.hit_points += hp_gain

    print(f"   ❤️  HP: +{hp_gain} ({character.max_hit_points} total)")

    # 2. Mettre à jour le bonus de maîtrise
    # (Déjà géré via la propriété calculée dans Character)

    # 3. Mettre à jour les spell slots si lanceur de sorts
    if hasattr(character, 'sc') and character.sc and level_data.spellcasting:
        character.sc.spell_slots = level_data.spellcasting.spell_slots.copy()
        print(f"   🔮 Spell slots mis à jour")

    # 4. Afficher les nouvelles features
    if level_data.features:
        print(f"   ✨ Nouvelles features:")
        for feature in level_data.features:
            print(f"      - {feature.name}")

    # 5. Appliquer les améliorations de caractéristiques si applicable
    if level_data.has_ability_score_improvement():
        print(f"   📈 Amélioration de caractéristique disponible!")
        # L'amélioration sera appliquée manuellement par le joueur

    # 6. Appliquer les bonus spécifiques à la classe
    if level_data.class_specific:
        for key, value in level_data.class_specific.items():
            print(f"   🎯 {key}: {value}")


if __name__ == "__main__":
    # Test du loader
    print("Testing class progression loader...")

    wizard_prog = load_class_progression('wizard')
    if wizard_prog:
        print(f"✅ Loaded {wizard_prog.class_name}")
        print(f"   Level 1 spell slots: {wizard_prog.get_spellcasting(1).spell_slots if wizard_prog.get_spellcasting(1) else 'None'}")
