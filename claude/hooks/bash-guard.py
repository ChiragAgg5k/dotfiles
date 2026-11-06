#!/usr/bin/env python3
"""PreToolUse hook for Bash: steer recurring agent mistakes found in the transcript audit.

1. CI polling: loops over `gh pr checks`, `gh api .../check-runs` or `pr-status`, and `gh run watch` -> deny,
   use `pr-status --wait`. One-off reads are fine.
2. Merging: `gh pr merge` (or a PUT to the merge endpoint) -> deny unless `pr-status` is green for that PR right now.
   There is no prompt: this is what makes merging without asking the user safe.
3. Heavy verification: PHP test/lint/analyse and composer install/update -> deny when another
   one is already running on the machine, or when the command fans them out in parallel.
"""
import json
import os
import re
import shlex
import subprocess
import sys

STATUS_COMMAND = re.compile(
    r'\bgh\s+(pr\s+checks|run\s+(watch|view|list)|pr\s+view\b[^|;&\n]*(statusCheckRollup|mergeStateStatus|reviewDecision)'
    r'|api\b[^|;&\n]*(check-runs|statusCheckRollup|/commits/[^/\s]+/status\b))'
    r'|\bpr-status\b'
)
POLLING = re.compile(r'\bsleep\s+\d|\buntil\b|\bwhile\b|--watch\b|\bgh\s+run\s+watch\b')
MERGE_COMMAND = re.compile(r'\bgh\s+pr\s+merge\b([^;&|\n]*)')
MERGE_ENDPOINT = re.compile(r'\bgh\s+api\b[^;&|\n]*/pulls/\S*/merge\b[^;&|\n]*')
LITERAL_ENDPOINT = re.compile(r'repos/([\w.-]+/[\w.-]+)/pulls/(\d+)/merge\b')
PUT_METHOD = re.compile(r'(-X|--method)[\s=]*PUT\b')
PR_URL = re.compile(r'https://github\.com/[\w.-]+/[\w.-]+/pull/\d+')
PR_SHORTHAND = re.compile(r'[\w.-]+/[\w.-]+#\d+')
REPOSITORY = re.compile(r'[\w.-]+/[\w.-]+')
VALUE_FLAGS = {'-t', '--subject', '-b', '--body', '-F', '--body-file', '-A', '--author-email', '--match-head-commit'}
BYPASS_FLAGS = {'--admin', '--auto'}
MERGE_OVERRIDE = re.compile(r'\bPR_MERGE_OVERRIDE=1\b')
PR_STATUS = os.path.expanduser('~/.local/bin/pr-status')
PR_STATUS_TIMEOUT_SECONDS = 150
HEAVY = re.compile(
    r'\b(phpunit|paratest|phpstan|psalm|rector|pint|php-cs-fixer|phpcs)\b'
    r'|\bcomposer\s+(install|update|require|lint|check|analyse|analyze|test|format|fix)\b'
)
PARALLEL = re.compile(r'(?<![&>])&(?!&)\s*(?:\n|;|$|done\b)|\bxargs\b[^|;\n]*-P\s*\d|(?:^|[|;&(]\s*)parallel\s')
SHELLS = {'sh', 'bash', 'zsh', 'dash', 'fish'}
RUNNING_PATTERN = r'(vendor/bin/(phpunit|paratest|phpstan|psalm|rector|pint|php-cs-fixer|phpcs)|composer (install|update|lint|check|analyse|test))'


def decide(decision: str, reason: str) -> None:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': decision,
        'permissionDecisionReason': reason,
    }}))
    sys.exit(0)


def running_heavy() -> list[str]:
    try:
        pids = subprocess.run(['pgrep', '-f', RUNNING_PATTERN], capture_output=True, text=True, timeout=3).stdout.split()
        if not pids:
            return []
        output = subprocess.run(['ps', '-o', 'pid=,comm=,args=', '-p', ','.join(pids)],
                                capture_output=True, text=True, timeout=3).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for line in output.splitlines():
        parts = line.split(None, 2)
        # Shells (agent `zsh -c` wrappers, snapshots) only mention the command; the real tool shows up as its own process.
        if len(parts) == 3 and parts[1].rsplit('/', 1)[-1].lstrip('-') not in SHELLS and 'bash-guard' not in line:
            found.append(f'{parts[0]} {parts[2]}'[:140])
    return found


