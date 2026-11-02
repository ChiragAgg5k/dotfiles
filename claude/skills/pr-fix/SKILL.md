---
name: pr-fix
description: Fix failing CI checks on a pull request
argument-hint: <url>
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Write, Grep, Glob
---

# Fix Failing PR Checks

Fix failing CI checks on a GitHub pull request, iterating until all checks pass.

## Arguments

- `$ARGUMENTS` - PR URL, `owner/repo#N`, or number (e.g., `https://github.com/owner/repo/pull/123`)

## Workflow

### 1. Get PR Status

```bash
gh pr checkout $ARGUMENTS
pr-status $ARGUMENTS
```

`pr-status` reports, for the current head SHA, each failing check with its failing step and log tail labelled `new`, `infra` or `red-on-base`, plus review-bot findings, unresolved threads and merge conflicts. For a fuller log of one job: `gh run view <run-id> --log-failed`.

### 2. Fix Issues

For each failure:
- Identify the root cause from the log
- `infra` failures (runner, network, registry): re-run the job with `gh run rerun <run-id> --failed` instead of changing code
- `red-on-base` failures also fail on the base branch: still fix them (there are no pre-existing failures), ideally in a separate commit
- Make the smallest change that fixes it, run the repo's formatter/linter on the changed files, and commit as `fix(<scope>): <what was wrong>`

### 3. Push and Wait

```bash
git push
pr-status $ARGUMENTS --wait   # run with run_in_background: true
```

`--wait` exits at the first new failure, conflict, new review thread, all-green, or a newer push. Act on its result instead of waiting for every check. Never hand-roll `gh pr checks` or `sleep` loops.

### 4. Iterate If Needed

Repeat steps 2–3 until `pr-status` exits 0, or 3 fix attempts have not resolved the same failure (then escalate to the user with what you tried).

## Test Failure Policy

There is no such thing as a "pre-existing" test failure. If any test fails, whether it looks related to the PR or not, fix it. The task completes with all checks passing.
