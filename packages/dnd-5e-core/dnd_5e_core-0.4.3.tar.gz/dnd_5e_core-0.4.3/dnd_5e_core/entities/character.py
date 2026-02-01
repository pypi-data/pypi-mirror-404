"""
D&D 5e Core - Character Entity
Player character class for D&D 5e
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import floor
from random import randint, choice
from typing import List, Optional, TYPE_CHECKING

# Import classes needed at runtime (for isinstance checks)
from ..equipment.weapon import Weapon
from ..equipment.armor import Armor

if TYPE_CHECKING:
	from ..abilities.abilities import Abilities
	from ..races.race import Race
	from ..races.subrace import SubRace
	from ..classes.class_type import ClassType
	from ..classes.proficiency import Proficiency, ProfType
	from ..equipment.equipment import Equipment
	from ..equipment.potion import HealingPotion, SpeedPotion, StrengthPotion, Potion
	from ..spells.spellcaster import SpellCaster
	from ..spells.spell import Spell
	from ..combat.condition import Condition
	from ..mechanics.dice import DamageDice
	from .monster import Monster


@dataclass
class Character:
	"""
	A player character in D&D 5e.

	Characters have all the complexity of D&D 5e:
	- Race and class
	- Abilities and proficiencies
	- Equipment and inventory
	- Spellcasting (if applicable)
	- Conditions and effects
	- XP and leveling

	Note: This is game logic only. UI layer handles Sprite positioning.
	"""
	name: str
	race: 'Race'
	subrace: Optional['SubRace']
	ethnic: str
	gender: str
	height: str
	weight: str
	age: int
	class_type: 'ClassType'
	proficiencies: List['Proficiency']
	abilities: 'Abilities'
	ability_modifiers: 'Abilities'
	hit_points: int
	max_hit_points: int
	speed: int
	haste_timer: float
	hasted: bool
	xp: int
	level: int
	inventory: List[Optional['Equipment']]
	gold: int
	sc: Optional['SpellCaster'] = None
	conditions: Optional[List['Condition']] = None
	st_advantages: Optional[List[str]] = None
	ac_bonus: int = 0
	multi_attack_bonus: int = 0
	str_effect_modifier: int = -1
	str_effect_timer: float = 0.0
	status: str = "OK"
	id_party: int = -1
	OUT: bool = False
	kills: List['Monster'] = field(default_factory=list)

	def __eq__(self, other):
		if not isinstance(other, Character):
			return NotImplemented
		return self.name == other.name

	def __repr__(self):
		race_display = self.subrace.name if self.subrace else self.race.name
		weapon_name = self.weapon.name if self.weapon else "None"
		armor_name = self.armor.name if self.armor else "None"
		return f"{self.name} (Level {self.level} {race_display} {self.class_type.name}, AC {self.armor_class}, HP {self.hit_points}/{self.max_hit_points})"

	# ===== Properties =====

	@property
	def is_alive(self) -> bool:
		"""Check if character is alive"""
		return self.hit_points > 0

	@property
	def is_dead(self) -> bool:
		"""Check if character is dead"""
		return self.hit_points <= 0

	@property
	def weapon(self) -> Optional['Weapon']:
		"""Get equipped weapon"""
		equipped_weapons = [item for item in self.inventory if item and isinstance(item, Weapon) and item.equipped]
		return equipped_weapons[0] if equipped_weapons else None

	@property
	def armor(self) -> Optional['Armor']:
		"""Get equipped armor (not shield)"""
		from ..equipment.armor import Armor
		# Treat shields by category.index == 'shield' to include magical shields
		equipped_armors = [item for item in self.inventory if item and isinstance(item, Armor) and item.equipped and (not hasattr(item, 'category') or getattr(item.category, 'index', None) != 'shield')]
		return equipped_armors[0] if equipped_armors else None

	@property
	def shield(self) -> Optional['Armor']:
		"""Get equipped shield"""
		from ..equipment.armor import Armor
		# identify shields by their equipment category index == 'shield'
		equipped_shields = [item for item in self.inventory if item and isinstance(item, Armor) and item.equipped and hasattr(item, 'category') and getattr(item.category, 'index', None) == 'shield']
		return equipped_shields[0] if equipped_shields else None

	@property
	def healing_potions(self) -> List['HealingPotion']:
		"""Get all healing potions in inventory"""
		from ..equipment.potion import HealingPotion
		return [item for item in self.inventory if item and isinstance(item, HealingPotion)]

	@property
	def speed_potions(self) -> List['SpeedPotion']:
		"""Get all speed potions in inventory"""
		from ..equipment.potion import SpeedPotion
		return [item for item in self.inventory if item and isinstance(item, SpeedPotion)]

	@property
	def is_spell_caster(self) -> bool:
		"""Check if character can cast spells"""
		return self.sc is not None

	@property
	def dc_value(self) -> int:
		"""Calculate spell save DC"""
		if not self.is_spell_caster:
			return 0

		spell_ability_mod = self.ability_modifiers.get_value_by_index(self.class_type.spellcasting_ability)
		prof_bonus = self.proficiency_bonus
		return 8 + spell_ability_mod + prof_bonus

	@property
	def proficiency_bonus(self) -> int:
		"""Calculate proficiency bonus based on level"""
		return self.class_type.get_proficiency_bonus(self.level)

	@property
	def in_dungeon(self) -> bool:
		"""Check if character is in a dungeon"""
		return self.id_party != -1

	def _get_ability(self, attr: str) -> int:
		"""Get total ability score (base + racial bonus)"""
		base = getattr(self.abilities, attr)
		racial_bonus = self.race.ability_bonuses.get(attr, 0)
		if self.subrace:
			racial_bonus += self.subrace.ability_bonuses.get(attr, 0)
		return base + racial_bonus

	@property
	def strength(self) -> int:
		"""Get effective strength (including potion effects)"""
		if self.str_effect_modifier != -1:
			return self.str_effect_modifier
		return self._get_ability("str")

	@property
	def dexterity(self) -> int:
		"""Get effective dexterity"""
		return self._get_ability("dex")

	@property
	def constitution(self) -> int:
		"""Get effective constitution"""
		return self._get_ability("con")

	@property
	def intelligence(self) -> int:
		"""Get effective intelligence"""
		return self._get_ability("int")

	@property
	def wisdom(self) -> int:
		"""Get effective wisdom"""
		return self._get_ability("wis")

	@property
	def charism(self) -> int:
		"""Get effective charisma"""
		return self._get_ability("cha")

	@property
	def armor_class(self):
		from ..equipment.magic_item import MagicItem

		# Separate shields from armors using category
		equipped_armors: List[Armor] = [
			item for item in self.inventory
			if isinstance(item, Armor) and item.equipped
			and hasattr(item, 'category') and item.category
			and item.category.index != "shield"
		]
		equipped_shields: List[Armor] = [
			item for item in self.inventory
			if isinstance(item, Armor) and item.equipped
			and hasattr(item, 'category') and item.category
			and item.category.index == "shield"
		]

		# Base AC from armor or 10 if no armor
		ac: int = (sum([item.armor_class["base"] for item in equipped_armors]) if equipped_armors else 10)

		# Shield AC stacks with armor
		ac += sum([item.armor_class["base"] for item in equipped_shields])

		# Add magic armor bonuses
		for armor in equipped_armors + equipped_shields:
			if hasattr(armor, 'armor_bonus'):
				ac += armor.armor_bonus

		# Add magic item bonuses (rings, amulets, cloaks, bracers, etc.)
		magic_items = [item for item in self.inventory if isinstance(item, MagicItem) and item.equipped]
		for item in magic_items:
			if item.can_use():  # Check if attuned if required
				ac += item.ac_bonus

		# Add character's ac_bonus attribute if exists
		if hasattr(self, "ac_bonus"):
			ac += self.ac_bonus

		return ac

	@property
	def damage_dice(self) -> 'DamageDice':
		"""Get damage dice from equipped weapon"""
		from ..mechanics.dice import DamageDice

		if not self.weapon:
			return DamageDice("1d2", 0)  # Unarmed

		# Use two-handed damage if available and no shield equipped
		# For versatile weapons (e.g., Longsword: 1d8 one-handed, 1d10 two-handed)
		if self.weapon.damage_dice_two_handed and not self.shield:
			return self.weapon.damage_dice_two_handed

		return self.weapon.damage_dice

	# ===== Methods =====

	def can_cast(self, spell: Spell) -> bool:
		return self.is_spell_caster and spell in self.sc.learned_spells and (self.sc.spell_slots[spell.level - 1] > 0 or spell.is_cantrip)

	def take_damage(self, damage: int, damage_type: str = "bludgeoning"):
		"""
		Take damage, applying resistances and immunities from magic armor

		Args:
			damage: Amount of damage
			damage_type: Type of damage (fire, cold, slashing, etc.)
		"""
		from ..equipment.armor import ArmorData

		actual_damage = damage

		# Check for damage immunities from armor
		if self.armor and isinstance(self.armor, ArmorData):
			if hasattr(self.armor, 'damage_immunities') and self.armor.damage_immunities:
				if damage_type in self.armor.damage_immunities:
					actual_damage = 0
			if actual_damage > 0 and hasattr(self.armor, 'damage_resistances') and self.armor.damage_resistances:
				if damage_type in self.armor.damage_resistances:
					actual_damage = damage // 2

		# Check for resistances from magic items (weapons like Frost Brand)
		from ..equipment.weapon import WeaponData
		if actual_damage > 0 and self.weapon and isinstance(self.weapon, WeaponData):
			if hasattr(self.weapon, 'resistances_granted') and self.weapon.resistances_granted:
				if damage_type in self.weapon.resistances_granted:
					actual_damage = actual_damage // 2

		self.hit_points = max(0, self.hit_points - actual_damage)
		return actual_damage

	def calculate_weapon_damage(self, target: Optional['Monster'] = None) -> int:
		"""
		Calculate total weapon damage including magic bonuses

		Args:
			target: Target monster (for creature-specific bonuses)

		Returns:
			Total damage roll
		"""
		from ..mechanics.dice import DamageDice
		from ..equipment.weapon import WeaponData

		# Base weapon damage
		base_damage = self.damage_dice.roll()

		# Add magic weapon bonus damage
		if self.weapon and isinstance(self.weapon, WeaponData):
			# Add flat damage bonus (+1/+2/+3 weapons)
			base_damage += self.weapon.damage_bonus

			# Add elemental bonus damage (e.g., Flame Tongue: +2d6 fire)
			if self.weapon.bonus_damage:
				for damage_type, dice_str in self.weapon.bonus_damage.items():
					bonus_dice = DamageDice(dice_str)
					base_damage += bonus_dice.roll()

			# Add creature-type bonus damage (e.g., Giant Slayer: +2d6 vs giants)
			if self.weapon.creature_type_damage and target and hasattr(target, 'creature_type'):
				if target.creature_type and target.creature_type in self.weapon.creature_type_damage:
					dice_str = self.weapon.creature_type_damage[target.creature_type]
					bonus_dice = DamageDice(dice_str)
					creature_bonus = bonus_dice.roll()
					base_damage += creature_bonus

		return base_damage

	def heal(self, amount: int):
		"""Heal hit points"""
		self.hit_points = min(self.max_hit_points, self.hit_points + amount)

	@property
	def is_full(self) -> bool:
		return all(item for item in self.inventory)

	def get_best_slot_level(self, heal_spell: Spell, target: Character) -> int:
		max_slot_level = max(i for i, slot in enumerate(self.sc.spell_slots) if slot)
		best_slot_level = None
		max_score = 0
		for slot_level in range(heal_spell.level - 1, max_slot_level + 1):
			dd: DamageDice = heal_spell.get_heal_effect(slot_level, self.sc.ability_modifier)
			score = min(target.hit_points + dd.avg, target.max_hit_points) / dd.avg
			if score > max_score:
				max_score = score
				best_slot_level = slot_level
		return best_slot_level

	def cast_heal(self, spell: Spell, slot_level: int, targets: List[Character]):
		ability_modifier: int = (self.get_ability_score(self.class_type.spellcasting_ability) - 10) // 2
		dd: DamageDice = spell.get_heal_effect(slot_level=slot_level, ability_modifier=ability_modifier)
		for char in targets:
			if char.hit_points < char.max_hit_points:
				hp_gained: int = min(dd.roll(), char.max_hit_points - char.hit_points)
				char.hit_points += hp_gained

	def gain_level(self, tome_spells: List = None, verbose: bool = False) -> tuple:
		"""
		Gain a level with optional ability changes and spell learning.

		Args:
			tome_spells: List of Spell objects available to learn from (for spellcasters)
			verbose: If True, print messages to console. If False, only return messages.

		Returns:
			tuple: (messages: str, new_spells: List[Spell])
				- messages: Newline-separated string of level-up events
				- new_spells: List of newly learned spells (empty if not a spellcaster)
		"""
		from random import randint
		from copy import deepcopy

		display_msg: List[str] = []
		new_spells = []

		# Increase level
		self.level += 1

		# Calculate HP gain
		level_up_hit_die = {12: 7, 10: 6, 8: 5, 6: 4}
		hp_gained = randint(1, level_up_hit_die[self.class_type.hit_die]) + self.ability_modifiers.con
		hp_gained = max(1, hp_gained)
		self.max_hit_points += hp_gained
		self.hit_points += hp_gained

		display_msg.append(f"New level #{self.level} gained!!!")
		display_msg.append(f"{self.name} gained {hp_gained} hit points")

		# Handle ability score changes due to aging (PROCEDURE GAINLOST from original Wizardry)
		attrs = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charism"]
		for attr in attrs:
			val = self.abilities.get_value_by_name(name=attr)
			if randint(0, 3) % 4:  # 75% chance
				if randint(0, 129) < self.age // 52:  # Age check (age in weeks)
					# Lose ability due to age
					if val == 18 and randint(0, 5) != 4:
						continue
					val -= 1
					if attr == "Constitution" and val == 2:
						display_msg.append("** YOU HAVE DIED OF OLD AGE **")
						self.status = "LOST"
						self.hit_points = 0
					else:
						display_msg.append(f"You lost {attr}")
				elif val < 18:
					# Gain ability
					val += 1
					display_msg.append(f"You gained {attr}")
			self.abilities.set_value_by_name(name=attr, value=val)

		# Handle spell learning for spellcasters
		if self.class_type.can_cast and tome_spells:
			available_spell_levels = [
				i + 1 for i, slot in enumerate(self.class_type.spell_slots[self.level]) if slot > 0
			]

			# Calculate new spells to learn
			if self.level > 1:
				new_spells_known_count = (
					self.class_type.spells_known[self.level - 1] -
					self.class_type.spells_known[self.level - 2]
				)
				new_cantrip_count = 0
				if self.class_type.cantrips_known:
					new_cantrip_count = (
						self.class_type.cantrips_known[self.level - 1] -
						self.class_type.cantrips_known[self.level - 2]
					)
			else:
				new_spells_known_count = self.class_type.spells_known[0] if self.class_type.spells_known else 0
				new_cantrip_count = self.class_type.cantrips_known[0] if self.class_type.cantrips_known else 0

			# Filter learnable spells
			learnable_spells = [
				s for s in tome_spells
				if s.level <= max(available_spell_levels)
				and s not in self.sc.learned_spells
				and hasattr(s, 'damage_type') and s.damage_type
			]

			# Update spell slots
			self.sc.spell_slots = deepcopy(self.class_type.spell_slots[self.level])

			# Sort by level (highest first)
			learnable_spells.sort(key=lambda s: s.level, reverse=True)

			# Learn new spells
			new_spells_count = 0
			while learnable_spells and (new_spells_known_count > 0 or new_cantrip_count > 0):
				learned_spell = learnable_spells.pop()

				if learned_spell.level == 0 and new_cantrip_count > 0:
					new_cantrip_count -= 1
					self.sc.learned_spells.append(learned_spell)
					new_spells.append(learned_spell)
					new_spells_count += 1
					display_msg.append(f"Learned cantrip: {learned_spell.name}")
				elif learned_spell.level > 0 and new_spells_known_count > 0:
					new_spells_known_count -= 1
					self.sc.learned_spells.append(learned_spell)
					new_spells.append(learned_spell)
					new_spells_count += 1
					display_msg.append(f"Learned spell: {learned_spell.name} (level {learned_spell.level})")

			if new_spells_count:
				display_msg.append(f"You learned {new_spells_count} new spell(s)!!!")
		elif self.class_type.can_cast:
			# Update spell slots even if no tome_spells provided
			if self.level <= len(self.class_type.spell_slots):
				self.sc.spell_slots = deepcopy(self.class_type.spell_slots[self.level])

		# Format messages
		messages = '\n'.join(display_msg)

		# Print if verbose
		if verbose:
			print(messages)

		return messages, new_spells

	def attack(self, monster, in_melee: bool = True, cast: bool = True, verbose: bool = False) -> tuple:
		"""
		Attack a monster with weapon or spell.

		Args:
			monster: Monster to attack
			in_melee: If True, melee combat. If False, ranged combat.
			cast: If True, can cast spells. If False, only weapon attacks.
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, damage: int)
		"""
		from random import randint

		display_msg: List[str] = []
		damage_roll = 0

		def prof_bonus(x):
			return x // 5 + 2 if x < 5 else (x - 5) // 4 + 3

		# Try to cast spell if possible
		castable_spells = []
		if self.is_spell_caster:
			cantrip_spells = [s for s in self.sc.learned_spells if not s.level]
			slot_spells = [s for s in self.sc.learned_spells if s.level and self.sc.spell_slots[s.level - 1] > 0 and hasattr(s, 'damage_type') and s.damage_type]
			castable_spells = cantrip_spells + slot_spells

		if cast and castable_spells and not in_melee:
			# Cast spell attack
			attack_spell = max(castable_spells, key=lambda s: s.level)
			spell_msg, damage_roll = self.cast_attack(attack_spell, monster, verbose=False)
			display_msg.append(spell_msg)
			if not attack_spell.is_cantrip:
				self.update_spell_slots(spell=attack_spell)
		else:
			# Weapon attack
			damage_multi = 0
			for _ in range(self.multi_attacks):
				if self.hit_points <= 0:
					break
				# Consider using magic item actions (wands, staves, necklace) at start of each attack
				from ..equipment.magic_item import MagicItem
				magic_actions = []
				for it in [i for i in self.inventory if i and getattr(i, 'equipped', False)]:
					if isinstance(it, MagicItem) and it.actions:
						for act in it.actions:
							if act.can_use():
								magic_actions.append((it, act))

				# If available, use one with a small probability (or prefer if no weapon)
				if magic_actions and (not self.weapon or __import__('random').random() < 0.4):
					item_obj, action_obj = __import__('random').choice(magic_actions)
					msg, dmg, heal = item_obj.perform_action(action_obj, monster, user=self, verbose=False)
					if msg:
						display_msg.append(msg)
					if dmg:
						damage_multi += dmg
						continue

				attack_roll = randint(1, 20) + ((self.get_ability_score('str') - 10) // 2) + prof_bonus(self.level)

				# Add magic weapon attack bonus
				if self.weapon and hasattr(self.weapon, 'attack_bonus'):
					attack_roll += self.weapon.attack_bonus

				if attack_roll >= monster.armor_class:
					# Use calculate_weapon_damage to include magic bonuses
					damage_roll = self.calculate_weapon_damage(target=monster)
					if damage_roll:
						attack_type = self.weapon.damage_type.index.replace("ing", "es") if self.weapon and hasattr(self.weapon, 'damage_type') else "punches"
						display_msg.append(f"{self.name} {attack_type} {monster.name} for {damage_roll} hit points!")

						# Check restrained condition
						if self.conditions and any(e.index == "restrained" for e in self.conditions):
							damage_roll //= 2
							self.hit_points -= damage_roll
							display_msg.append(f"{self.name} inflicts himself {damage_roll} hit points!")
							if self.hit_points <= 0:
								display_msg.append(f"{self.name} *** IS DEAD ***!")
						damage_multi += damage_roll
				else:
					display_msg.append(f"{self.name} misses {monster.name}!")

			damage_roll = damage_multi

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, damage_roll

	def cast_attack(self, spell, target, verbose: bool = False) -> tuple:
		"""
		Cast an offensive spell on a target.

		Args:
			spell: Spell to cast
			target: Target (Monster or Character)
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, damage: int)
		"""
		from random import randint

		display_msg: List[str] = []
		total_damage = 0

		display_msg.append(f"{self.name} CAST SPELL ** {spell.name.upper()} ** on {target.name}")

		ability_modifier = (self.get_ability_score(self.class_type.spellcasting_ability) - 10) // 2
		damages = spell.get_spell_damages(caster_level=self.level, ability_modifier=ability_modifier)

		if spell.dc_type:
			# Saving throw spell
			if target.saving_throw(dc_type=spell.dc_type, dc_value=self.dc_value):
				if spell.dc_success == "half":
					for damage in damages:
						total_damage += damage.roll() // 2
					display_msg.append(f"{target.name} resists the Spell!")
					display_msg.append(f"{target.name} is hit for {total_damage} hit points!")
				else:
					display_msg.append(f"{target.name} resists the Spell!")
			else:
				for damage in damages:
					total_damage += damage.roll()
				display_msg.append(f"{target.name} is hit for {total_damage} hit points!")
		else:
			# Direct attack spell
			def prof_bonus(x):
				return x // 5 + 2 if x < 5 else (x - 5) // 4 + 3

			attack_roll = randint(1, 20) + ability_modifier + prof_bonus(self.level)
			if attack_roll >= target.armor_class:
				for damage in damages:
					total_damage += damage.roll()
				display_msg.append(f"{target.name} is hit for {total_damage} hit points!")
			else:
				display_msg.append(f"{self.name} misses {target.name}!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, total_damage

	def victory(self, monster, solo_mode: bool = False, verbose: bool = False) -> tuple:
		"""
		Handle victory over a monster (XP and gold gain).

		Args:
			monster: Defeated monster
			solo_mode: If True, also gain gold
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, xp_gained: int, gold_gained: int)
		"""
		from random import randint
		from math import floor

		display_msg: List[str] = []

		# Gain XP
		self.xp += monster.xp
		if hasattr(self, 'kills'):
			self.kills.append(monster)

		# Gain gold if solo mode
		gold_gained = 0
		gold_msg = ""
		if solo_mode:
			gold_dice = randint(1, 3)
			if gold_dice == 1:
				max_gold = max(1, floor(10 * monster.xp / monster.level))
				gold_gained = randint(1, max_gold + 1)
				gold_msg = f" and found {gold_gained} gp!"
				self.gold += gold_gained

		display_msg.append(f"{self.name} gained {monster.xp} XP{gold_msg}!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, monster.xp, gold_gained

	def drink(self, potion, verbose: bool = False) -> tuple:
		"""
		Drink a potion.

		Args:
			potion: Potion to drink
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, success: bool, hp_restored: int)
		"""
		from random import randint
		import time
		from ..equipment import HealingPotion, SpeedPotion, StrengthPotion

		display_msg: List[str] = []
		hp_restored = 0

		# Check level requirement
		if not hasattr(potion, "min_level"):
			potion.min_level = 1
		if self.level < potion.min_level:
			messages = ""
			if verbose:
				print(messages)
			return messages, False, 0

		# Apply potion effects
		if isinstance(potion, StrengthPotion):
			self.str_effect_modifier = potion.value
			if hasattr(self, 'str_effect_timer'):
				self.str_effect_timer = time.time()
			display_msg.append(f"{self.name} drinks {potion.name} and gains *strength*!")

		elif isinstance(potion, SpeedPotion):
			if hasattr(self, 'hasted'):
				self.hasted = True
			if hasattr(self, 'haste_timer'):
				self.haste_timer = time.time()
			self.speed *= 2
			if hasattr(self, 'ac_bonus'):
				self.ac_bonus = 2
			if hasattr(self, 'multi_attack_bonus'):
				self.multi_attack_bonus = 1
			if not hasattr(self, "st_advantages"):
				self.st_advantages = []
			self.st_advantages += ["dex"]
			display_msg.append(f"{self.name} drinks {potion.name} potion and is *hasted*!")

		else:
			# Healing potion
			hp_to_recover = self.max_hit_points - self.hit_points
			if hasattr(potion, 'hit_dice'):
				dice_count, roll_dice = map(int, potion.hit_dice.split("d"))
				hp_restored = potion.bonus + sum([randint(1, roll_dice) for _ in range(dice_count)])
			else:
				# Fallback for potions without hit_dice
				hp_restored = randint(2, 7)

			self.hit_points = min(self.hit_points + hp_restored, self.max_hit_points)

			if hp_to_recover <= hp_restored:
				display_msg.append(f"{self.name} drinks {potion.name} potion and is *fully* healed!")
			else:
				display_msg.append(f"{self.name} drinks {potion.name} potion and has {min(hp_to_recover, hp_restored)} hit points restored!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, True, hp_restored

	def equip(self, item, verbose: bool = False) -> tuple:
		"""
		Equip or unequip an item (weapon, armor, shield).

		Args:
			item: Item to equip/unequip
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, success: bool)
		"""
		from ..equipment import Armor, Weapon

		display_msg: List[str] = []
		success = False

		if isinstance(item, Armor):
			if item.index == "shield":
				# Shield logic
				if self.used_shield:
					if item == self.used_shield:
						# Un-equip shield
						prev = item.equipped
						item.equipped = not item.equipped
						# If we just unequipped, remove passive effects
						if prev and not item.equipped:
							from ..equipment.magic_item import MagicItem
							if isinstance(item, MagicItem):
								item.remove_from_character(self)

						display_msg.append(f"{self.name} un-equipped {item.name}")
						success = True
					else:
						display_msg.append(f"Hero cannot equip {item.name} - Please un-equip {self.used_shield.name} first!")
				else:
					if self.used_weapon:
						is_two_handed = any(p.index == "two-handed" for p in self.used_weapon.properties if hasattr(self.used_weapon, 'properties'))
						if is_two_handed:
							display_msg.append(f"Hero cannot equip {item.name} with a 2-handed weapon - Please un-equip {self.used_weapon.name} first!")
						else:
							# Equip shield
							prev = item.equipped
							item.equipped = not item.equipped
							if not prev and item.equipped:
								from ..equipment.magic_item import MagicItem
								if isinstance(item, MagicItem):
									item.apply_to_character(self)
							display_msg.append(f"{self.name} equipped {item.name}")
							success = True
					else:
						# Equip shield
						prev = item.equipped
						item.equipped = not item.equipped
						if not prev and item.equipped:
							from ..equipment.magic_item import MagicItem
							if isinstance(item, MagicItem):
								item.apply_to_character(self)
						display_msg.append(f"{self.name} equipped {item.name}")
						success = True
			else:
				# Armor logic
				if self.used_armor:
					if item == self.used_armor:
						# Un-equip armor
						prev = item.equipped
						item.equipped = not item.equipped
						if prev and not item.equipped:
							from ..equipment.magic_item import MagicItem
							if isinstance(item, MagicItem):
								item.remove_from_character(self)
						display_msg.append(f"{self.name} un-equipped {item.name}")
						success = True
					else:
						display_msg.append(f"Hero cannot equip {item.name} - Please un-equip {self.used_armor.name} first!")
				else:
					if hasattr(item, 'str_minimum') and self.strength < item.str_minimum:
						display_msg.append(f"Hero cannot equip {item.name} - Minimum strength required is {item.str_minimum}!")
					else:
						# Equip armor
						prev = item.equipped
						item.equipped = not item.equipped
						if not prev and item.equipped:
							from ..equipment.magic_item import MagicItem
							if isinstance(item, MagicItem):
								item.apply_to_character(self)
						display_msg.append(f"{self.name} equipped {item.name}")
						success = True

		elif isinstance(item, Weapon):
			if self.used_weapon:
				if item == self.used_weapon:
					# Un-equip weapon
					prev = item.equipped
					item.equipped = not item.equipped
					if prev and not item.equipped:
						from ..equipment.magic_item import MagicItem
						if isinstance(item, MagicItem):
							item.remove_from_character(self)
					display_msg.append(f"{self.name} un-equipped {item.name}")
					success = True
				else:
					display_msg.append(f"Hero cannot equip {item.name} - Please un-equip {self.used_weapon.name} first!")
			else:
				is_two_handed = any(p.index == "two-handed" for p in item.properties if hasattr(item, 'properties'))
				if is_two_handed and self.used_shield:
					display_msg.append(f"Hero cannot equip {item.name} with a shield - Please un-equip {self.used_shield.name} first!")
				else:
					# Equip weapon
					prev = item.equipped
					item.equipped = not item.equipped
					if not prev and item.equipped:
						from ..equipment.magic_item import MagicItem
						if isinstance(item, MagicItem):
							item.apply_to_character(self)
					display_msg.append(f"{self.name} equipped {item.name}")
					success = True
		else:
			display_msg.append(f"Hero cannot equip {item.name}!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, success

	def treasure(self, weapons, armors, equipments, potions, solo_mode: bool = False, verbose: bool = False) -> tuple:
		"""
		Find random treasure.

		Args:
			weapons: Available weapons
			armors: Available armors
			equipments: Available equipment
			potions: Available potions
			solo_mode: Solo mode flag
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str, found_item)
		"""
		from random import randint, choice
		from ..equipment import Armor, Weapon, HealingPotion

		display_msg: List[str] = []
		found_item = None

		if self.is_full:
			display_msg.append(f"{self.name}'s inventory is full - no treasure!!!")
		else:
			free_slot = min([i for i, item in enumerate(self.inventory) if item is None])
			treasure_dice = randint(1, 3)

			if treasure_dice == 1:
				# Potion
				potion = choice(potions)
				display_msg.append(f"{self.name} found a {potion.name} potion!")
				self.inventory[free_slot] = potion
				found_item = potion

			elif treasure_dice == 2:
				# Weapon
				new_weapon = choice(self.prof_weapons)
				if not self.weapon or (hasattr(new_weapon, 'damage_dice') and hasattr(self.weapon, 'damage_dice') and new_weapon.damage_dice > self.weapon.damage_dice):
					display_msg.append(f"{self.name} found a better weapon {new_weapon.name}!")
				else:
					display_msg.append(f"{self.name} found a lesser weapon {new_weapon.name}!")
				self.inventory[free_slot] = new_weapon
				found_item = new_weapon

			else:
				# Armor
				if self.prof_armors:
					new_armor = choice(self.prof_armors)
					if hasattr(new_armor, 'armor_class') and new_armor.armor_class.get("base", 0) > self.armor_class:
						display_msg.append(f"{self.name} found a better armor {new_armor.name}!")
						for item in self.inventory:
							if isinstance(item, Armor) and item.equipped:
								item.equipped = False
					else:
						display_msg.append(f"{self.name} found a lesser armor {new_armor.name}!")
					self.inventory[free_slot] = new_armor
					found_item = new_armor

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, found_item

	def equip_magic_item(self, item, auto_attune: bool = True, verbose: bool = False) -> tuple:
		"""
		Equip a magic item (weapon, armor, or accessory) automatically.

		Args:
			item: Magic item to equip
			auto_attune: If True, automatically attune items that require it
			verbose: If True, print messages

		Returns:
			tuple: (messages: str, success: bool)
		"""
		from ..equipment import Armor, Weapon
		from ..equipment.magic_item import MagicItem

		display_msg: List[str] = []
		success = False

		# Mark as equipped
		if hasattr(item, 'equipped'):
			item.equipped = True

		# Handle attunement for magic items
		if isinstance(item, MagicItem) and auto_attune:
			if hasattr(item, 'requires_attunement') and item.requires_attunement:
				if hasattr(item, 'attuned'):
					item.attuned = True
					display_msg.append(f"✨ {self.name} attuned to {item.name}")

		# Add to inventory if not already there
		if item not in self.inventory:
			if not self.is_full:
				free_slot = min([i for i, inv_item in enumerate(self.inventory) if inv_item is None])
				self.inventory[free_slot] = item
				display_msg.append(f"📦 {item.name} added to inventory")
			else:
				display_msg.append(f"❌ Inventory full! Cannot add {item.name}")
				return '\n'.join(display_msg), False

		# Use the equip() method for weapons and armors
		if isinstance(item, (Weapon, Armor)):
			equip_msg, equip_success = self.equip(item, verbose=False)
			display_msg.append(equip_msg)
			success = equip_success
		else:
			# For other magic items (rings, amulets, etc.)
			# Determine equipment slot to enforce limits (rings max 2, others max 1)
			def _determine_slot(it):
				# Prefer explicit category.index
				cat = None
				if hasattr(it, 'category') and it.category:
					cat = getattr(it.category, 'index', None)
				name = getattr(it, 'index', '')
				# Rings
				if cat == 'ring' or 'ring' in name:
					return 'ring'
				# Cloak
				if 'cloak' in name:
					return 'cloak'
				# Belt
				if 'belt' in name:
					return 'belt'
				# Boots
				if 'boots' in name:
					return 'boots'
				# Gloves/Gauntlets
				if 'gauntlet' in name or 'glove' in name:
					return 'gloves'
				# Headband
				if 'headband' in name:
					return 'headband'
				# Amulet / Necklace
				if 'amulet' in name or 'necklace' in name:
					return 'amulet'
				# Bracers
				if 'bracers' in name:
					return 'bracers'
				# Wondrous items ambiguous
				if cat == 'wondrous-items' or cat == 'wondrous':
					return 'wondrous'
				# Default
				return 'misc'

			slot = _determine_slot(item)
			if slot == 'ring':
				# Allow up to 2 rings equipped
				equipped_rings = [it for it in self.inventory if getattr(it, 'equipped', False) and hasattr(it, 'index') and ('ring' in getattr(it, 'index'))]
				if len(equipped_rings) >= 2:
					display_msg.append(f"Hero cannot equip {item.name} - already wearing two rings!")
					messages = '\n'.join(display_msg)
					if verbose:
						print(messages)
					return messages, False
			elif slot in ('cloak','belt','boots','gloves','headband','amulet','bracers'):
				equipped_same = [it for it in self.inventory if getattr(it, 'equipped', False) and (_determine_slot(it) == slot)]
				if equipped_same:
					display_msg.append(f"Hero cannot equip {item.name} - already wearing {equipped_same[0].name} in slot {slot}!")
					messages = '\n'.join(display_msg)
					if verbose:
						print(messages)
					return messages, False
		# Otherwise equip
		display_msg.append(f"⚔️  {self.name} equipped {item.name}")
		success = True

		# For non-weapon/armor magic items, make sure passive bonuses are applied if equipped
		from ..equipment.magic_item import MagicItem
		if success and hasattr(item, 'equipped') and item.equipped and isinstance(item, MagicItem):
			item.apply_to_character(self)

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return messages, success

	def cancel_haste_effect(self, verbose: bool = False) -> tuple:
		"""
		Cancel haste effect from speed potion.

		Args:
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str,)
		"""
		display_msg: List[str] = []

		if hasattr(self, 'hasted'):
			self.hasted = False

		# Reset speed based on race
		if hasattr(self, 'race') and hasattr(self.race, 'index'):
			self.speed = 25 if self.race.index in ["dwarf", "halfling", "gnome"] else 30
		else:
			self.speed = 30

		if hasattr(self, 'ac_bonus'):
			self.ac_bonus = 0
		if hasattr(self, 'multi_attack_bonus'):
			self.multi_attack_bonus = 0

		if not hasattr(self, "st_advantages"):
			self.st_advantages = []
		if "dex" in self.st_advantages:
			self.st_advantages.remove("dex")

		display_msg.append(f"{self.name} is no longer *hasted*!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return (messages,)

	def cancel_strength_effect(self, verbose: bool = False) -> tuple:
		"""
		Cancel strength effect from strength potion.

		Args:
			verbose: If True, print messages. If False, only return them.

		Returns:
			tuple: (messages: str,)
		"""
		display_msg: List[str] = []

		if hasattr(self, 'str_effect_modifier'):
			self.str_effect_modifier = -1

		display_msg.append(f"{self.name} is no longer *strong*!")

		messages = '\n'.join(display_msg)
		if verbose:
			print(messages)

		return (messages,)

	def update_spell_slots(self, spell, slot_level: int = None):
		"""
		Update spell slots after casting a spell.

		Args:
			spell: Spell that was cast
			slot_level: Optional specific slot level to use
		"""
		if not self.is_spell_caster:
			return

		slot_level = slot_level + 1 if slot_level else spell.level

		# Warlock uses different slot mechanics
		if hasattr(self.class_type, 'name') and self.class_type.name == "Warlock":
			# all of your spell slots are the same level
			for level, slot in enumerate(self.sc.spell_slots):
				if slot:
					self.sc.spell_slots[level] -= 1
		else:
			# Standard spellcaster
			if 0 < slot_level <= len(self.sc.spell_slots):
				self.sc.spell_slots[slot_level - 1] -= 1

	@property
	def multi_attacks(self) -> int:
		"""
		Calculate number of attacks per round based on class and level.

		If class abilities have been applied (has_class_abilities=True),
		use the explicit multi_attack_bonus. Otherwise, calculate from class and level.
		"""
		# If class abilities have been explicitly applied, use multi_attack_bonus
		if hasattr(self, 'has_class_abilities') and self.has_class_abilities:
			return 1 + self.multi_attack_bonus

		# Otherwise, use default calculation for backward compatibility
		if not hasattr(self, 'class_type'):
			return 1

		if hasattr(self.class_type, 'index'):
			if self.class_type.index == "fighter":
				attack_counts = 1 if self.level < 5 else 2 if self.level < 11 else 3
			elif self.class_type.index in ("paladin", "ranger", "monk", "barbarian"):
				attack_counts = 1 if self.level < 5 else 2
			else:
				attack_counts = 1
		else:
			attack_counts = 1

		if hasattr(self, "multi_attack_bonus"):
			return attack_counts + self.multi_attack_bonus
		return attack_counts

	@property
	def used_armor(self):
		"""Get currently equipped armor (excluding shield)."""
		from ..equipment import Armor
		equipped_armors = [item for item in self.inventory if isinstance(item, Armor) and item.equipped and not (hasattr(item, 'category') and getattr(item.category, 'index', None) == 'shield')]
		return equipped_armors[0] if equipped_armors else None

	@property
	def used_shield(self):
		"""Get currently equipped shield."""
		from ..equipment import Armor
		equipped_shields = [item for item in self.inventory if isinstance(item, Armor) and item.equipped and (hasattr(item, 'category') and getattr(item.category, 'index', None) == 'shield')]
		return equipped_shields[0] if equipped_shields else None

	@property
	def used_weapon(self):
		"""Get currently equipped weapon."""
		equipped_weapons = [item for item in self.inventory if isinstance(item, Weapon) and item.equipped]
		return equipped_weapons[0] if equipped_weapons else None

	@property
	def is_full(self) -> bool:
		"""Check if inventory is full."""
		return all(item for item in self.inventory)

	@property
	def prof_weapons(self):
		"""Get all weapons this character is proficient with."""
		weapons = []
		if hasattr(self, 'proficiencies'):
			for p in self.proficiencies:
				if hasattr(p, 'type') and hasattr(p, 'ref'):
					from ..classes import ProfType
					if p.type == ProfType.WEAPON:
						weapons += p.ref if isinstance(p.ref, list) else [p.ref]
		return list(filter(None, weapons))

	@property
	def prof_armors(self):
		"""Get all armors this character is proficient with."""
		armors = []
		if hasattr(self, 'proficiencies'):
			for p in self.proficiencies:
				if hasattr(p, 'type') and hasattr(p, 'ref'):
					from ..classes import ProfType
					if p.type == ProfType.ARMOR:
						armors += p.ref if isinstance(p.ref, list) else [p.ref]
		return list(filter(None, armors))

	def saving_throw(self, dc_type: str, dc_value: int) -> bool:
		"""
		Make a saving throw.

		Args:
			dc_type: Ability type for saving throw (str, dex, con, etc.)
			dc_value: Difficulty class

		Returns:
			bool: True if saving throw succeeds
		"""
		from random import randint

		def ability_mod(x):
			return (x - 10) // 2

		def prof_bonus(x):
			return x // 5 + 2 if x < 5 else (x - 5) // 4 + 3

		st_type = f"saving-throw-{dc_type}"
		prof_modifiers = []

		if hasattr(self, 'proficiencies'):
			prof_modifiers = [p.value for p in self.proficiencies if hasattr(p, 'index') and st_type == p.index]

		if prof_modifiers:
			ability_modifier = prof_modifiers[0]
		else:
			ability_modifier = ability_mod(self.get_ability_score(dc_type)) + prof_bonus(self.level)

		# Add magic item bonuses to saving throws (Ring of Protection, Cloak of Protection)
		from ..equipment.magic_item import MagicItem
		magic_items = [item for item in self.inventory if isinstance(item, MagicItem) and item.equipped]
		for item in magic_items:
			if item.can_use() and hasattr(item, 'saving_throw_bonus'):
				ability_modifier += item.saving_throw_bonus

		# Check for advantage
		if hasattr(self, "st_advantages") and dc_type in self.st_advantages:
			return any(randint(1, 20) + ability_modifier > dc_value for _ in range(2))
		else:
			return randint(1, 20) + ability_modifier > dc_value

	def choose_best_potion(self):
		"""
		Choose the best healing potion based on HP to recover.

		Returns:
			HealingPotion: The best potion to use
		"""
		from ..equipment import HealingPotion

		hp_to_recover = self.max_hit_points - self.hit_points
		healing_potions = [p for p in self.inventory if isinstance(p, HealingPotion)]

		if not healing_potions:
			return None

		available_potions = [
			p for p in healing_potions
			if p.max_hp_restored >= hp_to_recover and
			hasattr(p, "min_level") and
			self.level >= p.min_level
		]

		return (
			min(available_potions, key=lambda p: p.max_hp_restored)
			if available_potions
			else max(healing_potions, key=lambda p: p.max_hp_restored)
		)

	def get_ability_score(self, ability: str) -> int:
		"""Return effective ability score including magic item bonuses"""
		# Base value from abilities object
		base = 0
		if hasattr(self, 'abilities') and hasattr(self.abilities, 'get_value_by_index'):
			try:
				base = int(self.abilities.get_value_by_index(ability))
			except Exception:
				base = 10

		# Add bonuses from equipped magic items
		bonus = 0
		from ..equipment.magic_item import MagicItem
		for item in [it for it in self.inventory if it and getattr(it, 'equipped', False)]:
			if isinstance(item, MagicItem) and hasattr(item, 'ability_bonuses') and item.ability_bonuses:
				bonus += item.ability_bonuses.get(ability, 0)

		return base + bonus
