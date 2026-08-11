---
name: grill-me
description: "[P1-1 Design] Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions \"grill me\"."
origin: matt-pocock
upstream: https://github.com/mattpocock/skills
bootcamp_module: M3.code.design
bootcamp_url: https://www.notion.so/Claude-34e5a7e135d2807daec1d83e41d93504
---
> **robobuilder pedagogy** (phase1)
> - **What**: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of ...
> - **When**: see the description above for trigger keywords; details in the body below.
> - **See Also**: /robobuilder:to-prd, /robobuilder:design-an-interface
> - **Bootcamp**: M3.code.design
> - **Origin**: Matt Pocock (mattpocock/skills, MIT)


Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

When the interview is done and the design is settled, dispatch the **`design-critic`**
agent on the result before anyone builds it. It attacks a design offline from angles an
interview does not reach — an interviewer follows the branches the user is already
thinking about, and the failure modes that matter are usually the ones neither of you
raised. Its own description names this skill as what it complements.

This is the same maker-≠-checker rule as the review skills: you ran the interview, so
you are the worst judge of what it missed. A clean report costs one pass and is a real
result.
