"""
D&D 5e Core - Class Level Progression System
Gère la progression des personnages par niveau avec les capacités spécifiques à chaque classe
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class FeatureType(Enum):
    """Types de features de classe"""
    ABILITY_SCORE_IMPROVEMENT = "ability_score_improvement"
    SPELLCASTING = "spellcasting"
    CHANNEL_DIVINITY = "channel_divinity"
    RAGE = "rage"
    SNEAK_ATTACK = "sneak_attack"
    MARTIAL_ARTS = "martial_arts"
    KI_POINTS = "ki_points"
    BARDIC_INSPIRATION = "bardic_inspiration"
    SORCERY_POINTS = "sorcery_points"
    SPELL_SLOTS = "spell_slots"
    OTHER = "other"


@dataclass
class ClassFeature:
    """
    Feature obtenue à un niveau spécifique

    Exemples:
    - Ability Score Improvement (niveau 4, 8, 12, etc.)
    - Extra Attack (Fighter niveau 5)
    - Spellcasting improvements
    """
    index: str
    name: str
    level: int
    desc: List[str] = field(default_factory=list)
    feature_type: FeatureType = FeatureType.OTHER

    # Données spécifiques selon le type
    prerequisites: List[Dict[str, Any]] = field(default_factory=list)
    class_index: Optional[str] = None
    subclass_index: Optional[str] = None


@dataclass
class SpellcastingInfo:
    """
    Informations sur les capacités de lancement de sorts à un niveau donné
    """
    level: int
    cantrips_known: int = 0
    spells_known: int = 0
    spell_slots_level_1: int = 0
    spell_slots_level_2: int = 0
    spell_slots_level_3: int = 0
    spell_slots_level_4: int = 0
    spell_slots_level_5: int = 0
    spell_slots_level_6: int = 0
    spell_slots_level_7: int = 0
    spell_slots_level_8: int = 0
    spell_slots_level_9: int = 0

    @property
    def spell_slots(self) -> List[int]:
        """Retourne les slots de sorts sous forme de liste"""
        return [
            0,  # Index 0 (pas utilisé)
            self.spell_slots_level_1,
            self.spell_slots_level_2,
            self.spell_slots_level_3,
            self.spell_slots_level_4,
            self.spell_slots_level_5,
            self.spell_slots_level_6,
            self.spell_slots_level_7,
            self.spell_slots_level_8,
            self.spell_slots_level_9,
        ]

    def get_total_spell_slots(self) -> int:
        """Nombre total de slots de sorts disponibles"""
        return sum(self.spell_slots[1:])


@dataclass
class ClassLevelProgression:
    """
    Progression complète pour un niveau spécifique d'une classe

    Basé sur les données de l'API /api/classes/:index/levels/:level
    """
    level: int
    class_index: str

    # Bonus
    ability_score_bonuses: int = 0
    prof_bonus: int = 2

    # Features obtenues à ce niveau
    features: List[ClassFeature] = field(default_factory=list)

    # Spellcasting (si applicable)
    spellcasting: Optional[SpellcastingInfo] = None

    # Capacités spécifiques aux classes
    class_specific: Dict[str, Any] = field(default_factory=dict)

    # Exemples de class_specific:
    # - Barbarian: rage_count, rage_damage_bonus
    # - Fighter: action_surge_count, indomitable_uses
    # - Monk: ki_points, unarmored_movement
    # - Rogue: sneak_attack_dice
    # - Sorcerer: sorcery_points
    # - Warlock: invocations_known, mystic_arcanum_level_6-9

    def has_spellcasting(self) -> bool:
        """Vérifie si la classe peut lancer des sorts à ce niveau"""
        return self.spellcasting is not None

    def get_feature_by_type(self, feature_type: FeatureType) -> Optional[ClassFeature]:
        """Récupère une feature par son type"""
        for feature in self.features:
            if feature.feature_type == feature_type:
                return feature
        return None

    def has_ability_score_improvement(self) -> bool:
        """Vérifie si ce niveau donne une amélioration de caractéristique"""
        return self.ability_score_bonuses > 0 or \
               self.get_feature_by_type(FeatureType.ABILITY_SCORE_IMPROVEMENT) is not None


@dataclass
class ClassProgression:
    """
    Progression complète pour une classe sur tous les niveaux (1-20)
    """
    class_index: str
    class_name: str
    hit_die: int  # d6, d8, d10, d12

    # Progression par niveau
    levels: Dict[int, ClassLevelProgression] = field(default_factory=dict)

    # Proficiencies
    saving_throws: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

    def get_level(self, level: int) -> Optional[ClassLevelProgression]:
        """Récupère la progression pour un niveau spécifique"""
        return self.levels.get(level)

    def get_prof_bonus(self, level: int) -> int:
        """Récupère le bonus de maîtrise pour un niveau"""
        level_data = self.get_level(level)
        return level_data.prof_bonus if level_data else 2

    def get_spellcasting(self, level: int) -> Optional[SpellcastingInfo]:
        """Récupère les infos de spellcasting pour un niveau"""
        level_data = self.get_level(level)
        return level_data.spellcasting if level_data else None

    def get_features_up_to_level(self, level: int) -> List[ClassFeature]:
        """Récupère toutes les features obtenues jusqu'à un niveau donné"""
        all_features = []
        for lvl in range(1, min(level + 1, 21)):
            level_data = self.get_level(lvl)
            if level_data:
                all_features.extend(level_data.features)
        return all_features

    def get_class_specific(self, level: int, key: str) -> Any:
        """Récupère une valeur spécifique à la classe pour un niveau"""
        level_data = self.get_level(level)
        if level_data and key in level_data.class_specific:
            return level_data.class_specific[key]
        return None


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_class_progression_from_api(class_index: str, api_data: List[Dict]) -> ClassProgression:
    """
    Crée un ClassProgression à partir des données de l'API

    Args:
        class_index: Index de la classe (ex: 'wizard')
        api_data: Liste des niveaux de l'API (/api/classes/:index/levels)

    Returns:
        ClassProgression complète
    """
    from ..data import load_class

    # Charger les données de base de la classe
    class_data = load_class(class_index)

    # Parser saving_throws de manière sécurisée
    saving_throws = []
    if class_data and hasattr(class_data, 'saving_throws'):
        for st in class_data.saving_throws:
            if hasattr(st, 'index'):
                saving_throws.append(st.index)
            elif hasattr(st, 'value'):
                saving_throws.append(st.value)
            elif isinstance(st, str):
                saving_throws.append(st)

    progression = ClassProgression(
        class_index=class_index,
        class_name=class_data.name if class_data else class_index.title(),
        hit_die=class_data.hit_die if class_data else 8,
        saving_throws=saving_throws,
    )

    # Parser chaque niveau
    for level_data in api_data:
        level = level_data['level']

        # Créer le spellcasting si présent
        spellcasting = None
        if 'spellcasting' in level_data:
            sc_data = level_data['spellcasting']
            spellcasting = SpellcastingInfo(
                level=level,
                cantrips_known=sc_data.get('cantrips_known', 0),
                spells_known=sc_data.get('spells_known', 0),
                spell_slots_level_1=sc_data.get('spell_slots_level_1', 0),
                spell_slots_level_2=sc_data.get('spell_slots_level_2', 0),
                spell_slots_level_3=sc_data.get('spell_slots_level_3', 0),
                spell_slots_level_4=sc_data.get('spell_slots_level_4', 0),
                spell_slots_level_5=sc_data.get('spell_slots_level_5', 0),
                spell_slots_level_6=sc_data.get('spell_slots_level_6', 0),
                spell_slots_level_7=sc_data.get('spell_slots_level_7', 0),
                spell_slots_level_8=sc_data.get('spell_slots_level_8', 0),
                spell_slots_level_9=sc_data.get('spell_slots_level_9', 0),
            )

        # Créer les features
        features = []
        for feat_data in level_data.get('features', []):
            feature = ClassFeature(
                index=feat_data['index'],
                name=feat_data['name'],
                level=level,
                class_index=class_index
            )

            # Déterminer le type de feature
            name_lower = feat_data['name'].lower()
            if 'ability score' in name_lower:
                feature.feature_type = FeatureType.ABILITY_SCORE_IMPROVEMENT
            elif 'spellcasting' in name_lower:
                feature.feature_type = FeatureType.SPELLCASTING

            features.append(feature)

        # Créer la progression du niveau
        level_prog = ClassLevelProgression(
            level=level,
            class_index=class_index,
            ability_score_bonuses=level_data.get('ability_score_bonuses', 0),
            prof_bonus=level_data.get('prof_bonus', 2),
            features=features,
            spellcasting=spellcasting,
            class_specific=level_data.get('class_specific', {})
        )

        progression.levels[level] = level_prog

    return progression


# =============================================================================
# EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    # Exemple de création d'une progression de classe
    example_wizard_levels = [
        {
            "level": 1,
            "prof_bonus": 2,
            "features": [
                {"index": "spellcasting-wizard", "name": "Spellcasting"},
                {"index": "arcane-recovery", "name": "Arcane Recovery"}
            ],
            "spellcasting": {
                "cantrips_known": 3,
                "spell_slots_level_1": 2
            }
        },
        {
            "level": 2,
            "prof_bonus": 2,
            "features": [
                {"index": "arcane-tradition", "name": "Arcane Tradition"}
            ],
            "spellcasting": {
                "cantrips_known": 3,
                "spell_slots_level_1": 3
            }
        }
    ]

    # wizard_progression = create_class_progression_from_api('wizard', example_wizard_levels)
    # print(f"Wizard Progression: {wizard_progression.class_name}")
    # print(f"Level 1 spell slots: {wizard_progression.get_spellcasting(1).spell_slots}")
