"""The marketing site may not claim a number the repo cannot prove.

`site/` is the public landing page for robobuilder. Every hard number it prints --
version, skill count, the size of the defect sweep -- is a claim about this
repository, and a landing page is exactly the artifact where a stale number
survives longest: nothing breaks, nobody notices, and the page quietly describes
a product that no longer exists.

So each number is declared once in `site/claims.json` with the source that
derives it, and this module re-derives every one of them from the repo. A claim
with no source is a failure, not an exemption -- that is the same
absent-measurement-counted-as-a-pass bug this suite exists to catch, and a
marketing page is not where we start making an exception for it.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
CLAIMS_PATH = SITE / "claims.json"

# Every locale the site ships, and the file that serves it.
LOCALES = {
    "en": SITE / "index.html",
    "ja": SITE / "ja" / "index.html",
}


def load_claims():
    return json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Source resolvers. Each returns the value the repo actually has right now.
# --------------------------------------------------------------------------


def _plugin_version():
    data = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return data["version"]


def _marketplace_pin(name):
    data = json.loads(
        (REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    for plugin in data["plugins"]:
        if plugin["name"] == name:
            return plugin["version"]
    raise AssertionError(f"marketplace.json has no plugin named {name!r}")


def _count_skills():
    return len(list((REPO / "skills").rglob("SKILL.md")))


def _count_agents():
    return len(list((REPO / "agents").glob("*.md")))


def _count_hooks():
    """Count lifecycle events, not the one key that wraps them.

    hooks.json nests every event under a single top-level "hooks" key, so
    len() of the document is 1 -- a number that looks like a measurement, passes
    every type check, and is wrong. Reach the event map explicitly.
    """
    data = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    events = data["hooks"]
    assert isinstance(events, dict) and events, "hooks.json has no event map"
    return len(events)


def _count_tests():
    """Collect the suite in a subprocess so this test never recurses into itself."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(REPO / "scripts" / "tests"), "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    match = re.search(r"(\d+) tests? collected", proc.stdout)
    if not match:
        raise AssertionError(
            "could not read a collected-test count out of pytest:\n" + proc.stdout[-2000:]
        )
    return int(match.group(1))


def _changelog_number(label):
    """Pull a number the CHANGELOG states, e.g. '114 findings raised'.

    The sweep numbers are history: they describe one dated event and must never
    drift, so their source is the entry that recorded them.
    """
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    # Collapse hard-wrapped prose so a number and its label can sit on two lines.
    flat = re.sub(r"\s+", " ", text)
    match = re.search(r"(\d+)\s+" + re.escape(label), flat)
    if not match:
        raise AssertionError(f"CHANGELOG.md states no number for {label!r}")
    return int(match.group(1))


def resolve(source):
    """Derive a claim's true value from its declared source."""
    kind = source["kind"]
    if kind == "plugin_version":
        return _plugin_version()
    if kind == "marketplace_pin":
        return _marketplace_pin(source["plugin"])
    if kind == "count_skills":
        return _count_skills()
    if kind == "count_agents":
        return _count_agents()
    if kind == "count_hooks":
        return _count_hooks()
    if kind == "count_tests":
        return _count_tests()
    if kind == "changelog_number":
        return _changelog_number(source["label"])
    raise AssertionError(f"unknown source kind {kind!r}")


KNOWN_KINDS = {
    "plugin_version",
    "marketplace_pin",
    "count_skills",
    "count_agents",
    "count_hooks",
    "count_tests",
    "changelog_number",
}


def claim_ids():
    if not CLAIMS_PATH.exists():
        return []
    return sorted(load_claims().keys())


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------


def test_claims_file_exists():
    assert CLAIMS_PATH.exists(), (
        f"{CLAIMS_PATH.relative_to(REPO)} is missing. Every number the site prints "
        "is declared there with the source that proves it."
    )


@pytest.mark.parametrize("claim_id", claim_ids())
def test_every_claim_declares_a_resolvable_source(claim_id):
    """A claim with no source is the bug, not an exception to it."""
    claim = load_claims()[claim_id]
    assert "source" in claim, (
        f"claim {claim_id!r} states a value with no source. A number nothing can "
        "check is exactly the absent measurement this suite refuses to count as a pass."
    )
    kind = claim["source"].get("kind")
    assert kind in KNOWN_KINDS, (
        f"claim {claim_id!r} declares source kind {kind!r}, which no resolver "
        f"implements. Known kinds: {sorted(KNOWN_KINDS)}"
    )


@pytest.mark.parametrize("claim_id", claim_ids())
def test_every_claim_matches_what_the_repo_derives(claim_id):
    claim = load_claims()[claim_id]
    actual = resolve(claim["source"])
    stated = claim["value"]

    if claim.get("compare") == "gte":
        assert actual >= stated, (
            f"claim {claim_id!r} says at least {stated}, but the repo now derives "
            f"{actual}. The site is overstating the product."
        )
    else:
        assert actual == stated, (
            f"claim {claim_id!r} says {stated!r}, but the repo derives {actual!r}. "
            "Update site/claims.json and the page copy together."
        )


# --------------------------------------------------------------------------
# The page must actually be wired to those claims.
#
# Verifying claims.json against the repo proves nothing on its own: an empty
# claims file passes every check above while the page prints whatever it likes.
# These tests bind the rendered copy to the declared claim.
# --------------------------------------------------------------------------

CLAIM_TAG = re.compile(r'data-claim="([^"]+)"[^>]*>([^<]*)<')


def tagged_claims(html):
    """Map every data-claim id in a page to the text it renders."""
    return {cid: text.strip() for cid, text in CLAIM_TAG.findall(html)}


