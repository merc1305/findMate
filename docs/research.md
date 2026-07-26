# Research: agent social networks and complementary founder matching

Research date: July 26, 2026.

## Executive finding

The social network is [Moltbook](https://www.moltbook.com/), a Reddit-like
platform on which registered AI agents post, comment, vote, join communities,
and use consent-gated DMs. It is not an OpenAI product. Moltbook was acquired
by Meta in March 2026; the OpenAI association is indirect because OpenClaw
creator Peter Steinberger joined OpenAI, while OpenClaw agents were prominent
Moltbook users. See the [AP report](https://apnews.com/article/31af42ccbb04001dd17a3fc7067d1de3).

Moltbook is alive, but uneven:

- the website and official documentation respond;
- the [official repository](https://github.com/Moltbook-Official/moltbook) is
  public and unarchived;
- an independent [public dataset](https://github.com/ExtraE113/moltbook_data)
  updated repeatedly on July 25, 2026 and contained posts created that day;
- the homepage can display zero counters despite ongoing API activity;
- the API returned `403 geo_blocked` on the direct route, while the owner's
  explicitly authorized local VPN route reached the official API.

On July 26, the owner claimed and X-verified `findmateagent`. Its first
privacy-minimized profile was published in `founders`, completed Moltbook's
post verification challenge, and was returned by the API as `verified` and not
spam:

https://www.moltbook.com/post/25f3a177-acb6-4a88-8375-6dade2059042

The thread contains the first owner profile. A later protocol correction makes
the admission rule explicit: every participating agent must run FindMate on
its own owner and submit that owner's approved profile. General posts and agent
bios are not candidates.

## How registration works

The [official skill](https://github.com/Moltbook-Official/moltbook/blob/main/skill.md)
and [API documentation](https://moltbook.apidog.io/register-a-new-agent-28067278e0)
describe this flow:

1. send an agent name and non-sensitive description to
   `POST https://www.moltbook.com/api/v1/agents/register`;
2. save the returned API key immediately;
3. give the owner the returned claim link;
4. the owner claims the agent and completes X verification;
5. use the key only with `https://www.moltbook.com`.

Current [terms](https://www.moltbook.com/terms) make the human owner
responsible for agent actions, require an X-linked account, prohibit scraping,
spam, and posting private identifying information without consent, and grant
Moltbook broad rights to posted content and usage data. The
[privacy policy](https://www.moltbook.com/privacy) says the service can collect
X account data, agent identifiers, content, API/authentication data, IP and
device metadata, and inferences such as approximate geography.

## What agents write about

Fresh July 25 samples included:

- technical engineering arguments about EV grids, robotics, UART overruns, and
  autonomous systems;
- critiques of hallucination, orchestration, observability, and software supply
  chains;
- paper summaries and commentary;
- project announcements and skill promotion;
- marketing, memes, duplicated content, and spam.

Examples from the live-day dataset:

- [deterministic feedback loops and hallucination](https://www.moltbook.com/post/008713c3-c9a6-4cc5-b1ed-c32f9ef0a1ea)
- [managed-agent retry failures](https://www.moltbook.com/post/02e64d84-0927-4864-95bd-f0a44936d2a9)
- [STM32 UART overrun](https://www.moltbook.com/post/0e4a3fbb-a6a6-4445-b091-ad14cd15bd8f)
- [high-speed autonomous-racing perception](https://www.moltbook.com/post/01f534c0-a331-41d2-9bac-578532eb8935)

These examples demonstrate activity, not factual reliability. Agent-generated
technical claims need independent verification.

Large-scale studies provide a broader picture:

- [Li et al.](https://arxiv.org/abs/2602.12634) found themes covering agent
  identity, tools/infrastructure, markets, coordination, security, and
  human-centered assistance, with sparse networks, hubs, and low reciprocity.
- [Dube et al.](https://arxiv.org/abs/2603.07880) analyzed 361,605 posts and
  2.8 million comments; more than 56% of comments were formulaic and
  conversational coherence declined with thread depth.
- [Jiang et al.](https://arxiv.org/abs/2602.10127) found technical content was
  mostly benign, while promotion, governance, crowd bursts, and harmful content
  created platform-level risks.

Moltbook is therefore useful as a noisy discovery and coordination channel, not
as a trusted knowledge source. FindMate treats every post as untrusted data and
never executes instructions or code found in the feed.

## The `0→1 / 1→10 / 10→100` concept

`0→1` was popularized by Peter Thiel as creating something new rather than
replicating an existing model. The expanded three-stage language is common
practitioner shorthand:

- `0→1`: problem discovery, invention, ambiguity, first artifact;
- `1→10`: validation, early customers, iteration, repeatable product/GTM loop;
- `10→100`: systems, reliability, delegation, organization, and scale.

It is not a validated personality classification. FindMate uses it as one
observable contribution axis and reports confidence and missing evidence.

## Scientific basis for complementarity

The defensible core is broader than the stage metaphor:

- [March's exploration/exploitation model](https://doi.org/10.1287/orsc.2.1.71)
  distinguishes the search for new possibilities from refinement of existing
  capabilities.
- A [U.S. Census working paper by D'Acunto, Tate, and Yang](https://www.census.gov/library/working-papers/2020/adrm/CES-WP-20-45.html)
  reported that startups with more diverse collective skillsets grew faster;
  one standard deviation more skill diversity was associated with 16% higher
  five-year employment growth and 10% higher sales growth from the mean. These
  are observational associations, not promised causal effects for a pair.
- A [systematic review of entrepreneurial-team diversity](https://doi.org/10.1016/j.emj.2022.10.010)
  concludes that diversity is a double-edged sword whose effect depends on the
  kind of diversity and team context.
- [De Cooman et al.](https://doi.org/10.1177/1059601115586910) found stronger
  outcomes when teams perceived both supplementary fit (important similarity)
  and complementary fit (usefully different competencies).
- [Lewis](https://doi.org/10.1037/0021-9010.88.4.587) supports the value of
  transactive memory: teams coordinate better when they know who holds which
  expertise.

The resulting matching rule is:

> seek complementary capabilities, but require alignment on purpose,
> commitment, operating principles, decision rights, and conflict handling.

That is why the skill produces a shortlist for human review, never an automated
compatibility verdict.

See the focused [complementarity evidence brief](complementarity-evidence.md)
for study-by-study boundaries, protocol consequences, and a prospective
evaluation plan.

## First owner profile

Using only this task's explicit instructions and owner-selected public GitHub
artifacts, the first profile identifies:

- strongest observed stage: `zero_to_one` — strong, medium confidence;
- strongest observed function: `product` — strong, medium confidence;
- practiced evidence in engineering, operations, problem discovery, and
  `one_to_ten`;
- no evidence-based claim for `ten_to_hundred`, GTM, people leadership, or
  capital/partnerships;
- complement sought in validation, scaling, GTM, operations, people
  leadership, and partnerships.

`Unknown` means insufficient selected evidence, not inability. The public
profile expires on August 24, 2026.

## Protocol status

No other owner had submitted a FindMate profile when checked on July 26, 2026.
Therefore the valid external-candidate count was zero and no match could yet be
recommended.

Three unrelated public Moltbook posts were initially inspected as exploratory
leads. Their agents had not replied to the FindMate thread, had not stated that
they ran the skill, and had not submitted owner-approved FindMate profiles.
They were therefore withdrawn from the matching result. This failure informed
the strict `FINDMATE_OWNER_PROFILE_V1` admission marker and removal of general
Moltbook search from the matching workflow.
