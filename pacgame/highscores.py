"""Top 10 highscores saved in a JSON file.

File format::

    [{"name": "Alice", "score": 1200}, {"name": "Bob", "score": 800}]

Reading never crashes: a missing or broken file gives an empty list and
bad entries are skipped.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, TypedDict

MAX_NAME_LENGTH = 10
MAX_ENTRIES = 10
DEFAULT_NAME = "Anonymous"


class ScoreEntry(TypedDict):
    """One line of the highscore table."""

    name: str
    score: int


def _warn(message: str) -> None:
    """Write a highscore warning on stderr."""
    print(f"[highscores] {message}", file=sys.stderr)


def is_allowed_char(char: str) -> bool:
    """Check one character of a player name.

    Args:
        char: a single character.

    Returns:
        True for ASCII letters, digits and space.
    """
    return len(char) == 1 and char.isascii() and (
        char.isalnum() or char == " ")


def is_valid_name(name: object) -> bool:
    """Check a player name: 1 to 10 characters, letters, digits and spaces.

    Args:
        name: any value.

    Returns:
        True if the name is ok.
    """
    return (isinstance(name, str) and 0 < len(name) <= MAX_NAME_LENGTH
            and all(is_allowed_char(char) for char in name))


def _is_valid_entry(entry: object) -> bool:
    """Check one entry read from the file."""
    if not isinstance(entry, dict):
        return False
    score = entry.get("score")
    return (is_valid_name(entry.get("name"))
            and isinstance(score, int) and not isinstance(score, bool)
            and score >= 0)


def _sorted_top(entries: list[ScoreEntry]) -> list[ScoreEntry]:
    """Best score first, keep the first 10."""
    ranked = sorted(entries, key=lambda entry: entry["score"], reverse=True)
    return ranked[:MAX_ENTRIES]


def load_scores(path: Path) -> list[ScoreEntry]:
    """Read the highscores, best first.

    Args:
        path: the highscore JSON file.

    Returns:
        10 valid entries at most, empty list if the file is missing or
        unusable.
    """
    if not path.exists():
        return []
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _warn(f"cannot read '{path}' ({exc}); starting with an empty table")
        return []
    if not isinstance(data, list):
        _warn(f"'{path}' does not contain a list; ignoring its content")
        return []
    entries: list[ScoreEntry] = []
    for item in data:
        if _is_valid_entry(item):
            entries.append({"name": item["name"], "score": item["score"]})
    return _sorted_top(entries)


def _clean_name(name: str) -> str:
    """Remove the forbidden characters and cut to 10 characters."""
    cleaned = "".join(c for c in name if is_allowed_char(c)).strip()
    cleaned = cleaned[:MAX_NAME_LENGTH].strip()
    return cleaned or DEFAULT_NAME


def save_score(path: Path, name: str, score: int) -> list[ScoreEntry]:
    """Add a score and write the table to disk.

    Args:
        path: the highscore JSON file.
        name: player name (cleaned if needed).
        score: final score (a negative one becomes 0).

    Returns:
        the new top 10, even if the file could not be written.
    """
    entries = load_scores(path)
    entries.append({"name": _clean_name(name), "score": max(0, int(score))})
    top = _sorted_top(entries)
    temporary = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(top, handle, indent=4)
        os.replace(temporary, path)
    except OSError as exc:
        _warn(f"cannot write '{path}' ({exc}); the score was not saved")
    return top
