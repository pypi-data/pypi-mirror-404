# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2026-01-31

### Added
- `simple_character_generator(..., strict_class_prereqs=True, max_attempts=10)` :
  - Nouveau paramètre `strict_class_prereqs` (bool) qui contrôle le comportement lors de
    la création d'un personnage avec une `class_name` explicite.
  - Par défaut (`strict_class_prereqs=True`) : si les caractéristiques ne remplissent
    pas les prérequis de la classe, la fonction lève une `ValueError` (comportement strict).
  - Si `strict_class_prereqs=False` : le générateur peut automatiquement reroller les
    caractéristiques jusqu'à `max_attempts` pour satisfaire la classe demandée.
- Lorsque `class_name` n'est pas fourni, `simple_character_generator` choisit désormais
  une classe compatible avec les caractéristiques tirées (ré-essais limités par `max_attempts`).
- Mise à jour de l'exemple `examples/combat_system.py` pour autoriser le reroll lors de la
  création du paladin d'exemple (utilisation de `strict_class_prereqs=False`) afin d'éviter
  des plantages non souhaités dans les démonstrations.
- Réutilisation centralisée des règles de prérequis de classes via
  `dnd_5e_core.classes.multiclass.can_multiclass_into` (évite la duplication des règles).

### Changed
- `dnd_5e_core/data/loaders.py` :
  - Validation des prérequis de classe lors de la génération simple de personnages.
  - Ajout d'une logique de reroll contrôlée (explicit class + non-strict mode, et choix de
    classe compatible si la classe n'est pas fournie).
  - Correction d'un import typing inutile (réduction des warnings linter).
- `examples/combat_system.py` : adaptation pour utiliser le nouveau paramètre dans l'exemple
  du paladin afin que les démos locales s'exécutent de façon robuste.

### Fixed
- Correction d'un bug : `can_multiclass_into` reçoit maintenant les scores d'ability bruts
  (`Abilities`) au lieu des modificateurs d'ability (fixe des refus erronés de validation).
- Amélioration de la robustesse des exemples : rappel d'utiliser `PYTHONPATH=.` pour forcer
  l'exécution du code local lors du développement (évite d'importer une version installée
  depuis le virtualenv).

### Notes
- Le comportement par défaut reste conservateur (strict) pour éviter d'assigner par erreur
  une classe incompatible dans des usages automatisés ou pipelines de publication.
- Pour exécuter les exemples localement avec les modifications source :

```bash
PYTHONPATH=. python examples/combat_system.py
```


## [0.4.2] - 2026-01-22

### Added
- `scripts/check_changelog.py` : utilitaire pour vérifier que `CHANGELOG.md` contient
  une entrée correspondant à la version définie dans `pyproject.toml`. Le script est
  utilisé pour bloquer les builds/publications si l'entrée manque.
- `.github/workflows/check-changelog.yml` : workflow GitHub Actions minimal pour
  valider automatiquement la présence de l'entrée de changelog sur les PRs et les pushes
  vers `main`.
- `.pre-commit-config.yaml` : hook local `check-changelog` qui exécute
  `python3 scripts/check_changelog.py` au moment du commit.

### Changed
- `build_package.sh` et `publish_final.sh` : ajout d'un contrôle qui exécute
  `scripts/check_changelog.py` avant la construction/publication pour empêcher les
  publications sans entrée de changelog.
- `requirements-dev.txt` : ajout de `pre-commit` aux dépendances de développement.
- `CONTRIBUTING.md` : ajout d'une section "CHANGELOG & Release checklist" décrivant
  la règle de mise à jour du changelog, les étapes locales à suivre et l'exemple de
  format d'entrée.

### Notes
- Le CI bloquera désormais les merges vers `main` si la section de changelog
  correspondante est absente. En cas d'exceptions (ex : documentation mineure),
  ajoutez une courte note "No notable changes" sous la nouvelle en-tête de version.


## [0.4.1] - 2026-01-21

