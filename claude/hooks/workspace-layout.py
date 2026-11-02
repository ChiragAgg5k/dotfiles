#!/usr/bin/env python3
"""PreToolUse hook for Bash: keep ~/Desktop/appwrite laid out as its README says.

- `git clone` / `gh repo clone` into the workspace must land at <org>/<repo> (SDKs in sdks/<repo>,
  other owners in 3rd-party/<repo>); personal repos belong in ~/Desktop/personal.
- `git worktree add` into the workspace must land at <org>/worktrees/<repo>/<branch-slug>.
- Nothing may be cloned or added as a worktree under the retired ~/Local.
"""
import json
import os
import re
import shlex
import subprocess
import sys

HOME = os.path.expanduser('~')
WORKSPACE = os.path.join(HOME, 'Desktop', 'appwrite')
PERSONAL = os.path.join(HOME, 'Desktop', 'personal')
RETIRED = os.path.join(HOME, 'Local')
WORK_ORGS = ('appwrite', 'appwrite-labs', 'utopia-php', 'open-runtimes')
PERSONAL_OWNERS = ('ChiragAgg5k',)
SEPARATORS = {';', '&&', '||', '|', '&', '\n'}
README = '~/Desktop/appwrite/README.md'


def deny(reason: str) -> None:
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PreToolUse',
        'permissionDecision': 'deny',
        'permissionDecisionReason': reason + f' See {README}.',
    }}))
    sys.exit(0)


def segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command.replace('\n', ' ; '), posix=True, punctuation_chars=';&|')
    lexer.whitespace_split = True
    current, result = [], []
    try:
        for token in lexer:
            if token in SEPARATORS:
                result.append(current)
                current = []
            else:
                current.append(token)
    except ValueError:  # unbalanced quotes (heredoc bodies etc.): judge what parsed
        pass
    result.append(current)
    return [s for s in result if s]


def resolve(path: str, cwd: str) -> str:
    return os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))


def inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root + os.sep)


def parse_slug(text: str) -> tuple[str, str] | None:
    match = re.search(r'github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$', text) or re.fullmatch(r'([\w.-]+)/([\w.-]+?)(?:\.git)?', text)
    return (match.group(1), match.group(2)) if match else None


def home_for(owner: str, repo: str) -> str:
    if owner in PERSONAL_OWNERS:
        return os.path.join(PERSONAL, repo)
    if repo.startswith('sdk-for-'):
        return os.path.join(WORKSPACE, 'sdks', repo)
    if owner in WORK_ORGS:
        return os.path.join(WORKSPACE, owner, repo)
    return os.path.join(WORKSPACE, '3rd-party', repo)


def positionals(args: list[str], with_value: set[str]) -> tuple[list[str], dict[str, str]]:
    found, options, skip = [], {}, None
    for arg in args:
        if skip:
            options[skip] = arg
            skip = None
        elif arg == '--':
            continue
        elif arg in with_value:
            skip = arg
        elif arg.startswith('-'):
            continue
        else:
            found.append(arg)
    return found, options


def check_clone(source: str, dest: str | None, cwd: str) -> None:
    slug = parse_slug(source)
    if not slug:
        return
    target = resolve(dest or slug[1], cwd)
    expected = home_for(*slug)
    if inside(target, RETIRED):
        deny(f'~/Local is retired. Clone {slug[0]}/{slug[1]} to {expected.replace(HOME, "~")} instead.')
    if (inside(target, WORKSPACE) or inside(target, PERSONAL)) and target != expected:
        if os.path.exists(os.path.join(expected, '.git')):
            deny(f'{slug[0]}/{slug[1]} is already checked out at {expected.replace(HOME, "~")} (one checkout per repo). '
                 'Use it, or `git worktree add` from it if you need a second working copy.')
        deny(f'Clone {slug[0]}/{slug[1]} to {expected.replace(HOME, "~")}, not {target.replace(HOME, "~")}.')


def check_worktree(repo_dir: str, args: list[str], cwd: str) -> None:
    found, options = positionals(args, {'-b', '-B', '--reason'})
    if not found:
        return
    target = resolve(found[0], cwd)
    if not (inside(target, WORKSPACE) or inside(target, RETIRED)):
        return  # worktrees in /tmp, scratchpads, etc. are fine
    url = subprocess.run(['git', '-C', repo_dir, 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout.strip()
    slug = parse_slug(url)
    branch = options.get('-b') or options.get('-B') or (found[1] if len(found) > 1 else os.path.basename(target))
    branch_slug = re.sub(r'[^A-Za-z0-9._-]+', '-', branch).strip('-') or 'detached'
    if not slug or slug[0] in PERSONAL_OWNERS:
        if inside(target, RETIRED):
            deny('~/Local is retired; put this worktree next to the repo instead.')
        return
    owner = slug[0] if slug[0] in WORK_ORGS and not slug[1].startswith('sdk-for-') else None
    if owner is None:
        deny(f'{slug[0]}/{slug[1]} is read-only in this workspace (sdks/ and 3rd-party/); change the upstream instead of adding a worktree here.')
    expected_parent = os.path.join(WORKSPACE, owner, 'worktrees', slug[1])
    if os.path.dirname(target) != expected_parent:
        deny(f'Worktrees of {slug[0]}/{slug[1]} go in {expected_parent.replace(HOME, "~")}/<branch-slug>; '
             f'use {expected_parent.replace(HOME, "~")}/{branch_slug}.')


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    if payload.get('tool_name') != 'Bash':
        return
    command = (payload.get('tool_input') or {}).get('command', '')
    if not re.search(r'\b(clone|worktree)\b', command):
        return
    cwd = payload.get('cwd') or os.getcwd()
    for words in segments(command):
        if words[0] == 'cd' and len(words) > 1:
            cwd = resolve(words[1], cwd)
            continue
        if words[0] == 'gh' and words[1:3] == ['repo', 'clone']:
            found, _ = positionals(words[3:], {'-u', '--upstream-remote-name'})
            if found:
                check_clone(found[0], found[1] if len(found) > 1 else None, cwd)
            continue
        if words[0] != 'git':
            continue
        index, repo_dir = 1, cwd
        while index < len(words) and words[index].startswith('-'):
            if words[index] == '-C' and index + 1 < len(words):
                repo_dir = resolve(words[index + 1], repo_dir)
                index += 2
            elif words[index] == '-c':
                index += 2
            else:
                index += 1
        rest = words[index:]
        if rest[:1] == ['clone']:
            found, _ = positionals(rest[1:], {'-b', '--branch', '-o', '--origin', '--depth', '--reference', '-c', '--config', '--filter', '-j', '--jobs', '--separate-git-dir', '--template', '-u', '--upload-pack'})
            if found:
                check_clone(found[0], found[1] if len(found) > 1 else None, repo_dir)
        elif rest[:2] == ['worktree', 'add']:
            check_worktree(repo_dir, rest[2:], repo_dir)


if __name__ == '__main__':
    main()
