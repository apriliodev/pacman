"""Loading of the image assets shipped with the game."""

from pathlib import Path

import pygame

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def load_image(name: str) -> pygame.Surface:
    """Load an image from the assets directory.

    The display must already be initialised (``convert_alpha`` needs it).

    Args:
        name: File name of the image inside the ``assets`` directory.

    Returns:
        The loaded surface, converted for fast blitting.

    Raises:
        FileNotFoundError: If the image does not exist.
        pygame.error: If the file cannot be decoded.
    """
    path = ASSETS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"missing asset: {path}")
    return pygame.image.load(str(path)).convert_alpha()
