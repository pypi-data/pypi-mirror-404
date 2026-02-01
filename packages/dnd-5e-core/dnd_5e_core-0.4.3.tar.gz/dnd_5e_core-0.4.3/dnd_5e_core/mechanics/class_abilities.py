"""
D&D 5e Core - Class Abilities System
Implémente les capacités spéciales de chaque classe
"""
from typing import Optional, TYPE_CHECKING
from random import randint, choice

if TYPE_CHECKING:
    from ..entities import Character


class ClassAbilities:
    """Gère les capacités spéciales des personnages par classe"""

    # =============================================================================
    # BARBARIAN
    # =============================================================================

    @staticmethod
    def apply_barbarian_rage(character: 'Character', verbose: bool = True) -> bool:
        """
        Active la rage du barbare

        Effets:
        - Bonus aux dégâts de mêlée (+2 niv 1-8, +3 niv 9-15, +4 niv 16+)
        - Résistance aux dégâts contondants, perforants, tranchants
        - Advantage aux jets de Force

        Utilisations par repos long:
        - Niveau 1-2: 2
        - Niveau 3-5: 3
        - Niveau 6-11: 4
        - Niveau 12-16: 5
        - Niveau 17-19: 6
        - Niveau 20: Illimité
        """
        if not hasattr(character, 'rage_active'):
            character.rage_active = False
            character.rage_uses_left = ClassAbilities._get_rage_uses(character.level)

        if not character.rage_active and character.rage_uses_left > 0:
            character.rage_active = True
            character.rage_uses_left -= 1

            # Bonus de dégâts selon le niveau
            character.rage_damage_bonus = ClassAbilities._get_rage_damage(character.level)

            if verbose:
                print(f"      😡 {character.name} entre en RAGE!")
                print(f"         Bonus de dégâts: +{character.rage_damage_bonus}")
                print(f"         Résistance aux dégâts physiques")
                print(f"         Rages restantes: {character.rage_uses_left}")

            return True
        return False

    @staticmethod
    def _get_rage_uses(level: int) -> int:
        """Nombre d'utilisations de rage par niveau"""
        if level < 3:
            return 2
        elif level < 6:
            return 3
        elif level < 12:
            return 4
        elif level < 17:
            return 5
        elif level < 20:
            return 6
        else:
            return 999  # Illimité au niveau 20

    @staticmethod
    def _get_rage_damage(level: int) -> int:
        """Bonus de dégâts de rage par niveau"""
        if level < 9:
            return 2
        elif level < 16:
            return 3
        else:
            return 4

    @staticmethod
    def use_reckless_attack(character: 'Character', verbose: bool = True) -> bool:
        """
        Reckless Attack (Barbarian)
        Advantage à l'attaque mais les ennemis ont advantage contre vous
        """
        if verbose:
            print(f"      💥 {character.name} utilise RECKLESS ATTACK!")
            print(f"         Advantage aux attaques, mais vulnérable!")
        return True

    # =============================================================================
    # FIGHTER
    # =============================================================================

    @staticmethod
    def use_fighter_action_surge(character: 'Character', verbose: bool = True) -> bool:
        """
        Action Surge

        Utilisations:
        - Niveau 2-16: 1 par repos court
        - Niveau 17+: 2 par repos court
        """
        if not hasattr(character, 'action_surge_uses'):
            character.action_surge_uses = 2 if character.level >= 17 else 1

        if character.action_surge_uses > 0:
            character.action_surge_uses -= 1
            if verbose:
                print(f"      ⚡ {character.name} utilise ACTION SURGE!")
                print(f"         Action supplémentaire ce tour!")
                print(f"         Utilisations restantes: {character.action_surge_uses}")
            return True
        return False

    @staticmethod
    def use_second_wind(character: 'Character', verbose: bool = True) -> bool:
        """
        Second Wind
        Soigne 1d10 + niveau HP
        1 utilisation par repos court
        """
        if not hasattr(character, 'second_wind_used'):
            character.second_wind_used = False

        if not character.second_wind_used:
            character.second_wind_used = True
            healing = randint(1, 10) + character.level
            old_hp = character.hit_points
            character.hit_points = min(character.max_hit_points, character.hit_points + healing)

            if verbose:
                print(f"      💨 {character.name} utilise SECOND WIND!")
                print(f"         Soigne {healing} HP ({old_hp} → {character.hit_points})")
            return True
        return False

    @staticmethod
    def get_extra_attacks(character: 'Character') -> int:
        """
        Extra Attack

        Niveau 5: 1 attaque supplémentaire (2 total)
        Niveau 11 (Fighter): 2 attaques supplémentaires (3 total)
        Niveau 20 (Fighter): 3 attaques supplémentaires (4 total)
        """
        if character.class_type.index == 'fighter':
            if character.level >= 20:
                return 4
            elif character.level >= 11:
                return 3
            elif character.level >= 5:
                return 2
        elif character.class_type.index in ['barbarian', 'paladin', 'ranger', 'monk']:
            if character.level >= 5:
                return 2

        return 1

    # =============================================================================
    # ROGUE
    # =============================================================================

    @staticmethod
    def use_rogue_cunning_action(character: 'Character', verbose: bool = True) -> bool:
        """
        Cunning Action
        Bonus action pour Dash, Disengage ou Hide
        Disponible dès le niveau 2
        """
        if character.level < 2:
            return False

        actions = ["Dash", "Disengage", "Hide"]
        action = choice(actions)

        if verbose:
            print(f"      🎭 {character.name} utilise CUNNING ACTION: {action}!")
        return True

    @staticmethod
    def apply_sneak_attack_damage(character: 'Character', base_damage: int, verbose: bool = True) -> int:
        """
        Sneak Attack

        Dés de dégâts par niveau:
        - Niveau 1-2: 1d6
        - Niveau 3-4: 2d6
        - Niveau 5-6: 3d6
        - etc. (+1d6 tous les 2 niveaux)
        """
        sneak_dice = (character.level + 1) // 2
        sneak_damage = sum(randint(1, 6) for _ in range(sneak_dice))

        if verbose:
            print(f"      🗡️  SNEAK ATTACK! +{sneak_damage} dégâts ({sneak_dice}d6)")

        return base_damage + sneak_damage

    @staticmethod
    def use_uncanny_dodge(character: 'Character', verbose: bool = True) -> bool:
        """
        Uncanny Dodge (niveau 5+)
        Réaction pour réduire de moitié les dégâts d'une attaque
        """
        if character.level < 5:
            return False

        if not hasattr(character, 'uncanny_dodge_used_this_round'):
            character.uncanny_dodge_used_this_round = False

        if not character.uncanny_dodge_used_this_round:
            character.uncanny_dodge_used_this_round = True
            if verbose:
                print(f"      🛡️  {character.name} utilise UNCANNY DODGE!")
                print(f"         Dégâts réduits de moitié!")
            return True
        return False

    # =============================================================================
    # MONK
    # =============================================================================

    @staticmethod
    def use_monk_ki(character: 'Character', ability_name: str = "Flurry of Blows",
                    cost: int = 1, verbose: bool = True) -> bool:
        """
        Utilise les points de Ki

        Ki points = niveau du Monk
        """
        if not hasattr(character, 'ki_points'):
            character.ki_points = character.level
            character.max_ki_points = character.level

        if character.ki_points >= cost:
            character.ki_points -= cost
            if verbose:
                print(f"      🥋 {character.name} utilise {ability_name}!")
                print(f"         Ki restants: {character.ki_points}/{character.max_ki_points}")
            return True
        return False

    @staticmethod
    def get_martial_arts_die(level: int) -> str:
        """
        Dé d'arts martiaux par niveau

        1-4: 1d4
        5-10: 1d6
        11-16: 1d8
        17+: 1d10
        """
        if level < 5:
            return "1d4"
        elif level < 11:
            return "1d6"
        elif level < 17:
            return "1d8"
        else:
            return "1d10"

    @staticmethod
    def get_unarmored_movement(level: int) -> int:
        """
        Bonus de vitesse sans armure

        Niveau 2: +10 ft
        Niveau 6: +15 ft
        Niveau 10: +20 ft
        Niveau 14: +25 ft
        Niveau 18: +30 ft
        """
        if level < 2:
            return 0
        elif level < 6:
            return 10
        elif level < 10:
            return 15
        elif level < 14:
            return 20
        elif level < 18:
            return 25
        else:
            return 30

    # =============================================================================
    # CLERIC
    # =============================================================================

    @staticmethod
    def use_channel_divinity(character: 'Character', verbose: bool = True) -> bool:
        """
        Channel Divinity

        Utilisations par repos court:
        - Niveau 2-5: 1
        - Niveau 6-17: 2
        - Niveau 18+: 3
        """
        if not hasattr(character, 'channel_divinity_uses'):
            if character.level < 6:
                character.channel_divinity_uses = 1
            elif character.level < 18:
                character.channel_divinity_uses = 2
            else:
                character.channel_divinity_uses = 3

        if character.channel_divinity_uses > 0:
            character.channel_divinity_uses -= 1

            if verbose:
                print(f"      ✨ {character.name} utilise CHANNEL DIVINITY!")
                print(f"         Utilisations restantes: {character.channel_divinity_uses}")
            return True
        return False

    # =============================================================================
    # PALADIN
    # =============================================================================

    @staticmethod
    def use_lay_on_hands(character: 'Character', target: 'Character',
                        hp_to_heal: int, verbose: bool = True) -> bool:
        """
        Lay on Hands

        Pool de HP = niveau × 5
        """
        if not hasattr(character, 'lay_on_hands_pool'):
            character.lay_on_hands_pool = character.level * 5

        if character.lay_on_hands_pool >= hp_to_heal:
            character.lay_on_hands_pool -= hp_to_heal
            old_hp = target.hit_points
            target.hit_points = min(target.max_hit_points, target.hit_points + hp_to_heal)

            if verbose:
                print(f"      🙏 {character.name} utilise LAY ON HANDS sur {target.name}!")
                print(f"         Soigne {hp_to_heal} HP ({old_hp} → {target.hit_points})")
                print(f"         Pool restant: {character.lay_on_hands_pool}")
            return True
        return False

    @staticmethod
    def use_divine_smite(character: 'Character', spell_level: int,
                        is_undead_or_fiend: bool = False, verbose: bool = True) -> int:
        """
        Divine Smite

        Dégâts: 2d8 + 1d8 par niveau de slot (max 5d8)
        +1d8 si la cible est un undead ou fiend
        """
        base_dice = 2 + min(spell_level, 4)
        if is_undead_or_fiend:
            base_dice += 1

        damage = sum(randint(1, 8) for _ in range(base_dice))

        if verbose:
            print(f"      ⚡ {character.name} utilise DIVINE SMITE!")
            print(f"         +{damage} dégâts radiants ({base_dice}d8)")

        return damage

    # =============================================================================
    # BARD
    # =============================================================================

    @staticmethod
    def use_bardic_inspiration(character: 'Character', verbose: bool = True) -> str:
        """
        Bardic Inspiration

        Dé d'inspiration:
        - Niveau 1-4: 1d6
        - Niveau 5-9: 1d8
        - Niveau 10-14: 1d10
        - Niveau 15+: 1d12

        Utilisations = modificateur de Charisme (min 1)
        """
        if not hasattr(character, 'bardic_inspiration_uses'):
            cha_mod = character.abilities.get_modifier('cha')
            character.bardic_inspiration_uses = max(1, cha_mod)

        if character.bardic_inspiration_uses > 0:
            character.bardic_inspiration_uses -= 1

            # Déterminer le dé
            if character.level < 5:
                die = "1d6"
            elif character.level < 10:
                die = "1d8"
            elif character.level < 15:
                die = "1d10"
            else:
                die = "1d12"

            if verbose:
                print(f"      🎵 {character.name} utilise BARDIC INSPIRATION!")
                print(f"         Donne {die} à un allié")
                print(f"         Utilisations restantes: {character.bardic_inspiration_uses}")

            return die
        return ""

    # =============================================================================
    # SORCERER
    # =============================================================================

    @staticmethod
    def get_sorcery_points(level: int) -> int:
        """Points de sorcellerie = niveau"""
        return level

    @staticmethod
    def use_metamagic(character: 'Character', metamagic_type: str,
                     cost: int, verbose: bool = True) -> bool:
        """
        Metamagic

        Types:
        - Twinned Spell
        - Heightened Spell
        - Quickened Spell
        - Subtle Spell
        - etc.
        """
        if not hasattr(character, 'sorcery_points'):
            character.sorcery_points = character.level

        if character.sorcery_points >= cost:
            character.sorcery_points -= cost

            if verbose:
                print(f"      ✨ {character.name} utilise {metamagic_type}!")
                print(f"         Sorcery points restants: {character.sorcery_points}")
            return True
        return False

    # =============================================================================
    # RANGER
    # =============================================================================

    @staticmethod
    def use_hunters_mark(character: 'Character', verbose: bool = True) -> bool:
        """
        Hunter's Mark
        Sort de niveau 1, donne +1d6 dégâts
        """
        if verbose:
            print(f"      🎯 {character.name} utilise HUNTER'S MARK!")
            print(f"         +1d6 dégâts à chaque attaque")
        return True

    # =============================================================================
    # WARLOCK
    # =============================================================================

    @staticmethod
    def get_eldritch_invocations_known(level: int) -> int:
        """
        Nombre d'invocations connues

        Niveau 2: 2
        Niveau 5: 3
        Niveau 7: 4
        Niveau 9: 5
        Niveau 12: 6
        Niveau 15: 7
        Niveau 18: 8
        """
        if level < 2:
            return 0
        elif level < 5:
            return 2
        elif level < 7:
            return 3
        elif level < 9:
            return 4
        elif level < 12:
            return 5
        elif level < 15:
            return 6
        elif level < 18:
            return 7
        else:
            return 8


__all__ = ['ClassAbilities']
