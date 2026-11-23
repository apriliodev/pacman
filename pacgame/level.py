"""One level: the maze, the start cells and the pellets left."""

import random

from pacgame.maze import SOLID, Cell, Maze, nearest_free_cell


class Level:
    """A maze plus the pacgums and super-pacgums still on it."""

    def __init__(self, maze: Maze, pacgum_count: int) -> None:
        """Build a level.

        Args:
            maze: the maze grid.
            pacgum_count: how many pacgums we want (never more than the
                free cells).
        """
        self.maze = maze
        self.rows = len(maze)
        self.cols = len(maze[0])
        self.player_start = nearest_free_cell(
            maze, (self.rows // 2, self.cols // 2))
        corners = [(0, 0), (0, self.cols - 1), (self.rows - 1, 0),
                   (self.rows - 1, self.cols - 1)]
        self.ghost_starts: list[Cell] = [
            nearest_free_cell(maze, corner) for corner in corners]
        self.super_pacgums: set[Cell] = set(self.ghost_starts)
        self.pacgums: set[Cell] = self._place_pacgums(pacgum_count)

    def _place_pacgums(self, count: int) -> set[Cell]:
        """Pick random free cells for the pacgums."""
        forbidden = set(self.ghost_starts) | {self.player_start}
        candidates = [
            (row, col)
            for row in range(self.rows)
            for col in range(self.cols)
            if self.maze[row][col] != SOLID and (row, col) not in forbidden
        ]
        count = max(0, min(count, len(candidates)))
        return set(random.sample(candidates, count))

    def eat(self, cell: Cell) -> str | None:
        """Eat what is on this cell, if anything.

        Args:
            cell: (row, column) where the player is.

        Returns:
            "pacgum", "super" or None if the cell was empty.
        """
        if cell in self.pacgums:
            self.pacgums.remove(cell)
            return "pacgum"
        if cell in self.super_pacgums:
            self.super_pacgums.remove(cell)
            return "super"
        return None

    @property
    def is_cleared(self) -> bool:
        """True when every pacgum has been eaten."""
        return not self.pacgums
