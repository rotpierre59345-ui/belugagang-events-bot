"""
Système de calcul de niveaux et XP pour BeluGANG Events Bot.
"""

import math


def xp_for_level(level: int) -> int:
    """Retourne le total d'XP nécessaire pour atteindre un niveau donné."""
    return int(5 * (level ** 2) + 50 * level + 100)


def level_from_xp(xp: int) -> int:
    """Retourne le niveau correspondant à un total d'XP."""
    level = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
    return level


def xp_progress(xp: int) -> tuple[int, int, int]:
    """
    Retourne (niveau actuel, XP dans le niveau courant, XP requis pour le prochain niveau).
    """
    level = 0
    remaining = xp
    while remaining >= xp_for_level(level):
        remaining -= xp_for_level(level)
        level += 1
    return level, remaining, xp_for_level(level)


def xp_gain_for_message() -> int:
    """Retourne le gain d'XP aléatoire pour un message (entre 15 et 25)."""
    import random
    return random.randint(15, 25)
