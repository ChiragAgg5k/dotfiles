#!/usr/bin/env python3
"""PreToolUse hook: enforce Conventional Commits v1.0.0 on `git commit` messages.

Reads the hook payload on stdin. If the Bash command is a `git commit` with an
inline message, the subject line must match `type(scope)?!?: description` with
a type from the Conventional Commits examples. Anything else (including the
legacy "(feat): ..." style) is denied with an explanatory reason.
Commands without an extractable message (e.g. -F file, --amend without -m,
interactive commits) are allowed through — there is nothing to validate.
"""
import json
import re
import shlex
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
SUBJECT_RE = re.compile(rf"^({TYPES})(\([^)]+\))?!?: \S.*")


def first_line(message: str) -> str:
    heredoc = re.match(r"\$\(cat\s*<<-?\s*['\"]?(\w+)['\"]?\s*\n(.*)", message, re.S)
    if heredoc:
        message = heredoc.group(2)
    for line in message.replace("\\n", "\n").split("\n"):
        if line.strip():
            return line.strip()
    return ""


def extract_subject(segment: str):
    """Subject of the first message given to this `git commit`, or None.

    Tokenises only up to the end of the commit command, so heredocs and bodies
    of later commands (python3 - <<EOF, gh pr create --body) are never read.
    """
    lexer = shlex.shlex(segment, posix=True, punctuation_chars=";&|<>")
    lexer.whitespace_split = True
    reads_stdin = False
    try:
        tokens = iter(lexer)
        for token in tokens:
            if token in (";", "&&", "||", "|", "&", "<<", "<<-", "<"):
                break
            if token in ("-m", "--message") or re.fullmatch(r"-[a-zA-Z]*m", token):
                return first_line(next(tokens, ""))
            if token.startswith("--message="):
                return first_line(token.split("=", 1)[1])
            attached = re.fullmatch(r"-[a-ln-zA-Z]*m(.+)", token, re.S)
            if attached:
                return first_line(attached.group(1))
            if token in ("-F", "--file") and next(tokens, "") == "-" or token == "--file=-":
                reads_stdin = True
    except ValueError:
        return None
    if reads_stdin:
        body = re.search(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\1\b", segment, re.S)
        if body:
            return first_line(body.group(2))
    return None


# `git commit` only where a command starts, so text that merely mentions it (a script, a PR body) is not parsed.
COMMIT_RE = re.compile(r"(?:^|[;&|\n])\s*(?:(?:sudo|env|\w+=\S*)\s+)*(git\s+commit\b)")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if data.get("tool_name") != "Bash":
        return
    cmd = data.get("tool_input", {}).get("command", "")
    commit = COMMIT_RE.search(cmd)
    if not commit:
        return
    subject = extract_subject(cmd[commit.start(1):])
    if subject is None:
        return
    if SUBJECT_RE.match(subject):
        return
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Commit subject {subject!r} is not Conventional Commits v1.0.0. "
                        f"Use `type(scope)?: description`, e.g. `feat: add url annotation` or "
                        f"`fix(alerts): render numeric value`. Allowed types: {TYPES.replace('|', ', ')}. "
                        "Parenthesized types like `(feat):` are not allowed."
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