### Fixed - Magic Items Loader
- **load_magic_item()** - Removed API fallback, use local JSON only (-12 lines, 100% offline)
- **list_magic_items()** - Simplified to single return statement (-8 lines, no network calls)
- **Performance** - Faster loading, no external dependencies for magic items
- **Reliability** - Works offline, no network errors

## [0.4.0] - 2026-01-20

### Validated
- **Phase 3 & 4: Magic Items & Multiclassing** ✅
  - Magic Items system already fully implemented
  - 10+ predefined magic items ready to use
  - Defensive items (Ring/Cloak of Protection, Bracers of Defense)
  - Offensive items (Wand of Magic Missiles, Wand of Paralysis, Poisoned Dagger)
  - Healing items (Staff of Healing)
  - Stat-enhancing items (Belt of Giant Strength, Amulet of Health)
  - Multiclassing system fully implemented
  - Ability prerequisites validation
  - Spell slots calculation for multiclass spellcasters
  
### Tests
- **test_phase3_phase4.py** - 5 comprehensive tests (100% passing ✅)
  - Tests magic items creation (10 items)
  - Tests magic items with characters
  - Tests multiclass prerequisites
  - Tests multiclass spell slots calculation
  - Tests defensive capabilities

### Documentation
- Phase 3 & 4 validated as already implemented
- No development required - code fully functional

## [0.3.0] - 2026-01-20

### Added
- **Phase 2: Automatic Condition Detection & Application** 🎯
  - ConditionParser automatically detects conditions from monster action descriptions
  - Supports detection of: poisoned, restrained, paralyzed, stunned, frightened, grappled, blinded, charmed, prone, incapacitated
  - DC and ability type automatically extracted from descriptions (e.g., "DC 12 Constitution saving throw")
  - Conditions automatically applied during combat when monsters attack
  - Saving throw system for escaping conditions
  - `extract_conditions_from_action()` integrated into monster loading
  
### Changed
- **Monster Loading** - Enhanced to automatically parse and add condition effects
  - All monster actions are now parsed for conditions during load
  - Conditions stored in action.effects list
  - Ready for automatic application in combat

### Tests
- **test_phase2_parser.py** - 6 comprehensive tests (100% passing ✅)
  - Tests condition detection for all major condition types
  - Tests DC and ability parsing
  - Tests condition application to characters
  - Tests saving throw mechanics

### Documentation
- Phase 2 validates that condition system is fully functional
- ConditionParser proven to work with real D&D 5e action descriptions

## [0.2.9] - 2026-01-20

### Added
- **Phase 1: Automatic Class Abilities Integration** 🎯
  - `simple_character_generator()` now automatically applies class abilities
  - New parameters: `apply_class_abilities` and `apply_racial_traits` (both default to `True`)
  - Fighter: Extra Attack (2 at L5, 3 at L11, 4 at L20) applied automatically
  - Barbarian: Rage system initialized (uses per day based on level)
  - Rogue: Sneak Attack dice calculated automatically
  - Monk: Ki points initialized (equal to level)
  - Paladin: Lay on Hands pool initialized (level × 5)
  - Ranger: Extra Attack at level 5
  - All characters marked with `has_class_abilities=True` flag

- **Phase 1: Automatic Racial Traits Integration** 🎯
  - Elf: Darkvision (60ft), Fey Ancestry, Trance, Keen Senses applied automatically
  - Dwarf: Darkvision (60ft), Dwarven Resilience, Stonecunning, Dwarven Toughness
  - Halfling: Lucky, Brave, Halfling Nimbleness
  - Gnome: Darkvision (60ft), Gnome Cunning
  - Half-Orc: Darkvision (60ft), Relentless Endurance, Savage Attacks
  - Tiefling: Darkvision (60ft), Hellish Resistance
  - Dragonborn: Breath Weapon uses initialized
  - All characters marked with `has_racial_traits=True` flag

- **Test Suite for Phase 1**
  - `tests/test_phase1_integration.py` - 8 comprehensive tests
  - Validates automatic application of abilities and traits
  - Tests backward compatibility (disable features)
  - All tests passing ✅

