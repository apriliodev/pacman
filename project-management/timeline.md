# Timeline and progress

Dates come from the git history of the repository.

| Date | Milestone |
|---|---|
| 2026-10-16 | First commit: first playable version (maze, player, ghosts) |
| 2026-11-03 | Lives, score, HUD, level timer, level progression, game over / victory states, menu |
| 2026-11-19 | Finishing phase: menus, instructions, highscores, pause menu, cheat mode, configuration, modular architecture, tooling, tests, packaging |

## Plan versus reality

| Phase | Content | Status |
|---|---|---|
| 1. Core gameplay | Maze display, player movement, pacgums, ghosts (BFS chase / flee), collisions | Done |
| 2. Rules | Lives, score, HUD, level timer, 10 levels, super-pacgums | Done |
| 3. Screens | Menu, instructions, highscores, pause menu, game over, victory, name entry | Done |
| 4. Persistence | Top 10 highscores in JSON, robust to file errors | Done |
| 5. Configuration | JSON with comments, defaults, clamping, no traceback | Done |
| 6. Cheat mode | Invincibility, level skip, ghost freeze, extra life, speed | Done |
| 7. Quality | flake8, mypy (`--strict` passes), type hints, docstrings, unit tests | Done |
| 8. Delivery files | Makefile, `.gitignore`, README, this directory | Done |
| 9. Packaging | PyInstaller spec builds and starts; **upload to itch.io/Steam** | Build done, **upload TO DO** |
| 10. Bonus | Different ghost behaviors (chaser, follower, random, runaway) | Not started |

**TO COMPLETE:** planned dates per phase and the actual dates of the
packaging/upload step.
