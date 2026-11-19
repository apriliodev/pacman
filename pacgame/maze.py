"""Maze helpers: generator wrapper, wall decoding and path finding.

A maze is a list of rows of integers. Each integer encodes the walls of a
cell: north=1, east=2, south=4, west=8. The value 15 is a fully closed cell
(a piece of the "42" pattern).
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
    """Generate a Pac-Man compatible maze with the A-Maze-ing package.

    Args:
        width: Number of columns.
        height: Number of rows.
        seed: A positive seed gives a reproducible maze, 0 a random one.

    Returns:
        The maze grid (``height`` rows of ``width`` cells).

    Raises:
        MazeError: If the generator fails or returns an unusable maze.
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
    """Decode the walls of a cell.

    Args:
        maze: The maze grid.
        cell: A ``(row, column)`` position.

    Returns:
        For each direction, True if there is a wall on that side.
    """
    value = maze[cell[0]][cell[1]]
    return {name: bool(value & bit) for name, bit in WALL_BITS.items()}


def neighbors(maze: Maze, cell: Cell) -> list[Cell]:
    """Return the cells reachable from ``cell`` in one move.

    Args:
        maze: The maze grid.
        cell: A ``(row, column)`` position.

    Returns:
        The adjacent cells that are not separated from ``cell`` by a wall.
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
    """Find the shortest path between two cells (breadth-first search).

    Args:
        maze: The maze grid.
        start: The starting ``(row, column)``.
        goal: The target ``(row, column)``.

    Returns:
        The cells from ``start`` to ``goal`` included, or an empty list if
        the goal cannot be reached.
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
    """Return the free (not solid) cell closest to ``cell``.

    Args:
        maze: The maze grid.
        cell: The wanted ``(row, column)``.

    Returns:
        ``cell`` itself if it is free, otherwise the nearest free cell.

    Raises:
        MazeError: If the maze has no free cell at all.
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
