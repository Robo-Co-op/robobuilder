"""Content checks for the skills that turn measurements into a score.

Executing `health` and `ship` end to end produced two real defects, and both
were the same shape: a measurement that never happened counted as a pass.

  - `health`'s five weights sum to 0.90, so dividing by the raw total capped a
    clean codebase at 9.0, and "a SKIPPED tool redistributes its weight" never
    said what it redistributes into. One dataset yielded three different
    composites depending on how a reader resolved that.
  - `ship`'s quality score rose as review coverage fell: a specialist that
    never ran contributed silence, and silence read as quality.

Neither was found by reading the skills — eleven rounds of prose review across
these repos missed both, and the sibling repos each had a third and fourth
instance of the same shape. So this guards the class, not the two instances.

A skill that aggregates per-item measurements into one number must say:

  1. what it divides by  — an unstated denominator is where 0.90-vs-1.0 hid
  2. what happens to an item it could not measure — that item must drop out,
     not score 0 (which penalises absent tooling) and not score 10 (which
     inflates a repo that measured nothing)

The registry below is closed on purpose. A new scoring skill fails this test
until someone adds it, which is exactly the moment they have to answer both.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

SCORING_SIGNATURE = re.compile(r"(composite|Σ\(|quality[_ ]score|overall score)", re.IGNORECASE)

STATES_DENOMINATOR = re.compile(
    # Deliberately narrow: it must name a division, not merely describe which
    # inputs counted. "the categories that actually ran" states the skip rule,
    # not the denominator, and letting it satisfy both is how a falsification
    # run found this test passing a rubric whose divisor had been removed.
    r"(÷|divid(?:e|ed|ing) by|number of \w+ scored|\bN of M\b)",
    re.IGNORECASE,
)

STATES_MISSING_INPUT_RULE = re.compile(
    r"(\bn/a\b|SKIPPED|drops? out|did not run|never ran)", re.IGNORECASE
)

SCORING_SKILLS = {"health", "ship"}


def _scoring_skills_on_disk() -> set[str]:
    return {
        p.parent.name
        for p in SKILLS_DIR.rglob("SKILL.md")
        if SCORING_SIGNATURE.search(p.read_text(encoding="utf-8"))
    }


def test_scoring_skill_registry_matches_disk() -> None:
    """A skill that aggregates scores must be registered, and vice versa."""
    on_disk = _scoring_skills_on_disk()
    unregistered = on_disk - SCORING_SKILLS
    assert not unregistered, (
        f"these skills aggregate scores but are not in SCORING_SKILLS: {sorted(unregistered)}. "
        "Add them, and make sure each states its denominator and its skip rule."
    )
    stale = SCORING_SKILLS - on_disk
    assert not stale, f"SCORING_SKILLS lists skills that no longer score: {sorted(stale)}"


def _skill_text(skill: str) -> str:
    matches = [p for p in SKILLS_DIR.rglob("SKILL.md") if p.parent.name == skill]
    assert len(matches) == 1, f"expected exactly one {skill}/SKILL.md, found {len(matches)}"
    return matches[0].read_text(encoding="utf-8")


@pytest.mark.parametrize("skill", sorted(SCORING_SKILLS))
def test_scoring_skill_states_its_denominator(skill: str) -> None:
    assert STATES_DENOMINATOR.search(_skill_text(skill)), (
        f"{skill} produces a score but never says what it divides by. "
        "An unstated denominator is how weights summing to 0.90 went unnoticed."
    )


@pytest.mark.parametrize("skill", sorted(SCORING_SKILLS))
def test_scoring_skill_states_its_missing_input_rule(skill: str) -> None:
    assert STATES_MISSING_INPUT_RULE.search(_skill_text(skill)), (
        f"{skill} produces a score but never says what happens to an input it "
        "could not measure. An absent measurement must drop out, not score 0 or 10."
    )
