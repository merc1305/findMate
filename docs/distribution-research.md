# Agent-native distribution research

Last reviewed July 26, 2026.

## Findings turned into experiments

### Portable Agent Skills are a real distribution surface

GitHub documents Agent Skills as an open standard supported by Copilot cloud
agent, code review, CLI, app, VS Code, and JetBrains. It recognizes project
skills in `.github/skills`, `.claude/skills`, and `.agents/skills`, and
personal skills under the user's home directory.

The open `skills` CLI can discover a GitHub repository, list its skills, and
install one into supported agent runtimes. A clean test against
`merc1305/findMate` discovered exactly one skill and installed its instructions,
scripts, references, and agent metadata.

Decision: make the portable CLI the shortest install path, retain direct clone
instructions as a transparent fallback, and document the CLI's optional
anonymous telemetry rather than hiding it.

Sources:

- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- https://www.skills.sh/docs/cli
- https://github.com/openai/skills

### Agent-readable entry points can carry the value proposition

Many coding agents read a repository's `AGENTS.md` before working. A concise
entry point can explain when FindMate is relevant and send the agent to the
canonical skill without relying on a human to translate the README.

Decision: add a root `AGENTS.md` with the owner-facing invitation, own-owner
invariant, and explicit boundary against unapproved public actions.

### Discovery metadata matters

GitHub topics are a first-class discovery surface: users can browse topic
pages and search repositories by topic. FindMate now has focused topics for
agent skills, founder matching, privacy, and Moltbook, plus an accurate
description and homepage.

Source:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics

### Shared links can explain the value before the click

GitHub repositories can define a social preview image for links shared on
social platforms. GitHub recommends at least 640×320 pixels, with 1280×640 as
the best display size, and accepts PNG, JPG, or GIF files under 1 MB.

Decision: install one 1280×640, privacy-safe preview that states the use case
and owner-control boundary. Treat it as a passive conversion experiment:
compare aggregate visitors, referrers, and stars before and after installation,
without adding trackers or claiming causation from the image alone.

Source:

- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview

### A canonical GitHub issue reduces transport friction

Moltbook remains the agent-social-network surface, but its geographic and
account requirements can block an otherwise valid own-owner submission.
FindMate already had one repository issue naming the Moltbook thread and
allowing the same approved profile to be linked there.

Decision: make GitHub issue 2 a documented fallback transport for the same
`FINDMATE_OWNER_PROFILE_V1` contract. Use a hash-bound draft and one explicit
owner approval before commenting. The reader fetches only that issue and
returns marked submission metadata; it does not search GitHub for people or
treat ordinary issues as candidates.

### Aggregate attribution has a short window

GitHub exposes clones, visitors, referrers, and popular content for the last 14
days. Clone and visitor data update hourly; referrers and popular content
update daily. Traffic requires push access, so the default GitHub Actions token
may report stars while owner-only traffic remains unavailable.

Decision: preserve the dated baseline, measure stars daily in the public
ledger, and use an owner-authenticated read during review windows for traffic.
Do not store a broad personal token in repository secrets merely to populate a
dashboard.

Sources:

- https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository
- https://docs.github.com/en/rest/metrics/traffic

### Curated catalogs need evidence before outreach

Community catalogs can produce durable discovery, but at least one large
catalog explicitly asks authors not to submit brand-new, unproven skills.

Decision: do not shotgun submissions. First collect real installs, valid owner
profiles, safety results, or owner-approved outcomes; then submit a precise
entry to relevant catalogs and measure its referrer traffic.

Source:

- https://github.com/VoltAgent/awesome-agent-skills

### The official OpenHands registry is a second agent-native surface

OpenHands maintains a public extensions registry for skills and plugins loaded
by OpenHands applications and Software Agent SDK consumers. Its contributor
contract requires a reusable `SKILL.md`, marketplace metadata, generated
catalog artifacts, vendor manifests, and repository validation.

Decision: submit one catalog-safe FindMate copy in pull request 419. Preserve
the full own-owner assessment, exact-consent publication, and local-shortlist
workflow, but omit FindMate's optional star suggestion from the catalog copy.
The external contribution must earn discovery through utility and clear
attribution; profile eligibility and ranking remain independent of promotion.
Treat the submission as pending distribution until maintainers merge it.

Sources:

- https://github.com/OpenHands/extensions
- https://docs.openhands.dev/overview/skills
- https://github.com/OpenHands/extensions/pull/419

### A portable validation contract compounds across ecosystems

JSON Schema's current published specification is Draft 2020-12. A
self-describing schema gives different agent runtimes a shared structural
contract without requiring them to execute FindMate code. Structural
validation alone cannot enforce time-dependent expiry, cross-field consent
consistency, privacy patterns, or FindMate's score semantics.

Decision: publish both a canonical Draft 2020-12 profile schema and a
standard-library offline validator. Make the matcher call the full validator
automatically. A profile that travels through a card, Moltbook reply, GitHub
comment, or third-party adapter therefore keeps one structure and one canonical
SHA-256 while still requiring local safety and consent checks.

Source:

- https://json-schema.org/draft/2020-12

## Loop decisions

Keep:

- portable one-command install;
- root agent entry point;
- precise topics and repository metadata;
- approved profile attribution;
- one aggregate ledger.

Test next:

- a synthetic two-owner demo;
- an owner-approved share card;
- localization of the proactive invitation;
- a material first release;
- a branded repository social preview;
- measurement of the two existing catalog submissions after maintainer review.

Reject:

- bulk catalog PRs;
- duplicate submissions or unsolicited review requests while a catalog PR is pending;
- repeated community posts with no new utility;
- hidden install telemetry;
- storing a broad owner token in Actions;
- any install, star, profile, or contact action without owner control.
