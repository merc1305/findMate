# Reusable offline profile validation

FindMate exposes its canonical profile validator as a composite GitHub Action.
Another repository can use it to reject a malformed, unsafe, or expired
`FINDMATE_OWNER_PROFILE_V1` file before matching, publication, or another
owner-approved operation.

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v6
  - id: findmate
    uses: merc1305/findMate@v1.6.0
    with:
      profile: owner-profile.public.json
```

The exact semver tag is protected and the corresponding release is immutable.
FindMate intentionally does not publish a moving `v1` tag. Callers therefore
choose when to review and adopt a new validator version.

## Validated outputs

After the complete profile check passes, downstream steps can consume two
bounded outputs without parsing the validator log:

```yaml
- name: Use the validated public-profile identity
  env:
    FINDMATE_CANONICAL_SHA256: ${{ steps.findmate.outputs.canonical_sha256 }}
    FINDMATE_EXPIRES_ON: ${{ steps.findmate.outputs.expires_on }}
  run: ./use-validated-profile.sh
```

`canonical_sha256` is the lowercase SHA-256 of the deterministic canonical
public profile. `expires_on` is its validated `YYYY-MM-DD` expiry. The action
does not expose the alias, summary, evidence, contact route, or any other
profile field as an output. Treat the hash as a stable reference to the
reviewed public bytes, not as proof that a claim or identity is true.

## Optional card draft

After validation passes, the same action can write a deterministic,
privacy-minimized Markdown card:

```yaml
- uses: merc1305/findMate@v1.6.0
  with:
    profile: owner-profile.public.json
    card-output: findmate-owner.card.md
```

`card-output` is optional. When supplied, the action creates or replaces that
exact caller-selected path in the workspace. It does not commit, upload, or
publish the file. The card deliberately omits contact routes and raw evidence,
but the owner must still inspect and approve the exact card and destination
before another step publishes it.

## Security boundary

The action:

- invokes the same standard-library Python validator shipped in the Agent
  Skill;
- treats the profile path as an environment value and a quoted positional
  argument, not as shell source;
- uses `--` so a path beginning with a dash cannot become a command-line
  option;
- performs no network request and requests no write permission;
- reads the selected file and prints the validator's JSON result, including
  the canonical profile hash;
- appends only the validated canonical SHA-256 and expiry date to GitHub's
  per-step output file;
- writes only the caller-selected `card-output` path when that optional input
  is non-empty, and refuses to write through a symlink;
- fails the step when the file violates the schema, privacy rules, explicit
  consent requirements, or expiry policy.

On a self-hosted runner, the caller must provide `bash` and Python 3. Relative
paths resolve from the caller repository workspace.

Running the action is not consent to assess an owner, publish a profile, star
FindMate, contact a candidate, or exchange identities. A repository workflow
is public evidence that the validator was referenced; it is not evidence that
the workflow ran, that a file belonged to a real person, or that a match
succeeded.

## Distribution decision

GitHub documents both direct action reuse and Marketplace publication.
FindMate uses the direct `owner/repository@exact-tag` path. It is a
multi-purpose protocol repository, so it is not represented as a GitHub
Marketplace listing.

Primary GitHub documentation:

- [Create a composite action](https://docs.github.com/en/actions/tutorials/create-actions/create-a-composite-action)
- [Release and maintain actions](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/release-and-maintain-actions)
- [Publish actions in GitHub Marketplace](https://docs.github.com/en/actions/how-tos/create-and-publish-actions/publish-in-github-marketplace)
