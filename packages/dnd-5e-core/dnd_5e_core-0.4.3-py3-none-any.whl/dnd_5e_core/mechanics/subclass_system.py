"""
D&D 5e Core - Subclass and Subrace System
Gère les sous-classes (archetypes) et sous-races
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


@dataclass
class Subclass:
    """
    Sous-classe (archetype) d'une classe

    Exemples:
    - Wizard: School of Evocation, School of Abjuration
    - Fighter: Champion, Battle Master
    - Cleric: Life Domain, War Domain
    """
    index: str
    name: str
    class_index: str  # Classe parente (wizard, fighter, etc.)
    subclass_flavor: str  # Description du thème
    desc: List[str] = field(default_factory=list)

    # Features obtenues par la sous-classe
    subclass_levels: List[int] = field(default_factory=list)  # Niveaux où on obtient des features
    spells: List[Dict[str, Any]] = field(default_factory=list)  # Sorts spéciaux si applicable

    def get_level_features(self, level: int) -> List[str]:
        """Récupère les features obtenues à un niveau donné"""
        # À implémenter avec les données de l'API
        return []


@dataclass
class Subrace:
    """
    Sous-race

    Exemples:
    - Elf: High Elf, Wood Elf, Dark Elf
    - Dwarf: Hill Dwarf, Mountain Dwarf
    """
    index: str
    name: str
    race_index: str  # Race parente (elf, dwarf, etc.)
    desc: str = ""

    # Modificateurs supplémentaires
    ability_bonuses: List[Dict[str, Any]] = field(default_factory=list)
    starting_proficiencies: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    racial_traits: List[str] = field(default_factory=list)


# =============================================================================
# MULTICLASSING
# =============================================================================

@dataclass
class MulticlassLevel:
    """Représente un niveau dans une classe pour un personnage multiclassé"""
    class_index: str
    level: int
    subclass_index: Optional[str] = None


@dataclass
class MulticlassCharacter:
    """
    Gère un personnage avec plusieurs classes

    Exemple:
    - Fighter 5 / Wizard 3
    - Rogue 4 / Cleric 4
    """
    character_name: str
    classes: List[MulticlassLevel] = field(default_factory=list)

    def add_class_level(self, class_index: str, subclass_index: Optional[str] = None):
        """Ajoute un niveau dans une classe"""
        # Chercher si la classe existe déjà
        for mc_level in self.classes:
            if mc_level.class_index == class_index:
                mc_level.level += 1
                if subclass_index and not mc_level.subclass_index:
                    mc_level.subclass_index = subclass_index
                return

        # Nouvelle classe
        self.classes.append(MulticlassLevel(
            class_index=class_index,
            level=1,
            subclass_index=subclass_index
        ))

    def get_total_level(self) -> int:
        """Niveau total du personnage"""
        return sum(mc.level for mc in self.classes)

    def get_class_level(self, class_index: str) -> int:
        """Récupère le niveau dans une classe spécifique"""
        for mc_level in self.classes:
            if mc_level.class_index == class_index:
                return mc_level.level
        return 0

    def get_primary_class(self) -> Optional[str]:
        """Retourne la classe avec le plus de niveaux"""
        if not self.classes:
            return None
        return max(self.classes, key=lambda x: x.level).class_index

    def get_spell_slots_multiclass(self) -> List[int]:
        """
        Calcule les spell slots pour un personnage multiclassé

        Règles D&D 5e:
        - Full casters (Wizard, Cleric, etc.): niveau complet
        - Half casters (Paladin, Ranger): niveau / 2
        - Third casters (Eldritch Knight, Arcane Trickster): niveau / 3
        - Warlock: slots séparés (pact magic)
        """
        caster_level = 0
        warlock_level = 0

        for mc in self.classes:
            if mc.class_index in ['wizard', 'sorcerer', 'bard', 'cleric', 'druid']:
                # Full caster
                caster_level += mc.level
            elif mc.class_index in ['paladin', 'ranger']:
                # Half caster
                caster_level += mc.level // 2
            elif mc.class_index == 'warlock':
                # Warlock utilise Pact Magic (séparé)
                warlock_level = mc.level
            # Fighter (Eldritch Knight) et Rogue (Arcane Trickster) = third casters
            # À gérer si la sous-classe est spécifiée

        # Charger les spell slots pour le caster level
        from .class_progression import ClassProgression
        from ..data.progression_loader import get_spell_slots_for_level

        if caster_level > 0:
            # Utiliser la table standard de full caster
            return get_spell_slots_for_level('wizard', caster_level)

        return [0] * 10

    def __str__(self):
        """Représentation textuelle (ex: "Fighter 5 / Wizard 3")"""
        class_strs = [f"{mc.class_index.title()} {mc.level}" for mc in self.classes]
        return " / ".join(class_strs)


# =============================================================================
# LOADERS
# =============================================================================

def load_subclass(subclass_index: str) -> Optional[Subclass]:
    """
    Charge une sous-classe depuis les données JSON

    Args:
        subclass_index: Index de la sous-classe (ex: 'champion', 'life-domain')

    Returns:
        Subclass ou None
    """
    from pathlib import Path
    import json

    data_file = Path(__file__).parent.parent / "data" / "subclasses" / f"{subclass_index}.json"

    if not data_file.exists():
        return None

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Vérifier que data est un dict
        if not isinstance(data, dict):
            return None

        # Extraire class_index de manière sécurisée
        class_data = data.get('class', {})
        class_index = ''
        if isinstance(class_data, dict):
            class_index = class_data.get('index', '')
        elif isinstance(class_data, str):
            class_index = class_data

        return Subclass(
            index=data.get('index', subclass_index),
            name=data.get('name', subclass_index.title()),
            class_index=class_index,
            subclass_flavor=data.get('subclass_flavor', ''),
            desc=data.get('desc', []),
            subclass_levels=[lvl.get('level', 0) for lvl in data.get('subclass_levels', []) if isinstance(lvl, dict)],
            spells=data.get('spells', [])
        )
    except Exception as e:
        print(f"Erreur lors du chargement de {subclass_index}: {e}")
        return None


def load_subrace(subrace_index: str) -> Optional[Subrace]:
    """
    Charge une sous-race depuis les données JSON

    Args:
        subrace_index: Index de la sous-race (ex: 'high-elf', 'hill-dwarf')

    Returns:
        Subrace ou None
    """
    from pathlib import Path
    import json

    data_file = Path(__file__).parent.parent / "data" / "subraces" / f"{subrace_index}.json"

    if not data_file.exists():
        return None

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Vérifier que data est un dict
        if not isinstance(data, dict):
            return None

        # Extraire race_index de manière sécurisée
        race_data = data.get('race', {})
        race_index = ''
        if isinstance(race_data, dict):
            race_index = race_data.get('index', '')
        elif isinstance(race_data, str):
            race_index = race_data

        # Parser ability_bonuses de manière sécurisée
        ability_bonuses = []
        for bonus in data.get('ability_bonuses', []):
            if isinstance(bonus, dict):
                ability_bonuses.append(bonus)

        # Parser starting_proficiencies de manière sécurisée
        starting_profs = []
        for prof in data.get('starting_proficiencies', []):
            if isinstance(prof, dict):
                starting_profs.append(prof.get('index', ''))
            elif isinstance(prof, str):
                starting_profs.append(prof)

        # Parser racial_traits de manière sécurisée
        racial_traits = []
        for trait in data.get('racial_traits', []):
            if isinstance(trait, dict):
                racial_traits.append(trait.get('index', ''))
            elif isinstance(trait, str):
                racial_traits.append(trait)

        return Subrace(
            index=data.get('index', subrace_index),
            name=data.get('name', subrace_index.title()),
            race_index=race_index,
            desc=data.get('desc', ''),
            ability_bonuses=ability_bonuses,
            starting_proficiencies=starting_profs,
            languages=[],  # Simplifié pour éviter les erreurs
            racial_traits=racial_traits
        )
    except Exception as e:
        print(f"Erreur lors du chargement de {subrace_index}: {e}")
        return None


def list_subclasses_for_class(class_index: str) -> List[str]:
    """
    Liste toutes les sous-classes disponibles pour une classe

    Args:
        class_index: Index de la classe (ex: 'wizard', 'fighter')

    Returns:
        Liste des indices de sous-classes
    """
    from pathlib import Path
    import json

    subclasses_dir = Path(__file__).parent.parent / "data" / "subclasses"

    if not subclasses_dir.exists():
        return []

    result = []
    for file in subclasses_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('class', {}).get('index') == class_index:
                result.append(data['index'])
        except Exception:
            continue

    return result


def list_subraces_for_race(race_index: str) -> List[str]:
    """
    Liste toutes les sous-races disponibles pour une race

    Args:
        race_index: Index de la race (ex: 'elf', 'dwarf')

    Returns:
        Liste des indices de sous-races
    """
    from pathlib import Path
    import json

    subraces_dir = Path(__file__).parent.parent / "data" / "subraces"

    if not subraces_dir.exists():
        return []

    result = []
    for file in subraces_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if data.get('race', {}).get('index') == race_index:
                result.append(data['index'])
        except Exception:
            continue

    return result


# =============================================================================
# EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    # Exemple: Charger une sous-classe
    champion = load_subclass('champion')
    if champion:
        print(f"✅ Sous-classe: {champion.name} ({champion.class_index})")
        print(f"   Flavor: {champion.subclass_flavor}")

    # Exemple: Charger une sous-race
    high_elf = load_subrace('high-elf')
    if high_elf:
        print(f"✅ Sous-race: {high_elf.name} ({high_elf.race_index})")

    # Exemple: Multiclassing
    mc_char = MulticlassCharacter("Gandalf")
    mc_char.add_class_level('fighter', None)
    mc_char.add_class_level('fighter', None)
    mc_char.add_class_level('fighter', None)
    mc_char.add_class_level('fighter', None)
    mc_char.add_class_level('fighter', 'champion')
    mc_char.add_class_level('wizard', None)
    mc_char.add_class_level('wizard', None)
    mc_char.add_class_level('wizard', 'evocation')

    print(f"\n✅ Multiclass: {mc_char}")
    print(f"   Niveau total: {mc_char.get_total_level()}")
    print(f"   Classe primaire: {mc_char.get_primary_class()}")
