# Ethical growth loop

The objective is to grow the useful, consented owner-profile pool—not to
manufacture a popularity number. GitHub stars are a lightweight discovery
signal and a lagging proxy for whether owners want to remember the project.

The initial July 26, 2026 snapshot was **0 stars**, **14 reported unique
cloners**, and no reported referral traffic. A later correlation with
repository-owned GitHub Actions showed that clone totals are confounded by
workflow checkouts, so reported cloners are no longer treated as external
users. See the
[2026-07-27 funnel review](funnel-review-2026-07-27.md).

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

GitHub's aggregate traffic is directional, not causal. Repository-owned
workflow runs can themselves check out the repository, so the ledger records
that count beside clone totals and leaves the external-cloner count unknown.
This project does not add tracking pixels, owner identifiers, agent
identifiers, cookies, or hidden telemetry merely to improve attribution.

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
| G10 | Complementarity evidence brief | active | a citable primary-source summary separates defensible team evidence from stage shorthand and makes the matching model useful beyond the repository |
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
| G23 | Owner-facing private-first page | active | a public, shareable, tracker-free explanation lets agents bring the protocol to owners without exposing owner data |
| G24 | Automatic pool validation receipts | active | every marked GitHub submission gets bounded contract feedback that other agents can reuse without manual moderation |
| G25 | Native GitHub CLI skill publication | active | one canonical semver package is searchable, previewable, installable, updatable, and pinnable without copied catalog code |
| G26 | Repository-owned Claude Code marketplace | active | Claude owners can discover and separately install one namespaced plugin without a copied skill or maintainer outreach |
| G27 | Automatic distribution-surface monitor | active | bounded daily reads distinguish genuine search, directory, release, and catalog transitions from maintainer verification tests |
| G28 | One material m/agentskills launch | active | one verified, non-repeating agent-community post can route independent agents into the canonical own-owner loop without repeated outreach |
| G29 | Intent-aligned skill search metadata | active | truthful owner-language triggers improve discovery in native skill search without extra outreach |
| G30 | AAS Core community catalog | active (released in v15.5.1) | one complete attributed catalog copy provides passive agent discovery without repeated outreach; the direct pinned route is advertised only after released-catalog verification, and copied source markers remain excluded from owner-card metrics |
| G31 | Protected portable releases | active | pinned installs become safer and more reproducible when semver tags cannot move and future releases are immutable |
| G32 | Anthropic Claude community marketplace | planned (authenticated form pending) | one reviewed, SHA-pinned official community entry can create passive Claude discovery without copied outreach |
| G33 | No-install private value loop | active | a canonical-link prompt gives first-time owners private evidence-based value before any installation or public action |
| G34 | Agent-readable web discovery | active | canonical metadata, a sitemap, and a concise `/llms.txt` help search tools and agents reach the exact own-owner protocol without tracking |
| G35 | Single-comment GitHub publication | active | one approved inline profile comment removes the separate public-repository prerequisite; the loop compares aggregate inline/linked sources and current validation receipts without tracking private drafts |
| G36 | Zero-copy discovery and portable upload | active | compatible agents discover one canonical project skill after clone, while a deterministic allowlisted archive gives ChatGPT owners a reviewable upload path without copied protocol code |
| G37 | Reusable offline profile-validation action | active | downstream projects gain a one-step, exact-version contract check while public workflow references create useful attribution without profile or owner telemetry |
| G38 | Owner-controlled profile-card action | active | a validated public profile can produce one deterministic local card draft that downstream owners may separately approve and publish with protocol attribution |
| G39 | Editor-native schema discovery | planned (compatibility gate) | a future specific filename and versioned migration could enable safe IDE validation; no SchemaStore PR or V1 `$schema` mutation before independent profile uptake |
| G40 | Composable validated profile outputs | active | downstream workflows receive only the canonical public-profile hash and validated expiry after the complete offline check, without log parsing or identity-field outputs |
| G41 | Quality-scanned Agent Plugins Directory | active (provider submission open) | one canonical-source request can enter a daily machine-readable catalog after format, secret, injection, maintenance, and documentation checks; the loop distinguishes the request from a verified listing |
| G42 | Privacy-minimized canonical pool monitor | active | one bounded daily read distinguishes external own-owner submissions from protocol chatter, exposes an honestly empty pool, and alerts maintainers when a marked profile needs local validation without retaining owner-level content |
| G43 | Curated Agent Skill Index | active (PR pending) | one minimal canonical-source entry in a maintained cross-runtime collaboration category can compound discovery; the loop distinguishes an open PR from the exact upstream listing |
| G44 | Private Founder Complement Canvas | active | a deterministic mode-0600 Markdown result gives owners useful evidence, gaps, unknowns, and review steps before the pool, publication, or optional project-support decision |
| G45 | Zero-owner-data Canvas preview | active | one renderer-checked synthetic output lets agents and owners inspect the private value before supplying evidence or authorizing any action |
| G46 | Contributor-safe feedback funnel | active | a conduct policy, bounded public forms, and review checklists convert real friction into reusable improvements without collecting owner artifacts or repeating outreach |
| G47 | One-shot search-engine discovery | active | one crawler-verifiable submission of the canonical tracker-free owner page tests external discovery without repeated posts or owner telemetry |

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

The script reads public repository data, one fixed canonical Moltbook thread,
and, when authorized, owner-only aggregate traffic. Moltbook content is treated
as untrusted data and reduced to aggregate state in memory; comment text,
authors, profile URLs, and hashes are discarded. It never stars, posts,
messages, follows, or changes the repository.
