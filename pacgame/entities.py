"""Moving entities: the player (Pac-Man) and the ghosts."""

import itertools
import math
from typing import Iterator

import pygame

from pacgame.assets import load_image
from pacgame.maze import (DELTAS, OPPOSITE, Cell, Maze, find_path,
                          neighbors, walls)

EPSILON = 1e-9
CENTER_TOLERANCE = 1e-6
SCARED_SPEED_FACTOR = 0.5
CATCH_DISTANCE_SQUARED = 0.5 ** 2

ANGLES: dict[str, int] = {"east": 0, "north": 90, "west": 180, "south": 270}

KEY_DIRECTIONS: dict[int, str] = {
    pygame.K_UP: "north",
    pygame.K_w: "north",
    pygame.K_z: "north",
    pygame.K_DOWN: "south",
    pygame.K_s: "south",
    pygame.K_LEFT: "west",
    pygame.K_a: "west",
    pygame.K_q: "west",
    pygame.K_RIGHT: "east",
    pygame.K_d: "east",
}

PLAYER_FRAMES = ("pacman_closed.png", "pacman_half_open.png",
                 "pacman_open.png")


def step(value: float, delta: float) -> float:
    """Move a coordinate by delta but never go past a cell center.

    Cell centers are the whole numbers. If the move reaches or passes the next
    one, we stop exactly on it. That way nobody can drift out of the grid,
    whatever the speed.

    Args:
        value: current coordinate.
        delta: distance to travel (negative = other way).

    Returns:
        the new coordinate.
    """
    new_value = value + delta
    if delta > 0:
        target = math.floor(value + EPSILON) + 1
        if new_value >= target - EPSILON:
            return float(target)
    elif delta < 0:
        target = math.ceil(value - EPSILON) - 1
        if new_value <= target + EPSILON:
            return float(target)
    return new_value


def advance(row: float, col: float, direction: str,
            speed: float) -> tuple[float, float]:
    """Move a position one step in a direction.

    Args:
        row: current row.
        col: current column.
        direction: north, east, south or west.
        speed: distance in cells.

    Returns:
        the new (row, column).
    """
    d_row, d_col = DELTAS[direction]
    return step(row, d_row * speed), step(col, d_col * speed)


def at_center(row: float, col: float) -> bool:
    """True if we are exactly on the center of a cell."""
    return (abs(row - round(row)) < CENTER_TOLERANCE
            and abs(col - round(col)) < CENTER_TOLERANCE)


