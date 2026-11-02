#!/usr/bin/env python3
"""PreToolUse hook for Bash: steer recurring agent mistakes found in the transcript audit.

1. CI polling: hand-rolled `gh pr checks` / `gh run watch` / sleep loops -> deny, use `pr-status`.
2. Merging: `gh pr merge` (or the merge REST endpoint) -> ask the user every time.
3. Heavy verification: PHP test/lint/analyse and composer install/update -> deny when another
   one is already running on the machine, or when the command fans them out in parallel.
"""
import json
import re
import subprocess
import sys

STATUS_COMMAND = re.compile(r'\bgh\s+(pr\s+checks|run\s+(watch|view|list)|pr\s+view\b[^|;&\n]*(statusCheckRollup|mergeStateStatus|reviewDecision))')
POLLING = re.compile(r'\bsleep\s+\d|\buntil\b|\bwhile\b|--watch\b|\bgh\s+run\s+watch\b')
MERGE = re.compile(r'\bgh\s+pr\s+merge\b|\bgh\s+api\b[^|;&\n]*/pulls/\d+/merge\b')
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


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if payload.get('tool_name') != 'Bash':
        return
    command = (payload.get('tool_input') or {}).get('command', '')
    background = bool((payload.get('tool_input') or {}).get('run_in_background'))

    if MERGE.search(command):
        decide('ask', 'Merging needs explicit approval from the user for this PR, in this conversation. '
                      'Subagents and standing loops never merge on their own.')

    status = STATUS_COMMAND.search(command)
    run_only = not re.search(r'\bgh\s+pr\s', command)
    if status and run_only and background:
        pass  # waiting on a non-PR workflow run (release, deploy) in the background is fine
    elif status and (POLLING.search(command) or not status.group(0).startswith(('gh run view', 'gh run list'))):
        decide('deny', 'Use `pr-status` instead of hand-rolled gh polling: `pr-status <url|owner/repo#N>...` '
                       'prints head SHA, failing checks with log tails (new/infra/red-on-base), review-bot verdict on head, '
                       'unresolved threads and mergeability; exit 0 green, 1 red, 2 blocked, 3 waiting. '
                       'To wait, run `pr-status <pr> --wait` with run_in_background (exits on first failure, green, '
                       'new review thread, or a newer push). One-off `gh run view <id> --log-failed` is fine; to wait on a non-PR '
                       'workflow run (release, deploy), poll `gh run list/view` with run_in_background.')

    # Heredoc bodies and quoted strings only mention tools (scripts, commit messages); don't treat them as runs.
    code = re.sub(r'<<-?\s*[\'"]?(\w+)[\'"]?.*?\n.*?\n\s*\1\b', '', command, flags=re.S)
    code = re.sub(r'\'[^\']*\'|"(?:\\.|[^"\\])*"', "''", code)
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
