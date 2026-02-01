"""
Module pour gérer les actions et capacités spéciales des monstres de 5e.tools

Ce module contient la logique pour construire les actions et capacités spéciales
des monstres qui ne sont pas inclus dans l'API officielle D&D 5e.

Note: Ce module est utilisé par extended_monsters.py pour construire les monstres
avec leurs capacités complètes.

Il prend en charge deux méthodes:
1. Extraction automatique depuis les fichiers JSON (format 5e.tools)
2. Définition manuelle pour les monstres nécessitant une logique personnalisée
"""
from typing import List, Optional, Tuple, TYPE_CHECKING, Dict, Any
import re

# Éviter les imports circulaires avec TYPE_CHECKING
if TYPE_CHECKING:
    from ..combat import Action, ActionType, SpecialAbility
    from ..spells import SpellCaster


class JSONActionExtractor:
    """
    Extracteur d'actions depuis les fichiers JSON au format 5e.tools

    Cette classe permet d'extraire automatiquement les actions, capacités spéciales
    et sorts depuis les données JSON des monstres étendus.
    """

    def __init__(self):
        """Initialise l'extracteur"""
        pass

    def extract_actions_from_json(self, monster_data: Dict[str, Any]) -> List['Action']:
        """
        Extrait les actions depuis les données JSON d'un monstre

        :param monster_data: Données du monstre au format 5e.tools
        :return: Liste d'actions
        """
        from ..combat import Action

        actions = []

        # Les actions sont dans la clé 'action' (peut être une liste)
        if 'action' in monster_data and isinstance(monster_data['action'], list):
            for action_data in monster_data['action']:
                try:
                    action = self._parse_action(action_data)
                    if action:
                        actions.append(action)
                except Exception as e:
                    print(f"⚠️ Erreur extraction action {action_data.get('name')}: {e}")

        return actions

    def extract_special_abilities_from_json(self, monster_data: Dict[str, Any]) -> List['SpecialAbility']:
        """
        Extrait les capacités spéciales depuis les données JSON d'un monstre

        :param monster_data: Données du monstre au format 5e.tools
        :return: Liste de capacités spéciales
        """
        from ..combat import SpecialAbility

        abilities = []

        # Les capacités spéciales sont dans 'trait'
        if 'trait' in monster_data and isinstance(monster_data['trait'], list):
            for trait_data in monster_data['trait']:
                try:
                    ability = self._parse_special_ability(trait_data)
                    if ability:
                        abilities.append(ability)
                except Exception as e:
                    print(f"⚠️ Erreur extraction trait {trait_data.get('name')}: {e}")

        return abilities

    def extract_spellcasting_from_json(self, monster_data: Dict[str, Any]) -> Optional['SpellCaster']:
        """
        Extrait le spellcasting depuis les données JSON d'un monstre

        :param monster_data: Données du monstre au format 5e.tools
        :return: SpellCaster ou None
        """
        # Chercher dans les traits pour le spellcasting
        if 'trait' in monster_data and isinstance(monster_data['trait'], list):
            for trait in monster_data['trait']:
                if 'name' in trait and 'Spellcasting' in trait['name']:
                    return self._parse_spellcasting(trait)

        # Chercher dans les actions
        if 'action' in monster_data and isinstance(monster_data['action'], list):
            for action in monster_data['action']:
                if 'name' in action and 'Spellcasting' in action['name']:
                    return self._parse_spellcasting(action)

        return None

    def _parse_action(self, action_data: Dict[str, Any]) -> Optional['Action']:
        """Parse une action depuis les données JSON"""
        from ..combat import Action, ActionType

        name = action_data.get('name', 'Unknown')

        # Skip spellcasting (handled separately)
        if 'Spellcasting' in name:
            return None

        # Déterminer le type d'action
        action_type = self._determine_action_type(action_data)

        # Extraire le bonus d'attaque
        attack_bonus = self._extract_attack_bonus(action_data)

        # Extraire les portées
        normal_range, long_range = self._extract_ranges(action_data)

        # Description
        desc = self._extract_description(action_data)

        # Pour l'instant, pas de parsing des dégâts (complexe)
        # TODO: Implémenter extraction dégâts

        return Action(
            name=name,
            desc=desc,
            type=action_type,
            attack_bonus=attack_bonus,
            damages=[],  # Liste vide au lieu de None
            normal_range=normal_range,
            long_range=long_range,
            dc_type=None,
            dc_value=None,
            dc_success=None
        )

    def _parse_special_ability(self, trait_data: Dict[str, Any]) -> Optional['SpecialAbility']:
        """Parse une capacité spéciale depuis les données JSON"""
        from ..combat import SpecialAbility

        name = trait_data.get('name', 'Unknown')

        # Skip spellcasting (handled separately)
        if 'Spellcasting' in name:
            return None

        desc = self._extract_description(trait_data)

        return SpecialAbility(
            name=name,
            desc=desc
        )

    def _parse_spellcasting(self, spell_data: Dict[str, Any]) -> Optional['SpellCaster']:
        """Parse le spellcasting depuis les données JSON"""
        # TODO: Implémenter le parsing du spellcasting (format 5e.tools complexe)
        return None

    def _determine_action_type(self, action_data: Dict[str, Any]) -> 'ActionType':
        """Détermine le type d'action"""
        from ..combat import ActionType

        name = action_data.get('name', '').lower()
        entries = action_data.get('entries', [])
        entries_str = str(entries).lower()

        if 'multiattack' in name:
            return ActionType.MELEE  # Multiattack is usually melee

        if 'melee' in entries_str and 'ranged' in entries_str:
            return ActionType.MIXED

        if 'ranged' in entries_str:
            return ActionType.RANGED

        return ActionType.MELEE

    def _extract_attack_bonus(self, action_data: Dict[str, Any]) -> Optional[int]:
        """Extrait le bonus d'attaque"""
        entries = action_data.get('entries', [])
        for entry in entries:
            if isinstance(entry, str):
                # Pattern: "+X to hit"
                match = re.search(r'\+(\d+)\s+to\s+hit', entry, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        return None

    def _extract_ranges(self, action_data: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
        """Extrait les portées"""
        entries = action_data.get('entries', [])
        for entry in entries:
            if isinstance(entry, str):
                # Pattern: "range X/Y ft"
                match = re.search(r'range\s+(\d+)/(\d+)\s*ft', entry, re.IGNORECASE)
                if match:
                    return int(match.group(1)), int(match.group(2))

                # Pattern: "range X ft"
                match = re.search(r'range\s+(\d+)\s*ft', entry, re.IGNORECASE)
                if match:
                    return int(match.group(1)), None

        return None, None

    def _extract_description(self, data: Dict[str, Any]) -> str:
        """Extrait la description"""
        entries = data.get('entries', [])

        desc_parts = []
        for entry in entries:
            if isinstance(entry, str):
                desc_parts.append(entry)
            elif isinstance(entry, dict):
                if 'text' in entry:
                    desc_parts.append(entry['text'])

        return ' '.join(desc_parts)


class SpecialMonsterActionsBuilder:
    """
    Constructeur d'actions et capacités spéciales pour les monstres de 5e.tools

    Cette classe encapsule la logique de création des actions et capacités
    pour chaque monstre spécifique.
    """

    def __init__(self):
        """Initialise le builder"""
        self._action_builders = {}
        self._json_extractor = JSONActionExtractor()
        self._monster_loader = None  # Lazy loaded
        self._register_action_builders()

    def _get_monster_loader(self):
        """Lazy load du monster loader"""
        if self._monster_loader is None:
            from .extended_monsters import FiveEToolsMonsterLoader
            self._monster_loader = FiveEToolsMonsterLoader()
        return self._monster_loader

    def _register_action_builders(self):
        """Enregistre les fonctions de construction pour chaque monstre"""
        # Chaque monstre a sa propre fonction de construction
        # Cette approche permet une meilleure organisation et maintenabilité
        self._action_builders = {
            "Orc Eye of Gruumsh": self._build_orc_eye_of_gruumsh,
            "Ogre Bolt Launcher": self._build_ogre_bolt_launcher,
            "Ogre Battering Ram": self._build_ogre_battering_ram,
            "Hobgoblin Captain": self._build_hobgoblin_captain,
            "Piercer": self._build_piercer,
            "Illusionist": self._build_illusionist,
            "Goblin Boss": self._build_goblin_boss,
            "Xvart": self._build_xvart,
            "Kobold Inventor": self._build_kobold_inventor,
            "Half-ogre": self._build_half_ogre,
            "Water Weird": self._build_water_weird,
            "Apprentice Wizard": self._build_apprentice_wizard,
            "Orc War Chief": self._build_orc_war_chief,
            "Deathlock": self._build_deathlock,
            "Allip": self._build_allip,
            "Orog": self._build_orog,
            "Warlock of the Great Old One": self._build_warlock_great_old_one,
            "Star Spawn Grue": self._build_star_spawn_grue,
            "Star Spawn Mangler": self._build_star_spawn_mangler,
            "Adult Oblex": self._build_adult_oblex,
            "Vampiric Mist": self._build_vampiric_mist,
            "Spawn of Kyuss": self._build_spawn_of_kyuss,
            "Hobgoblin Warlord": self._build_hobgoblin_warlord,
            "Duergar Mind Master": self._build_duergar_mind_master,
            "Duergar Screamer": self._build_duergar_screamer,
            "Duergar Kavalrachni": self._build_duergar_kavalrachni,
            "Female Steeder": self._build_female_steeder,
            "Succubus": self._build_succubus,
            "Incubus": self._build_incubus,
            "Sea Hag": self._build_sea_hag,
            "Kuo-toa Archpriest": self._build_kuotoa_archpriest,
            "Kuo-toa": self._build_kuotoa,
            "Kuo-toa Whip": self._build_kuotoa_whip,
            "Sahuagin Baron": self._build_sahuagin_baron,
            "Sahuagin Priestess": self._build_sahuagin_priestess,
            "Sea Spawn": self._build_sea_spawn,
            "Yuan-ti Pureblood": self._build_yuanti_pureblood,
            "Firenewt Warlock of Imix": self._build_firenewt_warlock,
            "Firenewt Warrior": self._build_firenewt_warrior,
            "Yuan-ti Malison": self._build_yuanti_malison,
            "Yuan-ti Broodguard": self._build_yuanti_broodguard,
            "Ogre Chain Brute": self._build_ogre_chain_brute,
            "Young Kruthik": self._build_young_kruthik,
            "Adult Kruthik": self._build_adult_kruthik,
            "Gnoll": self._build_gnoll,
            "Maw Demon": self._build_maw_demon,
            "Yuan-ti Pit Master": self._build_yuanti_pit_master,
        }

    def get_monster_actions(self, name: str, use_json_fallback: bool = True) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """
        Récupère les actions et capacités spéciales pour un monstre

        Essaie d'abord la définition manuelle, puis l'extraction JSON si disponible.

        :param name: Nom du monstre
        :param use_json_fallback: Si True, essaie l'extraction JSON si pas de définition manuelle
        :return: Tuple (actions, special_abilities, spell_caster)
        """
        builder_func = self._action_builders.get(name)

        if builder_func is not None:
            # Utiliser la définition manuelle
            return builder_func()

        # Essayer l'extraction automatique depuis JSON
        if use_json_fallback:
            try:
                loader = self._get_monster_loader()
                monster_data = loader.get_monster_by_name(name, use_all=False)

                if monster_data:
                    actions = self._json_extractor.extract_actions_from_json(monster_data)
                    abilities = self._json_extractor.extract_special_abilities_from_json(monster_data)
                    spellcaster = self._json_extractor.extract_spellcasting_from_json(monster_data)

                    if actions or abilities or spellcaster:
                        return actions, abilities, spellcaster
            except Exception as e:
                print(f"⚠️ Erreur extraction JSON pour {name}: {e}")

        # Monstre non implémenté et pas dans JSON
        return [], [], None

    def is_implemented(self, name: str) -> bool:
        """
        Vérifie si un monstre a ses actions implémentées

        :param name: Nom du monstre
        :return: True si implémenté, False sinon
        """
        return name in self._action_builders

    def get_implemented_monsters(self) -> List[str]:
        """
        Retourne la liste des noms de monstres implémentés

        :return: Liste des noms
        """
        return list(self._action_builders.keys())

    # ======================================================================
    # Fonctions de construction pour chaque monstre
    # ======================================================================
    # Note: Ces fonctions utilisent des imports locaux pour éviter les
    # dépendances circulaires. Elles doivent être appelées depuis
    # populate_functions.py qui a accès aux fonctions request_*
    # ======================================================================

    def _build_orc_eye_of_gruumsh(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Orc Eye of Gruumsh"""
        # Cette fonction doit être implémentée dans populate_functions.py
        # car elle dépend de request_damage_type, request_spell, etc.
        raise NotImplementedError(
            "Cette fonction doit être appelée depuis populate_functions.py "
            "avec les bonnes dépendances"
        )

    def _build_ogre_bolt_launcher(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Ogre Bolt Launcher"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_ogre_battering_ram(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Ogre Battering Ram"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_hobgoblin_captain(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Hobgoblin Captain"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_piercer(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Piercer"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_illusionist(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Illusionist"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_goblin_boss(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Goblin Boss"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_xvart(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Xvart"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_kobold_inventor(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Kobold Inventor"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_half_ogre(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Half-ogre"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_water_weird(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Water Weird"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_apprentice_wizard(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Apprentice Wizard"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_orc_war_chief(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Orc War Chief"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_deathlock(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Deathlock"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_allip(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Allip"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_orog(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Orog"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_warlock_great_old_one(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Warlock of the Great Old One"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_star_spawn_grue(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Star Spawn Grue"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_star_spawn_mangler(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Star Spawn Mangler"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_adult_oblex(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Adult Oblex"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_vampiric_mist(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Vampiric Mist"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_spawn_of_kyuss(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Spawn of Kyuss"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_hobgoblin_warlord(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Hobgoblin Warlord"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_duergar_mind_master(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Duergar Mind Master"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_duergar_screamer(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Duergar Screamer"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_duergar_kavalrachni(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Duergar Kavalrachni"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_female_steeder(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Female Steeder"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_succubus(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Succubus"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_incubus(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Incubus"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_sea_hag(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Sea Hag"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_kuotoa_archpriest(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Kuo-toa Archpriest"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_kuotoa(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Kuo-toa"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_kuotoa_whip(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Kuo-toa Whip"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_sahuagin_baron(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Sahuagin Baron"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_sahuagin_priestess(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Sahuagin Priestess"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_sea_spawn(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Sea Spawn"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_yuanti_pureblood(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Yuan-ti Pureblood"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_firenewt_warlock(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Firenewt Warlock of Imix"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_firenewt_warrior(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Firenewt Warrior"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_yuanti_malison(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Yuan-ti Malison"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_yuanti_broodguard(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Yuan-ti Broodguard"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_ogre_chain_brute(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Ogre Chain Brute"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_young_kruthik(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Young Kruthik"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_adult_kruthik(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Adult Kruthik"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_gnoll(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Gnoll"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_maw_demon(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Maw Demon"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")

    def _build_yuanti_pit_master(self) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
        """Construit les actions pour Yuan-ti Pit Master"""
        raise NotImplementedError("Voir _build_orc_eye_of_gruumsh")


# Instance globale
_builder_instance: Optional[SpecialMonsterActionsBuilder] = None


def get_builder() -> SpecialMonsterActionsBuilder:
    """
    Récupère l'instance globale du builder

    :return: Instance du builder
    """
    global _builder_instance
    if _builder_instance is None:
        _builder_instance = SpecialMonsterActionsBuilder()
    return _builder_instance


def get_special_monster_actions(monster_name: str, use_json_fallback: bool = True) -> Tuple[List['Action'], List['SpecialAbility'], Optional['SpellCaster']]:
    """
    Récupère les actions spéciales d'un monstre étendu

    Cette fonction essaie d'abord d'utiliser les définitions manuelles,
    puis extrait automatiquement depuis les fichiers JSON si disponible.

    :param monster_name: Nom du monstre
    :param use_json_fallback: Si True, essaie l'extraction JSON comme fallback
    :return: (actions, special_abilities, spell_caster)

    Exemple:
        >>> actions, abilities, spellcaster = get_special_monster_actions("Goblin Boss")
        >>> print(f"Actions: {len(actions)}")
        Actions: 3
    """
    builder = get_builder()
    return builder.get_monster_actions(monster_name, use_json_fallback=use_json_fallback)


if __name__ == "__main__":
    # Test du module
    builder = SpecialMonsterActionsBuilder()

    print("=== Monstres implémentés ===")
    implemented = builder.get_implemented_monsters()
    print(f"Total: {len(implemented)}")
    for i, monster in enumerate(sorted(implemented), 1):
        print(f"{i:3d}. {monster}")

