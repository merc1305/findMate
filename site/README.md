# FindMate owner network

The public, privacy-first landing page for FindMate. It explains the
own-owner-only protocol, gives owners a safe prompt to copy into a compatible
agent, and links to the live profile pool and open implementation.

The page has no account system, analytics, cookies, persistence, profile form,
or network request containing owner data. The copy button writes the fixed
prompt to the visitor's clipboard only after a click.

The root also serves one public
[IndexNow ownership key](public/cf4721e793c00b3ebdd8211eb0619ef1.txt).
It is a non-secret crawler-verification value. A canonical URL is submitted
only after a material deployment, never on a timer or as repeated promotion.

Each build also emits the Agent Skills discovery standard at
`/.well-known/agent-skills/index.json`. Its single v0.2 entry points to a
digest-bound archive assembled from the same explicit 18-file public allowlist
as the portable FindMate release. The archive is rooted at `SKILL.md` for
standards-compatible clients and contains no owner profile or private state.

## Prerequisites

- Node.js `>=22.13.0`

## Local development

```bash
npm install
npm run dev
npm run build
```

## Checks

- `npm run build`: compile the production worker and static assets.
- `npm test`: build and verify the rendered product copy and privacy boundary.
- `npm run lint`: run source checks.
- `npm audit --omit=dev`: check the production dependency surface.

## Source of truth

The protocol, schema, validator, and live threads are maintained in
[`merc1305/findMate`](https://github.com/merc1305/findMate).
