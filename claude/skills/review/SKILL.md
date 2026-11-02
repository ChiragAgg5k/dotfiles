---
name: review
description: Thorough code review of current branch against main
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Task
---

# Code Review

Perform a thorough code review of the current branch against the base branch using the `skills:reviewer` agent.

## Workflow

### 1. Determine Base Branch

```bash
# Base is the repository's default branch (main for Appwrite repos)
BASE=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
git fetch origin "$BASE"
BASE="origin/$BASE"
```

### 2. Get Changes

```bash
# See what files changed
git diff $BASE...HEAD --name-only

# Get full diff for review
git diff $BASE...HEAD
```

### 3. Invoke the Reviewer

Use the **skills:reviewer** subagent to perform a comprehensive review:

- Pass the diff and changed files to the reviewer agent
- Request a thorough, uncompromising review

### 4. Review Focus Areas

The reviewer should examine:

**Critical Issues**
- Security vulnerabilities (injection, auth bypass, data exposure)
- Data corruption risks
- Breaking changes to public APIs

**Code Quality**
- Logic errors and edge cases
- Error handling gaps
- Resource leaks
- Race conditions

**Maintainability**
- Code clarity and readability
- Proper naming conventions
- DRY violations
- Overly complex logic

**Performance**
- N+1 queries
- Unnecessary allocations
- Missing indexes (for DB changes)
- Inefficient algorithms

**Testing**
- Behaviour changes not covered by an existing e2e test (suggest extending one, not adding new unit tests)
- Flaky test patterns

**Project Standards**
- The repo's own CLAUDE.md / AGENTS.md conventions and its formatter/linter config
- The global rules in ~/.claude/CLAUDE.md (naming, code style, smallest change)

### 5. Output Format

Provide a structured report:

```
## Review Summary
- Files reviewed: X
- Issues found: Y (X critical, Y warnings, Z suggestions)

## Critical Issues (Must Fix)
1. [file:line] Description of issue
   - Why it's critical
   - Suggested fix

## Warnings (Should Fix)
1. [file:line] Description
   - Impact
   - Suggested fix

## Suggestions (Consider)
1. [file:line] Description
   - Rationale

## Positive Notes
- Things done well
```
