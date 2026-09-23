"""Builds the final, human-readable weekly planning text from the collected
(class session, group label) pairs.
"""
from __future__ import annotations

from .scraper import ClassSession, time_to_minutes

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_NAME_WIDTH = 35


def build_output(entries: list[tuple[ClassSession, str]]) -> str:
    by_day: dict[str, list[tuple[ClassSession, str]]] = {day: [] for day in DAY_ORDER}
    for session, label in entries:
        by_day[session.day].append((session, label))

    lines: list[str] = []
    for day in DAY_ORDER:
        day_entries = by_day[day]
        if not day_entries:
            continue
        day_entries.sort(key=lambda entry: time_to_minutes(entry[0].start))
        lines.append(day)
        for session, label in day_entries:
            name = session.description.ljust(_NAME_WIDTH)
            lines.append(f"- {name} | Room {session.room} | {session.start} - {session.end} | {label}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
