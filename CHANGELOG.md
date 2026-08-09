# Changelog

All notable changes to robobuilder.

## [1.5.0] — 2026-08-09

Four scoring and stopping-rule defects, all found by *executing* these skills rather
than reading them. Eleven rounds of prose review across the three repos found none of
them, and all four are the same shape: **a measurement that never happened counted as
a pass.**

### Fixed
- `health`'s composite could not reach 10. The five weights (tests 28, type check 22,
  lint 18, dead code 13, shell 9) sum to **90**, so dividing by the raw total capped a
  clean codebase at 9.0, and "a `SKIPPED` tool redistributes its weight" never said
  what it redistributes into — one dataset produced three different composites
  depending on how a reader resolved that. Now
  `Σ(score × weight for active) ÷ Σ(weight for active)`, with a worked example
- `ship`'s quality score rose as review coverage fell: a specialist that never ran
  contributed silence, and silence read as quality. The score now travels with its
  denominator — `score (N of M specialists)`
- `ship` Step 12 assumed a `VERSION` file. None of the three robobuilder repos has
  one, so `ship` could not ship the repo it lives in, and the failure was quiet —
  computing a bump against a nonexistent base rather than stopping. It now resolves
  the version file across `VERSION`, `.claude-plugin/plugin.json`, `package.json`,
  `pyproject.toml`, `Cargo.toml`
- `cross-review`'s two stopping rules, both disproved by this project's own review
  history: the "max 5 rounds, beyond that it diverges" cap would have shipped four
  real defects found in rounds 6-9, and "the same finding in 3+ rounds is a false
  positive" would have dismissed six consecutive genuine findings. The cap now keys on
  whether a round surfaced anything *new*, and the heuristic distinguishes the same
  *finding* recurring from the same *area* yielding new defects

### Added
- Test: any skill that aggregates per-item measurements must state what it divides by
  and what happens to an input it could not measure. The registry is closed, so a new
  scoring skill fails until someone answers both
- Test: `plugin.json`'s version must match the CHANGELOG's newest entry. Ported from
  Pro, which was the only repo whose version was correct — because it alone had this
- CI: the suite runs on push and pull request instead of only by hand

### Changed
- `marketplace.json` catches up the Pro entry (pinned at 1.0.0, stale since Pro tagged
  1.1.0) to 1.2.0 for the L5 graph layer, and Lite to 1.1.0
- README: the Pro row and the loop-stack line cover L5, the graph of loops above L3/L4

## [1.4.0] — 2026-07-03

Three-editions release. This repo is now **Robo Builder Standard**.

### Changed
- GitHub repo renamed `Robo-Co-op/robobuilder` → `Robo-Co-op/robobuilder-standard` (old URL redirects). The plugin name stays `robobuilder`, so installed `/robobuilder:*` commands are unaffected
- README: "Three editions" comparison table (Lite / Standard / Pro) with the L1-L4 loop-stack positioning
- marketplace.json bumped to v2.0.0: `robo-coop-tools` now lists all three plugins — `robobuilder` (this repo), `robobuilder-lite` (4 merged mega-skills for beginners), `robobuilder-pro` (Loop Engineering add-on)
- plugin.json description marks this as the Standard edition

## [1.3.0] — 2026-06-12

Workflow-order release. All-English content; upstream attribution fixes; blueprint-sync polish.

### Added
- Phase/order tag at the start of every skill description (e.g. `[P1-1 Design]`, `[Util-2]`) so the alphabetical `/plugin` skill list reads in workflow order. Within each phase, ordering follows practical usage order and frequency (grill family adjacent, review skills light → heavy, etc.)
- `upstream:` frontmatter field (canonical source repo URL) on all ingested Matt Pocock / GStack skills
- `origin: robobuilder` frontmatter on the 4 meta skills, 3 playbooks, and `blueprint-sync` (previously undeclared or mislabeled)
- `blueprint-sync`: resolution-direction table (stale-doc / violation / pivot) in drift classification; robobuilder pedagogy preamble; wired into `playbook-new-feature` Step 4 and `docs/WORKFLOW.md`
- "All 41 skills, in workflow order" table in README

### Changed
- **All-English content**: `cross-review`, `diff-review`, `grill`, `btw`, `export` (descriptions and bodies) and test comments translated from Japanese to English
- `setup` skill renamed from `setup-matt-pocock-skills` to `setup` (frontmatter `name:`); all internal references updated
- README attribution now links to the canonical upstream repos

### Fixed
- **LICENSE**: Matt Pocock upstream URL corrected from the non-existent `mattpocock/ai-engineering-skills` to `mattpocock/skills` (verified live); all in-repo references updated
- plugin.json version was still 1.0.0 despite the v1.1.0 tag; now tracks releases (1.3.0)

## [1.2.0] — 2026-05-23

New skill: `blueprint-sync` — keeps design documents honest as code evolves.

