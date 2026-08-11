# RoboBuilder Runtime

RoboBuilder stores durable local workflow state under:

```bash
${ROBOBUILDER_HOME:-$HOME/.robobuilder}
```

Project-scoped state lives under:

```bash
${ROBOBUILDER_HOME:-$HOME/.robobuilder}/projects/<project-slug>
```

Eval result files, when a workflow produces them, live under:

```bash
${ROBOBUILDER_HOME:-$HOME/.robobuilder}/evals
```

Use the helper scripts instead of repeating path and slug logic in skills. **Always
address them through `$RB`, never as a bare relative path:**

```bash
RB="${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}/bin"
[ -x "$RB/robobuilder-paths" ] || { echo "robobuilder helpers not found at $RB — state will not persist"; return 1 2>/dev/null || exit 1; }
eval "$("$RB/robobuilder-slug" 2>/dev/null)"
eval "$("$RB/robobuilder-paths")"
```

`bin/` ships *inside the plugin* and is never copied into the user's project or added
to `PATH`. A bare `bin/robobuilder-paths` therefore resolves only when the working
directory happens to be a checkout of this repo — which is never the case for the
supported install (`docs/INSTALL.md` installs the plugin under `~/.claude/plugins/`,
and `settings.json.example` pins the shell's cwd to the user's project).

The failure is silent by construction, which is why the guard line above is not
optional. `eval "$(missing-command)"` leaves `SLUG` and `ROBOBUILDER_STATE_ROOT`
**empty and exits 0**. Every downstream read then returns nothing — indistinguishable
from a genuinely empty store — and every downstream write lands in `/projects/…` and
fails. A skill that persists a learning, a review record or a context snapshot appears
to work and stores nothing. `${CLAUDE_PLUGIN_ROOT}` is the form `hooks/hooks.json` and
the meta skills already use, so it is known to be available at runtime.

Available helpers (all under `$RB`):

- `bin/robobuilder-slug`: emits `SLUG=<project-slug>` for the current git repo or directory.
- `bin/robobuilder-paths`: prints the configured state root.
- `bin/robobuilder-config`: prints existing local config values.
- `bin/robobuilder-learnings-log` / `bin/robobuilder-learnings-search`: append and search project learnings.
- `bin/robobuilder-review-log` / `bin/robobuilder-review-read`: append and read review records.
- `bin/robobuilder-diff-scope`: summarize changed-file scope for review and ship workflows.
- `bin/robobuilder-next-version`: choose the next local semver when no release metadata exists.

Do not add third-party runtime binary installers here. If a target project needs browser automation, database clients, or build tools, use that project's own dependency setup.
