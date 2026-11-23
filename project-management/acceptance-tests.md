# Acceptance test plan

"Auto" = covered by unit tests run during development (configuration, highscores,
maze helpers, movement, game rules and cheats; not part of the delivery) or by the scripted headless
play-through that drives the real `Game` with simulated key presses
(menu, instructions, highscores, play, pause, cheats, 10 levels, victory,
name entry, highscore saved). Last automatic run: 2026-11-19, all passing.
"Manual" tests must be played by a member before the defense; their result
column is left empty on purpose.

| # | Feature | How to test | Expected | Type | Result |
|---|---|---|---|---|---|
| 1 | Usage | `python3 pac-man.py` / with 2 args | Usage message, exit code 2, no traceback | Manual | |
| 2 | Missing config file | `python3 pac-man.py nope.json` | `[config]` message, game starts with defaults | Manual | |
| 3 | Invalid JSON / values | Break `config.json` (bad syntax, `"lives": "x"`) | Messages, defaults / clamping, no traceback | Auto (config tests) + manual | |
| 4 | Comments | Add `# ...` lines to the config | Ignored | Auto | Pass |
| 5 | Maze generation | Start a game | Maze of the configured size; level 1 identical at each start (seed 42) | Auto + manual | |
| 6 | Start positions | Look at level 1 | Player in the middle, 4 ghosts in corners, super-pacgums in corners | Manual | |
| 7 | Player movement | Arrows / WASD / ZQSD | Moves in corridors only, stops at walls | Manual | |
| 8 | Scoring | Eat a pacgum / super-pacgum / edible ghost | +10 / +50 / +200 (config) | Manual | |
| 9 | Edible ghosts | Eat a super-pacgum | Ghosts turn blue, flee, slower; normal after 6 s | Manual | |
| 10 | Lives | Touch a ghost | -1 life, everybody respawns; game over at 0 | Manual | |
| 11 | Level time | Wait 90 s | -1 life and clock restarts | Manual | |
| 12 | Level progression | Eat all pacgums | Next level, new maze, score and lives kept | Manual / Auto with cheat | |
| 13 | Victory | Clear level 10 | Victory screen with congratulations and score | Auto | Pass |
| 14 | Pause | `Esc` in game | Pause menu; clock, ghosts timers frozen; Resume / Return to menu work | Auto (clock) + manual | |
| 15 | Name entry | End a game, `Enter` | Max 10 chars, letters/digits/spaces only | Auto | Pass |
| 16 | Highscores | Finish games | Top 10 sorted, shown in menu (top 3) and highscore screen; persists after restart | Auto + manual | |
| 17 | Corrupted highscore file | Write garbage in `highscores.json` | Empty table, no crash | Auto | Pass |
| 18 | Cheat mode | `C`, then `I F V L N` | Each effect works; HUD shows `CHEAT` and active letters; `C` again clears everything | Auto + manual | |
| 19 | Lint | `make lint`, `make lint-strict` | No error | Auto | Pass |
| 20 | Distribution | Unzip the repository files on a clean Linux machine, `uv sync`, `uv run python pac-man.py config.json` | Game starts | Manual | |
