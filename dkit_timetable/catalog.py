"""Fetches and parses the list of "Student Group(s) to view" from the DKIT
timetable site (https://timetables.dkit.ie/studentset.php).

The site never sends this list to the browser via AJAX: it is embedded as a
big JavaScript array (``studsetarray``) inside js/filter.min.js and filtered
client-side. We reproduce that parsing here so we always have the up to date
catalogue of student groups (and their internal identifiers) without needing
a real browser.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests

FILTER_JS_URL = "https://timetables.dkit.ie/js/filter.min.js"

# Matches assignments like: studsetarray[12] [0] = "Some Title";
_ARRAY_ENTRY_RE = re.compile(r'studsetarray\[(\d+)\]\s*\[(\d)\]\s*=\s*"([^"]*)"')


@dataclass(frozen=True)
class StudentGroup:
    """One entry of the "Student Group(s) to view" list box."""

    title: str
    dept_code: str
    identifier: str  # already percent-encoded, used verbatim in report URLs


def fetch_student_groups(session: requests.Session | None = None) -> list[StudentGroup]:
    """Download js/filter.min.js and parse the full catalogue of student groups.

    We read the array as it is built inside ``FilterStudentSetsByTitle`` (the
    human readable, sorted-by-title variant) rather than the one built inside
    ``FilterStudentSetsByCode`` (which prefixes titles with the internal code).
    """
    session = session or requests.Session()
    resp = session.get(FILTER_JS_URL, timeout=20)
    resp.raise_for_status()
    content = resp.text

    marker = "function FilterStudentSetsByTitle"
    start = content.find(marker)
    if start == -1:
        raise RuntimeError(
            "Could not find FilterStudentSetsByTitle in filter.min.js "
            "(the DKIT timetable site's format may have changed)."
        )
    end = content.find("function ", start + len(marker))
    block = content[start:] if end == -1 else content[start:end]

    fields_by_index: dict[int, dict[int, str]] = {}
    for match in _ARRAY_ENTRY_RE.finditer(block):
        index, field, value = int(match.group(1)), int(match.group(2)), match.group(3)
        fields_by_index.setdefault(index, {})[field] = value

    groups: list[StudentGroup] = []
    for index in sorted(fields_by_index):
        fields = fields_by_index[index]
        if 0 not in fields or 2 not in fields:
            continue
        groups.append(
            StudentGroup(title=fields[0], dept_code=fields.get(1, ""), identifier=fields[2])
        )
    return groups
