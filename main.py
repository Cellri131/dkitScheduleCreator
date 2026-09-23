"""DKIT timetable planner.

Interactively asks for a list of "Course Name | Student Group" lines, looks
each course up on https://timetables.dkit.ie/studentset.php, and prints (and
saves) a merged weekly planning grouped by day.
"""
from __future__ import annotations

import sys

import requests

from dkit_timetable.catalog import StudentGroup, fetch_student_groups
from dkit_timetable.matching import find_matching_sessions, match_group
from dkit_timetable.output import build_output
from dkit_timetable.scraper import ClassSession, fetch_group_timetable

OUTPUT_FILE = "planning.txt"


def read_course_requests() -> list[tuple[str, str]]:
    print("Entrez vos cours, un par ligne, au format :")
    print("   Nom du cours | Nom du groupe (Student Group)")
    print("Tapez 'Stop' seul sur une ligne quand vous avez terminé.\n")

    requested: list[tuple[str, str]] = []
    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            break
        if line.lower() == "stop":
            break
        if not line:
            continue
        if "|" not in line:
            print("Format invalide. Utilisez : Nom du cours | Nom du groupe")
            continue
        course, group = (part.strip() for part in line.split("|", 1))
        group.replace(": BSc", ":BSc")
        if not course or not group:
            print("Format invalide. Utilisez : Nom du cours | Nom du groupe")
            continue
        requested.append((course, group))
    return requested


def main() -> int:
    print("Chargement du catalogue des groupes DKIT (studentset.php)...")
    try:
        catalog: list[StudentGroup] = fetch_student_groups()
    except requests.RequestException as exc:
        print(f"Impossible de contacter timetables.dkit.ie : {exc}")
        return 1
    print(f"{len(catalog)} groupes disponibles.\n")

    course_requests = read_course_requests()
    if not course_requests:
        print("Aucun cours renseigné, arrêt.")
        return 0

    http_session = requests.Session()
    timetable_cache: dict[str, list[ClassSession]] = {}
    entries: list[tuple[ClassSession, str]] = []

    print("\nRécupération des plannings...")
    for course_name, group_query in course_requests:
        group = match_group(catalog, group_query)
        if group is None:
            print(f"[Ignoré] Groupe introuvable pour '{group_query}'.")
            continue

        if group.identifier not in timetable_cache:
            print(f"  - Téléchargement du planning : {group.title}")
            try:
                timetable_cache[group.identifier] = fetch_group_timetable(
                    group.identifier, http_session
                )
            except requests.RequestException as exc:
                print(f"    Erreur lors du téléchargement : {exc}")
                timetable_cache[group.identifier] = []

        sessions = timetable_cache[group.identifier]
        matches = find_matching_sessions(sessions, course_name)
        if not matches:
            print(f"[Ignoré] Aucun cours correspondant à '{course_name}' dans '{group.title}'.")
            available = sorted({s.description for s in sessions})
            if available:
                print("    Cours disponibles dans ce groupe :")
                for description in available:
                    print(f"      - {description}")
            continue

        for session in matches:
            entries.append((session, group.title))

    if not entries:
        print("\nAucune séance trouvée, aucun planning généré.")
        return 0

    output = build_output(entries)
    print("\n" + output)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Planning enregistré dans {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
