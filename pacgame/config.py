"""Reads the config file (JSON with comments) and checks every value.

Lines starting with # or // are comments. If a key is missing or wrong we
print a message on stderr and use a default value, so the game never
crashes because of the config. Unknown keys are just ignored.
"""

import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Color = tuple[int, int, int]

MIN_LEVELS = 10
MAX_LEVELS = 50
MIN_MAZE_SIZE = 10
MAX_MAZE_SIZE = 60
DEFAULT_MAZE_SIZE = 15
MAX_SPEED = 0.5
MIN_SPEED = 0.005


KNOWN_KEYS = (
    "highscore_filename", "lives", "pacgum", "points_per_pacgum",
    "points_per_super_pacgum", "points_per_ghost", "seed", "level_max_time",
    "levels", "window_width", "window_height", "player_speed",
    "player_cheat_speed", "ghost_speed", "vulnerable_duration_ms",
    "ghost_respawn_ms", "wall_color", "background_color",
)


@dataclass(frozen=True)
class LevelConfig:
    """Size of the maze of one level, in cells."""

    width: int
    height: int


def _default_levels() -> list[LevelConfig]:
    """Return the default list of levels."""
    return [LevelConfig(DEFAULT_MAZE_SIZE, DEFAULT_MAZE_SIZE)
            for _ in range(MIN_LEVELS)]


@dataclass
class GameConfig:
    """All the game parameters, with their default values."""

    base_dir: Path = field(default_factory=Path.cwd)
    highscore_filename: str = "highscores.json"
    lives: int = 3
    pacgum: int = 200
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90
    levels: list[LevelConfig] = field(default_factory=_default_levels)
    window_width: int = 1500
    window_height: int = 600
    player_speed: float = 0.05
    player_cheat_speed: float = 0.1
    ghost_speed: float = 0.04
    vulnerable_duration_ms: int = 6000
    ghost_respawn_ms: int = 5000
    wall_color: Color = (33, 33, 222)
    background_color: Color = (0, 0, 0)

    @property
    def highscore_path(self) -> Path:
        """Highscore file path, next to the config file."""
        return self.base_dir / self.highscore_filename


def _warn(message: str) -> None:
    """Write a configuration warning on stderr."""
    print(f"[config] {message}", file=sys.stderr)


