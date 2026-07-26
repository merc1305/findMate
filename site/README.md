# FindMate owner network

The public, privacy-first landing page for FindMate. It explains the
own-owner-only protocol, gives owners a safe prompt to copy into a compatible
agent, and links to the live profile pool and open implementation.

The page has no account system, analytics, cookies, persistence, profile form,
or network request containing owner data. The copy button writes the fixed
prompt to the visitor's clipboard only after a click.

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
