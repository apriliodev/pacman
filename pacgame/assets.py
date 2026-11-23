"""Loading of the image assets shipped with the game."""

from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def load_image(name: str) -> pygame.Surface:
    """Load an image from the assets folder.

    Needs the display to be initialised already (because of convert_alpha).

    Args:
        name: file name inside assets/.

    Returns:
        The image surface.

    Raises:
        FileNotFoundError: if the file is missing.
        pygame.error: if the file cannot be read as an image.
    """
    path = ASSETS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"missing asset: {path}")
    return pygame.image.load(str(path)).convert_alpha()
