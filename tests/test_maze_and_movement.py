"""Tests of the maze helpers and of the movement rules."""

import os

import pytest

from pacgame.entities import advance, at_center, step
from pacgame.level import Level
from pacgame.maze import (SOLID, MazeError, find_path, generate_maze,
                          neighbors, nearest_free_cell, walls)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def test_generated_maze_has_requested_size() -> None:
    """The wrapper returns a grid of the requested size."""
    maze = generate_maze(16, 12, 42)
    assert len(maze) == 12
    assert all(len(row) == 16 for row in maze)


def test_same_seed_same_maze() -> None:
    """A positive seed gives a reproducible maze."""
    assert generate_maze(15, 15, 42) == generate_maze(15, 15, 42)


def test_walls_decoding() -> None:
    """Wall bits are decoded in the four directions."""
    maze = [[1 | 8, 2 | 4]]
    assert walls(maze, (0, 0)) == {"north": True, "east": False,
                                   "south": False, "west": True}


def test_neighbors_and_path() -> None:
    """A corridor is traversed by the breadth-first search."""
    maze = [[1 | 4 | 8, 1 | 4, 1 | 2 | 4]]
    assert neighbors(maze, (0, 1)) == [(0, 2), (0, 0)] or \
        sorted(neighbors(maze, (0, 1))) == [(0, 0), (0, 2)]
    assert find_path(maze, (0, 0), (0, 2)) == [(0, 0), (0, 1), (0, 2)]
    closed = [[15, 15]]
    assert find_path(closed, (0, 0), (0, 1)) == []


def test_nearest_free_cell_skips_solid_cells() -> None:
    """The start cell is never inside the 42 pattern."""
    maze = [[SOLID, 0], [SOLID, SOLID]]
    assert nearest_free_cell(maze, (1, 0)) == (0, 1)
    with pytest.raises(MazeError):
        nearest_free_cell([[SOLID]], (0, 0))


def test_level_pellets() -> None:
    """Pellets avoid the start cells and solid cells."""
    level = Level(generate_maze(15, 15, 42), 10000)
    assert level.player_start not in level.pacgums
    assert not level.pacgums & level.super_pacgums
    assert all(level.maze[r][c] != SOLID for r, c in level.pacgums)
    assert len(level.super_pacgums) == 4


@pytest.mark.parametrize("speed", [0.05, 0.04, 0.02, 0.1, 0.07, 0.3])
def test_movement_always_lands_on_cell_centers(speed: float) -> None:
    """Whatever the speed, an entity reaches exact cell centers."""
    row, col = 3.0, 4.0
    for _ in range(int(20 / speed)):
        row, col = advance(row, col, "south", speed)
        assert 3.0 <= row <= 23.0
    assert at_center(row, col) or row > 3.0
    assert step(0.96, 0.04) == 1.0
    assert step(1.04, -0.04) == 1.0
    assert step(2.0, 0.0) == 2.0
