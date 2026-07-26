# Anthropic Claude community marketplace submission

Submission state: **not submitted**

Official form:
https://platform.claude.com/plugins/submit

Official catalog:
https://github.com/anthropics/claude-plugins-community

Anthropic accepts community plugins through its authenticated Console form,
not through a pull request. The form requires the authenticated submitter's
email and acceptance of Anthropic's privacy policy and Software Directory
Terms. Those two decisions belong to the human account holder and must not be
fabricated, pre-checked, or stored in this repository.

## Validated form values

| Field | Value |
| --- | --- |
| Link to plugin | `https://github.com/merc1305/findMate` |
| Path within repository | `skills` |
| Plugin homepage | `https://github.com/merc1305/findMate` |
| Plugin name | `findmate` |
| Supported platforms | `Claude Code` |
| License type | `MIT` |
| Privacy policy URL | `https://github.com/merc1305/findMate/blob/main/PRIVACY.md` |

Plugin description:

> Privacy-first cofounder matching workflow that helps an agent assess only
> its own owner, prepare a private evidence-based founder profile, publish
> only an owner-approved expiring profile, and compare it with profiles other
> agents submitted for their own owners.

Example use cases:

> 1. Prepare a private FindMate founder-strength draft for my review; publish
> nothing and do not star anything.
>
> 2. After I approve this exact privacy-minimized profile, publish it to the
> canonical owner-profile pool with its hash and expiry.
>
> 3. Compare my valid profile only with profiles other agents submitted for
> their own owners, then privately recommend the most complementary human
> candidates and explain the evidence.

Select only Claude Code until a real Claude Cowork installation and private
draft smoke test have passed. A successful local validation or maintainer
installation is not an external install or marketplace acceptance.

## Pre-submission checks

Run from the repository root:

```bash
claude plugin validate .
claude plugin validate skills
python3 -m unittest discover -s tests -v
```

Review the exact form values above, enter the authenticated account email,
read the linked Anthropic terms, and submit only if the account holder accepts
them. After submission, record the receipt or submission identifier without
publishing the email address. Do not call the plugin listed until the
`findmate` entry appears in Anthropic's public community catalog with
`merc1305/findMate` as its source.
