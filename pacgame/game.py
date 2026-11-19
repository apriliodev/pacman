"""Game rules (``Session``) and the state machine (``Game``).

States: menu, instructions, highscores, playing, paused, game_over, victory,
name_entry.
"""

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import pygame

from pacgame.config import GameConfig
from pacgame.entities import Ghost, Player
from pacgame.highscores import (DEFAULT_NAME, MAX_NAME_LENGTH, ScoreEntry,
                                is_allowed_char, load_scores, save_score)
from pacgame.level import Level
from pacgame.maze import Maze, MazeError, generate_maze
from pacgame.renderer import Renderer

FPS = 30
MAX_FRAME_MS = 100

MENU_OPTIONS = ("Start Game", "View Highscores", "Instructions", "Exit")
PAUSE_OPTIONS = ("Resume", "Return to main menu")

EventList = list[pygame.event.Event]


class Outcome(Enum):
    """Result of one game update."""

    CONTINUE = 0
    GAME_OVER = 1
    VICTORY = 2


@dataclass
class CheatState:
    """The cheat mode switches (used to ease peer review)."""

    enabled: bool = False
    invincible: bool = False
    freeze: bool = False
    fast: bool = False


class Session:
    """One game in progress: player, ghosts, level, timers and cheats.

    Time is a counter of *played* milliseconds: it does not advance during
    the pause, so every timer (level time, edible ghosts, respawn) is
    naturally frozen while the game is paused.
    """

    def __init__(self, config: GameConfig, renderer: Renderer,
                 maze: Maze) -> None:
        """Start a new game on its first level.

        Args:
            config: The game configuration.
            renderer: Used to size the window for each maze.
            maze: The maze of the first level.
        """
        self.config = config
        self.renderer = renderer
        self.cheats = CheatState()
        self.now_ms = 0
        self.level_started_ms = 0
        self._skip_level = False
        self.level = Level(maze, config.pacgum)
        cell = renderer.prepare_level(maze)
        self.player = Player(self.level.player_start, cell,
                             config.player_speed, config.lives)
        self.ghosts = [
            Ghost(start, f"ghost_{number}.png", cell, config.ghost_speed)
            for number, start in enumerate(self.level.ghost_starts, 1)]

    # -- information ------------------------------------------------------

    @property
    def time_left(self) -> int:
        """Whole seconds left on the level clock."""
        played = (self.now_ms - self.level_started_ms) // 1000
        return max(0, self.config.level_max_time - played)

    @property
    def cheat_text(self) -> str:
        """Text shown in the HUD while the cheat mode is on."""
        if not self.cheats.enabled:
            return ""
        flags = [letter for letter, active in (
            ("I", self.cheats.invincible), ("F", self.cheats.freeze),
            ("V", self.cheats.fast)) if active]
        return " ".join(["CHEAT"] + flags)

    # -- input ------------------------------------------------------------

    def handle_key(self, key: int) -> None:
        """Handle a key press: cheat keys, then movement keys."""
        if key == pygame.K_c:
            self._toggle_cheat_mode()
            return
        if self.cheats.enabled:
            if key == pygame.K_n:
                self._skip_level = True
            elif key == pygame.K_i:
                self.cheats.invincible = not self.cheats.invincible
            elif key == pygame.K_f:
                self.cheats.freeze = not self.cheats.freeze
            elif key == pygame.K_v:
                self.cheats.fast = not self.cheats.fast
                self._apply_player_speed()
            elif key == pygame.K_l:
                self.player.lives += 1
        self.player.handle_key(key)

    def _toggle_cheat_mode(self) -> None:
        """Turn the cheat mode on or off (off also clears every effect)."""
        self.cheats = CheatState(enabled=not self.cheats.enabled)
        self._apply_player_speed()

    def _apply_player_speed(self) -> None:
        """Set the player speed according to the cheat state."""
        if self.cheats.fast:
            self.player.speed = self.config.player_cheat_speed
        else:
            self.player.speed = self.config.player_speed

    # -- simulation -------------------------------------------------------

    def tick(self, elapsed_ms: int) -> None:
        """Advance the played-time counter."""
        self.now_ms += elapsed_ms

    def update(self) -> Outcome:
        """Simulate one frame.

        Returns:
            Whether the game goes on, is lost or is won.
        """
        if self.time_left == 0:
            self.level_started_ms = self.now_ms
            if not self.cheats.invincible and self._lose_life():
                return Outcome.GAME_OVER
        self.player.update(self.level.maze)
        for ghost in self.ghosts:
            ghost.refresh(self.now_ms)
            if not self.cheats.freeze:
                ghost.update(self.level.maze, self.player.cell)
        self._eat_pellets()
        if self._collide_with_ghosts():
            return Outcome.GAME_OVER
        if self.level.is_cleared or self._skip_level:
            self._skip_level = False
            return self._next_level()
        return Outcome.CONTINUE

    def _eat_pellets(self) -> None:
        """Eat the pellet under the player and apply its effect."""
        eaten = self.level.eat(self.player.cell)
        if eaten == "pacgum":
            self.player.score += self.config.points_per_pacgum
        elif eaten == "super":
            self.player.score += self.config.points_per_super_pacgum
            until = self.now_ms + self.config.vulnerable_duration_ms
            for ghost in self.ghosts:
                ghost.make_vulnerable(until)

    def _collide_with_ghosts(self) -> bool:
        """Resolve ghost contacts; return True if the game is over."""
        for ghost in self.ghosts:
            if not ghost.touches(self.player):
                continue
            if ghost.vulnerable:
                self.player.score += self.config.points_per_ghost
                ghost.eat(self.now_ms + self.config.ghost_respawn_ms)
            elif not self.cheats.invincible:
                return self._lose_life()
        return False

    def _lose_life(self) -> bool:
        """Remove a life and respawn everybody; True if none is left."""
        self.player.lives -= 1
        self.player.reset_position()
        for ghost in self.ghosts:
            ghost.reset_position()
        return self.player.lives <= 0

    def _next_level(self) -> Outcome:
        """Go to the next level, or win if it was the last one."""
        self.player.level += 1
        if self.player.level > len(self.config.levels):
            return Outcome.VICTORY
        size = self.config.levels[self.player.level - 1]
        try:
            maze = generate_maze(size.width, size.height, 0)
        except MazeError as exc:
            print(f"[maze] {exc}; keeping the previous maze",
                  file=sys.stderr)
            maze = self.level.maze
        self._load_level(maze)
        return Outcome.CONTINUE

    def _load_level(self, maze: Maze) -> None:
        """Install a new maze and put everybody back in place."""
        cell = self.renderer.prepare_level(maze)
        self.level = Level(maze, self.config.pacgum)
        self.player.rescale(cell)
        self.player.start = self.level.player_start
        self.player.reset_position()
        for ghost, start in zip(self.ghosts, self.level.ghost_starts):
            ghost.rescale(cell)
            ghost.start = start
            ghost.reset_position()
        self.level_started_ms = self.now_ms

    # -- drawing ----------------------------------------------------------

    def draw(self) -> None:
        """Draw the maze, the pellets, the entities and the HUD."""
        self.renderer.draw_maze()
        self.renderer.draw_pellets(self.level)
        for ghost in self.ghosts:
            ghost.draw(self.renderer.play_area)
        self.player.draw(self.renderer.play_area)
        self.renderer.draw_hud(self.player.lives, self.player.score,
                               self.player.level, self.time_left,
                               self.cheat_text)


