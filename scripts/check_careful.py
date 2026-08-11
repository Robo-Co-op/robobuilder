#!/usr/bin/env python3
"""
check_careful.py — PreToolUse hook for /robobuilder:guard (Bash).

Blocks destructive shell commands so the user has to confirm them deliberately
instead of watching one scroll past.

Hook input: JSON on stdin with tool_name and tool_input.
Hook output:
  - exit 0 → allow
  - exit 2 with stderr message → block

guard's frontmatter used to point at `../careful/bin/check-careful.sh`, in a
sibling skill directory that exists in no robobuilder repo. The hook therefore
never ran: guard announced "full safety mode" and enforced nothing, which is
worse than not shipping guard at all — a user who turned it on for a prod
session got a false sense of a net that was not there.

Fail closed. If this script cannot parse its input, it blocks rather than
allows: an unparseable command is exactly the case where the user wanted a
second look.
"""
from __future__ import annotations

import json
import re
import sys

# Each entry: (compiled pattern, what it would do)
DESTRUCTIVE = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+"), "recursive/forced delete"),
    (re.compile(r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)"), "force-push"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "discards uncommitted work"),
    (re.compile(r"\bgit\s+clean\b.*-[a-zA-Z]*[fd]"), "deletes untracked files"),
    (re.compile(r"\bgit\s+checkout\s+(--\s+)?\."), "discards uncommitted work"),
    (re.compile(r"\bgit\s+branch\s+-D\b"), "force-deletes a branch"),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "drops a database object"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "empties a table"),
    (re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE), "unbounded DELETE"),
    (re.compile(r"\bUPDATE\b(?!.*\bWHERE\b).*\bSET\b", re.IGNORECASE), "unbounded UPDATE"),
    (re.compile(r"\bmkfs(\.\w+)?\b"), "formats a filesystem"),
    (re.compile(r"\bdd\b.*\bof=/dev/"), "writes directly to a device"),
    (re.compile(r">\s*/dev/(sd|nvme|disk)"), "writes directly to a device"),
    (re.compile(r"\bchmod\s+(-[a-zA-Z]+\s+)*777\b"), "world-writable permissions"),
    (re.compile(r"\bkill\s+-9\s+-?1\b"), "kills every process"),
    (re.compile(r"\bshutdown\b|\breboot\b|\bhalt\b"), "powers the machine down"),
    (re.compile(r"\bdocker\s+(system\s+prune|volume\s+rm)\b"), "removes docker state"),
    (re.compile(r"\bterraform\s+destroy\b"), "destroys infrastructure"),
    (re.compile(r"\bkubectl\s+delete\b.*(--all\b|\bnamespace\b)"), "deletes cluster resources"),
    (re.compile(r"\bnpm\s+publish\b|\bcargo\s+publish\b|\btwine\s+upload\b"), "publishes a release"),
    (re.compile(r"\baws\s+s3\s+rm\b.*--recursive"), "recursive S3 delete"),
    (re.compile(r"\bgh\s+repo\s+delete\b"), "deletes a repository"),
]


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Fail closed: see module docstring.
        print(
            "guard: could not parse the hook payload, so the command was not "
            "inspected. Blocking rather than assuming it is safe.",
            file=sys.stderr,
        )
        return 2

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command.strip():
        return 0

    hits = [what for pattern, what in DESTRUCTIVE if pattern.search(command)]
    if not hits:
        return 0

    print(
        "guard blocked a destructive command.\n"
        f"  command: {command.strip()[:400]}\n"
        f"  because: {'; '.join(dict.fromkeys(hits))}\n"
        "\n"
        "guard is on, so this needs a deliberate decision rather than a reflex. "
        "If you meant it, say so and run it again, or turn guard off.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
