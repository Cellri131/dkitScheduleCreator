"""Fetches and parses a student group's timetable from the DKIT timetable
report backend, mimicking what studentset.php does when you click "View
Timetable" (see js/local.min.js: myFunction() -> alert("Generated") then
window.open("process.php?url=...")).

We parse the "Grid Format" report (style=individual) because it exposes the
real 15-minute timetable grid used by the site. The "List Format" report
rounds some sessions to whole hours, which loses the exact finish times.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

PROCESS_URL = "https://timetables.dkit.ie/process.php"
REPORT_HOST = "spenterpriselive.dkit.ie:8000"

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_CODES = {
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday",
}

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")


@dataclass
class ClassSession:
    day: str
    start: str  # "HH:MM", zero-padded
    end: str
    description: str
    activity: str
    staff: str
    room: str


def _normalize_time(value: str) -> str:
    match = _TIME_RE.match(value.strip())
    if not match:
        return value.strip()
    hour, minute = match.groups()
    return f"{int(hour):02d}:{minute}"


def time_to_minutes(value: str) -> int:
    match = _TIME_RE.match(value.strip())
    if not match:
        return 0
    hour, minute = match.groups()
    return int(hour) * 60 + int(minute)


def build_report_url(
    identifier: str,
    *,
    style: str = "textspreadsheet",
    days: str = "1-5",
    weeks: str = "",
    periods: str = "5-40",
) -> str:
    """Build the process.php proxy URL for a given student-set identifier.

    Mirrors getTimetable() in js/form.min.js: identifier is already
    percent-encoded exactly as found in the site's catalogue, so it must NOT
    be re-decoded before being embedded in the target report URL.
    """
    template = f"student+set+{style}"
    target = (
        f"http://{REPORT_HOST}/reporting/{style};student+set;id;{identifier}"
        f"?t={template}&days={days}&weeks={weeks}&periods={periods}&template={template}"
    )
    return PROCESS_URL + "?url=" + urllib.parse.quote(target, safe="")


def fetch_group_timetable(
    identifier: str, session: requests.Session | None = None
) -> list[ClassSession]:
    """Fetch and parse one student group's "this week" timetable (all weekdays,
    09:00-18:00), merging back-to-back periods of the same class into one
    session.
    """
    session = session or requests.Session()
    url = build_report_url(identifier, style="individual")
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return _parse_grid_report(resp.text)


def _minutes_to_time(total_minutes: int) -> str:
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def _parse_grid_report(html: str) -> list[ClassSession]:
    soup = BeautifulSoup(html, "html.parser")
    sessions: list[ClassSession] = []

    main_table = soup.find("table", attrs={"border": "1"})
    if main_table is None:
        return sessions

    rows = main_table.find_all("tr", recursive=False)
    if len(rows) < 2:
        return sessions

    header_cells = rows[0].find_all("td", recursive=False)
    slot_times = [cell.get_text(strip=True) for cell in header_cells[1:]]
    if not slot_times:
        return sessions

    for row in rows[1:]:
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue

        day_code = cells[0].get_text(strip=True)
        day = DAY_CODES.get(day_code)
        if day is None:
            continue

        slot_index = 0
        for cell in cells[1:]:
            colspan = int(cell.get("colspan", "1"))
            text = cell.get_text(" ", strip=True)
            if not text or text == "\xa0":
                slot_index += colspan
                continue

            tables = cell.find_all("table", recursive=False)
            if len(tables) < 3 or slot_index >= len(slot_times):
                slot_index += colspan
                continue

            description = tables[0].get_text(" ", strip=True)
            details_cells = tables[1].find_all("td")
            room = details_cells[0].get_text(strip=True) if details_cells else ""
            staff = details_cells[1].get_text(strip=True) if len(details_cells) > 1 else ""
            weeks = tables[2].get_text(" ", strip=True)

            start_minutes = time_to_minutes(slot_times[slot_index])
            end_minutes = start_minutes + (colspan - 1) * 15
            sessions.append(
                ClassSession(
                    day=day,
                    start=_minutes_to_time(start_minutes),
                    end=_minutes_to_time(end_minutes),
                    description=description,
                    activity=weeks,
                    staff=staff,
                    room=room,
                )
            )
            slot_index += colspan

    return _merge_contiguous(sessions)


def _merge_contiguous(sessions: list[ClassSession]) -> list[ClassSession]:
    """The report lists one row per timetabled period, so a single 2-hour
    class can appear as two consecutive 1-hour rows. Merge rows that are
    back-to-back (previous end == next start) and describe the same class.
    """
    by_day: dict[str, list[ClassSession]] = {}
    for session in sessions:
        by_day.setdefault(session.day, []).append(session)

    merged: list[ClassSession] = []
    for day in by_day:
        day_sessions = sorted(by_day[day], key=lambda s: time_to_minutes(s.start))
        current: ClassSession | None = None
        for session in day_sessions:
            if (
                current is not None
                and time_to_minutes(session.start) == time_to_minutes(current.end) + 15
                and current.description == session.description
                and current.activity == session.activity
                and current.staff == session.staff
                and current.room == session.room
            ):
                current.end = session.end
            else:
                if current is not None:
                    merged.append(current)
                current = ClassSession(**vars(session))
        if current is not None:
            merged.append(current)

    return merged
