"""
D&D 5e Core - Advanced Encounter Builder
Utilise les tables de rencontres exactes de D&D 5e comme dans main.py
"""
from typing import List, Tuple, Dict, Optional
from fractions import Fraction
from random import choice, randint


# Table de rencontres basée sur Encounter_Levels.csv
# Format: {level: (pair_crs, {nombre_monstres: [crs_possibles]})}
ENCOUNTER_TABLE = {
    1: (
        (Fraction(1, 2), Fraction(1, 3)),
        {
            "1": [Fraction(1), Fraction(2)],
            "2": [Fraction(1, 2)],
            "3": [Fraction(1, 3)],
            "4": [Fraction(1, 4)],
            "5-6": [Fraction(1, 6)],
            "7-9": [Fraction(1, 8)],
            "10-12": [Fraction(1, 8)],
        }
    ),
    2: (
        (Fraction(1), Fraction(1, 2)),
        {
            "1": [Fraction(2), Fraction(3)],
            "2": [Fraction(1)],
            "3": [Fraction(1, 2), Fraction(1)],
            "4": [Fraction(1, 2)],
            "5-6": [Fraction(1, 3)],
            "7-9": [Fraction(1, 4)],
            "10-12": [Fraction(1, 6)],
        }
    ),
    3: (
        (Fraction(2), Fraction(1)),
        {
            "1": [Fraction(3), Fraction(4)],
            "2": [Fraction(1), Fraction(2)],
            "3": [Fraction(1)],
            "4": [Fraction(1, 2), Fraction(1)],
            "5-6": [Fraction(1, 2)],
            "7-9": [Fraction(1, 3)],
            "10-12": [Fraction(1, 4)],
        }
    ),
    4: (
        (Fraction(3), Fraction(1)),
        {
            "1": [Fraction(3), Fraction(4), Fraction(5)],
            "2": [Fraction(2)],
            "3": [Fraction(1), Fraction(2)],
            "4": [Fraction(1)],
            "5-6": [Fraction(1, 2), Fraction(1)],
            "7-9": [Fraction(1, 2)],
            "10-12": [Fraction(1, 3)],
        }
    ),
    5: (
        (Fraction(4), Fraction(2)),
        {
            "1": [Fraction(4), Fraction(5), Fraction(6)],
            "2": [Fraction(3)],
            "3": [Fraction(2)],
            "4": [Fraction(1), Fraction(2)],
            "5-6": [Fraction(1)],
            "7-9": [Fraction(1, 2)],
            "10-12": [Fraction(1, 2)],
        }
    ),
    6: (
        (Fraction(5), Fraction(3)),
        {
            "1": [Fraction(5), Fraction(6), Fraction(7)],
            "2": [Fraction(4)],
            "3": [Fraction(3)],
            "4": [Fraction(2)],
            "5-6": [Fraction(1), Fraction(2)],
            "7-9": [Fraction(1)],
            "10-12": [Fraction(1, 2)],
        }
    ),
    7: (
        (Fraction(6), Fraction(4)),
        {
            "1": [Fraction(6), Fraction(7), Fraction(8)],
            "2": [Fraction(5)],
            "3": [Fraction(4)],
            "4": [Fraction(3)],
            "5-6": [Fraction(2)],
            "7-9": [Fraction(1)],
            "10-12": [Fraction(1, 2)],
        }
    ),
    8: (
        (Fraction(7), Fraction(5)),
        {
            "1": [Fraction(7), Fraction(8), Fraction(9)],
            "2": [Fraction(6)],
            "3": [Fraction(5)],
            "4": [Fraction(4)],
            "5-6": [Fraction(3)],
            "7-9": [Fraction(2)],
            "10-12": [Fraction(1)],
        }
    ),
    9: (
        (Fraction(8), Fraction(6)),
        {
            "1": [Fraction(8), Fraction(9), Fraction(10)],
            "2": [Fraction(7)],
            "3": [Fraction(6)],
            "4": [Fraction(5)],
            "5-6": [Fraction(4)],
            "7-9": [Fraction(3)],
            "10-12": [Fraction(2)],
        }
    ),
    10: (
        (Fraction(9), Fraction(7)),
        {
            "1": [Fraction(9), Fraction(10), Fraction(11)],
            "2": [Fraction(8)],
            "3": [Fraction(7)],
            "4": [Fraction(6)],
            "5-6": [Fraction(5)],
            "7-9": [Fraction(4)],
            "10-12": [Fraction(3)],
        }
    ),
    11: (
        (Fraction(10), Fraction(8)),
        {
            "1": [Fraction(10), Fraction(11), Fraction(12)],
            "2": [Fraction(9)],
            "3": [Fraction(8)],
            "4": [Fraction(7)],
            "5-6": [Fraction(6)],
            "7-9": [Fraction(5)],
            "10-12": [Fraction(4)],
        }
    ),
    12: (
        (Fraction(11), Fraction(9)),
        {
            "1": [Fraction(11), Fraction(12), Fraction(13)],
            "2": [Fraction(10)],
            "3": [Fraction(9)],
            "4": [Fraction(8)],
            "5-6": [Fraction(7)],
            "7-9": [Fraction(6)],
            "10-12": [Fraction(5)],
        }
    ),
    13: (
        (Fraction(12), Fraction(10)),
        {
            "1": [Fraction(12), Fraction(13), Fraction(14)],
            "2": [Fraction(11)],
            "3": [Fraction(10)],
            "4": [Fraction(9)],
            "5-6": [Fraction(8)],
            "7-9": [Fraction(7)],
            "10-12": [Fraction(6)],
        }
    ),
    14: (
        (Fraction(13), Fraction(11)),
        {
            "1": [Fraction(13), Fraction(14), Fraction(15)],
            "2": [Fraction(12)],
            "3": [Fraction(11)],
            "4": [Fraction(10)],
            "5-6": [Fraction(9)],
            "7-9": [Fraction(8)],
            "10-12": [Fraction(7)],
        }
    ),
    15: (
        (Fraction(14), Fraction(12)),
        {
            "1": [Fraction(14), Fraction(15), Fraction(16)],
            "2": [Fraction(13)],
            "3": [Fraction(12)],
            "4": [Fraction(11)],
            "5-6": [Fraction(10)],
            "7-9": [Fraction(9)],
            "10-12": [Fraction(8)],
        }
    ),
    16: (
        (Fraction(15), Fraction(13)),
        {
            "1": [Fraction(15), Fraction(16), Fraction(17)],
            "2": [Fraction(14)],
            "3": [Fraction(13)],
            "4": [Fraction(12)],
            "5-6": [Fraction(11)],
            "7-9": [Fraction(10)],
            "10-12": [Fraction(9)],
        }
    ),
    17: (
        (Fraction(16), Fraction(14)),
        {
            "1": [Fraction(16), Fraction(17), Fraction(18)],
            "2": [Fraction(15)],
            "3": [Fraction(14)],
            "4": [Fraction(13)],
            "5-6": [Fraction(12)],
            "7-9": [Fraction(11)],
            "10-12": [Fraction(10)],
        }
    ),
    18: (
        (Fraction(17), Fraction(15)),
        {
            "1": [Fraction(17), Fraction(18), Fraction(19)],
            "2": [Fraction(16)],
            "3": [Fraction(15)],
            "4": [Fraction(14)],
            "5-6": [Fraction(13)],
            "7-9": [Fraction(12)],
            "10-12": [Fraction(11)],
        }
    ),
    19: (
        (Fraction(18), Fraction(16)),
        {
            "1": [Fraction(18), Fraction(19), Fraction(20)],
            "2": [Fraction(17)],
            "3": [Fraction(16)],
            "4": [Fraction(15)],
            "5-6": [Fraction(14)],
            "7-9": [Fraction(13)],
            "10-12": [Fraction(12)],
        }
    ),
    20: (
        (Fraction(19), Fraction(17)),
        {
            "1": [19],  # 19+ signifie >= 19
            "2": [Fraction(18)],
            "3": [Fraction(17)],
            "4": [Fraction(16)],
            "5-6": [Fraction(15)],
            "7-9": [Fraction(14)],
            "10-12": [Fraction(13)],
        }
    ),
}


