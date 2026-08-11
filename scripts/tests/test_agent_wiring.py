"""Every shipped agent must be dispatched by at least one skill.

Five of the nine agents shipped in plugin.json with nothing calling them, and
three of those named the skill they belong to in their own description:

  - requirements-validator: "Use after /to-prd is generated" -- to-prd never
    dispatched it
  - tdd-pair: "Use whenever /tdd is invoked" -- tdd never dispatched it
  - codebase-explorer: "for the Phase 0.5 workflow" -- zoom-out, the Phase 0.5
    skill, never dispatched it
  - design-critic: "Complements the interactive /grill-me" -- grill-me never
    dispatched it
  - release-notes-writer: "Use during /ship" -- ship never dispatched it

They were installed and invisible: reachable only if a user named them by hand.
Same shape as the rest of this repo's defects -- a step declared to run that
never ran.

A note on how this test counts, because a naive version got it wrong. The first
pass at this survey searched raw skill text and concluded only three agents were
unwired, because `upgrade` renders a mock console diff containing the lines
"AGENTS ~ design-critic (modified)" and "+ agents/release-notes-writer.md
(added)". Those are sample output, not dispatches. So fenced code blocks and
blockquotes -- the two places this repo puts example output and sample dialogue
-- are stripped before matching. Without that, an agent named only in an example
counts as wired and the test blesses exactly the bug it exists to catch.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = ROOT / "agents"
SKILLS_DIR = ROOT / "skills"
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"

FENCED_BLOCK = re.compile(r"```.*?```", re.DOTALL)
BLOCKQUOTE = re.compile(r"^>.*$", re.MULTILINE)


def _prose(text: str) -> str:
    """Skill text with example output and sample dialogue removed."""
    return BLOCKQUOTE.sub("", FENCED_BLOCK.sub("", text))


def _agents() -> list[str]:
    return sorted(p.stem for p in AGENTS_DIR.glob("*.md"))


def _skill_prose() -> dict[str, str]:
    return {
        p.parent.name: _prose(p.read_text(encoding="utf-8"))
        for p in SKILLS_DIR.rglob("SKILL.md")
    }


def _dispatchers(agent: str) -> list[str]:
    return sorted(name for name, text in _skill_prose().items() if agent in text)


@pytest.mark.parametrize("agent", _agents())
def test_agent_is_dispatched_by_some_skill(agent: str) -> None:
    assert _dispatchers(agent), (
        f"no skill dispatches the {agent!r} agent, so it ships and never runs unless a "
        "user names it by hand. Wire it into the skill its own description points at, or "
        "remove it. Mentioning it inside a code fence or blockquote does not count — "
        "those are example output."
    )


def test_shipped_agents_match_disk() -> None:
    """An agent in the manifest but not on disk can never be dispatched at all."""
    manifest = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    declared = manifest.get("agents")
    if declared is None:
        pytest.skip("plugin.json does not enumerate agents")
    declared_names = {Path(str(a)).stem for a in declared}
    on_disk = set(_agents())
    assert declared_names == on_disk, (
        f"plugin.json agents and agents/ disagree: "
        f"only in manifest {sorted(declared_names - on_disk)}, "
        f"only on disk {sorted(on_disk - declared_names)}"
    )
