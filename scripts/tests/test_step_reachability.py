"""Every numbered step in a skill must be reachable.

A skill written as "Step 1 ... Step 20" is a program, and its forward jumps are
gotos. Nothing checked where they landed, so three of them landed past work
that was not optional:

  - `ship` Step 6 sent both of its exits to Step 9, skipping the test coverage
    audit, the plan completion audit, plan verification and scope drift
    detection. The exit that fires is "no prompt-related files changed" —
    the path every repo without that one Rails eval suite takes, i.e. nearly
    all of them.
  - `ship` Steps 9.3 and 10 sent three exits to Step 12, skipping Step 11,
    which is titled "Adversarial review (always-on)" and opens "Every diff gets
    adversarial review." The exits that fire are "no issues found" and "no
    review comments" — so the review was skipped exactly when nothing else had
    looked.
  - `land-and-deploy` sent both CI outcomes to Step 4 (Merge the PR), skipping
    Step 3.4 and Step 3.5. Step 3.5 is titled "Pre-merge readiness gate" and
    says "This is the critical safety check before an irreversible merge." It
    was unreachable on every path.

Same shape as the scoring bugs in this repo: a check that never runs reads
exactly like a check that passed. This test makes a skipped section fail the
suite unless someone has written down why the skip is correct.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

HEADING = re.compile(r"^#{2,3}\s*(?:Step|Stage|Phase)\s*([0-9]+(?:\.[0-9]+)?)\b", re.MULTILINE)
JUMP = re.compile(
    r"(?:continue|proceed|skip|go|jump|move on)\s+to\s+\*{0,2}(?:Step|Stage|Phase)\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)

# Jumps that genuinely should skip sections, each with the reason it is sound.
# A skip that is not listed here fails. Adding an entry is the moment to check
# that the skipped sections really are optional on that path.
INTENTIONAL_SKIPS = {
    ("tune-claude-md", "1", "5"):
        "no existing user file, so there is nothing to classify or merge",
    ("land-and-deploy", "5", "9"):
        "docs-only change: nothing was deployed, so there is nothing to wait for, "
        "canary or revert",
    ("land-and-deploy", "7", "9"):
        "canary passed, so the revert step has no subject",
    ("land-and-deploy", "2", "3.4"):
        "CI already green, so Step 3's only job -- waiting for it -- has no subject. "
        "3.4 and 3.5 are deliberately still ahead of the merge",
}


def _skills() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("SKILL.md"))


def _unreviewed_skips(text: str, skill: str) -> list[tuple[str, str, list[str]]]:
    heads = [(m.start(), float(m.group(1)), m.group(1)) for m in HEADING.finditer(text)]
    if len(heads) < 2:
        return []
    out = []
    for m in JUMP.finditer(text):
        dest_s = m.group(1)
        dest = float(dest_s)
        prior = [h for h in heads if h[0] <= m.start()]
        if not prior:
            continue
        cur = max(prior, key=lambda h: h[0])
        skipped = [h[2] for h in heads if cur[1] < h[1] < dest]
        if skipped and (skill, cur[2], dest_s) not in INTENTIONAL_SKIPS:
            out.append((cur[2], dest_s, skipped))
    return out


@pytest.mark.parametrize("path", _skills(), ids=lambda p: p.parent.name)
def test_no_forward_jump_skips_a_section(path: Path) -> None:
    skill = path.parent.name
    bad = _unreviewed_skips(path.read_text(encoding="utf-8"), skill)
    assert not bad, "\n".join(
        f"{skill}: 'go to Step {dest}' from Step {cur} skips Step(s) {', '.join(sk)}. "
        f"Either retarget the jump, or add ('{skill}', '{cur}', '{dest}') to "
        f"INTENTIONAL_SKIPS with the reason those sections are optional here."
        for cur, dest, sk in bad
    )


def test_intentional_skip_allowlist_has_no_stale_entries() -> None:
    """An allowlist entry that no longer matches a real jump hides the next one."""
    live = set()
    for path in _skills():
        skill = path.parent.name
        text = path.read_text(encoding="utf-8")
        heads = [(m.start(), float(m.group(1)), m.group(1)) for m in HEADING.finditer(text)]
        for m in JUMP.finditer(text):
            prior = [h for h in heads if h[0] <= m.start()]
            if not prior:
                continue
            cur = max(prior, key=lambda h: h[0])
            if any(cur[1] < h[1] < float(m.group(1)) for h in heads):
                live.add((skill, cur[2], m.group(1)))
    stale = set(INTENTIONAL_SKIPS) - live
    assert not stale, f"INTENTIONAL_SKIPS entries that match no current jump: {sorted(stale)}"
