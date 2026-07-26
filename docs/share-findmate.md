# Share FindMate without sharing owner data

These snippets are optional attribution, not star requests. Use them only in
places the owner controls.

## Agent-to-owner invitation

```text
I found FindMate, an open workflow where agents help their own owners find
complementary human partners. It can create a private evidence-based draft
first and publishes nothing without your approval. Want me to show you the
repository or prepare the private draft?
```

## Small project badge

```markdown
[![Find a complementary project partner with FindMate](https://img.shields.io/badge/FindMate-complementary_project_partners-7B61FF)](https://github.com/merc1305/findMate)
```

[![Find a complementary project partner with FindMate](https://img.shields.io/badge/FindMate-complementary_project_partners-7B61FF)](https://github.com/merc1305/findMate)

## Profile footer

```text
Created with the owner-approved FindMate profile protocol:
https://github.com/merc1305/findMate
```

## Deterministic profile-card draft

After the owner has approved a public profile, generate a local Markdown card:

```bash
python3 skills/find-complementary-founders/scripts/profile_card.py \
  owner-profile.public.json \
  --output owner-profile.card.md
```

The card shows only the alias, strongest demonstrated vectors, complement
sought, expiry, canonical profile hash, and protocol source. It intentionally
omits the contact route and raw proof. Inspect it with the owner and obtain
separate approval for the exact card and destination before sharing it.

The same local draft can be created in a downstream GitHub workflow after the
canonical validator passes:

```yaml
- uses: merc1305/findMate@v1.6.0
  with:
    profile: owner-profile.public.json
    card-output: findmate-owner.card.md
```

This step writes only the selected workspace file. It does not commit, upload,
or publish the card. Treat a public profile's approval and approval to share
the rendered card at a named destination as separate decisions.

Do not add a legal name, direct contact detail, precise location, private
evidence, or unapproved claim to make a share more engaging. Source
attribution may remain after the repository reaches 101 stars; active star
suggestions may not.
