---
name: diff-review
description: "[P4-1 Review] Daily-driver diff review. Reviews the current branch's diff with 3 parallel subagents (code-simplifier / test-writer / security-auditor) and merges their findings into one prioritized fix list"
user-invocable: true
argument-hint: "[--base <branch>] override the target branch/commit range"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
origin: jin-custom
bootcamp_module: M3.code.review
bootcamp_url: https://www.notion.so/Claude-34e5a7e135d2807daec1d83e41d93504
---
> **robobuilder pedagogy** (phase4)
> - **What**: Daily-driver diff review — 3 parallel subagents (simplification / tests / security) merged into one prioritized fix list.
> - **When**: see the description above for trigger keywords; details in the body below.
> - **See Also**: /robobuilder:cross-review, /robobuilder:grill, /robobuilder:playbook-review-deep
> - **Bootcamp**: M3.code.review
> - **Origin**: Robo Co-op (Jin Kim)


# /diff-review — 3-Agent Parallel Review

Review the current branch's diff (vs `main`) with **subagents running in parallel**.

## Steps
1. Get an overview with `git diff main...HEAD --stat` and `git diff main...HEAD`
2. **Ask the diff whether this change renders.** Do not decide this from memory or from
   what the change felt like — run it:

   ```sh
   git diff main...HEAD --name-only \
     | grep -qE '\.(html|css|scss|sass|less|tsx|jsx|vue|svelte|astro)$' && echo RENDERS
   ```

3. Invoke the following agents **in parallel** (multiple Agent tool calls in a single message):
   - `code-simplifier` — redundancy, over-abstraction, naming
   - `test-writer` — missing test coverage
   - `security-auditor` — OWASP perspective
   - `e2e-tester` — **whenever step 2 printed `RENDERS`.** Not "if it seems worth it":
     the diff already answered. Everything above reads the change; only this one opens it.

   The condition is a fact about the diff on purpose. Asking the author whether their
   own change counts as a UI change puts the decision back with the maker, and the
   answer is reliably "not really" — which is how a review ships a verdict about a page
   nobody rendered.

4. **If `e2e-tester` fired but could not actually run** — no dev server, no reachable
   URL, no browser available — that is a result, not a non-event. Carry
   `UNVERIFIED: rendered behaviour not checked (<reason>)` into the verdict below.
   A render check that vanishes quietly is an unmeasured thing counted as a pass.

5. Merge the outputs into a **prioritized fix list** at the end:
   ```
   ## Merged verdict
   ### Must fix (before merge)
   1. ...
   ### Should fix (recommended in this PR)
   1. ...
   ### Nice to have (can defer)
   1. ...
   ### Not checked
   - UNVERIFIED: <what nobody measured, and why> — omit this heading only when it is empty
   ## One-liner: SHIP / FIX FIRST
   ```

   `SHIP` on a diff that renders, with an `UNVERIFIED` render line still standing, is a
   verdict about a page nobody opened. Say so in the one-liner rather than letting the
   heading carry it alone.

`$ARGUMENTS` can override the target branch/commit range (e.g. `--base develop`).

$ARGUMENTS