class Player:
    """Pac-Man: moves in the maze, keeps the score and the lives."""

    def __init__(self, start: Cell, cell_size: int, speed: float,
                 lives: int) -> None:
        """Create the player.

        Args:
            start: (row, column) where it starts.
            cell_size: size of a cell in pixels.
            speed: cells per frame.
            lives: lives at the start of the game.
        """
        self.start = start
        self.row = float(start[0])
        self.col = float(start[1])
        self.direction = "east"
        self.next_direction = "east"
        self.speed = speed
        self.score = 0
        self.lives = lives
        self.level = 1
        self.cell_size = cell_size
        self._raw_frames = [load_image(name) for name in PLAYER_FRAMES]
        self._animation: Iterator[pygame.Surface] = iter(())
        self._offset = 0.0
        self.rescale(cell_size)

    def rescale(self, cell_size: int) -> None:
        """Resize the sprites for a new cell size."""
        self.cell_size = cell_size
        size = max(1, cell_size // 2)
        closed, half, opened = [
            pygame.transform.scale(frame, (size, size))
            for frame in self._raw_frames]
        self._animation = itertools.cycle(
            [half, half, closed, closed, half, half, opened, opened])
        self._offset = (cell_size - size) / 2

    @property
    def cell(self) -> Cell:
        """The cell the player is currently in."""
        return round(self.row), round(self.col)

    def reset_position(self) -> None:
        """Put the player back on its start cell."""
        self.row = float(self.start[0])
        self.col = float(self.start[1])
        self.direction = "east"
        self.next_direction = "east"

    def handle_key(self, key: int) -> None:
        """Remember the direction requested by a key press."""
        direction = KEY_DIRECTIONS.get(key)
        if direction is not None:
            self.next_direction = direction

    def update(self, maze: Maze) -> None:
        """Move the player for one frame.

        Turns only happen on cell centers, except U-turns which work anywhere.
        The player stops in front of a wall.
        """
        if at_center(self.row, self.col):
            self.row = float(round(self.row))
            self.col = float(round(self.col))
            blocked = walls(maze, (round(self.row), round(self.col)))
            if not blocked[self.next_direction]:
                self.direction = self.next_direction
            if blocked[self.direction]:
                return
        elif self.next_direction == OPPOSITE[self.direction]:
            self.direction = self.next_direction
        self.row, self.col = advance(self.row, self.col, self.direction,
                                     self.speed)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the player on the maze surface."""
        image = pygame.transform.rotate(next(self._animation),
                                        ANGLES[self.direction])
        surface.blit(image, (self.col * self.cell_size + self._offset,
                             self.row * self.cell_size + self._offset))


class Ghost:
    """A ghost: chases the player, flees when edible."""

    def __init__(self, start: Cell, image_name: str, cell_size: int,
                 speed: float) -> None:
        """Create a ghost.

        Args:
            start: (row, column) of its corner.
            image_name: file name of its sprite in assets/.
            cell_size: size of a cell in pixels.
            speed: cells per frame.
        """
        self.start = start
        self.row = float(start[0])
        self.col = float(start[1])
        self.direction: str | None = None
        self.speed = speed
        self.vulnerable = False
        self.vulnerable_until = 0
        self.eaten = False
        self.eaten_until = 0
        self.cell_size = cell_size
        self._raw_normal = load_image(image_name)
        self._raw_scared = load_image("ghost_scared.png")
        self._normal = self._raw_normal
        self._scared = self._raw_scared
        self._offset = 0.0
        self.rescale(cell_size)

    def rescale(self, cell_size: int) -> None:
        """Resize the sprites for a new cell size."""
        self.cell_size = cell_size
        size = max(1, cell_size // 2)
        self._normal = pygame.transform.scale(self._raw_normal, (size, size))
        self._scared = pygame.transform.scale(self._raw_scared, (size, size))
        self._offset = (cell_size - size) / 2

    @property
    def cell(self) -> Cell:
        """The cell the ghost is currently in."""
        return round(self.row), round(self.col)

    def reset_position(self) -> None:
        """Back to the corner, back to normal."""
        self.row = float(self.start[0])
        self.col = float(self.start[1])
        self.direction = None
        self.vulnerable = False
        self.eaten = False

    def make_vulnerable(self, until_ms: int) -> None:
        """Make the ghost edible until the given game time."""
        if not self.eaten:
            self.vulnerable = True
            self.vulnerable_until = until_ms

    def eat(self, until_ms: int) -> None:
        """Ghost eaten: back to its corner, it returns at until_ms."""
        self.eaten = True
        self.eaten_until = until_ms
        self.vulnerable = False
        self.row = float(self.start[0])
        self.col = float(self.start[1])
        self.direction = None

    def refresh(self, now_ms: int) -> None:
        """End the edible / eaten states whose time is over."""
        if self.eaten and now_ms >= self.eaten_until:
            self.eaten = False
        if self.vulnerable and now_ms >= self.vulnerable_until:
            self.vulnerable = False

    def touches(self, player: Player) -> bool:
        """Tell whether the ghost is close enough to catch the player."""
        if self.eaten:
            return False
        d_row = self.row - player.row
        d_col = self.col - player.col
        return d_row ** 2 + d_col ** 2 < CATCH_DISTANCE_SQUARED

    def _face(self, target: Cell) -> None:
        """Turn toward an adjacent cell."""
        row, col = self.cell
        if target[0] > row:
            self.direction = "south"
        elif target[0] < row:
            self.direction = "north"
        elif target[1] > col:
            self.direction = "east"
        elif target[1] < col:
            self.direction = "west"

    def _flee(self, maze: Maze, player_cell: Cell) -> None:
        """Choose the adjacent cell farthest from the player."""
        best: Cell | None = None
        best_distance = -1
        for candidate in neighbors(maze, self.cell):
            distance = ((candidate[0] - player_cell[0]) ** 2
                        + (candidate[1] - player_cell[1]) ** 2)
            if distance > best_distance:
                best = candidate
                best_distance = distance
        if best is None:
            self.direction = None
        else:
            self._face(best)

    def _chase(self, maze: Maze, player_cell: Cell) -> None:
        """Follow the shortest path toward the player."""
        path = find_path(maze, self.cell, player_cell)
        if len(path) > 1:
            self._face(path[1])
        else:
            self.direction = None

    def update(self, maze: Maze, player_cell: Cell) -> None:
        """Move the ghost for one frame.

        Args:
            maze: the maze grid.
            player_cell: cell the player is in.
        """
        if self.eaten:
            return
        if at_center(self.row, self.col):
            self.row = float(round(self.row))
            self.col = float(round(self.col))
            if self.vulnerable:
                self._flee(maze, player_cell)
            else:
                self._chase(maze, player_cell)
        if self.direction is None:
            return
        speed = self.speed
        if self.vulnerable:
            speed *= SCARED_SPEED_FACTOR
        self.row, self.col = advance(self.row, self.col, self.direction,
                                     speed)

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the ghost on the maze surface (nothing if it is eaten)."""
        if self.eaten:
            return
        image = self._scared if self.vulnerable else self._normal
        surface.blit(image, (self.col * self.cell_size + self._offset,
                             self.row * self.cell_size + self._offset))
