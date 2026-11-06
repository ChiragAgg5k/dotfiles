# Global Instructions

## General Rules

- Before using any SDK, CLI, or API, verify the current version and its actual API surface. Do NOT guess dependency versions, class names, or method signatures — check docs and package registries first.

## HTTP tooling

- Prefer `ax` (https://github.com/yusukebe/ax) over `curl`/`wget` for fetching URLs, probing websites/docs, and quick API checks. Installed at `~/.local/bin/ax`; `~/.local/bin` is usually on PATH.
- Useful flags: default report (status/ms/body); `--outline`, `--md`, `--locate`, `--row` for HTML/docs; JSON is parsed; `--body` for body only; `--headers` for full headers; `--all`/`--budget` for large responses.
- Still use `curl` for low-level HTTP (full headers/HTTP2, uploads, cookies, complex scripting/pipelines).

## Naming

- Prefer single-word names over two-word names when context makes the meaning obvious. e.g. `connections` not `backendConnections` when there's only one set of connections, `pools` not `backendPools`, `timeout` not `connectTimeout` when it's the only timeout. Drop redundant qualifiers.
- Don't abbreviate names. Use full words: `certificate` not `cert`, `connection` not `conn`, `request` not `req`, `message` not `msg`, etc. Well-known acronyms (TLS, HTTP, TCP, CA) are fine.
- Acronyms in method/function names should be camelCase: `updateMfa()` not `updateMFA()`. Uppercase acronyms break SDK generation (`create_m_f_a` instead of `create_mfa`). In non-method identifiers (constants, config keys), fully capitalise: `cacheTTL`, `parseURL`.
- Don't double up namespace in file names. e.g. `Engine/Driver.php` not `Engine/EngineDriver.php` — namespace already provides context. Put implementations in nested subdirectories (e.g. `Engine/Driver/{Postgres,MySQL,Mongo}.php`).
- REST endpoints: plural nouns (`/collections` not `/collection`), kebab-case for multi-word paths (`/acme-challenge` not `/acmeChallenge`).

## Code Style

- Never use "section header" style comments like `// ---` or `// ===` and if you see any, remove them.
- Prefer typed config objects over associative arrays/maps.
- Use readonly classes with typed constructor properties where the language supports it.
- Use constants or enums instead of magic strings.
- Don't impose arbitrary limits (max file sizes, max entries, etc.) unless there's a real technical constraint. Validate claimed sizes against actual file/container size instead.
- Full type hints on all parameters and return types. Catch errors at compile time, not runtime.
- One class/interface per file. Filename matches class name.
- Imports: alphabetical, one per statement, grouped by const/class/function.
- Single quotes for strings by default. Double quotes only when the string contains a single quote.
- Sparse updates — when updating a record, pass only changed attributes, not the full object.
- Domain-driven design — group business logic by domain. No helper files, no random global functions, no fat controllers.
- Fix violations of the above rules in the lines you change, not across the whole file — unrelated cleanup bloats the PR.

## PHP

- Singular nouns for namespaces: `Adapter` not `Adapters` — a namespace is a folder, plurality is implied.
- When extending a Utopia library in Appwrite or Cloud, use `src/Utopia` namespace: `Appwrite\Utopia\Database\Adapter\MySQL` not `Appwrite\Database\Adapter\MySQL`.
- Dependency versions: use `^` caret ranges not `~`/`*`. `"utopia-php/framework": "^0.33"` not `"0.33.*"`. Exception: `appwrite/appwrite` and `appwrite-labs/cloud` constrain `utopia-php/*` packages with `"*"`; keep that.
- First-class callable syntax: `$this->action(...)` not `[$this, 'action']`.
- Use `array_push($items, ...$new)` instead of `$items = array_merge($items, $new)` in loops — merge copies the entire array every iteration.
- Use `array_values()` after `unset()` or `array_unique()` to re-index and keep the array a list.
- `??` (null coalescing) for null/isset checks. `?:` (elvis) for falsy checks. `getenv()` never returns null, so use `?:` with it.
- Prefer `assertSame` over `assertEquals` in new PHPUnit tests — assertSame checks type and value.

## Testing

- There are no "pre-existing issues". If tests fail, fix them, regardless of when you think the issue was introduced.
- Don't add new unit tests unless I ask. Cover a fix by extending an existing e2e test (or adding an assertion to one); verify with the existing suites, CI and real end-to-end runs. This overrides any skill that says every fix needs a new test.

## Session Persistence & Autonomy

- Don't stop mid-implementation to ask if I want to review. Keep going until success criteria is reached. Unnecessary pauses are disruptive. Exception: when I say "discuss first", "don't start yet", "plan" or "just study", only investigate and propose — no edits, commits or PRs until I say go.
- Make the smallest change that fixes the problem. If a PR grows large, needs a second script/abstraction, or a bot review loop goes 2–3 rounds on edge cases, stop and simplify instead of adding more code.
- Put a fix in the lowest repo that owns the code (shared library → core service → product built on it), not in the consumer where the symptom showed up. Say which repo and why before writing it.
- Try at least 3 meaningfully different approaches before escalating to the user. A retry of the same thing doesn't count. Diagnose why it failed, then try something different.
- When a test, build, or lint command fails, fix the issue immediately in the same turn. Do not report the failure and wait for instructions — diagnose the root cause and fix it. Only escalate if the same failure persists after 3 fix attempts.
- When given a multi-step task, track progress with the task-list tool. If one step fails, fix it and continue to the next step — don't abandon the whole task or ask whether to continue.
- If context is getting long and there's remaining work, spawn a continuation agent with a detailed handoff summary: what's done, what's left, the current git state, which files were touched, and any decisions made. The continuation agent must be self-contained.
- When spawning agents for parallel work, always launch them in a single message to maximize concurrency. Never serialize independent work.
- Prefer `/loop` for tasks that require monitoring or iteration — polling for changes, iterating on review cycles. For CI and PR reviews, use `pr-status --wait` (below).
- After completing a fix or implementation, always verify by running the relevant tests/build/lint before reporting success. "I made the change" is not done — "the change passes all checks" is done.

## Pull Requests & Merging

- PR/CI/review status: always use `pr-status <url|owner/repo#N>...` (in `~/.local/bin`). It reports, for the current head SHA: failing checks with the failing step and log tail labelled `new` / `infra` / `red-on-base`, pending and unregistered checks, the review-bot verdict (approved if APPROVED on the current head or the bot's check on head is Tier S), unresolved threads and mergeability/conflicts. Exit 0 green, 1 red, 2 blocked, 3 waiting, 5 head moved. Don't hand-roll `gh pr checks`/`sleep` loops (a hook blocks them).
- To wait for CI or a review-bot re-review, run `pr-status <pr>... --wait` with `run_in_background: true`. It exits at the first new failure, conflict, new review thread, all-green, or a newer push — act on that immediately instead of waiting for every check. Never call a PR green, approved or "done" from an earlier result or a stale approval; re-run `pr-status` after every push.
- Merge without asking me once `pr-status` exits 0 for the current head: all CI green and approved. Re-run it right before merging. This applies to main sessions, subagents and background loops. Don't merge if I said to hold that PR.
- Never merge a PR (in any repo) without all CI checks passing first. No `--admin`, no `--auto` to skip checks. Wait for green CI, then merge.
- This applies especially to cross-repo dependency fixes: if a fix is in a base repo (a shared library), wait for that repo's CI to pass before merging and propagating (`composer update`) to the repos that depend on it.
- Only bypass CI checks if explicitly instructed to do so for a specific PR.
- If a PR changes anything a reviewer can see (UI, rendered docs, emails, OG cards, dashboards), verify it with Playwright MCP and put screenshots in the PR description without being asked: before and after for fixes, light and dark for UI. Name each file for what it shows, reference it as `![alt](./name.png)` in the body, and upload with `gh pr create --attach` / `gh pr edit --attach`. Never host screenshots on a branch that gets deleted, and never commit `.playwright-mcp/` or stray PNGs.

## Workflow

- When executing a loaded skill, treat each numbered step as a checklist — execute them in order, do not skip. Before running any command, verify it matches what the loaded skill specifies, not what you recall the command should be. Skills are specifications, not suggestions — except where a skill contradicts this file, which wins (e.g. the `skills@claudes` plugin's `/skills:commit` and `/skills:pr-fix` still use the `(type):` format and `gh pr checks`).
- For multi-file features and refactors, use the **`skills:orchestrator`** agent, which runs the full cycle: planner → verifier → parallel architects (worktrees) → consolidator → reviewer → verifier. Small fixes don't need it: work directly and keep the change minimal. For independent lightweight work (research, code reading), launch concurrent subagents in a single message. Heavy verification is always serial (see Multi-Agent Coordination).
- Never revert PR changes to work around missing dependencies. Add the dependency properly (e.g. as a VCS repository in `composer.json`).
- Never use shims or patch files for local dependencies. Edit source in the dependency repo, commit and push, then run the package manager update in the consuming repo.
- Format and lint before every commit. PHP: `composer lint` (Pint, PSR-12). Kotlin: ktlint. Rust: `cargo fmt` + `cargo clippy -D warnings`. JS/TS: Prettier.
- Conventional commits: `type(scope): subject` or `type: subject` — never `(type): subject`. Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`, `perf`, `build`, `ci`, `revert`. Focus on "why" not "what". Put the subject in the first `-m`; body in a second `-m` or via `-F -` with a heredoc.
- Git: don't `--amend` commits that are already pushed — add a new commit. Force-push only as `git push --force-with-lease origin <branch>`. In worktree subagents, run git as plain separate commands from the worktree root (no `cd … &&` chains with heredocs), or the command is refused.
- Never hard-wrap prose in PR/issue bodies or comments. GitHub renders these with GFM `breaks: true`, so every newline inside a paragraph becomes a `<br>` and wrapped text renders as a narrow ragged column with dead space on the right. Write one line per paragraph and let the browser wrap. Blank lines between blocks, and hard wrapping inside code fences, are fine.
- In Appwrite repos (`appwrite/appwrite`, `appwrite/console`, `appwrite/sdk-generator`), PRs target `main`. Version branches like `1.9.x` exist for release management and backports — only target one when explicitly backporting. Confirm with `gh pr list --state merged --limit 10 --json baseRefName` if unsure.
- Once work is finalised and I confirm it's good, clean up before stopping. Delete dead code, failed attempts, abandoned files, temporary branches, commented-out earlier iterations, `// TODO: remove` markers, debug logging, scratch scripts, and anything else that was only useful during the iteration. Don't leave "loose ends" or "we can migrate this later" notes in the final state — finish them. The last commit of a finished change should be ready to review as if the earlier iterations never happened.

## Multi-Agent Coordination

- For multi-file features and refactors, spawn the **orchestrator** (`subagent_type: "skills:orchestrator"`), which runs the full cycle: **planner** → **verifier** → parallel **architect** agents in worktrees → **consolidator** → **reviewer** → **verifier**. Each agent has a single responsibility.
- Never serialize work just because agents touch the same file. Worktree isolation means every agent gets its own repo copy. The consolidator merges intelligently at the end.
- Parallelise editing: if in doubt whether edit tasks are independent, they probably are — launch them in worktrees and let the consolidator sort it out.
- Parallel editing, serial verification. Never run test suites, rector, phpstan, pint, `composer install/update` or SDK generation in several worktrees/branches at once (no `&`, `xargs -P`, or parallel subagents each running them) — each run spawns its own worker pool and 5+ parallel runs saturate the machine (load 70+ on 2026-10-26). Architect subagents edit only; only the consolidator (or main session) verifies, one worktree at a time. Prefer pushing and letting GitHub CI verify (`pr-status --wait`); locally, run quick single-file checks. A hook denies a heavy command while another one is running — wait for it, don't work around it.

## Claude Code Plugin Development

- Slash commands can be skills (`skills/<name>/SKILL.md`, preferred for new ones) or legacy `commands/<name>.md`; both show up as `/name`. In an existing plugin, follow its current layout.

## UI Changes

- After any UI change, take a screenshot and analyse it to verify the result matches intent. Don't report a UI task as complete without visual confirmation. If screenshots aren't available, say so explicitly rather than assuming it looks right.
- When modifying UI composables (especially wrapping in `AnimatedVisibility`, adding/removing containers), always verify that ALL sibling elements remain visible and correctly structured. Check that section headers, dividers, and other structural elements aren't accidentally hidden.
- When making visual/UI refinements (gradients, colors, spacing, sizing), make the MINIMAL change requested. Do not proactively change related visual properties unless explicitly asked. If iterating on visual tuning, present 2-3 options with descriptions rather than guessing.

## Release Process

- Always bump version numbers (`plugin.json`, `build.gradle`, `package.json`) as part of any release or publishing workflow. Do not wait to be reminded.

## Projects

Work repos live in `~/Desktop/appwrite/<org>/<repo>`, mirroring GitHub; worktrees go in `~/Desktop/appwrite/<org>/worktrees/<repo>/<branch>` and non-repo work files in `~/Desktop/appwrite/scratch/` (rules in `~/Desktop/appwrite/README.md`). Personal projects live in `~/Desktop/personal/<name>`. Never clone into `~/Local`. Primary ecosystem is Appwrite — backend platform, cloud hosting, edge, SDKs for 11+ languages, console, database/query libraries, and supporting infrastructure (proxy, websocket, audit, cache, framework). Most backend services are PHP 8.3+ on Swoole 6. Utopia PHP framework throughout — no Laravel/Symfony.

<!-- postman-cli:installation:start -->
Postman CLI is installed on this device, and can be used for API Engineering work.
<!-- postman-cli:installation:end -->
