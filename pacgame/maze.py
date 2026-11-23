"""Maze helpers: wrapper around the generator, walls, path finding.

A maze is a list of rows of ints. Each int gives the walls of one cell:
north=1, east=2, south=4, west=8. 15 means the cell is fully closed (it is
part of the "42" drawing).
"""

from collections import deque

import mazegenerator

Maze = list[list[int]]
Cell = tuple[int, int]

SOLID = 15
WALL_BITS: dict[str, int] = {"north": 1, "east": 2, "south": 4, "west": 8}
DELTAS: dict[str, Cell] = {
    "north": (-1, 0),
    "east": (0, 1),
    "south": (1, 0),
    "west": (0, -1),
}
OPPOSITE: dict[str, str] = {
    "north": "south",
    "south": "north",
    "east": "west",
    "west": "east",
}


class MazeError(Exception):
    """Raised when a maze cannot be generated or used."""


def generate_maze(width: int, height: int, seed: int) -> Maze:
    """Ask the A-Maze-ing package for a maze (PERFECT is always False).

    Args:
        width: number of columns.
        height: number of rows.
        seed: above 0 always gives the same maze, 0 gives a random one.

    Returns:
        the grid, `height` rows of `width` cells.

    Raises:
        MazeError: if the generator fails or the maze is unusable.
    """
    try:
        generator = mazegenerator.MazeGenerator(
            size=(width, height), perfect=False, seed=seed)
        maze = [list(row) for row in generator.maze]
    except Exception as exc:
        raise MazeError(f"maze generation failed: {exc}") from exc
    if not maze or not maze[0] or any(len(r) != len(maze[0]) for r in maze):
        raise MazeError("the maze generator returned an invalid maze")
    return maze


def walls(maze: Maze, cell: Cell) -> dict[str, bool]:
    """Tell which sides of a cell have a wall.

    Args:
        maze: the maze grid.
        cell: (row, column).

    Returns:
        for each direction, True if there is a wall.
    """
    value = maze[cell[0]][cell[1]]
    return {name: bool(value & bit) for name, bit in WALL_BITS.items()}


def neighbors(maze: Maze, cell: Cell) -> list[Cell]:
    """Cells we can walk to from this cell in one move.

    Args:
        maze: the maze grid.
        cell: (row, column).

    Returns:
        the adjacent cells with no wall in between.
    """
    row, col = cell
    if not (0 <= row < len(maze) and 0 <= col < len(maze[0])):
        return []
    result: list[Cell] = []
    for direction, closed in walls(maze, cell).items():
        d_row, d_col = DELTAS[direction]
        target = (row + d_row, col + d_col)
        if (not closed and 0 <= target[0] < len(maze)
                and 0 <= target[1] < len(maze[0])):
            result.append(target)
    return result


def find_path(maze: Maze, start: Cell, goal: Cell) -> list[Cell]:
    """Shortest path between two cells (BFS).

    Args:
        maze: the maze grid.
        start: (row, column) where we start.
        goal: (row, column) we want to reach.

    Returns:
        the cells from start to goal included, empty list if there is no way.
    """
    parents: dict[Cell, Cell | None] = {start: None}
    queue: deque[Cell] = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for target in neighbors(maze, current):
            if target not in parents:
                parents[target] = current
                queue.append(target)
    if goal not in parents:
        return []
    path: list[Cell] = []
    step: Cell | None = goal
    while step is not None:
        path.append(step)
        step = parents[step]
    path.reverse()
    return path


def nearest_free_cell(maze: Maze, cell: Cell) -> Cell:
    """Closest cell that is not part of the "42" drawing.

    Args:
        maze: the maze grid.
        cell: (row, column) we would like.

    Returns:
        the cell itself if it is free, else the nearest free one.

    Raises:
        MazeError: if there is no free cell at all.
    """
    best: Cell | None = None
    best_distance = 0
    for row, line in enumerate(maze):
        for col, value in enumerate(line):
            if value == SOLID:
                continue
            distance = (row - cell[0]) ** 2 + (col - cell[1]) ** 2
            if best is None or distance < best_distance:
                best = (row, col)
                best_distance = distance
    if best is None:
        raise MazeError("the maze has no free cell")
    return best