@pytest.mark.parametrize("locale", sorted(LOCALES))
def test_locale_page_exists(locale):
    path = LOCALES[locale]
    assert path.exists(), f"the {locale} page is missing at {path.relative_to(REPO)}"


@pytest.mark.parametrize("locale", sorted(LOCALES))
def test_page_prints_no_untraced_claim(locale):
    html = LOCALES[locale].read_text(encoding="utf-8")
    claims = load_claims()
    tagged = tagged_claims(html)

    assert tagged, (
        f"the {locale} page tags no claims at all. Every hard number on the page "
        'carries data-claim="<id>" so this suite can trace it back to the repo.'
    )

    unknown = sorted(set(tagged) - set(claims))
    assert not unknown, (
        f"the {locale} page cites claims that site/claims.json does not define: {unknown}"
    )

    for cid, rendered in sorted(tagged.items()):
        claim = claims[cid]
        expected = f"{claim['value']}+" if claim.get("compare") == "gte" else str(claim["value"])
        assert rendered == expected, (
            f"the {locale} page renders {rendered!r} for claim {cid!r}, but the claim "
            f"says {expected!r}."
        )


def test_no_claim_goes_unused():
    """A claim nothing renders is a number nobody is checking against the page."""
    claims = set(load_claims())
    used = set()
    for path in LOCALES.values():
        if path.exists():
            used |= set(tagged_claims(path.read_text(encoding="utf-8")))

    orphans = sorted(claims - used)
    assert not orphans, (
        f"site/claims.json defines claims no page renders: {orphans}. Either put them "
        "on the page or drop them -- a verified claim nobody shows is not a claim."
    )


# Anything the browser must fetch to render the page. Hyperlinks are excluded on
# purpose: <a href="https://github.com/..."> is the point of the page, not a
# third-party dependency.
SUBRESOURCE = re.compile(
    r'(?:<link\b[^>]*\bhref|<(?:script|img|iframe|source|video|audio)\b[^>]*\bsrc)="([^"]+)"',
    re.IGNORECASE,
)
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\")]+)", re.IGNORECASE)


@pytest.mark.parametrize("locale", sorted(LOCALES))
def test_page_fetches_nothing_from_a_third_party_host(locale):
    """The site must render with no request leaving our own origin.

    Fonts are self-hosted for this reason, and the stylesheet says so. A CDN
    <link> added later would silently break that promise: the page still looks
    right in the browser of whoever added it, so nothing surfaces the change.
    """
    html = LOCALES[locale].read_text(encoding="utf-8")
    external = [
        ref
        for ref in SUBRESOURCE.findall(html)
        if ref.startswith(("http://", "https://", "//"))
    ]
    assert not external, (
        f"the {locale} page fetches subresources from another origin: {external}. "
        "Everything the page needs to render ships in this repo."
    )


def test_stylesheets_fetch_nothing_from_a_third_party_host():
    for css in sorted((SITE / "assets").glob("*.css")):
        external = [
            ref
            for ref in CSS_URL.findall(css.read_text(encoding="utf-8"))
            if ref.startswith(("http://", "https://", "//"))
        ]
        assert not external, f"{css.name} fetches from another origin: {external}"


@pytest.mark.parametrize("locale", sorted(LOCALES))
def test_page_ships_no_script(locale):
    """site/vercel.json serves the page under script-src 'none'.

    That header is a promise the pages have to keep. A script added later would
    be silently blocked in production while still working in a local file
    preview, which is the worst way to find out.
    """
    html = LOCALES[locale].read_text(encoding="utf-8")
    assert "<script" not in html.lower(), (
        f"the {locale} page contains a <script>, but the site is served under "
        "script-src 'none' -- it would be blocked in production. Either the page "
        "drops the script or site/vercel.json stops promising there isn't one."
    )


def test_both_locales_inline_the_same_diagram():
    """The graph is inlined per page so it inherits the theme tokens.

    Inlining means two copies, and two copies drift. If the diagram changes,
    it changes in both places or this fails.
    """
    svgs = {}
    for locale, path in LOCALES.items():
        if not path.exists():
            continue
        html = path.read_text(encoding="utf-8")
        # The favicon is an inline SVG inside a data: URI. It is an attribute
        # value, not a document node, so drop those before looking for the diagram.
        html = re.sub(r'data:image/svg\+xml,[^"\']*', "", html)
        found = re.findall(r"<svg\b.*?</svg>", html, re.DOTALL)
        assert len(found) == 1, f"the {locale} page has {len(found)} inline SVGs, expected 1"
        # The aria-label is deliberately translated; the geometry is not.
        svgs[locale] = re.sub(r'\saria-label="[^"]*"', "", found[0])

    distinct = set(svgs.values())
    assert len(distinct) == 1, (
        "the inline diagram has drifted between locales: "
        f"{sorted(svgs)} do not share identical markup."
    )


def test_locales_assert_the_same_facts():
    """Translation is where a stale number survives: one locale gets updated, one doesn't."""
    per_locale = {
        locale: tagged_claims(path.read_text(encoding="utf-8"))
        for locale, path in LOCALES.items()
        if path.exists()
    }
    if len(per_locale) < 2:
        pytest.fail(f"expected every locale in {sorted(LOCALES)} to exist, found {sorted(per_locale)}")

    reference_locale, reference = sorted(per_locale.items())[0]
    for locale, tagged in sorted(per_locale.items())[1:]:
        assert set(tagged) == set(reference), (
            f"the {locale} page and the {reference_locale} page cite different claims. "
            f"only in {locale}: {sorted(set(tagged) - set(reference))}; "
            f"only in {reference_locale}: {sorted(set(reference) - set(tagged))}"
        )
