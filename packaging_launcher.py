"""Launcher used by the packaged (PyInstaller) build.

The packaged game is started without any argument, so this launcher looks
for a configuration file and falls back on the one bundled with the game.
From the command line, ``python3 pac-man.py config.json`` stays the
reference way to run the game.
"""

import sys
from pathlib import Path

from pacgame.config import load_config
from pacgame.game import run_game


def find_config(argv: list[str]) -> str:
    """Choose the configuration file to use.

    Args:
        argv: The command line arguments (program name included).

    Returns:
        The path given on the command line, else ``config.json`` next to
        the executable, else the bundled one.
    """
    if len(argv) == 2:
        return argv[1]
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
        candidates.append(Path(getattr(sys, "_MEIPASS", ".")))
    candidates.append(Path(__file__).resolve().parent)
    for directory in candidates:
        if (directory / "config.json").is_file():
            return str(directory / "config.json")
    return "config.json"


if __name__ == "__main__":
    sys.exit(run_game(load_config(find_config(sys.argv))))