### Changed
- **Character.multi_attacks Property**
  - Modified to prioritize explicit `multi_attack_bonus` when `has_class_abilities=True`
  - Maintains backward compatibility with old calculation method
  - Prevents double-counting of extra attacks

### Documentation
- **CODE_REVIEW_REPORT.md** - Comprehensive code review (20+ pages)
  - Analysis of package usage in DnD-5th-Edition-API and DnD5e-Scenarios
  - Identified underutilized features (ClassAbilities, RacialTraits, Conditions, etc.)
  - Technical solutions with before/after code examples
- **INTEGRATION_PLAN.md** - Technical implementation plan for Phase 1
- **EXECUTIVE_SUMMARY.md** - Executive summary with priorities and ROI estimates

## [0.2.8] - 2026-01-20

### Fixed
- **Spell Loading Fix** - Correction critique du chargement des sorts dans `simple_character_generator`
  - Déplacement du répertoire `collections` dans `dnd_5e_core/data/collections` pour inclusion dans le package
  - Correction de l'indentation dans `loaders.py` pour créer `spell_caster` même si `get_spell_slots_for_level()` échoue
  - Initialisation de `learned_spells` pour éviter les erreurs de référence
  - Amélioration des messages d'erreur pour le débogage du chargement des sorts
  - Mise à jour de `MANIFEST.in` pour inclure les fichiers collections dans le package distribué

### Changed
- **Package Data Structure** - Réorganisation des données pour une distribution correcte
  - Les données JSON sont maintenant correctement incluses dans le package PyPI
  - Auto-détection améliorée des répertoires de données

## [0.2.7] - 2026-01-18

### Added
- **PyPI Optimization** - Amélioration complète des métadonnées PyPI
  - Description mise à jour avec les nouvelles fonctionnalités majeures
  - 32 mots-clés ajoutés pour une meilleure découvrabilité
  - Métadonnées complètes pour le positionnement "Ultimate D&D 5e Rules Engine"

### Changed
- **CHANGELOG Synthesis** - Synthèse des anciennes versions pour lisibilité
  - Réduction de ~570 à ~200 lignes (65% de réduction)
  - Conservation des changements majeurs
  - Suppression des détails techniques répétitifs

### Fixed
- **Version Consistency** - Synchronisation parfaite des versions
  - pyproject.toml, setup.py, et __init__.py alignés
  - Prévention des conflits de publication PyPI

## [0.2.6] - 2026-01-18

### Added
- **ClassAbilities** - Système complet des capacités de classe
  - 24 capacités implémentées pour toutes les classes
  - Barbarian: Rage, Reckless Attack
  - Fighter: Action Surge, Second Wind, Extra Attack
  - Rogue: Sneak Attack, Cunning Action, Uncanny Dodge
  - Monk: Ki Points, Flurry of Blows, Martial Arts
  - Cleric: Channel Divinity
  - Paladin: Lay on Hands, Divine Smite
  - Bard: Bardic Inspiration
  - Sorcerer: Sorcery Points, Metamagic
  - Ranger: Hunter's Mark
  - Warlock: Eldritch Invocations

- **RacialTraits** - Système complet des traits raciaux
  - 20 traits implémentés pour toutes les races
  - Elf: Darkvision, Fey Ancestry, Trance, Keen Senses, Mask of the Wild
  - Dwarf: Dwarven Resilience, Stonecunning, Dwarven Toughness
  - Halfling: Lucky, Brave, Halfling Nimbleness, Naturally Stealthy
  - Human: Versatility
  - Dragonborn: Breath Weapon, Damage Resistance
  - Gnome: Gnome Cunning
  - Half-Orc: Relentless Endurance, Savage Attacks
  - Tiefling: Hellish Resistance, Infernal Legacy

