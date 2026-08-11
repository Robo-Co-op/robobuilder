#!/usr/bin/env python3
"""
check_freeze.py — PreToolUse hook for /robobuilder:guard (Edit/Write/MultiEdit).

Blocks edits outside the directory the user froze work to.

Hook input: JSON on stdin with tool_name and tool_input.
Hook output:
  - exit 0 → allow
  - exit 2 with stderr message → block

The boundary is read from ROBOBUILDER_FREEZE_DIR, which `/robobuilder:guard`
sets when the user names a directory.

guard's frontmatter used to point at `../freeze/bin/check-freeze.sh`, in a
sibling skill directory that exists in no robobuilder repo, so this never ran.

**No boundary set means no freeze, and that is deliberate** — but it is stated
here rather than left to be inferred, because "no boundary" and "boundary that
nothing violates" produce identical silence, and this repo has shipped that
confusion repeatedly. `/robobuilder:guard` announces which of the two it is when
it turns the mode on.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PATH_KEYS = ("file_path", "notebook_path", "path")


def _targets(tool_input: dict) -> list[str]:
    out = [str(tool_input[k]) for k in PATH_KEYS if tool_input.get(k)]
    # MultiEdit-style payloads carry a list of per-file edits.
    for edit in tool_input.get("edits", []) or []:
        if isinstance(edit, dict):
            out += [str(edit[k]) for k in PATH_KEYS if edit.get(k)]
    return out


def main() -> int:
    frozen = os.environ.get("ROBOBUILDER_FREEZE_DIR", "").strip()
    if not frozen:
        return 0

    try:
        boundary = Path(frozen).expanduser().resolve()
    except OSError:
        print(
            f"guard: freeze boundary {frozen!r} could not be resolved. Blocking "
            "rather than editing outside a boundary that may or may not apply.",
            file=sys.stderr,
        )
        return 2

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        print(
            "guard: could not parse the hook payload, so the edit target was not "
            "checked against the freeze boundary. Blocking rather than assuming.",
            file=sys.stderr,
        )
        return 2

    targets = _targets(payload.get("tool_input", {}) or {})
    if not targets:
        return 0

    outside = []
    for t in targets:
        try:
            resolved = Path(t).expanduser().resolve()
        except OSError:
            outside.append(t)
            continue
        if resolved != boundary and boundary not in resolved.parents:
            outside.append(str(resolved))

    if not outside:
        return 0

    print(
        "guard blocked an edit outside the freeze boundary.\n"
        f"  boundary: {boundary}\n"
        f"  outside:  {', '.join(outside[:5])}\n"
        "\n"
        "Move the change inside the boundary, widen it with /robobuilder:guard, "
        "or turn guard off.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
