"""Drawing of the maze, the HUD and the menu screens."""

from typing import Sequence

import pygame

from pacgame.assets import load_image
from pacgame.config import GameConfig
from pacgame.highscores import ScoreEntry
from pacgame.level import Level
from pacgame.maze import SOLID, WALL_BITS, Maze

HUD_HEIGHT = 50
MIN_WIDTH = 600
MIN_HEIGHT = 560
MIN_CELL = 8
WALL_THICKNESS = 1

WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREY = (150, 150, 150)
LIGHT_GREY = (200, 200, 200)
BLACK = (0, 0, 0)


class Renderer:
    """Owns the window and knows how to draw every screen."""

    def __init__(self, config: GameConfig) -> None:
        """Open the window.

        Args:
            config: The game configuration (colors, window size).
        """
        self.config = config
        self.screen = pygame.display.set_mode((MIN_WIDTH, MIN_HEIGHT))
        pygame.display.set_caption("Pac-Man")
        self.font = pygame.font.Font(None, 25)
        self.title_font = pygame.font.Font(None, 80)
        self.cell_size = MIN_CELL
        self.play_area = self.screen
        self._maze_surface = pygame.Surface((1, 1))
        self._raw_pellet = load_image("pacgum.png")
        self._pacgum = self._raw_pellet
        self._super = self._raw_pellet
        self._pacgum_offset = 0.0
        self._super_offset = 0.0

    # -- level preparation ------------------------------------------------

    def prepare_level(self, maze: Maze) -> int:
        """Size the window for a maze and pre-render its walls.

        Args:
            maze: The maze grid of the level.

        Returns:
            The cell size in pixels.
        """
        rows, cols = len(maze), len(maze[0])
        available_w = self.config.window_width
        available_h = self.config.window_height - HUD_HEIGHT
        cell = max(MIN_CELL, min(available_w // cols, available_h // rows))
        maze_w, maze_h = cols * cell, rows * cell
        width = max(MIN_WIDTH, maze_w)
        height = max(MIN_HEIGHT, HUD_HEIGHT + maze_h)
        self.screen = pygame.display.set_mode((width, height))
        self.play_area = self.screen.subsurface(
            ((width - maze_w) // 2, HUD_HEIGHT, maze_w, maze_h))
        self.cell_size = cell
        self._maze_surface = self._render_maze(maze)
        pacgum_size = max(2, cell // 6)
        super_size = max(4, cell // 2)
        self._pacgum = pygame.transform.scale(
            self._raw_pellet, (pacgum_size, pacgum_size))
        self._super = pygame.transform.scale(
            self._raw_pellet, (super_size, super_size))
        self._pacgum_offset = (cell - pacgum_size) / 2
        self._super_offset = (cell - super_size) / 2
        return cell

    def _render_maze(self, maze: Maze) -> pygame.Surface:
        """Draw the walls of a maze once on a surface."""
        cell = self.cell_size
        thick = WALL_THICKNESS
        wall = self.config.wall_color
        surface = pygame.Surface((len(maze[0]) * cell, len(maze) * cell))
        surface.fill(self.config.background_color)
        for row, line in enumerate(maze):
            for col, value in enumerate(line):
                x, y = col * cell, row * cell
                if value == SOLID:
                    surface.fill(wall, (x, y, cell, cell))
                    continue
                if value & WALL_BITS["north"]:
                    surface.fill(wall, (x, y, cell, thick))
                if value & WALL_BITS["east"]:
                    surface.fill(wall, (x + cell - thick, y, thick, cell))
                if value & WALL_BITS["south"]:
                    surface.fill(wall, (x, y + cell - thick, cell, thick))
                if value & WALL_BITS["west"]:
                    surface.fill(wall, (x, y, thick, cell))
        return surface

    # -- gameplay drawing -------------------------------------------------

    def draw_maze(self) -> None:
        """Draw the pre-rendered maze."""
        self.play_area.blit(self._maze_surface, (0, 0))

    def draw_pellets(self, level: Level) -> None:
        """Draw the pacgums and the super-pacgums of a level."""
        cell = self.cell_size
        for row, col in level.pacgums:
            self.play_area.blit(
                self._pacgum, (col * cell + self._pacgum_offset,
                               row * cell + self._pacgum_offset))
        for row, col in level.super_pacgums:
            self.play_area.blit(
                self._super, (col * cell + self._super_offset,
                              row * cell + self._super_offset))

    def draw_hud(self, lives: int, score: int, level: int, time_left: int,
                 cheat_text: str) -> None:
        """Draw the status bar: score, lives, level and remaining time."""
        width = self.screen.get_width()
        self.screen.fill(self.config.background_color,
                         (0, 0, width, HUD_HEIGHT))
        items = ((f"Lives : {lives}", 10), (f"Score : {score}", 112),
                 (f"Level : {level}", 245), (f"Time : {time_left}", 360))
        for text, x in items:
            self.screen.blit(self.font.render(text, True, WHITE), (x, 10))
        if cheat_text:
            self.screen.blit(self.font.render(cheat_text, True, RED),
                             (470, 10))

    # -- full-screen menus ------------------------------------------------

    def clear(self) -> None:
        """Fill the whole window with black."""
        self.screen.fill(BLACK)

    def text(self, text: str, y: int, color: tuple[int, int, int] = WHITE,
             big: bool = False) -> None:
        """Draw a horizontally centered line of text."""
        font = self.title_font if big else self.font
        image = font.render(text, True, color)
        x = (self.screen.get_width() - image.get_width()) // 2
        self.screen.blit(image, (x, y))

    def draw_menu(self, options: Sequence[str], selected: int,
                  top_scores: Sequence[ScoreEntry], error: str) -> None:
        """Draw the main menu with a preview of the best scores."""
        self.clear()
        self.text("Pac-Man", 40, YELLOW, big=True)
        for index, option in enumerate(options):
            color = YELLOW if index == selected else WHITE
            self.text(option, 150 + index * 50, color)
        if error:
            self.text(error, 360, RED)
        if top_scores:
            self.text("Best scores", 410, GREY)
            for rank, entry in enumerate(top_scores[:3], start=1):
                self.text(f"{rank}. {entry['name']} - {entry['score']} pts",
                          435 + (rank - 1) * 25, LIGHT_GREY)

    def draw_highscores(self, scores: Sequence[ScoreEntry]) -> None:
        """Draw the top 10 screen."""
        self.clear()
        self.text("TOP 10", 30, YELLOW, big=True)
        if not scores:
            self.text("No score yet", 150, WHITE)
        for rank, entry in enumerate(scores, start=1):
            self.text(f"{rank}. {entry['name']} : {entry['score']} pts",
                      110 + (rank - 1) * 30, WHITE)
        self.text("Press Esc to go back", 450, GREY)

    def draw_lines(self, title: str, lines: Sequence[str]) -> None:
        """Draw a title followed by lines of text."""
        self.clear()
        self.text(title, 20, YELLOW, big=True)
        for index, line in enumerate(lines):
            self.text(line, 110 + index * 34, WHITE)

    def draw_pause(self, options: Sequence[str], selected: int) -> None:
        """Draw the pause menu."""
        self.clear()
        self.text("PAUSE", 80, WHITE, big=True)
        for index, option in enumerate(options):
            color = YELLOW if index == selected else WHITE
            self.text(option, 200 + index * 50, color)

    def draw_end(self, title: str, subtitle: str, score: int) -> None:
        """Draw the game over / victory screen."""
        self.clear()
        self.text(title, 100, WHITE, big=True)
        if subtitle:
            self.text(subtitle, 180, YELLOW)
        self.text(f"Score : {score}", 230, WHITE)
        self.text("Press ENTER to save your score", 320, LIGHT_GREY)
        self.text("Press Esc to go back to the menu", 350, GREY)

    def draw_name_entry(self, name: str, max_length: int) -> None:
        """Draw the player name entry screen."""
        self.clear()
        self.text("Enter your name", 150, WHITE, big=True)
        self.text(name + "_", 250, YELLOW)
        self.text(f"{max_length} characters max: letters, digits, spaces",
                  320, GREY)
        self.text("ENTER : save   Esc : skip", 360, GREY)
