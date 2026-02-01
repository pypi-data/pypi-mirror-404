"""
D&D 5e Core - Monster Entity
Monster class for D&D 5e enemies and NPCs
"""
from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field
from random import randint, choice
from typing import List, Optional, TYPE_CHECKING

from ..combat.special_ability import SpecialAbility

if TYPE_CHECKING:
    from ..abilities.abilities import Abilities
    from ..classes.proficiency import Proficiency
    from ..combat.action import Action, ActionType
    from ..combat.damage import Damage
    from ..spells.spellcaster import SpellCaster
    from ..spells.spell import Spell
    from ..mechanics.dice import DamageDice
    from .sprite import Sprite
    from .character import Character


@dataclass
class Monster:
    """
    A monster in D&D 5e.

    Monsters have:
    - Abilities (STR, DEX, CON, INT, WIS, CHA)
    - Armor class and hit points
    - Actions (attacks)
    - Special abilities
    - Spellcasting (optional)
    - Challenge rating
    - Source (book/module where monster appears)

    Note: This is the game logic only. UI layer handles Sprite positioning.
    """
    index: str
    name: str
    abilities: 'Abilities'
    proficiencies: List['Proficiency']
    armor_class: int
    hit_points: int
    hit_dice: str  # e.g., "2d8+2"
    xp: int
    speed: int
    challenge_rating: float
    actions: List['Action']
    sc: Optional['SpellCaster'] = None  # Spellcaster (if monster can cast spells)
    sa: Optional[List['SpecialAbility']] = None  # Special abilities
    source: Optional[str] = None  # Source book (e.g., "MM", "MPMM", "SKT")
    creature_type: Optional[str] = None  # Type (aberration, beast, celestial, construct, dragon, elemental, fey, fiend, giant, humanoid, monstrosity, ooze, plant, undead)
    attack_round: int = 0
    max_hit_points: int = field(init=False)

    def __post_init__(self):
        """Initialize max_hit_points"""
        self.max_hit_points = self.hit_points

    def __repr__(self):
        return f"{self.name} (AC {self.armor_class}, HP {self.hit_points}/{self.max_hit_points}, CR {self.challenge_rating})"

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other: 'Monster'):
        """Compare monsters by challenge rating"""
        return self.challenge_rating < other.challenge_rating

    def __gt__(self, other: 'Monster'):
        """Compare monsters by challenge rating"""
        return self.challenge_rating > other.challenge_rating

    @property
    def is_alive(self) -> bool:
        """Check if monster is still alive"""
        return self.hit_points > 0

    @property
    def is_dead(self) -> bool:
        """Check if monster is dead"""
        return self.hit_points <= 0

    @property
    def is_spell_caster(self) -> bool:
        """Check if monster can cast spells"""
        return self.sc is not None

    @property
    def dc_value(self) -> Optional[int]:
        """Get spell save DC"""
        return self.sc.dc_value if self.sc else None

    @property
    def level(self) -> int:
        """
        Calculate effective level from hit dice.

        Returns:
            int: Effective level
        """
        hit_dice_str = self.hit_dice
        bonus = 0

        if "+" in hit_dice_str:
            hit_dice_str, bonus_str = hit_dice_str.split("+")
            bonus = int(bonus_str.strip())

        dice_count, roll_dice = map(int, hit_dice_str.strip().split("d"))
        return dice_count * roll_dice + bonus

    def __copy__(self):
        """Create a copy of this monster"""
        return Monster(
            self.index,
            self.name,
            self.abilities,
            self.proficiencies,
            self.armor_class,
            self.hit_points,
            self.hit_dice,
            self.xp,
            self.speed,
            self.challenge_rating,
            self.actions,
            copy(self.sc) if self.sc else None,
            self.sa,
            self.attack_round
        )

    def hp_roll(self):
        """Reroll hit points based on hit dice"""
        hit_dice_str = self.hit_dice
        bonus = 0

        if "+" in hit_dice_str:
            hit_dice_str, bonus_str = hit_dice_str.split("+")
            bonus = int(bonus_str.strip())

        dice_count, roll_dice = map(int, hit_dice_str.strip().split("d"))
        self.hit_points = sum([randint(1, roll_dice) for _ in range(dice_count)]) + bonus
        self.max_hit_points = self.hit_points

    def saving_throw(self, dc_type: str, dc_value: int) -> bool:
        """
        Make a saving throw.

        Args:
            dc_type: Ability for saving throw (e.g., "dex", "con")
            dc_value: Difficulty class

        Returns:
            bool: True if saving throw succeeds
        """
        st_type = f"saving-throw-{dc_type}"
        prof_modifiers = [p.value for p in self.proficiencies if st_type == p.index]
        ability_modifier = prof_modifiers[0] if prof_modifiers else 0
        return randint(1, 20) + ability_modifier > dc_value

    def cast_heal(self, spell: 'Spell', slot_level: int, targets: List['Monster']) -> List[int]:
        """
        Cast a healing spell on targets.

        Args:
            spell: The healing spell
            slot_level: Spell slot level used
            targets: List of monsters to heal

        Returns:
            List[int]: HP gained by each target
        """
        if not self.is_spell_caster:
            return []

        dd = spell.get_heal_effect(slot_level=slot_level, ability_modifier=self.sc.ability_modifier)
        hp_gained_list = []

        for target in targets:
            if target.hit_points < target.max_hit_points:
                hp_gained = min(dd.roll(), target.max_hit_points - target.hit_points)
                target.hit_points += hp_gained
                hp_gained_list.append(hp_gained)
            else:
                hp_gained_list.append(0)

        return hp_gained_list

    def cast_attack(self, target, spell: 'Spell', verbose: bool = False) -> tuple:
        """
        Cast an attack spell.

        Args:
            target: The target (Character or Monster)
            spell: The spell to cast
            verbose: If True, print messages. If False, only return them.

        Returns:
            tuple: (messages: str, damage: int, damage_type: str)
        """
        from typing import List as ListType

        display_msg: ListType[str] = []

        if not self.is_spell_caster:
            messages = ""
            if verbose:
                print(messages)
            return messages, 0, "force"

        total_damage = 0
        primary_damage_type = spell.damage_type if hasattr(spell, 'damage_type') and spell.damage_type else "force"

        display_msg.append(f"{self.name} casts {spell.name.upper()} on {target.name}!")

        # Use spell slot (cantrips don't use slots)
        if spell.level > 0:
            self.sc.use_spell_slot(spell.level)

        # Calculate damage
        damage_dices = spell.get_spell_damages(
            caster_level=self.sc.level,
            ability_modifier=self.sc.ability_modifier
        )
        for dd in damage_dices:
            total_damage += dd.roll()

        # Handle saving throw
        if spell.dc_type is not None:
            st_success = target.saving_throw(dc_type=spell.dc_type, dc_value=self.sc.dc_value)
            if st_success:
                if spell.dc_success == "half":
                    total_damage //= 2
                    display_msg.append(f"{target.name} resists! Damage halved to {total_damage}!")
                elif spell.dc_success == "none":
                    total_damage = 0
                    display_msg.append(f"{target.name} resists completely!")
            else:
                display_msg.append(f"{target.name} is hit for {total_damage} hit points!")
        else:
            display_msg.append(f"{target.name} is hit for {total_damage} hit points!")

        messages = '\n'.join(display_msg)
        if verbose:
            print(messages)

        return messages, total_damage, primary_damage_type

    def special_attack(self, target, sa: 'SpecialAbility', verbose: bool = False) -> tuple:
        """
        Perform a special ability attack.

        Args:
            target: The target (Character or Monster)
            sa: Special ability to use
            verbose: If True, print messages. If False, only return them.

        Returns:
            tuple: (messages: str, damage: int, damage_type: str)
        """
        from typing import List as ListType

        display_msg: ListType[str] = []

        total_damage = 0
        primary_damage_type = "force"  # Default for special abilities

        for damage in sa.damages:
            damage_roll = damage.roll()
            total_damage += damage_roll
            # Track primary damage type
            if hasattr(damage, 'type') and damage.type:
                primary_damage_type = damage.type.index

        display_msg.append(f"{self.name} uses {sa.name} on {target.name}!")

        # Handle saving throw
        if sa.dc_type is not None:
            st_success = target.saving_throw(dc_type=sa.dc_type, dc_value=sa.dc_value)
            if st_success:
                if sa.dc_success == "half":
                    total_damage //= 2
                    display_msg.append(f"{target.name} resists! Damage halved to {total_damage}!")
                elif sa.dc_success == "none":
                    total_damage = 0
                    display_msg.append(f"{target.name} resists completely!")
            else:
                display_msg.append(f"{target.name} is hit for {total_damage} hit points!")
        else:
            display_msg.append(f"{target.name} is hit for {total_damage} hit points!")

        messages = '\n'.join(display_msg)
        if verbose:
            print(messages)

        return messages, total_damage, primary_damage_type

    def attack(self, target: 'Character', actions: Optional[List['Action']] = None, distance: float = 5.0, verbose: bool = False) -> tuple:
        """
        Perform an attack.

        Args:
            target: The target (Character)
            actions: Actions to choose from (uses self.actions if None)
            distance: Distance to target in feet
            verbose: If True, print messages. If False, only return them.

        Returns:
            tuple: (messages: str, damage: int, damage_type: str)
        """
        from typing import List as ListType

        display_msg: ListType[str] = []

        if actions is None:
            actions = self.actions

        total_damage = 0
        primary_damage_type = "bludgeoning"  # Default damage type

        if not actions:
            messages = ""
            if verbose:
                print(messages)
            return messages, 0, primary_damage_type

        # Choose an action
        action = choice(actions)

        # Handle multi-attack
        if action.multi_attack:
            attacks = [a for a in action.multi_attack]
            if len(attacks) > 1:
                display_msg.append(f"{self.name} multi-attacks {target.name}!")
        else:
            attacks = [action]

        # Execute each attack
        for attack_action in attacks:
            # Special ability attack
            if isinstance(attack_action, SpecialAbility):
                special_msg, special_damage, special_type = self.special_attack(target, attack_action, verbose=False)
                display_msg.append(special_msg)
                total_damage += special_damage
                if total_damage > 0 and special_type:
                    primary_damage_type = special_type
            else:
                # Normal attack
                from ..combat.action import ActionType

                # Calculate attack roll
                if attack_action.type == ActionType.MELEE:
                    attack_roll = randint(1, 20) + attack_action.attack_bonus
                else:
                    # Ranged attack with possible disadvantage
                    disadvantage = distance > attack_action.normal_range
                    if not disadvantage:
                        attack_roll = randint(1, 20) + attack_action.attack_bonus
                    else:
                        # Roll with disadvantage (take minimum of 2 rolls)
                        attack_roll = min([randint(1, 20) + attack_action.attack_bonus for _ in range(2)])

                # Check if attack hits
                if attack_roll >= target.armor_class:
                    # Deal damage
                    attack_damage = 0
                    if attack_action.damages:
                        for damage in attack_action.damages:
                            damage_given = damage.roll()
                            attack_damage += damage_given
                            total_damage += damage_given

                            # Track primary damage type
                            if hasattr(damage, 'type') and damage.type:
                                primary_damage_type = damage.type.index

                    # Format attack message
                    attack_type = attack_action.name if attack_action.name else attack_action.type.value
                    if attack_action.damages and len(attack_action.damages) > 0:
                        damage_type = attack_action.damages[0].type.index if hasattr(attack_action.damages[0], 'type') else ""
                        if damage_type:
                            action_verb = damage_type.replace("ing", "es") if damage_type.endswith("ing") else damage_type
                        else:
                            action_verb = "hits"
                    else:
                        action_verb = "hits"

                    display_msg.append(f"{self.name} {action_verb} {target.name} for {attack_damage} hit points!")

                    # Apply effects/conditions
                    if attack_action.effects:
                        applied_conditions = []
                        for effect in attack_action.effects:
                            # Create a copy of the condition
                            condition_copy = copy(effect)

                            # Set the creature reference if needed
                            if condition_copy.index in ["restrained", "grappled", "frightened", "charmed"]:
                                condition_copy.creature = self

                            # Try to apply the condition
                            if hasattr(condition_copy, 'apply_to_character'):
                                condition_copy.apply_to_character(target)
                                applied_conditions.append(condition_copy.name)
                            elif hasattr(target, 'conditions'):
                                # Fallback: manual application
                                if target.conditions is None:
                                    target.conditions = []
                                if not any(c.index == condition_copy.index for c in target.conditions):
                                    target.conditions.append(condition_copy)
                                    applied_conditions.append(condition_copy.name)

                        if applied_conditions:
                            effects_str = ", ".join(applied_conditions)
                            display_msg.append(f"{target.name} is now {effects_str}!")
                else:
                    display_msg.append(f"{self.name} misses {target.name}!")

        messages = '\n'.join(display_msg)
        if verbose:
            print(messages)

        return messages, total_damage, primary_damage_type

    def take_damage(self, damage: int):
        """
        Take damage.

        Args:
            damage: Amount of damage to take
        """
        self.hit_points = max(0, self.hit_points - damage)

    def heal(self, amount: int):
        """
        Heal hit points.

        Args:
            amount: Amount to heal
        """
        self.hit_points = min(self.max_hit_points, self.hit_points + amount)