def strip_comments(text: str) -> str:
    """Empty the comment lines so json can parse the text.

    The lines are emptied, not removed, so the line numbers in the JSON error
    messages stay right.

    Args:
        text: raw content of the config file.

    Returns:
        the same text without the comments.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            lines.append("")
        else:
            lines.append(line)
    return "\n".join(lines)


def _read_int(data: dict[str, Any], key: str, default: int, low: int,
              high: int, label: str = "") -> int:
    """Get an int between low and high from data.

    Missing key: default (build_config prints one message for all of them).
    Wrong type: default + message. Out of range: clamped + message.
    """
    name = label or key
    if key not in data:
        return default
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        _warn(f"'{name}' must be an integer (got {value!r}); "
              f"using default {default}")
        return default
    if value < low or value > high:
        clamped = max(low, min(high, value))
        _warn(f"'{name}'={value} is out of range [{low}, {high}]; "
              f"using {clamped}")
        return clamped
    return value


def _read_float(data: dict[str, Any], key: str, default: float, low: float,
                high: float) -> float:
    """Same as _read_int but for numbers with decimals."""
    if key not in data:
        return default
    value = data[key]
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value)):
        _warn(f"'{key}' must be a number (got {value!r}); "
              f"using default {default}")
        return default
    number = float(value)
    if number < low or number > high:
        clamped = max(low, min(high, number))
        _warn(f"'{key}'={number} is out of range [{low}, {high}]; "
              f"using {clamped}")
        return clamped
    return number


def _read_string(data: dict[str, Any], key: str, default: str) -> str:
    """Read a non-empty string from ``data``."""
    if key not in data:
        return default
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        _warn(f"'{key}' must be a non-empty string (got {value!r}); "
              f"using default {default!r}")
        return default
    return value.strip()


def _read_color(data: dict[str, Any], key: str, default: Color) -> Color:
    """Get an [r, g, b] color from data (0-255 each)."""
    if key not in data:
        return default
    value = data[key]
    if (isinstance(value, list) and len(value) == 3
            and all(isinstance(c, int) and not isinstance(c, bool)
                    and 0 <= c <= 255 for c in value)):
        return (value[0], value[1], value[2])
    _warn(f"'{key}' must be a list of 3 integers in [0, 255] "
          f"(got {value!r}); using default {list(default)}")
    return default


def _read_levels(data: dict[str, Any]) -> list[LevelConfig]:
    """Get the list of levels, 10 at least (we repeat the last one)."""
    raw = data.get("levels")
    if raw is None:
        return _default_levels()
    if not isinstance(raw, list) or not raw:
        _warn("'levels' must be a non-empty list; using default levels")
        return _default_levels()
    if len(raw) > MAX_LEVELS:
        _warn(f"'levels' has more than {MAX_LEVELS} entries; truncating")
        raw = raw[:MAX_LEVELS]
    levels: list[LevelConfig] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, dict):
            _warn(f"levels[{index}] must be an object; using defaults")
            entry = {}
        width = _read_int(entry, "width", DEFAULT_MAZE_SIZE, MIN_MAZE_SIZE,
                          MAX_MAZE_SIZE, f"levels[{index}].width")
        height = _read_int(entry, "height", DEFAULT_MAZE_SIZE,
                           MIN_MAZE_SIZE, MAX_MAZE_SIZE,
                           f"levels[{index}].height")
        levels.append(LevelConfig(width, height))
    if len(levels) < MIN_LEVELS:
        _warn(f"the game needs at least {MIN_LEVELS} levels; "
              "repeating the last one")
        while len(levels) < MIN_LEVELS:
            levels.append(levels[-1])
    return levels


def build_config(data: dict[str, Any], base_dir: Path,
                 report_missing: bool = True) -> GameConfig:
    """Build the config from the parsed JSON, checking every value.

    Args:
        data: parsed JSON object (unknown keys are ignored).
        base_dir: folder used for the highscore file.
        report_missing: print one message with all the missing keys.

    Returns:
        a GameConfig where every value is valid.
    """
    missing = [key for key in KNOWN_KEYS if key not in data]
    if missing and report_missing:
        _warn("missing keys, using defaults for: " + ", ".join(missing))
    defaults = GameConfig(base_dir=base_dir)
    return GameConfig(
        base_dir=base_dir,
        highscore_filename=_read_string(
            data, "highscore_filename", defaults.highscore_filename),
        lives=_read_int(data, "lives", defaults.lives, 1, 99),
        pacgum=_read_int(data, "pacgum", defaults.pacgum, 1, 2000),
        points_per_pacgum=_read_int(
            data, "points_per_pacgum", defaults.points_per_pacgum, 0, 10000),
        points_per_super_pacgum=_read_int(
            data, "points_per_super_pacgum",
            defaults.points_per_super_pacgum, 0, 10000),
        points_per_ghost=_read_int(
            data, "points_per_ghost", defaults.points_per_ghost, 0, 10000),
        seed=_read_int(data, "seed", defaults.seed, 0, 2 ** 31 - 1),
        level_max_time=_read_int(
            data, "level_max_time", defaults.level_max_time, 5, 3600),
        levels=_read_levels(data),
        window_width=_read_int(
            data, "window_width", defaults.window_width, 400, 3000),
        window_height=_read_int(
            data, "window_height", defaults.window_height, 400, 2000),
        player_speed=_read_float(
            data, "player_speed", defaults.player_speed,
            MIN_SPEED, MAX_SPEED),
        player_cheat_speed=_read_float(
            data, "player_cheat_speed", defaults.player_cheat_speed,
            MIN_SPEED, MAX_SPEED),
        ghost_speed=_read_float(
            data, "ghost_speed", defaults.ghost_speed, MIN_SPEED, MAX_SPEED),
        vulnerable_duration_ms=_read_int(
            data, "vulnerable_duration_ms", defaults.vulnerable_duration_ms,
            500, 60000),
        ghost_respawn_ms=_read_int(
            data, "ghost_respawn_ms", defaults.ghost_respawn_ms, 500, 60000),
        wall_color=_read_color(data, "wall_color", defaults.wall_color),
        background_color=_read_color(
            data, "background_color", defaults.background_color),
    )


def _read_json_file(path: Path) -> dict[str, Any]:
    """Read the file, give {} if anything goes wrong."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        _warn(f"cannot read '{path}' ({exc}); using default configuration")
        return {}
    try:
        data = json.loads(strip_comments(text))
    except ValueError as exc:
        _warn(f"'{path}' is not valid JSON ({exc}); "
              "using default configuration")
        return {}
    if not isinstance(data, dict):
        _warn(f"'{path}' must contain a JSON object; "
              "using default configuration")
        return {}
    return data


def load_config(path: str) -> GameConfig:
    """Load the config file. Never raises.

    Args:
        path: path of the JSON config file.

    Returns:
        the config (defaults for everything invalid).
    """
    file_path = Path(path)
    base_dir = file_path.resolve().parent
    data = _read_json_file(file_path)
    return build_config(data, base_dir, report_missing=bool(data))
