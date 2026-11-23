"""Entry point of the game: ``python3 pac-man.py config.json``."""

import sys

from pacgame.config import load_config
from pacgame.game import run_game


def main(argv: list[str]) -> int:
    """Check the command line and run the game.

    Args:
        argv: command line arguments (program name included).

    Returns:
        the exit code.
    """
    if len(argv) != 2:
        print("Usage: python3 pac-man.py <config.json>", file=sys.stderr)
        return 2
    return run_game(load_config(argv[1]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
