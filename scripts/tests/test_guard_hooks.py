"""guard's hooks must exist and must actually block.

`/robobuilder:guard` sells itself as "full safety mode". Its frontmatter declared
three PreToolUse hooks pointing at `${CLAUDE_SKILL_DIR}/../careful/bin/check-careful.sh`
and `${CLAUDE_SKILL_DIR}/../freeze/bin/check-freeze.sh` — sibling skill directories
that exist in no robobuilder repo.

So guard installed, announced two active protections, and enforced nothing. That is
worse than not shipping guard: a user who turned it on before touching prod got a
false sense of a net that was not there.

The hooks are implemented now, but a hook that exists is not a hook that blocks, and
this repo's recurring defect is exactly that gap. So this tests behaviour, not
presence: real payloads in, exit codes out.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
GUARD_SKILL = ROOT / "skills" / "utils" / "guard" / "SKILL.md"

CAREFUL = SCRIPTS / "check_careful.py"
FREEZE = SCRIPTS / "check_freeze.py"

BLOCK = 2
ALLOW = 0


def _run(script: Path, payload, env: dict | None = None) -> int:
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(script)],
        input=body,
        text=True,
        capture_output=True,
        env={"PATH": "/usr/bin:/bin", **(env or {})},
    ).returncode


def test_guard_hook_commands_point_at_files_that_exist() -> None:
    """The original defect: three hooks aimed at scripts in directories that do not exist."""
    text = GUARD_SKILL.read_text(encoding="utf-8")
    commands = re.findall(r"command:\s*\"(.+?)\"\s*$", text, re.MULTILINE)
    assert commands, "guard declares no hook commands — did the frontmatter change?"
    missing = []
    for cmd in commands:
        for token in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s\"\\]+)", cmd):
            if not (ROOT / token).exists():
                missing.append(token)
        if "CLAUDE_PLUGIN_ROOT" not in cmd:
            missing.append(f"{cmd} (not rooted at the plugin, so it will not resolve)")
    assert not missing, f"guard hooks reference targets that do not exist: {missing}"


@pytest.mark.parametrize(
    "command,expected,label",
    [
        ("rm -rf /tmp/x", BLOCK, "recursive delete"),
        ("git push --force origin main", BLOCK, "force-push"),
        ("git reset --hard HEAD~3", BLOCK, "discards work"),
        ("DROP TABLE users;", BLOCK, "drops a table"),
        ("DELETE FROM users", BLOCK, "unbounded delete"),
        ("terraform destroy -auto-approve", BLOCK, "destroys infra"),
        ("DELETE FROM users WHERE id = 1", ALLOW, "bounded delete"),
        ("ls -la", ALLOW, "harmless"),
        ("git status", ALLOW, "harmless"),
        ("rm ./one-file.txt", ALLOW, "non-recursive single file"),
    ],
)
def test_careful_blocks_destructive_and_allows_the_rest(command, expected, label) -> None:
    got = _run(CAREFUL, {"tool_input": {"command": command}})
    verb = "block" if expected == BLOCK else "allow"
    assert got == expected, f"guard should {verb} {label}: {command!r} (exit {got})"


def test_careful_fails_closed_on_unparseable_input() -> None:
    """An unparseable command is exactly when the user wanted a second look."""
    assert _run(CAREFUL, "this is not json") == BLOCK


def test_freeze_blocks_outside_and_allows_inside(tmp_path: Path) -> None:
    inside = tmp_path / "keep"
    inside.mkdir()
    env = {"ROBOBUILDER_FREEZE_DIR": str(inside)}
    assert _run(FREEZE, {"tool_input": {"file_path": str(inside / "a.py")}}, env) == ALLOW
    assert _run(FREEZE, {"tool_input": {"file_path": str(tmp_path / "b.py")}}, env) == BLOCK


def test_freeze_checks_every_path_in_a_multi_edit(tmp_path: Path) -> None:
    """One outside path among several must still block, or the boundary is decorative."""
    inside = tmp_path / "keep"
    inside.mkdir()
    payload = {
        "tool_input": {
            "edits": [
                {"file_path": str(inside / "a.py")},
                {"file_path": str(tmp_path / "escape.py")},
            ]
        }
    }
    assert _run(FREEZE, payload, {"ROBOBUILDER_FREEZE_DIR": str(inside)}) == BLOCK


def test_freeze_is_inert_with_no_boundary_set() -> None:
    """Deliberate — but asserted, so it stays a decision rather than an accident."""
    assert _run(FREEZE, {"tool_input": {"file_path": "/anywhere/at/all.py"}}) == ALLOW
