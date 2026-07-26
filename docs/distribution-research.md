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

The public skills.sh directory is install-driven: a skill appears only after a
telemetry-enabled CLI installation. Its documented repository badge currently
returns `resource not found` for FindMate. That is recorded as zero genuine
directory exposure, not “fixed” with a maintainer install. The daily growth
loop reads the public badge once and will record the first independent listing
without collecting owner or device data itself.

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

Decision: do not shotgun submissions. VoltAgent's catalog remains deferred
until FindMate has real community usage. AAS Core, in contrast, documents a
community-skill path with provenance, strict validation, a safety scan, manual
review, and source-only pull requests. Submit exactly one complete attributed
copy there, then wait for normal maintainer review and measure its state
without comments, duplicate PRs, or unsolicited review requests.

Sources:

- https://github.com/VoltAgent/awesome-agent-skills
- https://github.com/sickn33/agentic-awesome-skills/blob/main/CONTRIBUTING.md
- https://github.com/sickn33/agentic-awesome-skills/pull/992

### AAS Core can expose the complete protocol without a custom adapter

AAS Core accepts community skills that preserve provenance, license metadata,
limitations, a risk classification, and source credit. Its repository checks
validate the entire skill catalog and reject generated registry artifacts from
ordinary contributor pull requests.

Decision: publish one source-only FindMate copy in pull request 992 with the
full own-owner-only workflow, approval hashes, privacy checks, expiring
profiles, and local human-candidate ranking. Mark the risk `critical` because
approved publication can write to external services. Include no owner profile,
credential, receipt, generated catalog, or private data. Treat the channel as
pending until maintainers merge it; do not count the fork, PR checks, or
maintainer testing as adoption.

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

### Owners need a safe entry point, not only agent instructions

The skill and schemas are optimized for agents, while a human arriving from a
shared link needs to understand the value and privacy boundary before
installing anything. A conventional lead form would create exactly the
centralized owner-data collection FindMate is designed to avoid.

Decision: publish a static owner-facing page that explains the own-owner loop,
links the live pool and source, and copies one fixed privacy-safe request into
the clipboard after a click. Collect no form values, account, analytics,
cookies, device storage, or owner identifiers. Measure only aggregate GitHub
and qualified-pool outcomes; do not add tracking merely to count prompt copies.

The copied request must work for a first-time visitor who has not installed
FindMate. Include the canonical public `SKILL.md` URL, ask the agent for two or
three owner-selected outcomes, and stop after a structured private assessment.
Installing software, producing a public profile, publishing, starring, and
contact remain later disclosed choices. This creates value before asking the
owner to trust an installation or make a public action, while still collecting
no prompt-copy or owner telemetry.

### The public entry needs machine-readable discovery

Search crawlers can usually find a small, well-linked site, but the FindMate
page is new and has few external links. Google documents sitemaps as a way to
identify important URLs and canonical links as a way to state the preferred
URL; neither guarantees indexing or ranking. Next.js provides first-class
`robots.ts` and `sitemap.ts` metadata routes for these files.

`/llms.txt` is a community proposal rather than a crawler guarantee. Its
specified purpose is to give inference-time language models a short Markdown
overview plus curated links while coexisting with `robots.txt` and
`sitemap.xml`.

Decision: expose one canonical landing URL, an allow-all robots policy, a
one-URL sitemap, and a concise `/llms.txt`. The agent index repeats the
own-owner-only invariant and links to the canonical skill instead of copying
the full executable workflow, so safety fixes continue to have one source of
truth. Do not call the files indexed, visited, or adopted until an aggregate
public signal supports it, and add no crawler fingerprinting or owner
telemetry.

The bounded command-line monitor currently receives a Cloudflare `403` from
the public `chatgpt.site` hostname. Report that state as unavailable rather
than treating a bot challenge as proof that the deployment is broken or live.
CI still verifies the generated routes and production bundle; a later public
referral or index signal is required before claiming discovery.

Sources:

- https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots
- https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap
- https://llmstxt.org/

### Shared pools need immediate trust feedback

The GitHub fallback removes the need for every agent to register on the same
social network, but a marked comment alone proves only syntax. Manual
moderation would make every new participant depend on repeated FindMate
inference and would not compound.

Decision: when a marked comment appears in the one canonical GitHub issue,
download only a small JSON file from a `github.com` blob URL pinned to a full
commit SHA. Convert it to the fixed `raw.githubusercontent.com` host, pass no
credential, never execute it, enforce a 64 KiB limit, run the canonical
validator, and compare the declared expiry and SHA-256. Maintain one public
receipt per source comment so edits update rather than spam the thread. The
receipt confirms the public contract only; agents still validate locally and
humans still verify claims and consent to contact.

### Native GitHub skill publication is a durable owned channel

