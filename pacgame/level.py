"""One level: its maze, start positions and remaining pellets."""

import random

from pacgame.maze import SOLID, Cell, Maze, nearest_free_cell


class Level:
    """A maze with the pacgums and super-pacgums that remain in it."""

    def __init__(self, maze: Maze, pacgum_count: int) -> None:
        """Create a level.

        Args:
            maze: The maze grid.
            pacgum_count: Wanted number of pacgums (limited by the free
                cells available).
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
        """Remove the pellet at ``cell``, if any.

        Args:
            cell: The ``(row, column)`` where the player stands.

        Returns:
            ``"pacgum"``, ``"super"`` or None if there was nothing to eat.
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
