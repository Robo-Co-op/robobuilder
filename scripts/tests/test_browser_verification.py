"""A review that never renders the page cannot report on how the page renders.

Every review path in this suite was static: read the diff, reason about it. The one
agent that can open a browser -- `e2e-tester` -- was dispatched by a single skill,
behind the condition "only for UI features". That is a judgement the maker makes
about its own change, and it is the same defect `tdd` already had: gating an
independent check on the self-assessment the check exists to replace means the check
goes unused in exactly the cases that needed it.

So the trigger has to be a fact about the diff, not an opinion about it, and the
skill has to say what it reports when the browser check cannot run at all. A skipped
render check that prints nothing is an unmeasured thing counted as a pass, which is
the failure this whole suite exists to refuse.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"

# The review entry points. Each must be able to reach a browser, or it is claiming a
# verdict on rendered behaviour it never observed.
REVIEW_SKILLS = {
    "diff-review": SKILLS / "phase4" / "diff-review" / "SKILL.md",
    "cross-review": SKILLS / "phase4" / "cross-review" / "SKILL.md",
}

# Phrasings that hand the decision back to the maker. Each of these appeared in this
# repo, or in Lite, before this guard existed.
SUBJECTIVE_TRIGGERS = [
    "only for ui features",
    "for ui changes",
    "if it's a ui change",
    "if this is a ui change",
    "when the change is ui",
    "for ui work",
    "if ui is affected",
    "at your discretion",
    "if you think",
    "when you judge",
]

# An observable trigger has to name the file types that make a change a UI change.
# These three are the floor: plain pages, styling, and at least one component format.
REQUIRED_EXTENSIONS = ["html", "css"]
COMPONENT_EXTENSIONS = ["tsx", "jsx", "vue", "svelte"]

CONTEXT_LINES = 25


def dispatch_context(text, needle="e2e-tester"):
    """The lines around every mention of the agent, joined.

    The trigger does not have to sit on the same line as the dispatch, but it does
    have to sit near it -- a condition stated in a different section is a condition
    the reader will not connect to the call.
    """
    lines = text.splitlines()
    hits = [i for i, line in enumerate(lines) if needle in line]
    chunks = []
    for i in hits:
        lo = max(0, i - CONTEXT_LINES)
        hi = min(len(lines), i + CONTEXT_LINES + 1)
        chunks.append("\n".join(lines[lo:hi]))
    return hits, "\n".join(chunks)


# A dispatch is a list item whose subject IS the agent -- the shape the other three
# agents are already written in:
#
#     - `e2e-tester` — whenever ...
#     4. `e2e-tester` — in every round ...
#
# Not merely a sentence that says the name. The skills below also mention the agent
# in their fallback prose ("If `e2e-tester` fired but could not run"), and an earlier
# version of this guard accepted that as proof of wiring: deleting the real call while
# leaving the prose kept the suite green. A naive substring match blesses the exact
# bug it exists to catch, which is the same correction test_agent_wiring.py needed.
DISPATCH_LINE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+`e2e-tester`")


@pytest.mark.parametrize("name", sorted(REVIEW_SKILLS))
def test_review_skill_can_reach_a_browser(name):
    path = REVIEW_SKILLS[name]
    assert path.exists(), f"{name} is missing at {path.relative_to(REPO)}"
    text = path.read_text(encoding="utf-8")
    dispatched = [line for line in text.splitlines() if DISPATCH_LINE.match(line)]
    assert dispatched, (
        f"{name} dispatches no browser-capable agent, so every verdict it prints about "
        "a rendered page is about a page it never opened. (Naming e2e-tester in prose is "
        "not a dispatch -- it has to be listed alongside the other agents.)"
    )


@pytest.mark.parametrize("name", sorted(REVIEW_SKILLS))
def test_browser_trigger_is_a_fact_about_the_diff(name):
    text = REVIEW_SKILLS[name].read_text(encoding="utf-8")
    hits, context = dispatch_context(text)
    assert hits, f"{name} never mentions e2e-tester"

    lowered = context.lower()
    found = [phrase for phrase in SUBJECTIVE_TRIGGERS if phrase in lowered]
    assert not found, (
        f"{name} gates the browser check on a judgement call: {found}. The maker decides "
        "whether its own change 'is a UI change', which is the judgement the independent "
        "check exists to replace. State a condition over the diff instead."
    )


# The extension list as it appears in a real trigger: an alternation inside the grep
# pattern, e.g. \.(html|css|tsx)$ . Parse the alternation rather than searching for
# ".html" as a literal -- that substring never appears, because the pattern reads
# "\.(html". Checking for prose mentions instead would pass on a skill that merely
# talks about CSS somewhere near the dispatch.
EXTENSION_ALTERNATION = re.compile(r"\\\.\(([a-z0-9|]+)\)")


def trigger_extensions(context):
    """Every extension the skill's own grep pattern would actually match."""
    found = set()
    for group in EXTENSION_ALTERNATION.findall(context):
        found.update(part for part in group.split("|") if part)
    return found


@pytest.mark.parametrize("name", sorted(REVIEW_SKILLS))
def test_browser_trigger_names_the_file_types_that_fire_it(name):
    text = REVIEW_SKILLS[name].read_text(encoding="utf-8")
    _, context = dispatch_context(text)

    assert "--name-only" in context, (
        f"{name} states no command that evaluates the trigger. The condition has to be "
        "runnable (`git diff ... --name-only`), not merely described."
    )

    extensions = trigger_extensions(context)
    assert extensions, (
        f"{name}'s browser trigger contains no extension alternation "
        r"(expected a grep pattern like \.(html|css|tsx)$ ). A condition stated only in "
        "prose is one every reader resolves differently."
    )

    missing = [ext for ext in REQUIRED_EXTENSIONS if ext not in extensions]
    assert not missing, (
        f"{name}'s browser trigger does not match {missing}; it matches {sorted(extensions)}. "
        "A change to a plain page or a stylesheet would not fire the render check."
    )
    assert extensions & set(COMPONENT_EXTENSIONS), (
        f"{name}'s browser trigger matches no component file type "
        f"(one of {COMPONENT_EXTENSIONS}); it matches {sorted(extensions)}. A diff that only "
        "touches components would not fire it."
    )


@pytest.mark.parametrize("name", sorted(REVIEW_SKILLS))
def test_an_unrunnable_browser_check_is_reported_not_skipped(name):
    """No dev server, no Playwright, no reachable URL -- that is a known state, not a pass.

    The skill has to name the outcome so it reaches the verdict. Silence here is the
    absent-measurement bug wearing a different hat: the reviewer reports SHIP having
    checked nothing, and nothing in the output says so.
    """
    text = REVIEW_SKILLS[name].read_text(encoding="utf-8")
    _, context = dispatch_context(text)
    assert "UNVERIFIED" in context, (
        f"{name} does not say what it reports when the browser check cannot run. It has to "
        "surface UNVERIFIED in the verdict rather than dropping the check silently."
    )