def generate_encounter_distribution(party_level: int) -> List[int]:
    """
    Générer une distribution de niveaux de rencontre basée sur le niveau du groupe.

    Suit les probabilités D&D 5e:
    - 30% rencontres faciles (niveau < party_level)
    - 50% rencontres moyennes (niveau = party_level)
    - 15% rencontres difficiles (niveau = party_level + 1-4)
    - 5% rencontres mortelles (niveau = party_level + 5-20)

    Args:
        party_level: Niveau moyen du groupe

    Returns:
        Liste de 20 niveaux de rencontre
    """
    encounter_levels = []

    # 30% faciles (divisé par 5 pour 20 rencontres = 6 rencontres)
    for _ in range(6):
        if party_level > 1:
            encounter_levels.append(randint(1, party_level - 1))
        else:
            encounter_levels.append(1)

    # 50% moyennes (10 rencontres)
    for _ in range(10):
        encounter_levels.append(party_level)

    # 15% difficiles (3 rencontres)
    for _ in range(3):
        encounter_levels.append(party_level + randint(1, 4))

    # 5% mortelles (1 rencontre)
    encounter_levels.append(party_level + randint(5, 20))

    # Mélanger la liste
    from random import shuffle
    shuffle(encounter_levels)

    return encounter_levels


def select_monsters_by_encounter_table(
    encounter_level: int,
    available_monsters: List,
    spell_casters_only: bool = False,
    allow_pairs: bool = True
) -> Tuple[List, str]:
    """
    Sélectionner des monstres selon la table de rencontres D&D 5e officielle.

    Args:
        encounter_level: Niveau de la rencontre (1-20)
        available_monsters: Liste de monstres disponibles (avec attribut challenge_rating)
        spell_casters_only: Si True, ne sélectionne que des lanceurs de sorts
        allow_pairs: Si True, peut générer des paires de monstres de CR différents

    Returns:
        Tuple de (liste_monstres, type_rencontre)
        type_rencontre peut être "pair" ou "group"
    """
    encounter_level = min(20, max(1, encounter_level))

    if encounter_level not in ENCOUNTER_TABLE:
        encounter_level = min(ENCOUNTER_TABLE.keys(), key=lambda k: abs(k - encounter_level))

    pair_crs, group_dict = ENCOUNTER_TABLE[encounter_level]

    # Décider entre paire ou groupe (50/50 si allow_pairs)
    use_pair = allow_pairs and choice([True, False])

    if use_pair:
        # Générer une paire de monstres de CR différents
        cr1, cr2 = pair_crs

        # Trouver des monstres avec CR approprié
        cr1_monsters = [
            m for m in available_monsters
            if Fraction(str(m.challenge_rating)) == cr1
            and (not spell_casters_only or getattr(m, 'is_spell_caster', False))
        ]

        cr2_monsters = [
            m for m in available_monsters
            if Fraction(str(m.challenge_rating)) == cr2
            and (not spell_casters_only or getattr(m, 'is_spell_caster', False))
        ]

        # Si pas de monstres exacts, trouver les plus proches
        if not cr1_monsters:
            available_crs = sorted(set(Fraction(str(m.challenge_rating)) for m in available_monsters))
            if available_crs:
                closest_cr1 = min(available_crs, key=lambda cr: abs(float(cr - cr1)))
                cr1_monsters = [m for m in available_monsters if Fraction(str(m.challenge_rating)) == closest_cr1]

        if not cr2_monsters:
            available_crs = sorted(set(Fraction(str(m.challenge_rating)) for m in available_monsters))
            if available_crs:
                closest_cr2 = min(available_crs, key=lambda cr: abs(float(cr - cr2)))
                cr2_monsters = [m for m in available_monsters if Fraction(str(m.challenge_rating)) == closest_cr2]

        if cr1_monsters and cr2_monsters:
            return [choice(cr1_monsters), choice(cr2_monsters)], "pair"

    # Générer un groupe de monstres du même CR
    # Choisir une taille de groupe aléatoire
    group_size_key = choice(list(group_dict.keys()))
    group_size_range = list(map(int, group_size_key.split("-")))
    group_size = choice(group_size_range) if len(group_size_range) > 1 else group_size_range[0]

    # Obtenir les CR possibles pour cette taille de groupe
    possible_crs = group_dict[group_size_key]

    # Pour le niveau 20, CR 19+ signifie >= 19
    if encounter_level == 20 and group_size_key == "1":
        min_cr = possible_crs[0]
        matching_monsters = [
            m for m in available_monsters
            if m.challenge_rating >= min_cr
            and (not spell_casters_only or getattr(m, 'is_spell_caster', False))
        ]
    else:
        # Trouver des monstres avec un des CR possibles
        matching_monsters = [
            m for m in available_monsters
            if Fraction(str(m.challenge_rating)) in possible_crs
            and (not spell_casters_only or getattr(m, 'is_spell_caster', False))
        ]

    # Si pas de monstres exacts, trouver les plus proches
    if not matching_monsters:
        available_crs = sorted(set(Fraction(str(m.challenge_rating)) for m in available_monsters))
        if available_crs:
            target_cr = choice(possible_crs) if possible_crs else Fraction(encounter_level)
            closest_cr = min(available_crs, key=lambda cr: abs(float(cr - target_cr)))
            matching_monsters = [m for m in available_monsters if Fraction(str(m.challenge_rating)) == closest_cr]

    if matching_monsters:
        selected_monster = choice(matching_monsters)
        return [selected_monster] * group_size, "group"

    # Fallback: retourner un monstre aléatoire
    if available_monsters:
        return [choice(available_monsters)], "group"

    return [], "group"


def get_encounter_info(encounter_level: int) -> Dict:
    """
    Obtenir les informations de rencontre pour un niveau donné.

    Args:
        encounter_level: Niveau de la rencontre (1-20)

    Returns:
        Dictionnaire avec les informations de rencontre
    """
    encounter_level = min(20, max(1, encounter_level))

    if encounter_level not in ENCOUNTER_TABLE:
        encounter_level = min(ENCOUNTER_TABLE.keys(), key=lambda k: abs(k - encounter_level))

    pair_crs, group_dict = ENCOUNTER_TABLE[encounter_level]

    return {
        "level": encounter_level,
        "pair_crs": pair_crs,
        "group_options": group_dict,
    }

