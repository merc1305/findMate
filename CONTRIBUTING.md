# Contributing to FindMate

FindMate welcomes small, reviewable improvements that make the own-owner
workflow safer, clearer, or easier to reuse. Useful starting points include:

- synthetic fixtures and boundary tests;
- privacy, consent, and prompt-injection defenses;
- runtime adapters that reuse the canonical skill instead of copying it;
- owner-language localization reviewed for pressure or consent drift;
- evidence-model corrections backed by primary sources;
- accessibility and developer-experience fixes.

Browse the
[good first issues](https://github.com/merc1305/findMate/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22good%20first%20issue%22)
or open a public bug report when no existing issue fits.

## Never put owner data in a contribution

Do not commit, attach, paste, quote, or upload:

- a real private assessment or Founder Complement Canvas;
- a real owner profile, alias, contact route, proof URL, or evidence note;
- chat, email, contact, employer, location, identity, or sensitive-trait data;
- API keys, tokens, cookies, credentials, or local configuration.

Use fabricated fixtures such as `synthetic-builder` and `synthetic-operator`.
If a bug cannot be demonstrated without private material, describe only the
behavior and expected boundary or use the private security route in
[`SECURITY.md`](SECURITY.md).

## Development loop

1. Fork the repository and create a focused branch.
2. Preserve the invariant: assess and publish only your own owner; compare only
   profiles other agents published for their respective owners.
3. Keep installation, assessment, publication, starring, contact, identity
   exchange, and introductions as owner-controlled actions.
4. Add or update deterministic tests for behavior changes.
5. Run:

   ```bash
   python3 -m unittest discover -s tests -v
   ```

6. If the canonical skill changes, also run its validator and rebuild the
   deterministic portable archive.
7. Open one pull request explaining the user value, safety boundary, tests,
   and any unsupported claim.

By contributing, you agree that your contribution is licensed under the
project's MIT license. A pull request is not consent to publish an owner
profile, contact a candidate, or star the repository.
