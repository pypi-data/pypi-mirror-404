"""
D&D 5e Core - Gold Rewards & Treasure System
Treasure rewards based on encounter level from DMG including magic items
"""
import random
from typing import Dict, List, Any, Optional
from fractions import Fraction

# Encounter gold rewards table (DMG p.133)
# Based on "Treasure per Encounter" by level
ENCOUNTER_GOLD_TABLE = {1: 300, 2: 600, 3: 900, 4: 1200, 5: 1600, 6: 2000, 7: 2600, 8: 3400, 9: 4500, 10: 5800, 11: 7500, 12: 9800, 13: 13000, 14: 17000, 15: 22000, 16: 28000, 17: 36000, 18: 47000, 19: 61000, 20: 80000, }

# Treasure Hoard Tables based on DMG p.137-139
# Challenge Rating ranges for treasure hoards
TREASURE_HOARD_CR_RANGES = {'tier1': (0, 4),  # CR 0-4
	'tier2': (5, 10),  # CR 5-10
	'tier3': (11, 16),  # CR 11-16
	'tier4': (17, 100),  # CR 17+
}

# Magic Item Rarity by CR/Level (DMG guidelines)
MAGIC_ITEM_RARITY_BY_CR = {'tier1': ['common', 'uncommon'],  # CR 0-4
	'tier2': ['uncommon', 'rare'],  # CR 5-10
	'tier3': ['rare', 'very rare'],  # CR 11-16
	'tier4': ['very rare', 'legendary'],  # CR 17+
}

# Probability of magic items in treasure hoard (DMG p.137-139)
# Format: {tier: (num_items_min, num_items_max, probability)}
MAGIC_ITEM_PROBABILITY = {'tier1': (0, 2, 0.30),  # 30% chance, 0-2 items
	'tier2': (1, 3, 0.50),  # 50% chance, 1-3 items
	'tier3': (2, 4, 0.70),  # 70% chance, 2-4 items
	'tier4': (3, 6, 0.85),  # 85% chance, 3-6 items
}

# Equipment type distribution
EQUIPMENT_TYPE_WEIGHTS = {'weapon': 0.25, 'armor': 0.20, 'potion': 0.30, 'wondrous': 0.15, 'ring': 0.05, 'wand': 0.03, 'staff': 0.02, }


def get_tier_from_cr(cr: float) -> str:
	"""
	Determine treasure tier from Challenge Rating.

	Args:
		cr: Challenge Rating (can be fraction like 0.5 for CR 1/2)

	Returns:
		Tier name ('tier1', 'tier2', 'tier3', 'tier4')
	"""
	if isinstance(cr, str):
		# Handle fractional CR like "1/2"
		if '/' in cr:
			cr = float(Fraction(cr))
		else:
			cr = float(cr)

	for tier, (min_cr, max_cr) in TREASURE_HOARD_CR_RANGES.items():
		if min_cr <= cr <= max_cr:
			return tier
	return 'tier1'


def get_tier_from_level(level: int) -> str:
	"""
	Determine treasure tier from character/encounter level.

	Args:
		level: Character or encounter level (1-20)

	Returns:
		Tier name ('tier1', 'tier2', 'tier3', 'tier4')
	"""
	if level <= 4:
		return 'tier1'
	elif level <= 10:
		return 'tier2'
	elif level <= 16:
		return 'tier3'
	else:
		return 'tier4'


def get_encounter_gold(encounter_level: int) -> int:
	"""
	Get gold reward for an encounter based on level.

	Args:
		encounter_level: Encounter difficulty level (1-20)

	Returns:
		Gold pieces for this encounter level
	"""
	encounter_level = max(1, min(20, encounter_level))
	return ENCOUNTER_GOLD_TABLE.get(encounter_level, 0)


