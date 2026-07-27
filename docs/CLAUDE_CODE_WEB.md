# RoboBuilder outside the terminal CLI (desktop app & web)

`/plugin` is a **terminal-CLI command** — it opens an interactive panel that doesn't
exist in the Claude desktop app or in Claude Code on the web. Running it there gives:

```
/plugin isn't available in this environment.
```

That is expected, not a broken install. Pick whichever option below matches your
environment.

## Option 1: The desktop app's plugin browser

The Claude desktop app ships a graphical plugin browser. Use it instead of
`/plugin` — same marketplaces, same plugins, no terminal needed.

## Option 2: Declare plugins in `.claude/settings.json` (desktop, web, cloud)

The documented path for web and cloud sessions, and it works in the desktop app
too. Add to your project's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "robo-coop-tools": {
      "source": { "source": "github", "repo": "Robo-Co-op/robobuilder-standard" }
    }
  },
  "enabledPlugins": {
    "robobuilder@robo-coop-tools": true
  }
}
```

Swap or add `robobuilder-lite@robo-coop-tools` / `robobuilder-pro@robo-coop-tools`
for the other editions — one marketplace entry serves all three, since the
`robo-coop-tools` catalog lives in this repo and lists every edition.

Commit the file and everyone working in that repo gets the same setup.

## Option 3: Commit the skills themselves into the repo

If you want a couple of specific skills rather than a whole plugin, a session reads
`.claude/skills/` (and `.claude/agents/`) straight from the repo:

1. Copy the skill(s) from `skills/<phase>/<name>/SKILL.md` into your project under
   `.claude/skills/<name>/SKILL.md` (plus `.claude/agents/` for any agents the skill
   calls).
2. Commit and merge to the **default branch**. Skills sitting on an unmerged feature
   branch are invisible to a fresh web session — an open PR is not enough.
3. Start a new session; the skill shows up with no reload step.

This bypasses the plugin system entirely, so you also lose the hooks and the
`/robobuilder:*` namespacing — you invoke the skill by its bare name.

## Option 4: Register as an account-level skill

claude.ai's **Customize > Skills > Add > Describe skill instructions** creates a
skill tied to your account rather than a repo, and it **is** picked up by Claude Code
web sessions (confirmed 2026-07-18). Useful when you want a skill available across
every project without touching each repo.

1. Split a `SKILL.md` into the form's **description** and **instructions** fields.
2. Drop references to `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`,
   `bin/robobuilder-*`, and sibling doc files — none of those exist outside the
   plugin, so the standalone skill needs to be self-contained prose.
3. Condense large skills. The form has practical size limits well under some skills'
   source (e.g. `ship` at 120K+ chars); keep the process, decision logic, and
   anti-patterns, drop the rest.
4. **Name collisions return an error** ("This skill name is already in use"). This
   covers reserved words (a name containing the literal word `claude` is rejected)
   and collisions with any skill already on the account — including a different
   edition's same-named skill, e.g. Lite's `ship` vs Standard's `ship`. Rename
   defensively (`ship` → `robobuilder-ship`, `tune-claude-md` → `tune-agents-md`)
   and record the renames somewhere your team can find them.
5. It's manual and one-skill-at-a-time — there's no bulk import, so this doesn't
   scale to a whole edition the way Options 1–2 do.

## Which to use

| Situation | Use |
|---|---|
| Desktop app, want the full plugin | Option 1 (plugin browser) |
| Web/cloud, want the full plugin, team-wide | Option 2 (`settings.json`) |
| Just a few skills, scoped to one repo | Option 3 (commit skills) |
| A personal skill across every project | Option 4 (account-level) |

Options 1 and 2 keep hooks, agents, and the `/robobuilder:*` namespace. Options 3
and 4 give you the skill text only.
