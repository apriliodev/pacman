"""Tests of the configuration loader."""

from pathlib import Path

import pytest

from pacgame.config import (MIN_LEVELS, build_config, load_config,
                            strip_comments)


def test_strip_comments_blanks_comment_lines() -> None:
    """Comment lines are removed, line count is preserved."""
    text = '# a\n{\n  // b\n  "lives": 4\n}\n'
    assert strip_comments(text).splitlines()[0] == ""
    assert strip_comments(text).count("\n") == text.count("\n") - 1


def test_defaults_for_empty_object(tmp_path: Path) -> None:
    """An empty object gives the default configuration."""
    config = build_config({}, tmp_path)
    assert config.lives == 3
    assert len(config.levels) == MIN_LEVELS
    assert config.highscore_path == tmp_path / "highscores.json"


def test_invalid_values_fall_back(tmp_path: Path,
                                  capsys: pytest.CaptureFixture[str]
                                  ) -> None:
    """Wrong types use defaults, out-of-range numbers are clamped."""
    config = build_config(
        {"lives": "three", "pacgum": 10 ** 9, "player_speed": True,
         "wall_color": [1, 2], "unknown_key": 1, "levels": 5}, tmp_path)
    assert config.lives == 3
    assert config.pacgum == 2000
    assert config.player_speed == 0.05
    assert config.wall_color == (33, 33, 222)
    assert len(config.levels) == MIN_LEVELS
    assert "[config]" in capsys.readouterr().err


def test_short_level_list_is_padded(tmp_path: Path) -> None:
    """The game always has at least 10 levels."""
    config = build_config({"levels": [{"width": 20, "height": 12}]},
                          tmp_path)
    assert len(config.levels) == MIN_LEVELS
    assert config.levels[-1].width == 20


def test_load_config_with_comments(tmp_path: Path) -> None:
    """A commented file is parsed."""
    path = tmp_path / "c.json"
    path.write_text('# comment\n{\n"lives": 5\n}\n', encoding="utf-8")
    assert load_config(str(path)).lives == 5


def test_load_config_never_raises(tmp_path: Path) -> None:
    """Missing, broken and non-object files give the defaults."""
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    listing = tmp_path / "list.json"
    listing.write_text("[1, 2]", encoding="utf-8")
    for path in (tmp_path / "missing.json", broken, listing):
        assert load_config(str(path)).lives == 3
