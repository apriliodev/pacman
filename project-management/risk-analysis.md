# Risk analysis

| # | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| 1 | Graphics library judged not "MLX-equivalent" (the subject only allows functions that have an MLX equivalent). pygame functions such as `transform.scale/rotate`, `font.render` or `subsurface` have none. | High | Medium | Confirm with the staff which library features are accepted; if needed, replace them with pixel/image operations (`set_at`, `blit`) and pre-scaled assets. |
| 2 | The assigned A-Maze-ing package must be used **as-is**; the `mazegenerator/` copy must be the unmodified assigned one, otherwise the review fails. | High | Medium | Compare `mazegenerator/` with the assigned package before the defense; all adaptation lives in `pacgame/maze.py`, never in the package. |
| 3 | Crash during the review (unhandled exception). | High | Low | Config, highscores, maze generation and asset loading are wrapped; faulty inputs covered by tests; `run_game` turns failures into a message. |
| 4 | Config changed during the defense ("the game configuration will be updated"). | Medium | High | Every value is validated and clamped; unknown keys ignored; levels, sizes and points are all configurable. |
| 5 | Entities drifting off the grid (float movement) and walking through walls. | High | Low (fixed) | `step()` snaps to cell centers whatever the speed; tested with several speeds. |
| 6 | Hard-to-review game (10 levels, 90 s each). | Medium | High | Cheat mode (skip level, invincibility, freeze, extra life, speed). |
| 7 | The distributed version (Python source) does not run on a clean machine (missing Python or dependency). | Medium | Medium | Dependencies pinned in `pyproject.toml` / `uv.lock`; the run command is `uv sync && uv run python pac-man.py config.json`; test it on a clean Linux machine before the upload. |
| 8 | Highscore file corrupted or unwritable. | Medium | Low | Tolerant reader, atomic writes, errors reported not raised. |
| 9 | Not being able to explain AI-assisted code during the review. | High | Medium | README describes the AI usage; both members read and explain each module before the defense. |
