"""Version consistency across CHANGELOG.md, plugin.json, and marketplace.json.

Three versions have to agree and nothing enforced it, so they didn't:

  - `marketplace.json` pinned `robobuilder-pro` at 1.0.0 and stayed there after
    Pro released 1.1.0, then 1.2.0. The catalog served a version that was two
    releases behind for weeks.
  - This repo shipped `health`, `ship` and `cross-review` behavior changes with
    plugin.json still reading 1.4.0 and no CHANGELOG entry, which leaves an
    installed copy with no signal that anything changed.

Pro was the only one of the three repos whose version was right, and the only
one carrying a guard like this. That is the whole argument for porting it.

The pins for `robobuilder-pro` and `robobuilder-lite` live in other
repositories and cannot be verified from here — see
`test_marketplace_cross_repo_pins_are_not_checked_here` for what that leaves
uncovered.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = ROOT / ".claude-plugin" / "marketplace.json"
CHANGELOG = ROOT / "CHANGELOG.md"

SELF = "robobuilder"


def _plugin_version() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def _marketplace_pins() -> dict[str, str]:
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    return {p["name"]: p.get("version") for p in data["plugins"]}


def test_plugin_json_version_matches_changelog_latest() -> None:
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", CHANGELOG.read_text(encoding="utf-8"), re.MULTILINE)
    assert m, "could not find a version heading in CHANGELOG.md"
    assert _plugin_version() == m.group(1), (
        f"plugin.json version {_plugin_version()!r} does not match "
        f"CHANGELOG's latest entry {m.group(1)!r}"
    )


def test_marketplace_self_pin_matches_plugin_json() -> None:
    """The catalog's entry for this repo must match this repo's own manifest."""
    pinned = _marketplace_pins().get(SELF)
    assert pinned == _plugin_version(), (
        f"marketplace.json pins {SELF} at {pinned!r} but plugin.json says "
        f"{_plugin_version()!r}"
    )


def test_marketplace_pins_every_plugin_it_lists() -> None:
    """A missing version is how a pin silently stops meaning anything."""
    unpinned = [name for name, v in _marketplace_pins().items() if not v]
    assert not unpinned, f"marketplace.json lists these plugins with no version: {unpinned}"


def test_marketplace_cross_repo_pins_are_not_checked_here() -> None:
    """Records what this suite cannot verify, so the gap stays visible.

    `robobuilder-pro` and `robobuilder-lite` are pinned here but live in other
    repositories, so nothing local can tell whether a pin matches the manifest
    it points at. That is exactly how the Pro pin went two releases stale. Until
    a release step checks it across repos, the check is manual: before merging a
    pin bump, confirm the target repo's default branch actually carries that
    version.
    """
    cross_repo = set(_marketplace_pins()) - {SELF}
    assert cross_repo == {"robobuilder-pro", "robobuilder-lite"}, (
        "the set of cross-repo pins changed; update the release checklist in this "
        f"test's docstring to cover {sorted(cross_repo)}"
    )