class Game:
    """The application: window, main loop and screens."""

    def __init__(self, config: GameConfig) -> None:
        """Initialise pygame, the window and load the highscores.

        Args:
            config: The game configuration.
        """
        pygame.init()
        self.config = config
        self.renderer = Renderer(config)
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.running = True
        self.menu_index = 0
        self.pause_index = 0
        self.session: Session | None = None
        self.scores: list[ScoreEntry] = load_scores(config.highscore_path)
        self.name_input = ""
        self.error = ""
        self._handlers: dict[str, Callable[[EventList, int], None]] = {
            "menu": self._menu,
            "instructions": self._instructions,
            "highscores": self._highscores,
            "playing": self._playing,
            "paused": self._paused,
            "game_over": self._game_over,
            "victory": self._victory,
            "name_entry": self._name_entry,
        }

    def run(self) -> None:
        """Run the main loop until the player quits."""
        while self.running:
            elapsed = min(self.clock.tick(FPS), MAX_FRAME_MS)
            events = pygame.event.get()
            if any(event.type == pygame.QUIT for event in events):
                break
            self._handlers[self.state](events, elapsed)
            pygame.display.flip()
        pygame.quit()

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _pressed(events: EventList) -> list[int]:
        """Return the keys pressed during this frame."""
        return [event.key for event in events
                if event.type == pygame.KEYDOWN]

    @staticmethod
    def _is_enter(key: int) -> bool:
        """Tell whether a key is one of the Enter keys."""
        return key in (pygame.K_RETURN, pygame.K_KP_ENTER)

    # -- screens ----------------------------------------------------------

    def _menu(self, events: EventList, elapsed: int) -> None:
        """Main menu: Start, Highscores, Instructions, Exit."""
        for key in self._pressed(events):
            if key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % len(MENU_OPTIONS)
            elif key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % len(MENU_OPTIONS)
            elif self._is_enter(key):
                self._choose_menu_option()
                break
        self.renderer.draw_menu(MENU_OPTIONS, self.menu_index, self.scores,
                                self.error)

    def _choose_menu_option(self) -> None:
        """Run the selected main menu entry."""
        if self.menu_index == 0:
            self._start_new_game()
        elif self.menu_index == 1:
            self.scores = load_scores(self.config.highscore_path)
            self.state = "highscores"
        elif self.menu_index == 2:
            self.state = "instructions"
        else:
            self.running = False

    def _start_new_game(self) -> None:
        """Generate the first level and start playing."""
        first = self.config.levels[0]
        try:
            maze = generate_maze(first.width, first.height, self.config.seed)
            self.session = Session(self.config, self.renderer, maze)
        except MazeError as exc:
            self.error = str(exc)
            print(f"[maze] {exc}", file=sys.stderr)
            return
        self.error = ""
        self.state = "playing"

    def _instructions(self, events: EventList, elapsed: int) -> None:
        """Instructions screen (controls and rules)."""
        if pygame.K_ESCAPE in self._pressed(events):
            self.state = "menu"
        cfg = self.config
        self.renderer.draw_lines("Instructions", [
            "Arrows / WASD / ZQSD : move",
            "Esc : pause",
            "Eat all the pacgums to clear a level",
            f"Pacgum : {cfg.points_per_pacgum} pts   "
            f"Super pacgum : {cfg.points_per_super_pacgum} pts",
            f"Edible ghost : {cfg.points_per_ghost} pts",
            "A ghost touches you : you lose a life",
            f"{cfg.lives} lives, {cfg.level_max_time}s per level, "
            f"{len(cfg.levels)} levels",
            "C : cheat mode, then I F V L N",
            "I invincible  F freeze ghosts  V speed",
            "L extra life  N skip level",
            "Esc : back",
        ])

    def _highscores(self, events: EventList, elapsed: int) -> None:
        """Top 10 screen."""
        if pygame.K_ESCAPE in self._pressed(events):
            self.state = "menu"
        self.renderer.draw_highscores(self.scores)

    def _playing(self, events: EventList, elapsed: int) -> None:
        """Gameplay: input, simulation and drawing."""
        session = self.session
        if session is None:
            self.state = "menu"
            return
        for key in self._pressed(events):
            if key == pygame.K_ESCAPE:
                self.pause_index = 0
                self.state = "paused"
            else:
                session.handle_key(key)
        if self.state == "playing":
            session.tick(elapsed)
            outcome = session.update()
            if outcome is Outcome.GAME_OVER:
                self.state = "game_over"
            elif outcome is Outcome.VICTORY:
                self.state = "victory"
        if self.state == "playing":
            session.draw()

    def _paused(self, events: EventList, elapsed: int) -> None:
        """Pause menu: Resume or return to the main menu."""
        for key in self._pressed(events):
            if key == pygame.K_ESCAPE:
                self.state = "playing"
            elif key in (pygame.K_UP, pygame.K_DOWN):
                self.pause_index = 1 - self.pause_index
            elif self._is_enter(key):
                self.state = "playing" if self.pause_index == 0 else "menu"
                if self.state == "menu":
                    self.session = None
                break
        self.renderer.draw_pause(PAUSE_OPTIONS, self.pause_index)

    def _end_screen(self, events: EventList, title: str,
                    subtitle: str) -> None:
        """Common code of the game over and victory screens."""
        session = self.session
        score = session.player.score if session else 0
        for key in self._pressed(events):
            if self._is_enter(key):
                self.name_input = ""
                self.state = "name_entry"
            elif key == pygame.K_ESCAPE:
                self.session = None
                self.state = "menu"
        self.renderer.draw_end(title, subtitle, score)

    def _game_over(self, events: EventList, elapsed: int) -> None:
        """Game over screen."""
        self._end_screen(events, "GAME OVER", "")

    def _victory(self, events: EventList, elapsed: int) -> None:
        """Victory screen."""
        self._end_screen(events, "VICTORY !",
                         "Congratulations, you cleared every level!")

    def _name_entry(self, events: EventList, elapsed: int) -> None:
        """Name entry, then the score is saved in the highscores."""
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self._is_enter(event.key):
                self._save_score()
            elif event.key == pygame.K_ESCAPE:
                self.session = None
                self.state = "menu"
            elif event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            elif (len(self.name_input) < MAX_NAME_LENGTH
                    and is_allowed_char(event.unicode)):
                self.name_input += event.unicode
        self.renderer.draw_name_entry(self.name_input, MAX_NAME_LENGTH)

    def _save_score(self) -> None:
        """Save the final score and go back to the main menu."""
        score = self.session.player.score if self.session else 0
        name = self.name_input.strip() or DEFAULT_NAME
        self.scores = save_score(self.config.highscore_path, name, score)
        self.session = None
        self.state = "menu"


def run_game(config: GameConfig) -> int:
    """Run the game and turn unexpected failures into clean messages.

    Args:
        config: The game configuration.

    Returns:
        The process exit code (0 on success).
    """
    try:
        Game(config).run()
    except (pygame.error, OSError, MazeError) as exc:
        pygame.quit()
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pygame.quit()
        return 130
    return 0
