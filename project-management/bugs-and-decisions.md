# Bugs found and fixed, decisions, blocking points

## Bugs found and fixed

| Bug | Cause | Fix |
|---|---|---|
| Crash when closing the window | `event.key` read on a `QUIT` event | Separate `QUIT` and `KEYDOWN` handling |
| Ghost crash when no path to the player | Path list empty, index out of range | Ghost stands still when there is no path |
| Ghosts moving twice / east-west inverted | Movement applied twice; wrong sign | Single move per frame, directions fixed |
| Window closed when the level time ran out | Timer not restarted | Lose a life, respawn, restart the clock |
| Edible state never ending | State kept in local variables | State stored on each ghost |
| Level 1 not using the fixed seed | Missing `else` in maze creation | `if level == 1` / `else` |
| Ghost flee bugs | Neighbors of the wrong entity, wrong index | Rewritten to pick the farthest neighbor of the ghost |
| Crash on resume after pause | `debut_pause` only set by the cheat key | Time spent in pause no longer needs a start mark: the game counts played time only |
| Ghosts staying slow forever | The slow flag was not cleared when a ghost was eaten or respawned | Slowness derived from the edible state, one flag |
| Instructions showing wrong points | Numbers typed by hand | Text built from the configuration |
| Highscore reader crashing on bad lines | `int()` on unchecked text | Tolerant JSON reader that skips invalid entries |
| Possible drift off the grid when a ghost's speed changed mid-cell | Float steps not multiples of the remaining distance | `entities.step()` snaps to the cell center; any speed is safe |
| Player start inside the "42" pattern for some maze sizes | Start was the exact center | Nearest free cell to the center |

## Technical decisions

| Decision | Reason |
|---|---|
| Split the single script into the `pacgame` package | Readability, testability, the subject asks for a modular architecture |
| Own configuration validator instead of `pydantic` | The subject wants defaults + clamping + no traceback; avoids an extra dependency |
| Game time counter instead of wall-clock time | Pausing freezes every timer for free |
| Highscores in a JSON file next to the config | Simple, readable, dependency-free; matches the subject's suggestion |
| Pre-rendered maze surface | Walls are drawn once per level instead of pixel by pixel every frame |
| English UI texts and identifiers | Matches the subject's menu names and the English README |

## Blocking points and conflicts

- A copy of the repository existed twice (project folder and a nested
  clone); the duplicate was removed after checking nothing was lost.
- Git was not on the `PATH` of the terminal; fixed by adding Git's `cmd`
  folder to the user `PATH`.

**TO COMPLETE:** any disagreement or blocking point the team remembers.