### Added
- `skills/utils/blueprint-sync/` — new cross-cutting skill with 4 modes:
  - `drift-check`: detect gaps between docs and code, output a structured drift report
  - `update-docs`: surgically update docs to match current reality, commit changes
  - `retrospective`: post-ship review + doc sync + optional ADR creation
  - `living-doc`: lightweight single-pass update after small PRs
  - Auto-detects mode from context (post-ship → retrospective, etc.)
- `ship` skill: added `/robobuilder:blueprint-sync` to See Also; added post-ship suggestion rule to Important Rules

## [1.1.0] — 2026-05-12

Polish & ship release. Same skill/agent/hook surface as v1.0; security and ergonomics hardening.

### Added
- robobuilder pedagogy preamble on all 33 ingested SKILL.md (What / When / See Also / Bootcamp / Origin) — propagated by `scripts/dev/update_skill_frontmatter.py`, idempotent on re-run
- `origin:`, `bootcamp_module:`, `bootcamp_url:` frontmatter fields on every ingested skill (Living Knowledge Loop scaffolding)
- 29 new unit tests under `scripts/tests/` covering `auto_format.py`, `memory_consolidate.py`, `notification.py` (90 tests total, all passing)
- `scripts/tests/conftest.py` with shared fixtures (`run_script`, `tmp_memory_dir`); runtime-built attack strings so tests don't trip block_secrets when edited in-session
- `scripts/pytest.ini` + `scripts/tests/README.md`
- Test-fixture exemption for content scanning in `block_secrets.py` — paths under `tests/`, `__tests__/`, `fixtures/`, `*_test.py`, `conftest.py`, `*.spec.{ts,js,tsx,jsx}`, `*.test.{ts,js,tsx,jsx}` skip CONTENT scanning (file-name scanning still applies)
- Legacy binary installer supply-chain guard in `install_binaries.sh` — refused to auto-confirm installs from moving branch tips before the installer was replaced by a no-op compatibility shim
- `## Security-sensitive code` section in `CLAUDE.md.baseline`
- Explicit precedence note in `settings.json.example` (deny → ask → allow, verified against docs)

### Changed
- `block_secrets.py` `_audit_log()` now uses `Path.home()` (OS-API resolution) instead of `HOME`/`USERPROFILE` env reads — not hijackable by env manipulation

### Documented
- `docs/CONTRIBUTING.md` — `.md.bak` and other compound-extension edge cases as known limitations

## [1.0.0] — 2026-05-11

Initial release. Built and reviewed in one session.

### Plugin surface
- 40 SKILL.md across 11 phase directories (meta, phase0, phase05, phase1, phase2, phase3, phase35, phase4, phase5, utils, playbooks)
  - 33 ingested from Matt Pocock (13, MIT), GStack (10, MIT), Jin custom (10)
  - 3 robobuilder-original meta-skills: `start`, `tune-claude-md`, `upgrade`, `install-companions`
  - 3 playbooks: `playbook-new-feature`, `playbook-bug-fix`, `playbook-review-deep`
- 9 phase-specific subagents (5 new for robobuilder: `codebase-explorer`, `design-critic`, `requirements-validator`, `tdd-pair`, `release-notes-writer`)
- 6 lifecycle hooks (SessionStart / PreToolUse / PostToolUse / Notification / PreCompact / SessionEnd)
- 4 Python hook scripts + 3 setup shell scripts
- 6 documentation files
- `CLAUDE.md.baseline` for `/robobuilder:tune-claude-md` personalization wizard
- `company.yaml` — Robo Co-op intelligence (Teams / Asana / 1Password / Vercel / Supabase / Stripe / Azure SQL / Notion)
- `marketplace.json` registering robobuilder under `robo-coop-tools` marketplace

### Security fixes (caught by `/cross-review` 5 rounds, before any release)
- PowerShell command injection in `notification.py` (no user content interpolation; sound-only)
- AppleScript injection in `notification.py` (`_sanitize()` strips non-printable + injection chars)
- Supply-chain pinning for `install_binaries.sh` (3-path coverage: fresh / upgrade / re-run + AUTO_YES env var for CI)
- `memory_consolidate.py` stat-after-open bug (header duplicated on every invocation; now checked before `open("a")`)
- `block_secrets.py` credentials regex prefix bug (`db_credentials.json` was bypassing)
- `block_secrets.py` MultiEdit content not scanned (now iterates `edits[*].new_string`)
- Expanded `block_secrets.py` SECRET_CONTENT_PATTERNS to cover: Stripe (live/test), GitHub variants (p/s/o/r/u), JWT, Azure connection strings, 1Password service-account tokens
- `block_secrets.py` doc-extension lookbehind so docs like `credentials-management-guide.md` are not blocked
- Tightened `settings.json.example` deny patterns (`.env.local`, `.envrc`, `id_rsa`, `wget -O- | sh`, etc.)
- Audit log to `~/.claude/logs/block_secrets.log` for blocked attempts

### Licensing
MIT, with attribution to Matt Pocock and Garry Tan for redistributed skills. See `LICENSE`.
