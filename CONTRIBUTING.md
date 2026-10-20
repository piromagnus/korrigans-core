# Contributing to Korrigans

Thank you for wanting to join the Pact. Korrigans is free software under the GNU Affero General Public
License v3.0 (see `LICENSE`). By contributing, you agree that your contribution is released under the same
license.

## What fits in the core

The core is the part every household shares: scripts, default agents, skills, personalities, rules,
templates and optional modules. It must stay generic.

- Nothing personal: no names, paths, projects, accounts or data of a real user. `tests/test_no_personal_data.py`
  checks this; keep it green.
- English in the core. Agents speak the user's language at run time (`language` in `korrigans.toml`).
- Python 3.10+ standard library only. A new dependency needs a strong reason and goes in a module.
- No telemetry, ever. Nothing leaves the user's machine except what their own harnesses send.
- The fixed prohibitions in `AGENTS.md` (the Rule) are never weakened: no sending, no deleting mail, no push to
  the default branch, no force push, no spending, no contact with anyone but the user.
- Anything that only some users need (a task manager, a mail client, a research library, quota tracking) is a
  module under `modules/<name>/`.

## How to contribute

1. Open an issue first for anything larger than a fix, so we can agree on the shape.
2. Work on a branch, keep commits small, and explain the why in the message.
3. Run the tests: `bash tests/run.sh`.
4. Sign off every commit (see below), then open a pull request.

## Developer Certificate of Origin

We use the Developer Certificate of Origin (DCO) instead of a contributor license agreement. Add a
`Signed-off-by` line to each commit message, with your real name and email:

```text
Signed-off-by: Jane Doe <jane@example.org>
```

`git commit -s` adds it for you. By signing off, you certify the following (DCO 1.1, from
https://developercertificate.org):

```text
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.


Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```
