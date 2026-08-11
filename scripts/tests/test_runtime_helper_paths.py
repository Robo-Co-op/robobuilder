"""Helper scripts must be addressed through the plugin root, and their absence must stop the skill.

`bin/` ships inside the plugin. It is never copied into the user's project and
never added to PATH — `docs/INSTALL.md` installs under `~/.claude/plugins/`, and
`settings.json.example` sets CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=true, which
pins the shell's cwd to the user's project. So a bare `bin/robobuilder-paths`
resolves only when cwd happens to be a checkout of this repo, which the supported
install never produces.

`docs/RUNTIME.md` used to prescribe exactly that bare form, and 11 skills followed
it across 124 call sites — health, plan-eng-review, browse, learn, cso, canary,
land-and-deploy, ship, context-save, context-restore, guard.

The failure was silent by construction, which is the reason this test exists rather
than a lint rule. Reproduced from a real project before the fix:

    $ eval "$(bin/robobuilder-slug 2>/dev/null)"; eval "$(bin/robobuilder-paths)"
    SLUG=[]  ROBOBUILDER_STATE_ROOT=[]
    exit 0

`eval "$(missing-command)"` leaves the variables empty and exits zero. Every
downstream read then returns nothing — indistinguishable from a genuinely empty
store — and every downstream write lands in `/projects/…` and fails. Skills that
persist learnings, review records and context snapshots appeared to work and
stored nothing.

Same shape as this repo's other defects: an absent measurement read as a pass.
So this checks two things, and the second is the one that matters — addressing
the helper correctly is not enough if a missing helper still lets the skill
continue as though it had data.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
RUNTIME_DOC = ROOT / "docs" / "RUNTIME.md"

# A helper invoked as a bare relative path: `bin/robobuilder-x`, not `$RB/robobuilder-x`
# and not the `bin/robobuilder-x` that appears in prose describing the file layout.
BARE_INVOCATION = re.compile(r"(?<![\w/\"$])bin/robobuilder-[a-z-]+")

# The bootstrap that resolves the helper directory.
DEFINES_RB = re.compile(r"""RB=["']?\$\{CLAUDE_PLUGIN_ROOT""")

# The line that refuses to continue when the helpers are not there.
GUARDS_MISSING_HELPERS = re.compile(r"""\[\s*-x\s+["']?\$RB/robobuilder-""")

FENCED_SHELL = re.compile(r"```(?:bash|sh|shell)\n(.*?)```", re.DOTALL)


def _skills() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


@pytest.mark.parametrize("path", _skills(), ids=lambda p: p.parent.name)
def test_no_bare_relative_helper_invocation(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    bad = BARE_INVOCATION.findall(text)
    assert not bad, (
        f"{path.parent.name} invokes {sorted(set(bad))} as a bare relative path. "
        "bin/ ships inside the plugin and is never on PATH, so this resolves to nothing "
        'from a user project and fails silently. Use "$RB/robobuilder-..." with the '
        "bootstrap from docs/RUNTIME.md."
    )


@pytest.mark.parametrize("path", _skills(), ids=lambda p: p.parent.name)
def test_shell_block_using_rb_defines_and_guards_it(path: Path) -> None:
    """Using $RB without defining it is the same silent-empty failure by another route."""
    for block in FENCED_SHELL.findall(path.read_text(encoding="utf-8")):
        if "$RB/" not in block:
            continue
        assert DEFINES_RB.search(block), (
            f"{path.parent.name} has a shell block using $RB without defining it. "
            "An undefined $RB expands to empty, so the command becomes '/robobuilder-x' "
            "and fails — silently, if stderr is suppressed."
        )
        assert GUARDS_MISSING_HELPERS.search(block), (
            f"{path.parent.name} defines $RB but does not check the helpers exist. "
            "Without the `[ -x \"$RB/robobuilder-paths\" ] || ...` guard, a missing "
            "helper leaves SLUG and ROBOBUILDER_STATE_ROOT empty and exits 0, and the "
            "skill continues as though it had measured something."
        )


def test_runtime_doc_prescribes_the_plugin_rooted_form() -> None:
    """The contract is what the next skill author copies; it has to be right at the source."""
    text = RUNTIME_DOC.read_text(encoding="utf-8")
    assert DEFINES_RB.search(text), "docs/RUNTIME.md must show the $RB bootstrap"
    assert GUARDS_MISSING_HELPERS.search(text), (
        "docs/RUNTIME.md must show the guard, not just the path — the silent-empty "
        "failure is the reason the path matters"
    )
    for block in FENCED_SHELL.findall(text):
        assert not BARE_INVOCATION.findall(block), (
            "docs/RUNTIME.md still shows a bare relative helper invocation in a shell "
            "block; that is the exact form 11 skills copied"
        )
