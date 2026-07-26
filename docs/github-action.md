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
  - uses: merc1305/findMate@v1.4.0
    with:
      profile: owner-profile.public.json
```

The exact semver tag is protected and the corresponding release is immutable.
FindMate intentionally does not publish a moving `v1` tag. Callers therefore
choose when to review and adopt a new validator version.

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