def strip_strings(text: str) -> str:
    return re.sub(r'\'[^\']*\'|"(?:\\.|[^"\\])*"', "''", text)


def merge_reference(tokens: list[str]) -> str | None:
    repository = None
    target = None
    values = iter(tokens)
    for token in values:
        if token in ('-R', '--repo'):
            repository = next(values, None)
        elif token.startswith('--repo='):
            repository = token.split('=', 1)[1]
        elif token in VALUE_FLAGS:
            next(values, None)
        elif not token.startswith('-') and target is None:
            target = token
    if target and (PR_URL.fullmatch(target) or PR_SHORTHAND.fullmatch(target)):
        return target
    if target and target.isdigit() and repository and REPOSITORY.fullmatch(repository):
        return f'{repository}#{target}'
    return None


def check_merges(code: str) -> None:
    references = []
    for match in MERGE_COMMAND.finditer(code):
        try:
            tokens = shlex.split(match.group(1))
        except ValueError:
            tokens = []
        if '--disable-auto' in tokens:
            continue
        bypass = BYPASS_FLAGS.intersection(tokens)
        if bypass:
            decide('deny', f"`gh pr merge {' '.join(sorted(bypass))}` skips the merge checks. Only if the user told you to for this "
                           'specific PR, prefix the command with PR_MERGE_OVERRIDE=1.')
        references.append(merge_reference(tokens))
    for match in MERGE_ENDPOINT.finditer(code):
        if PUT_METHOD.search(match.group(0)):
            literal = LITERAL_ENDPOINT.search(match.group(0))
            references.append(f'{literal.group(1)}#{literal.group(2)}' if literal else None)
    if not references:
        return
    if None in references:
        decide('deny', 'Cannot tell which PR this merges, so `pr-status` cannot check it. Write a literal target with no shell '
                       'variables: `gh pr merge <url>` or `gh pr merge <number> -R owner/repo`.')
    try:
        result = subprocess.run([PR_STATUS, *references, '--brief'], capture_output=True, text=True, timeout=PR_STATUS_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as error:
        decide('deny', f'Could not verify this merge with pr-status: {error}')
    if result.returncode != 0:
        decide('deny', 'Not merging: pr-status is not green for the current head.\n' + (result.stdout or result.stderr).strip() +
                       '\nFix it, or wait with `pr-status <pr> --wait` in the background. Use PR_MERGE_OVERRIDE=1 only if the user '
                       'told you to merge this specific PR anyway.')


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if payload.get('tool_name') != 'Bash':
        return
    command = (payload.get('tool_input') or {}).get('command', '')
    background = bool((payload.get('tool_input') or {}).get('run_in_background'))

    # Heredoc bodies and quoted strings only mention tools (scripts, commit messages, grep patterns); don't treat them as runs.
    code = re.sub(r'<<-?\s*[\'"]?(\w+)[\'"]?.*?\n.*?\n\s*\1\b', '', command, flags=re.S)
    if not MERGE_OVERRIDE.search(command):
        # Keep plain quoted targets ("owner/repo") readable; anything else in quotes could be a variable or just prose.
        check_merges(strip_strings(re.sub(r'([\'"])([\w./:#-]+)\1', r'\2', code)))
    code = strip_strings(code)

    status = STATUS_COMMAND.search(code)
    run_only = bool(status) and status.group(0).startswith('gh run') and not re.search(r'\bgh\s+pr\s', code)
    if status and POLLING.search(code) and not (run_only and background):
        decide('deny', 'Don\'t poll CI by hand. Run `pr-status <pr> --wait` with run_in_background: it exits on the first failure, '
                       'green, new review thread, or a newer push. One-off reads are fine, and `pr-status <pr> --brief` gives just '
                       'the verdict. To wait on a non-PR workflow run (release, deploy), poll `gh run list/view` with run_in_background.')

    if HEAVY.search(code):
        if PARALLEL.search(code):
            decide('deny', 'Do not run PHP tests/lint/analysis or composer install/update in parallel (machine load hit 60-70). '
                           'Run them one at a time, or push and let GitHub CI verify (`pr-status <pr> --wait`).')
        others = running_heavy()
        if others:
            decide('deny', 'Another heavy verification is already running on this machine:\n  ' + '\n  '.join(others[:5]) +
                           '\nWait for it to finish (or push and let CI verify with `pr-status`). Never run these concurrently.')


if __name__ == '__main__':
    main()
