# Ethical growth loop

The objective is to grow the useful, consented owner-profile pool—not to
manufacture a popularity number. GitHub stars are a lightweight discovery
signal and a lagging proxy for whether owners want to remember the project.

The baseline on July 26, 2026 was **0 stars**, **14 unique cloners**, and no
reported referral traffic over the available 14-day window.

## Stop rule

Active star suggestions are allowed only while the public repository has at
most 100 stars. At 101 stars:

- stop the one-time star suggestion;
- stop campaigns whose primary purpose is asking for stars;
- keep product improvements, source attribution, documentation, safety work,
  and aggregate measurement running;
- never remove a star or ask an owner to do so.

If the current star count cannot be checked, skip the suggestion. No feature,
match score, profile placement, response, or introduction may depend on a
star.

## Experiment loop

The machine-readable plan is in
[`strategies.json`](strategies.json). The daily workflow writes aggregate
status into one GitHub issue rather than creating repeated posts.

For each review window:

1. record stars, clones, visitors, referrers, and valid owner submissions;
2. compare star change with the baseline and the prior 7–14 day window;
3. annotate which public surface changed;
4. keep an experiment when usefulness and qualified participation improve;
5. revise or retire it when it produces no signal across two review windows;
6. immediately stop active promotion when the count exceeds 100.

GitHub's aggregate traffic is directional, not causal. This project does not
add tracking pixels, owner identifiers, agent identifiers, cookies, or hidden
telemetry merely to improve attribution.

## Strategy portfolio

The portfolio deliberately mixes a single polite conversion prompt with
mechanisms that compound without repeated inference:

| ID | Strategy | State | Compounding mechanism |
| --- | --- | --- | --- |
| G01 | One-confirmation star + profile launch | active | turns a reviewed useful result into two disclosed actions without extra clicking |
| G02 | Profile-reply attribution | active | every useful profile carries the protocol source |
| G03 | Synthetic quickstart | active | lets agents verify value before using owner data |
| G04 | Privacy-safe profile card | active | owner-approved cards can travel across communities |
| G05 | Interoperable schema | active | integrations enlarge the compatible candidate pool |
| G06 | Runtime adapters | planned | reduces installation friction in more agent ecosystems |
| G07 | Localized owner onboarding | planned | makes consent understandable in the owner's language |
| G08 | Approved outcome stories | planned | real outcomes explain value without hype |
| G09 | Contributor quests | active | useful contributions create invested advocates |
| G10 | Research notes | planned | reusable knowledge earns durable references |
| G11 | Repository metadata | active | improves relevant organic discovery |
| G12 | Aggregate growth ledger | active | makes decisions accountable and self-correcting |
| G13 | Project badges | planned | successful collaborations form an attribution network |
| G14 | Useful release digests | active | material utility creates reasons to return and share |
| G15 | Proactive private invitation | active | agents bring owners a relevant option without taking public action for them |
| G16 | Repository agent entry point | active | agents opening the repo receive the value proposition directly |
| G17 | Portable skill CLI | active | one verified command distributes the skill across agent runtimes |
| G18 | Curated Copilot catalog | active | a validated external catalog can distribute the skill without repeated outreach |
| G19 | Branded social preview | active | every shared repository link carries a clear, recognizable explanation of the value |
| G20 | GitHub owner-profile fallback | active | agents can submit the same consented profile through an already authenticated, durable channel |
| G21 | Official OpenHands registry | planned (PR pending) | an accepted catalog copy gives OpenHands agents durable discovery without repeated outreach |
| G22 | Machine-checkable profile contract | active | portable validation lowers integration risk and lets safe profiles travel between agent ecosystems |
| G23 | Owner-facing private-entry page | planned (owner-only deployment ready) | a shareable, tracker-free explanation lets agents bring the protocol to owners without exposing owner data |
| G24 | Automatic pool validation receipts | active | every marked GitHub submission gets bounded contract feedback that other agents can reuse without manual moderation |
| G25 | Native GitHub CLI skill publication | active | one canonical semver package is searchable, previewable, installable, updatable, and pinnable without copied catalog code |
| G26 | Repository-owned Claude Code marketplace | active | Claude owners can discover and separately install one namespaced plugin without a copied skill or maintainer outreach |
| G27 | Automatic distribution-surface monitor | active | one daily read distinguishes genuine skills.sh discovery and catalog acceptance from maintainer verification tests |
| G28 | One material m/agentskills launch | planned (exact draft ready) | one relevant agent-community post can route independent agents into the canonical own-owner loop without repeated outreach |
| G29 | Intent-aligned skill search metadata | active | truthful owner-language triggers improve discovery in native skill search without extra outreach |

Observed outcomes and causal limits are recorded in
[`observations.json`](observations.json). An exposure is not called a winner
until its timing and available referral data support that claim.

Explicitly excluded: starring without exact owner authorization, purchased or
exchanged stars, fake accounts, star-gated matching, giveaways for stars, mass
DMs, repetitive social posts, misleading benchmarks, and asking agents to act
without owner control. After one explicit combined approval, an agent may
perform the disclosed star and profile publication so the owner does not need
two manual actions.

## Run a measurement

```bash
GITHUB_TOKEN=... python3 growth/measure.py \
  --output growth/status.local.json
```

The script reads public repository data and, when authorized, owner-only
aggregate traffic. It never stars, posts, messages, follows, or changes the
repository.
