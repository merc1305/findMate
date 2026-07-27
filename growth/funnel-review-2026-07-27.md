# Growth funnel review — 2026-07-27

Snapshot time: `2026-07-27T19:32:01Z`.

This review separates repository readiness from independent adoption. GitHub
traffic is aggregate and cannot identify a person, agent, installation, or
clone source.

## Current funnel

| Stage | Measured signal | Interpretation |
| --- | --- | --- |
| Discovery | 8 repository views from 4 unique visitors; 5 GitHub referrer views from 3 uniques | Real but very small visible reach |
| Clone traffic | 794 clones from 166 reported uniques | Not usable as external reach: the same window contains 307 repository-owned GitHub Actions runs, including 256 on the same day as 777 clones |
| Activation | 0 downloads for every published portable release asset | No evidence that the release archive activated an independent user |
| Pool participation | 0 external eligible owner profiles on GitHub; the last successful Moltbook read saw 6 comment nodes and 0 external own-owner markers | The matching network has no independent supply yet |
| Reuse | 0 external GitHub Action references and 0 external rendered profile-card markers | No public evidence of downstream integration |
| Advocacy | 1 current star, down from the previously observed peak of 2 | No sustained star growth |

The exact FindMate and `find-complementary-founders` queries did not produce a
FindMate result in a public search check. The landing page, sitemap, and agent
index exist, but availability is not indexing.

## What is working

- **Technical distribution works.** AAS Core merged FindMate and released the
  attributed copy in `v15.5.1`; three catalog pull requests and one directory
  integration remain open without repeat pings.
- **The product can demonstrate value without owner data.** The immutable
  `v1.7.1` release contains the renderer-checked synthetic Founder Complement
  Canvas and the local reciprocal matching demo.
- **The trust surface is complete.** The repository has protected releases,
  tests, privacy boundaries, contribution forms, a conduct policy, private
  vulnerability reporting, and 100 percent GitHub community-profile health.
- **The loop catches null results.** It reports zero profiles, zero release
  downloads, and zero integrations instead of calling posts, builds, or
  catalog copies “leads.”

These are readiness outcomes, not acquisition or matching outcomes.

## What is not working

- **Clone totals are dominated by an internal measurement confounder.** The
  project generated hundreds of its own workflow runs. A clone-to-star ratio
  would reward CI activity rather than independent use.
- **Rapid product and release iteration has not converted.** Multiple releases,
  the landing page, the synthetic preview, and community-readiness work
  produced no release downloads and no owner-profile supply.
- **Moltbook publication has not activated the protocol.** The last successful
  aggregate read found no external agent posting its own owner's marked
  profile. A later read was blocked with HTTP 403, so the current loop must say
  “unavailable,” not silently reuse a prior value.
- **The network is below minimum liquidity.** With no independent owner
  profiles, agents cannot return a real shortlist. Additional matcher polish
  does not solve that bottleneck.
- **Search discovery is not yet visible.** The owned page is not appearing for
  exact project queries, and visible GitHub traffic remains tiny.

## Decisions

1. Stop treating clones or unique cloners as external users while repository
   Actions can generate checkouts. Record the Actions count beside clone
   totals and leave `external_unique_cloners` unknown.
2. Stop rapid release churn, repeated manual growth-workflow dispatches,
   repeated Moltbook launch posts, and low-fit directory submissions. Existing
   catalog pull requests should wait for normal maintainer review without
   pings.
3. Keep one daily passive measurement. Review sooner only after a real event:
   an external profile, download, referrer, integration, contribution, catalog
   merge, or star change.
4. Run G47 as the next bounded acquisition test: publish one public IndexNow
   ownership key on the tracker-free landing site and submit the canonical URL
   once after deployment. IndexNow is only a discovery notification; it does
   not guarantee crawling, ranking, visits, profiles, or stars.
5. Judge G47 by exact-query visibility, aggregate search referrers, qualified
   own-owner submissions, release downloads, and star change. Do not add
   cookies, pixels, owner identifiers, or repeated resubmission.

## G47 execution

Sites version 12 was built from and saved against exact pushed commit
`fa7b0da14d30fbb97f9a212593ffb7a7d2d92eca`, then deployed successfully to
the existing public FindMate URL. The build serves the public IndexNow key
from the root and passed the rendered discovery test.

At `2026-07-27T19:39:42Z`, one POST containing only the canonical landing URL,
public host, public key, and key location returned HTTP `202`. Under the
IndexNow response contract, this means the URL was received and key validation
is pending. It is not proof that the key was validated or the page was crawled,
indexed, ranked, visited, used, or starred.

The current local VPN route returned HTTP `403` when independently fetching
the public Sites URL, while the Sites control plane reported the deployment
succeeded and the access mode remained public. That network-path discrepancy
is retained as an uncertainty. The submission will not be repeated merely to
turn `202` into a more favorable-looking result.

The active-promotion stop remains 101 stars. Optional starring stays a
one-time, disclosed, owner-authorized action after private value; it never
changes ranking, publication, support, or matching.

## Primary references

- [GitHub traffic API](https://docs.github.com/en/rest/metrics/traffic)
- [GitHub Actions workflow runs API](https://docs.github.com/en/rest/actions/workflow-runs)
- [IndexNow protocol documentation](https://www.indexnow.org/documentation)
- [Google Search sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
- [Public FindMate growth ledger](https://github.com/merc1305/findMate/issues/4)
