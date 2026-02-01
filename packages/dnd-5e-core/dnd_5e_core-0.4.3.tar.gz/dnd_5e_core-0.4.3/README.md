# dnd-5e-core

[![PyPI version](https://badge.fury.io/py/dnd-5e-core.svg)](https://pypi.org/project/dnd-5e-core/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Complete D&D 5e Rules Engine** - 24 Class Abilities, 20 Racial Traits, 40+ Subclasses, Multiclassing, Advanced Combat, 332 Monsters, 319+ Spells, 49 Magic Items, Treasure System, Conditions. **100% Offline** with 8.7MB bundled data.

## 🚀 Quick Start

```bash
pip install dnd-5e-core
```

```python
from dnd_5e_core.data.loaders import simple_character_generator
from dnd_5e_core import load_monster
from dnd_5e_core.combat import CombatSystem

# Create characters
fighter = simple_character_generator(5, "human", "fighter", "Conan")
wizard = simple_character_generator(5, "elf", "wizard", "Gandalf")

# Load monster
orc = load_monster("orc")

# Combat
combat = CombatSystem(verbose=True)
party = [fighter, wizard]
combat.character_turn(wizard, party, [orc], party)
```

## ✨ Features

### Complete D&D 5e Implementation
- **24 Class Abilities** - Rage, Extra Attack, Sneak Attack, Ki Points, etc.
- **20 Racial Traits** - Darkvision, Lucky, Fey Ancestry, Relentless Endurance, etc.
- **40+ Subclasses** - Champion, Evocation, Life Domain, etc.
- **Multiclassing** - Full support with spell slot calculation
- **Advanced Combat** - Automatic spellcasting, conditions, special attacks
- **49 Magic Items** - Rings, Wands, Weapons, Armor with magical properties
- **Treasure System** - DMG-compliant treasure generation by CR/level
- **Conditions System** - Poisoned, Paralyzed, Frightened, etc.

### Bundled Data (8.7MB)
- **332 Monsters** with complete stats and abilities
- **319+ Spells** with full descriptions and mechanics
- **65+ Weapons** with damage, properties, ranges
- **30+ Armors** with AC calculations
- **237+ Equipment** items
- **100% Offline** - No API calls required

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete API for external projects
- **[Examples & Demos](https://github.com/codingame-team/DND5e-Test)** - Working examples
- **[Full Applications](https://github.com/codingame-team/DnD-5th-Edition-API)** - Complete games

## 🎮 Examples

### Character Creation
```python
from dnd_5e_core.data.loaders import simple_character_generator

# Automatic abilities and traits
fighter = simple_character_generator(5, "dwarf", "fighter", "Gimli")
# Gets: Extra Attack, Darkvision, Dwarven Resilience, etc.

wizard = simple_character_generator(5, "elf", "wizard", "Elrond")
# Gets: Spellcasting, Darkvision, Fey Ancestry, etc.
```

### Combat System
```python
from dnd_5e_core.combat import CombatSystem

combat = CombatSystem(verbose=True)

# Automatic combat decisions:
# - Spellcasters cast spells from back row
# - Fighters use weapons and special attacks
# - Healing spells used on wounded allies
# - Conditions applied automatically

combat.character_turn(character, party, monsters, party)
combat.monster_turn(monster, monsters, party, party, round_num)
```

### Equipment & Magic Items
```python
from dnd_5e_core.equipment import get_magic_item, get_special_weapon

# Magic items
ring = get_magic_item("ring-of-protection")  # +1 AC, +1 saves
wand = get_magic_item("wand-of-magic-missiles")  # 7 charges

# Magical weapons
flame_tongue = get_special_weapon("flame-tongue")  # +1, +2d6 fire
vorpal_sword = get_special_weapon("vorpal-sword")  # Legendary

character.equip(flame_tongue)
```

### Treasure Generation
```python
from dnd_5e_core.mechanics import calculate_treasure_hoard

treasure = calculate_treasure_hoard(
    encounter_level=5,
    difficulty="hard",
    cr=5,
    include_items=True
)

print(f"Gold: {treasure['gold']} gp")
print(f"Items: {[item.name for item in treasure['items']]}")
print(f"Total value: {treasure['total_value']} gp")
```

## 🏗️ Architecture

**UI-Agnostic Design** - Use with any interface:

```python
# Your game provides UI
import pygame  # or tkinter, web framework, etc.

# dnd-5e-core provides game logic
from dnd_5e_core import Character, Monster, CombatSystem

# Game loop
while running:
    # Handle input (your code)
    action = get_user_input()
    
    # Process game logic (dnd-5e-core)
    if action == "attack":
        damage = player.attack(monster)
    
    # Render (your code)
    render_game_state(player, monster)
```

## 🔧 Advanced Usage

### Multiclassing
```python
from dnd_5e_core.mechanics.subclass_system import MulticlassCharacter

# Fighter 5 / Wizard 3
gish = MulticlassCharacter("Elric")
for _ in range(5): gish.add_class_level('fighter')
for _ in range(3): gish.add_class_level('wizard')

print(f"Spell slots: {gish.get_spell_slots_multiclass()}")
```

### Encounter Building
```python
from dnd_5e_core.mechanics import select_monsters_by_encounter_table

monsters, difficulty = select_monsters_by_encounter_table(
    encounter_level=5,
    available_monsters=all_monsters,
    allow_pairs=True
)
```

### Extended Monsters
```python
from dnd_5e_core.entities import get_extended_monster_loader

loader = get_extended_monster_loader()
goblins = loader.search_monsters(name_contains="goblin", min_cr=1)
```

## 📦 Installation

### For Users
```bash
pip install dnd-5e-core
```

### For Developers
```bash
git clone https://github.com/codingame-team/dnd-5e-core.git
cd dnd-5e-core
pip install -e .[dev]
```

## 🧪 Testing

```bash
pytest tests/
python tests/verify_package.py
```

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🔗 Related Projects

- **[DND5e-Test](https://github.com/codingame-team/DND5e-Test)** - Examples and demos
- **[DnD-5th-Edition-API](https://github.com/codingame-team/DnD-5th-Edition-API)** - Complete applications
- **[DnD5e-Scenarios](https://github.com/codingame-team/DnD5e-Scenarios)** - 36 D&D scenarios