- **Subclass System** - Sous-classes et multiclassing
  - Support de 40+ sous-classes (Champion, Evocation, Life Domain, etc.)
  - Support de 20+ sous-races (High Elf, Hill Dwarf, etc.)
  - Système de multiclassing avec calcul automatique des spell slots
  - `MulticlassCharacter` pour gérer plusieurs classes

### Fixed
- Parsing robuste des `saving_throws` (gestion des AbilityType)
- Parsing sécurisé des données JSON de subclasses et subraces
- Corrections dans le système de progression des classes

### Changed
- Archivage de 36 fichiers obsolètes vers `archive/2026-01-docs/` et `archive/2026-01-scripts/`
- Structure du projet épurée (6 documents MD essentiels à la racine)
- Script `build_package.sh` amélioré avec options complètes

## [0.2.4] - 2026-01-18

### Added
- **ConditionParser** - Système de parsing automatique des conditions depuis descriptions textuelles
- **Magic Items with Conditions** - Objets magiques appliquant des conditions
- **Monster Condition Application** - Application automatique des conditions par les monstres

### Changed
- **Monster.attack()** - Amélioration de l'application des conditions

## [0.2.3] - 2026-01-18

### Changed
- **ARCHITECTURE MAJEURE** - Réorganisation complète des données dans le package
- Tous les fichiers JSON (monsters, spells, equipment, etc.) sont maintenant dans `dnd_5e_core/data/`
- Les données sont **toujours incluses** dans le package installé

## [0.2.2] - 2026-01-18

### Fixed
- **Condition Class Implementation** - Migration complète de `Condition` depuis `dao_classes.py`
- 14 fonctions helper pour toutes les conditions D&D 5e standard

## [0.2.1] - 2026-01-18

### Added
- **Conditions System** - Système complet de conditions D&D 5e
- **Magic Items System** - Objets magiques avec actions de combat
- **Defensive Spells System** - Sorts défensifs avec bonus AC et sauvegardes

## [0.2.0] - 2026-01-18

### Added
- **Magic Items System** - Objets magiques avec bonus passifs et actions actives
- **Defensive Spells System** - Sorts défensifs (Shield, Mage Armor, etc.)
- 8 objets magiques prédéfinis (Ring of Protection, Wand of Magic Missiles, etc.)

## [0.1.9] - 2026-01-17

### Changed
- **BREAKING CHANGE**: Toutes les fonctions `load_*()` retournent maintenant des objets au lieu de dictionnaires
- Migration complète vers une API orientée objet

## [0.1.4] - 2026-01-05

### Added
- **Implémentation complète** de toutes les classes vides (28 classes migrées)
- **Système d'expérience** complet avec niveaux 1-20
- **Multiclassing** avec prérequis et calculs de spell slots
- **Challenge Rating** et difficulté de rencontres
- **26+ fonctions utilitaires** (dice rolling, modifiers, combat, etc.)
- **200+ constantes** du jeu D&D 5e

## [0.1.3] - 2026-01-05

### Fixed
- Inclusion correcte des données de monstres dans le package distribué

## [0.1.2] - 2026-01-05

### Added
- **Documentation complète** pour la publication PyPI et GitHub
- Métadonnées PyPI complètes avec 11 mots-clés

## [0.1.1] - 2026-01-03

### Added
- Métadonnées PyPI complètes pour meilleure découvrabilité
- Configuration GitHub "About" section

## [0.1.0] - 2025-12-24

### Added
- **Intégration majeure** du répertoire Collections D&D 5e API (26 index files)
- **Intégration majeure** des données JSON D&D 5e (8.7 MB, 2000+ fichiers)
- Structure de package initiale avec entités, races, classes, équipements
- Système de combat avec actions et capacités spéciales
- Chargeur de données depuis fichiers JSON locaux

### Changed
- Auto-détection des répertoires de données (plus de configuration manuelle)
- Priorité de chargement : package inclus → API DnD-5th-Edition-API → ./data

## [0.1.0] - 2025-01-XX

### Added
- Première release alpha
- Mécaniques de base D&D 5e implémentées
