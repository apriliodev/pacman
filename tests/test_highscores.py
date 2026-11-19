"""Tests of the highscore storage."""

import json
from pathlib import Path

from pacgame.highscores import (MAX_ENTRIES, is_valid_name, load_scores,
                                save_score)


def test_name_rules() -> None:
    """Names: 1-10 characters, letters, digits and spaces only."""
    assert is_valid_name("Alice 42")
    assert not is_valid_name("")
    assert not is_valid_name("x" * 11)
    assert not is_valid_name("bob!")
    assert not is_valid_name(12)


def test_missing_and_corrupted_files(tmp_path: Path) -> None:
    """Unusable files give an empty table, never an exception."""
    assert load_scores(tmp_path / "none.json") == []
    broken = tmp_path / "broken.json"
    broken.write_text("not json", encoding="utf-8")
    assert load_scores(broken) == []
    other = tmp_path / "other.json"
    other.write_text('{"a": 1}', encoding="utf-8")
    assert load_scores(other) == []


def test_invalid_entries_are_skipped(tmp_path: Path) -> None:
    """Only valid entries are kept, sorted by score."""
    path = tmp_path / "s.json"
    path.write_text(json.dumps([
        {"name": "Alice", "score": 200},
        {"name": "", "score": 50},
        {"name": "Eve", "score": -5},
        {"name": "Zed", "score": True},
        {"name": "Dave", "score": 300},
        {"score": 1},
        "junk",
    ]), encoding="utf-8")
    assert load_scores(path) == [{"name": "Dave", "score": 300},
                                 {"name": "Alice", "score": 200}]


def test_save_keeps_top_ten(tmp_path: Path) -> None:
    """The table keeps the 10 best scores, best first."""
    path = tmp_path / "s.json"
    for score in range(15):
        save_score(path, f"P{score}", score)
    scores = load_scores(path)
    assert len(scores) == MAX_ENTRIES
    assert scores[0] == {"name": "P14", "score": 14}
    assert scores[-1]["score"] == 5


def test_save_cleans_the_name(tmp_path: Path) -> None:
    """Invalid names are sanitized; empty names become Anonymous."""
    path = tmp_path / "s.json"
    save_score(path, "  bad!name--too long  ", -7)
    save_score(path, "!!!", 3)
    names = {entry["name"] for entry in load_scores(path)}
    assert "Anonymous" in names
    assert all(is_valid_name(name) for name in names)
    assert load_scores(path)[-1]["score"] == 0


def test_save_to_unwritable_path_does_not_raise(tmp_path: Path) -> None:
    """A write failure is reported but never raises."""
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    table = save_score(blocker / "scores.json", "Bob", 10)
    assert table == [{"name": "Bob", "score": 10}]
