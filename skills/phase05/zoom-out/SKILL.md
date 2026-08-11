---
name: zoom-out
description: "[P0.5-1 Investigate] Tell the agent to zoom out and give broader context or a higher-level perspective. Use when you're unfamiliar with a section of code or need to understand how it fits into the bigger picture."
disable-model-invocation: true
origin: matt-pocock
upstream: https://github.com/mattpocock/skills
bootcamp_module: M3.code.investigate
bootcamp_url: https://www.notion.so/Claude-34e5a7e135d2807daec1d83e41d93504
---
> **robobuilder pedagogy** (phase05)
> - **What**: Tell the agent to zoom out and give broader context or a higher-level perspective
> - **When**: see the description above for trigger keywords; details in the body below.
> - **See Also**: /robobuilder:diagnose, /robobuilder:health
> - **Bootcamp**: M3.code.investigate
> - **Origin**: Matt Pocock (mattpocock/skills, MIT)


I don't know this area of code well. Go up a layer of abstraction. Give me a map of all the relevant modules and callers, using the project's domain glossary vocabulary. If the project has no glossary, use plain module names — say which you used.

For anything larger than a handful of files, dispatch the **`codebase-explorer`** agent to build the map. That is the agent's whole job — module relationships, call graphs, key abstractions, entry points — and its own description names this Phase 0.5 workflow as where it belongs. Running it in a subagent also keeps the file-by-file reading out of the main context, which is the point of mapping before you dig.

Answer "what is this area, and what depends on it" — not "what's wrong with it". Measurement is `/robobuilder:health`, and a finding you cannot place on this map is a finding you cannot rank.
