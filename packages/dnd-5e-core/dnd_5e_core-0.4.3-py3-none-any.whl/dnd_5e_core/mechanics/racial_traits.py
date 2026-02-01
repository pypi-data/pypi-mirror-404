"""
D&D 5e Core - Racial Traits System
Implémente les traits spéciaux de chaque race
"""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities import Character


class RacialTraits:
    """Gère les traits raciaux spéciaux"""

    # =============================================================================
    # ELF TRAITS
    # =============================================================================

    @staticmethod
    def apply_darkvision(character: 'Character', range_feet: int = 60):
        """
        Darkvision
        Vision dans le noir jusqu'à 60 pieds (ou 120 pour Drow)

        Races: Elf, Dwarf, Half-Elf, Gnome, Half-Orc, Tiefling
        """
        if not hasattr(character, 'darkvision'):
            character.darkvision = range_feet

    @staticmethod
    def apply_fey_ancestry(character: 'Character'):
        """
        Fey Ancestry
        Advantage aux jets de sauvegarde contre charmed
        Immunité au sommeil magique

        Races: Elf, Half-Elf
        """
        if not hasattr(character, 'fey_ancestry'):
            character.fey_ancestry = True

    @staticmethod
    def apply_trance(character: 'Character'):
        """
        Trance
        Les elfes ne dorment pas, ils méditent 4 heures

        Race: Elf
        """
        if not hasattr(character, 'trance'):
            character.trance = True

    @staticmethod
    def apply_keen_senses(character: 'Character'):
        """
        Keen Senses
        Proficiency en Perception

        Race: Elf
        """
        if not hasattr(character, 'proficiencies'):
            character.proficiencies = []

        if 'perception' not in character.proficiencies:
            character.proficiencies.append('perception')

    @staticmethod
    def apply_mask_of_the_wild(character: 'Character'):
        """
        Mask of the Wild
        Peut se cacher en étant légèrement obscurci par feuillage, pluie, etc.

        Subrace: Wood Elf
        """
        if not hasattr(character, 'mask_of_the_wild'):
            character.mask_of_the_wild = True

    # =============================================================================
    # DWARF TRAITS
    # =============================================================================

    @staticmethod
    def apply_dwarven_resilience(character: 'Character'):
        """
        Dwarven Resilience
        Advantage aux jets de sauvegarde contre poison
        Résistance aux dégâts de poison

        Race: Dwarf
        """
        if not hasattr(character, 'dwarven_resilience'):
            character.dwarven_resilience = True

    @staticmethod
    def apply_stonecunning(character: 'Character'):
        """
        Stonecunning
        Double bonus de proficiency pour History checks liés à la pierre

        Race: Dwarf
        """
        if not hasattr(character, 'stonecunning'):
            character.stonecunning = True

    @staticmethod
    def apply_dwarven_toughness(character: 'Character'):
        """
        Dwarven Toughness
        HP maximum augmente de 1 par niveau

        Subrace: Hill Dwarf
        """
        if not hasattr(character, 'dwarven_toughness_applied'):
            character.max_hit_points += character.level
            character.hit_points += character.level
            character.dwarven_toughness_applied = True

    # =============================================================================
    # HALFLING TRAITS
    # =============================================================================

    @staticmethod
    def apply_lucky(character: 'Character'):
        """
        Lucky
        Peut relancer un 1 naturel aux jets d'attaque, de capacité ou de sauvegarde

        Race: Halfling
        """
        if not hasattr(character, 'lucky'):
            character.lucky = True

    @staticmethod
    def apply_brave(character: 'Character'):
        """
        Brave
        Advantage aux jets de sauvegarde contre frightened

        Race: Halfling
        """
        if not hasattr(character, 'brave'):
            character.brave = True

    @staticmethod
    def apply_halfling_nimbleness(character: 'Character'):
        """
        Halfling Nimbleness
        Peut se déplacer à travers l'espace de créatures plus grandes

        Race: Halfling
        """
        if not hasattr(character, 'halfling_nimbleness'):
            character.halfling_nimbleness = True

    @staticmethod
    def apply_naturally_stealthy(character: 'Character'):
        """
        Naturally Stealthy
        Peut se cacher derrière une créature plus grande

        Subrace: Lightfoot Halfling
        """
        if not hasattr(character, 'naturally_stealthy'):
            character.naturally_stealthy = True

    # =============================================================================
    # HUMAN TRAITS
    # =============================================================================

    @staticmethod
    def apply_human_versatility(character: 'Character'):
        """
        Human Versatility
        +1 à toutes les caractéristiques

        Race: Human
        """
        if not hasattr(character, 'human_versatility_applied'):
            for ability in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
                current = getattr(character.abilities, ability)
                setattr(character.abilities, ability, current + 1)
            character.human_versatility_applied = True

    # =============================================================================
    # DRAGONBORN TRAITS
    # =============================================================================

    @staticmethod
    def apply_breath_weapon(character: 'Character', dragon_type: str = "fire"):
        """
        Breath Weapon
        Arme de souffle selon l'ascendance draconique

        Dégâts: 2d6 au niveau 1, 3d6 au niveau 6, 4d6 au niveau 11, 5d6 au niveau 16
        DC = 8 + CON mod + proficiency bonus

        Race: Dragonborn
        """
        if not hasattr(character, 'breath_weapon'):
            # Calculer les dégâts selon le niveau
            if character.level < 6:
                dice_count = 2
            elif character.level < 11:
                dice_count = 3
            elif character.level < 16:
                dice_count = 4
            else:
                dice_count = 5

            character.breath_weapon = {
                'type': dragon_type,
                'damage_dice': f"{dice_count}d6",
                'dc': 8 + character.abilities.get_modifier('con') + (2 + (character.level - 1) // 4),
                'uses': 1  # 1 utilisation par repos court/long
            }

    @staticmethod
    def apply_damage_resistance(character: 'Character', damage_type: str):
        """
        Damage Resistance
        Résistance selon l'ascendance draconique

        Race: Dragonborn
        """
        if not hasattr(character, 'damage_resistances'):
            character.damage_resistances = []

        if damage_type not in character.damage_resistances:
            character.damage_resistances.append(damage_type)

    # =============================================================================
    # GNOME TRAITS
    # =============================================================================

    @staticmethod
    def apply_gnome_cunning(character: 'Character'):
        """
        Gnome Cunning
        Advantage aux jets de sauvegarde INT, WIS, CHA contre la magie

        Race: Gnome
        """
        if not hasattr(character, 'gnome_cunning'):
            character.gnome_cunning = True

    # =============================================================================
    # HALF-ORC TRAITS
    # =============================================================================

    @staticmethod
    def apply_relentless_endurance(character: 'Character'):
        """
        Relentless Endurance
        Une fois par repos long, si HP tombe à 0, reste à 1 HP

        Race: Half-Orc
        """
        if not hasattr(character, 'relentless_endurance_available'):
            character.relentless_endurance_available = True

    @staticmethod
    def apply_savage_attacks(character: 'Character'):
        """
        Savage Attacks
        Sur un critique, lance un dé de dégâts supplémentaire

        Race: Half-Orc
        """
        if not hasattr(character, 'savage_attacks'):
            character.savage_attacks = True

    # =============================================================================
    # TIEFLING TRAITS
    # =============================================================================

    @staticmethod
    def apply_hellish_resistance(character: 'Character'):
        """
        Hellish Resistance
        Résistance aux dégâts de feu

        Race: Tiefling
        """
        if not hasattr(character, 'damage_resistances'):
            character.damage_resistances = []

        if 'fire' not in character.damage_resistances:
            character.damage_resistances.append('fire')

    @staticmethod
    def apply_infernal_legacy(character: 'Character'):
        """
        Infernal Legacy
        Connaissance de Thaumaturgy (cantrip)
        Hellish Rebuke au niveau 3
        Darkness au niveau 5

        Race: Tiefling
        """
        if not hasattr(character, 'infernal_legacy_spells'):
            spells = ['thaumaturgy']

            if character.level >= 3:
                spells.append('hellish-rebuke')

            if character.level >= 5:
                spells.append('darkness')

            character.infernal_legacy_spells = spells


__all__ = ['RacialTraits']