def select_magic_items_for_tier(tier: str, num_items: int, party_proficiencies: Optional[List[str]] = None) -> List[str]:
	"""
	Select appropriate magic items for a given tier.

	Args:
		tier: Treasure tier ('tier1', 'tier2', 'tier3', 'tier4')
		num_items: Number of items to select
		party_proficiencies: List of party weapon/armor proficiencies (optional)

	Returns:
		List of magic item indices
	"""
	# Simplified approach to avoid circular imports and infinite loops
	# Build a simple pool based on tier without creating all items

	# Get allowed rarities for this tier
	allowed_rarities = MAGIC_ITEM_RARITY_BY_CR.get(tier, ['common', 'uncommon'])

	# Simple item pool with predefined appropriate items per tier
	tier_items = {'tier1': ['potion-of-healing', 'potion-of-climbing', 'antitoxin', 'rope-of-climbing', 'bag-of-holding', ], 'tier2': ['potion-of-greater-healing', 'potion-of-hill-giant-strength', 'ring-of-protection', 'cloak-of-protection', 'wand-of-magic-missiles', 'bag-of-holding', 'boots-of-elvenkind', ], 'tier3': ['potion-of-superior-healing', 'potion-of-fire-giant-strength', 'ring-of-protection', 'ring-of-spell-storing', 'wand-of-fireballs', 'staff-of-healing', 'bracers-of-defense', 'belt-of-giant-strength', ], 'tier4': ['potion-of-supreme-healing', 'potion-of-storm-giant-strength', 'ring-of-regeneration', 'ring-of-spell-storing', 'wand-of-fireballs', 'staff-of-healing', 'belt-of-cloud-giant-strength', 'belt-of-storm-giant-strength', ], }

	# Get items for this tier
	available_items = tier_items.get(tier, tier_items['tier1'])

	# Add some weapons if proficiencies allow
	if party_proficiencies:
		# Convert Proficiency objects to strings if needed
		prof_strings = []
		for p in party_proficiencies:
			if isinstance(p, str):
				prof_strings.append(p.lower())
			elif hasattr(p, 'name'):
				# It's a Proficiency object
				prof_strings.append(p.name.lower())
			elif hasattr(p, 'index'):
				prof_strings.append(p.index.lower())

		weapon_profs = [p for p in prof_strings if 'weapon' in p or 'martial' in p or 'simple' in p]
		if weapon_profs:
			if tier == 'tier1':
				available_items.extend(['javelin-of-lightning', 'trident-of-fish-command'])
			elif tier == 'tier2':
				available_items.extend(['flame-tongue', 'giant-slayer'])
			elif tier in ['tier3', 'tier4']:
				available_items.extend(['flame-tongue', 'frost-brand', 'sun-blade', 'vorpal-sword'])

	# Add some armors if proficiencies allow
	if party_proficiencies:
		# Use same prof_strings from above if available
		if not 'prof_strings' in locals():
			prof_strings = []
			for p in party_proficiencies:
				if isinstance(p, str):
					prof_strings.append(p.lower())
				elif hasattr(p, 'name'):
					prof_strings.append(p.name.lower())
				elif hasattr(p, 'index'):
					prof_strings.append(p.index.lower())

		armor_profs = [p for p in prof_strings if 'armor' in p]
		if armor_profs:
			if tier == 'tier1':
				available_items.extend(['mithral-chain-shirt'])
			elif tier == 'tier2':
				available_items.extend(['elven-chain', 'adamantine-plate'])
			elif tier in ['tier3', 'tier4']:
				available_items.extend(['dwarven-plate', 'dragon-scale-mail', 'armor-of-invulnerability'])

	# Select random items
	if not available_items:
		return []

	num_items = min(num_items, len(available_items))
	selected_items = random.sample(available_items, num_items)

	return selected_items


def calculate_treasure_hoard(level: int, multiplier: float = 1.0, cr: Optional[float] = None, party_proficiencies: Optional[List[str]] = None, include_items: bool = True) -> Dict[str, Any]:
	"""
	Calculate comprehensive treasure hoard for a given level/CR.

	Based on D&D 5e DMG treasure hoard tables (p.137-139), this function
	generates appropriate treasure including gold, gems, art objects, and
	magic items based on the encounter difficulty.

	Args:
		level: Character/encounter level (1-20)
		multiplier: Difficulty multiplier (easy=0.5, medium=1.0, hard=1.5, deadly=2.0)
		cr: Challenge Rating (optional, overrides level for tier determination)
		party_proficiencies: List of party proficiencies for item selection
		include_items: Whether to include magic items in treasure

	Returns:
		Dictionary containing:
			- 'gold': Gold pieces
			- 'items': List of magic item indices (if include_items=True)
			- 'tier': Treasure tier
			- 'total_value_gp': Estimated total value
	"""
	# Determine tier
	if cr is not None:
		tier = get_tier_from_cr(cr)
	else:
		tier = get_tier_from_level(level)

	# Calculate base gold
	base_gold = get_encounter_gold(level)
	# print(level, base_gold, multiplier)
	gold = int(base_gold * multiplier)

	# Add variance (±20%)
	variance = random.uniform(0.8, 1.2)
	gold = int(gold * variance)

	treasure = {'gold': gold, 'items': [], 'tier': tier, 'total_value_gp': gold}

	# Add magic items if requested
	if include_items:
		min_items, max_items, probability = MAGIC_ITEM_PROBABILITY[tier]

		# Check if magic items are awarded
		if random.random() < probability:
			# Determine number of items (higher multiplier = more items)
			num_items = random.randint(min_items, max_items)

			# Increase item count for harder encounters
			if multiplier >= 1.5:
				num_items += 1
			if multiplier >= 2.0:
				num_items += 1

			# Select items
			items = select_magic_items_for_tier(tier, num_items, party_proficiencies)
			treasure['items'] = items

			# Estimate total value (items worth roughly 50-200% of gold)
			if items:
				item_value_multiplier = random.uniform(0.5, 2.0)
				treasure['total_value_gp'] += int(gold * item_value_multiplier)

	return treasure


def get_treasure_by_cr(cr: float, party_proficiencies: Optional[List[str]] = None) -> Dict[str, Any]:
	"""
	Convenience function to get treasure based on Challenge Rating.

	Args:
		cr: Challenge Rating
		party_proficiencies: List of party proficiencies

	Returns:
		Treasure hoard dictionary
	"""
	# Convert CR to approximate level
	if cr <= 1:
		level = max(1, int(cr * 4))
	else:
		level = min(20, int(cr))

	return calculate_treasure_hoard(level=level, cr=cr, party_proficiencies=party_proficiencies)


__all__ = ['ENCOUNTER_GOLD_TABLE', 'TREASURE_HOARD_CR_RANGES', 'MAGIC_ITEM_RARITY_BY_CR', 'MAGIC_ITEM_PROBABILITY', 'get_encounter_gold', 'get_tier_from_cr', 'get_tier_from_level', 'select_magic_items_for_tier', 'calculate_treasure_hoard', 'get_treasure_by_cr', ]