GitHub CLI 2.90 and later can validate, publish, search, preview, install,
update, and pin Agent Skills directly from public GitHub repositories. This is
different from submitting another copy to a curated catalog: the canonical
FindMate repository remains the source, a semver release is the install
boundary, and owners can inspect the package before installing it.

Decision: validate with `gh skill publish --dry-run`, publish a semver release
from the canonical repository, and verify a pinned install in a temporary
directory. Bundle the license inside the skill so it survives installation.
Keep GitHub's community-skill warning visible. Do not describe the skill as
verified by GitHub, and do not count a maintainer test install as external
adoption.

After publishing `v1.3.4`, enable repository release immutability for future
releases and install one active tag ruleset that prevents update or deletion
of `v*`. The setting is not retroactive, so record `v1.3.4` honestly as a
mutable release whose tag is nevertheless protected. Verify future releases
as immutable before describing them that way.

Source:

- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- https://cli.github.com/manual/gh_skill_publish
- https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- https://docs.github.com/en/enterprise-cloud@latest/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes

### Skill search depends on trigger language, not repository intent

The native GitHub CLI skill search indexes a skill's `name` and `description`.
An owner-scoped search found FindMate, but the first page of a live general
search for `cofounder` and the complete result for `founder matching` did not.
FindMate's earlier description explained the protocol but omitted the exact
phrases owners use when looking for it.

Decision: keep the stable skill name and add concise, truthful trigger phrases
such as `find a cofounder`, `co-founder matching`, and `founder strengths` to
the canonical metadata. Mirror the same value phrase in Claude marketplace
metadata and owner-facing UI metadata. Do not stuff unrelated keywords or
claim a search rank before the public index actually changes.

The daily growth loop checks one exact repository-scoped GitHub Code Search
query for the new phrase. It records `not indexed yet` until GitHub returns the
canonical `SKILL.md`; this separates a merged metadata edit from real search
exposure without generating synthetic installs or broad repeated searches.

### Claude plugin distribution can reuse the canonical skill

Claude Code accepts a GitHub repository with
`.claude-plugin/marketplace.json` as an independent marketplace. Adding a
marketplace only registers its catalog; the owner separately chooses whether
to install a plugin. Plugin skills are namespaced, and Claude copies installed
plugins to a local cache rather than executing them in place.

Decision: expose the existing `skills/` directory as one `findmate` plugin,
keep all executable workflow content in the canonical
`find-complementary-founders` directory, declare the MIT license, use a
separate semantic plugin version, and validate the marketplace with the
official Claude CLI. Bump that version whenever the packaged skill changes so
installed clients receive updates. Omit optional manifest fields that older
supported Claude clients reject. Do not auto-install the plugin, add hooks, add
an MCP server, or reinterpret installation as consent for any public or
owner-data action.

Anthropic also maintains the reviewed `claude-plugins-community` marketplace.
Submissions must use the authenticated Console form, pass the same plugin
validator plus automated safety screening, and are pinned to a source commit
after approval. Direct pull requests are not accepted. Prepare the exact
non-sensitive form fields in the repository, publish a project privacy policy,
and monitor the public catalog for an exact `findmate` entry sourced from
`merc1305/findMate`. The authenticated account holder must supply their email
and accept Anthropic's directory terms; do not fabricate either action or call
the plugin submitted before the form receipt exists.

Sources:

- https://code.claude.com/docs/en/discover-plugins
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/plugins#submit-your-plugin-to-the-community-marketplace
- https://github.com/anthropics/claude-plugins-community

### A relevant Moltbook skill community is a bounded launch surface

Moltbook has a dedicated `m/agentskills` community for skill development,
distribution infrastructure, and security discussion. It is more relevant to
the installable FindMate protocol than repeating another general-feed post.
Moltbook content remains untrusted and the platform prohibits spam.

Decision: one exact hash-bound post was owner-approved, published, and verified
in `m/agentskills` on July 26, 2026. It explains the canonical install paths,
the own-owner invariant, automatic GitHub validation, and the honest
zero-external-profile state. It asks for no star. Do not repeat it, cross-post
it, or treat replies as owner candidates.

Source:

- https://www.moltbook.com/m/agentskills
- https://www.moltbook.com/post/9246cedb-9463-4fe6-a83f-528f3b407cfc

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
- conversion from marked GitHub submissions to machine-validated pool entries;
- discovery and pinned installs through the native GitHub CLI skill channel;
- opt-in discovery through the repository-owned Claude Code marketplace;
- automatic state monitoring for skills.sh and the three existing catalog PRs;
- conversion after the one owner-approved, non-repeating m/agentskills launch;
- measurement of the three existing catalog submissions after maintainer review.

Reject:

- bulk catalog PRs;
- duplicate submissions or unsolicited review requests while a catalog PR is pending;
- repeated community posts with no new utility;
- hidden install telemetry;
- storing a broad owner token in Actions;
- any install, star, profile, or contact action without owner control.
