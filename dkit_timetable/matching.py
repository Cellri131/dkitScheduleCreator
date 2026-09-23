"""Helpers to match free-typed user input (course names, student group names)
against the site's real data, with interactive disambiguation when the input
isn't an exact match.
"""
from __future__ import annotations

import difflib

from .catalog import StudentGroup
from .scraper import ClassSession


def _prompt_choice(prompt: str, options: list[str]) -> int | None:
    """Show a numbered list of options and ask the user to pick one.

    Returns the chosen index, or None if the user typed 0 / left it blank
    (meaning "skip").
    """
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"   {i}. {option}")
    print("   0. Aucun de ceux-ci / ignorer")
    while True:
        try:
            choice = input("Votre choix: ").strip()
        except EOFError:
            return None
        if choice in ("", "0"):
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        print("Choix invalide, réessayez.")


def match_group(catalog: list[StudentGroup], query: str) -> StudentGroup | None:
    """Find the StudentGroup matching a user-typed group name.

    Tries an exact (case-insensitive) match first, then falls back to fuzzy
    matching and asks the user to disambiguate if there are several close
    candidates.
    """
    # Correction de l'espace spécifique pour ": BSc" avant le traitement
    query = query.replace(": BSc", ":BSc")

    query_norm = query.strip().lower()

    exact = [g for g in catalog if g.title.lower() == query_norm]
    if exact:
        return exact[0]

    contains = [g for g in catalog if query_norm in g.title.lower()]
    if len(contains) == 1:
        return contains[0]

    titles = [g.title for g in catalog]
    candidates = contains or [
        g for g in catalog if g.title in difflib.get_close_matches(query, titles, n=5, cutoff=0.5)
    ]
    if not candidates:
        print(f"Aucun groupe trouvé pour '{query}'.")
        return None

    if len(candidates) == 1:
        return candidates[0]

    chosen = _prompt_choice(
        f"Plusieurs groupes correspondent à '{query}', lequel voulez-vous ?",
        [g.title for g in candidates],
    )
    return None if chosen is None else candidates[chosen]


# Above this similarity ratio a fuzzy match is treated as an obvious typo and
# accepted automatically; below it (but above _FUZZY_CUTOFF) we ask the user
# to confirm rather than silently picking a possibly unrelated course.
_FUZZY_AUTOACCEPT_RATIO = 0.9
_FUZZY_CUTOFF = 0.6


def find_matching_sessions(sessions: list[ClassSession], course_query: str) -> list[ClassSession]:
    """Find the sessions in a group's timetable whose Description matches a
    user-typed course name.
    """
    query_norm = course_query.strip().lower()

    exact = [s for s in sessions if s.description.lower() == query_norm]
    if exact:
        return exact

    contains = [
        s
        for s in sessions
        if query_norm in s.description.lower() or s.description.lower() in query_norm
    ]
    if contains:
        matched_descriptions = {s.description for s in contains}
        if len(matched_descriptions) == 1:
            return contains
        chosen = _prompt_choice(
            f"Plusieurs cours correspondent à '{course_query}' dans ce groupe, lequel voulez-vous ?",
            sorted(matched_descriptions),
        )
        if chosen is not None:
            picked = sorted(matched_descriptions)[chosen]
            return [s for s in sessions if s.description == picked]
        return []

    descriptions = sorted({s.description for s in sessions})
    close = difflib.get_close_matches(course_query, descriptions, n=5, cutoff=_FUZZY_CUTOFF)
    if not close:
        return []

    best_ratio = difflib.SequenceMatcher(None, query_norm, close[0].lower()).ratio()
    if len(close) == 1 and best_ratio >= _FUZZY_AUTOACCEPT_RATIO:
        return [s for s in sessions if s.description == close[0]]

    chosen = _prompt_choice(
        f"Aucune correspondance exacte pour '{course_query}' dans ce groupe. Vouliez-vous dire :",
        close,
    )
    if chosen is not None:
        return [s for s in sessions if s.description == close[chosen]]
    return []

    return []
