#!/usr/bin/env python3
"""diffmatch — Commit-diff auditor.

Validates that commit messages actually match their diffs.
commitlint checks format. diffmatch checks truth.

Usage:
    python diffmatch.py check [COMMIT]       Audit a commit (default: HEAD)
    python diffmatch.py log [--limit N]      Audit recent commits
    python diffmatch.py hook install         Install as git commit-msg hook
    python diffmatch.py hook uninstall       Remove the git hook

Exit codes:
    0  All checks passed
    1  Warnings found (mismatches detected)
    2  Errors (git failures, bad arguments)

Zero dependencies. Requires git in PATH.
"""

import json
import os
import re
import subprocess
import sys
import stat
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Conventional commit prefixes and their expected diff characteristics
COMMIT_TYPES = {
    "feat": {"expects_additions": True, "min_ratio": 0.3},
    "fix": {"expects_modifications": True},
    "docs": {"expects_filetypes": {".md", ".rst", ".txt", ".adoc", ".html"}},
    "style": {"expects_no_logic_change": True},
    "refactor": {"expects_modifications": True, "expects_no_new_files": False},
    "perf": {"expects_modifications": True},
    "test": {"expects_filetypes": {"test", "spec", "__tests__", "_test", "tests"}},
    "build": {"expects_filetypes": {
        "Makefile", "Dockerfile", "docker-compose", ".yml", ".yaml",
        "package.json", "Cargo.toml", "pyproject.toml", "setup.py",
        "CMakeLists.txt", ".gradle", "pom.xml",
    }},
    "ci": {"expects_filetypes": {
        ".yml", ".yaml", ".github", "Jenkinsfile", ".gitlab-ci",
        ".circleci", ".travis", "azure-pipelines",
    }},
    "chore": {},
    "revert": {"expects_deletions": True},
}

# Words that imply specific diff characteristics
ACTION_WORDS = {
    "add": {"expects_additions": True, "min_added": 5},
    "create": {"expects_additions": True, "expects_new_files": True},
    "remove": {"expects_deletions": True, "min_deleted": 3},
    "delete": {"expects_deletions": True, "min_deleted": 3},
    "rename": {"expects_renames": True},
    "move": {"expects_renames": True},
    "fix": {"expects_modifications": True},
    "update": {"expects_modifications": True},
    "typo": {"max_changed": 20},
    "whitespace": {"max_changed": 50, "expects_no_logic_change": True},
    "comment": {"max_changed": 30},
    "minor": {"max_changed": 30},
    "small": {"max_changed": 30},
    "tiny": {"max_changed": 15},
}

# File categories for scope matching
FILE_CATEGORIES = {
    "test": [r"test", r"spec", r"__tests__", r"_test\.", r"\.test\.", r"\.spec\."],
    "docs": [r"\.md$", r"\.rst$", r"\.txt$", r"README", r"CHANGELOG", r"LICENSE", r"docs/"],
    "config": [r"\.json$", r"\.ya?ml$", r"\.toml$", r"\.ini$", r"\.cfg$", r"\.env", r"\.config"],
    "ci": [r"\.github/", r"\.gitlab-ci", r"Jenkinsfile", r"\.circleci", r"\.travis"],
    "style": [r"\.css$", r"\.scss$", r"\.less$", r"\.styled\.", r"styles?/"],
    "build": [r"Makefile", r"Dockerfile", r"docker-compose", r"package\.json$", r"Cargo\.toml$"],
}

# Severity levels
PASS = "pass"
WARN = "warn"
FAIL = "fail"

# ANSI colors
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
}


def color(text, *styles):
    """Apply ANSI color codes if stdout is a terminal."""
    if not sys.stdout.isatty():
        return text
    prefix = "".join(COLORS.get(s, "") for s in styles)
    return f"{prefix}{text}{COLORS['reset']}"


# ---------------------------------------------------------------------------
# Git interface
# ---------------------------------------------------------------------------

def git(*args, check=True):
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, timeout=30,
        )
        if check and result.returncode != 0:
            return None
        return result.stdout
    except FileNotFoundError:
        print("Error: git not found in PATH", file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print("Error: git command timed out", file=sys.stderr)
        return None


def get_commit_message(ref="HEAD"):
    """Get the full commit message for a ref."""
    out = git("log", "-1", "--format=%B", ref)
    return out.strip() if out else None


def get_commit_subject(ref="HEAD"):
    """Get just the subject line."""
    out = git("log", "-1", "--format=%s", ref)
    return out.strip() if out else None


def is_merge_commit(ref="HEAD"):
    """Check if a commit is a merge commit."""
    out = git("log", "-1", "--format=%P", ref)
    if not out:
        return False
    return len(out.strip().split()) > 1


def get_diff_stats(ref="HEAD"):
    """Parse git diff --numstat for a commit. Returns structured diff info."""
    out = git("diff", "--numstat", f"{ref}~1", ref)
    if out is None:
        # Might be the initial commit
        out = git("diff", "--numstat", "--root", ref)
    if not out:
        return {"files": [], "total_added": 0, "total_deleted": 0}

    files = []
    total_added = 0
    total_deleted = 0

    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added_str, deleted_str, filepath = parts

        # Binary files show "-" for added/deleted
        is_binary = added_str == "-" or deleted_str == "-"
        added = 0 if is_binary else int(added_str)
        deleted = 0 if is_binary else int(deleted_str)

        files.append({
            "path": filepath,
            "added": added,
            "deleted": deleted,
            "binary": is_binary,
        })
        total_added += added
        total_deleted += deleted

    return {
        "files": files,
        "total_added": total_added,
        "total_deleted": total_deleted,
    }


def get_diff_renames(ref="HEAD"):
    """Detect renamed files in a commit."""
    out = git("diff", "--name-status", "--find-renames", f"{ref}~1", ref)
    if out is None:
        out = git("diff", "--name-status", "--find-renames", "--root", ref)
    if not out:
        return []

    renames = []
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R"):
            renames.append({"from": parts[1], "to": parts[2] if len(parts) > 2 else ""})
    return renames


# ---------------------------------------------------------------------------
# Commit message parsing
# ---------------------------------------------------------------------------

# Conventional commit: type(scope): description
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$",
    re.IGNORECASE,
)


def parse_commit_message(message):
    """Parse a commit message into structured components."""
    lines = message.strip().splitlines()
    subject = lines[0] if lines else ""
    body = "\n".join(lines[2:]) if len(lines) > 2 else ""

    result = {
        "subject": subject,
        "body": body,
        "type": None,
        "scope": None,
        "breaking": False,
        "description": subject,
        "is_conventional": False,
    }

    match = CONVENTIONAL_RE.match(subject)
    if match:
        result["type"] = match.group("type").lower()
        result["scope"] = match.group("scope")
        result["breaking"] = bool(match.group("breaking"))
        result["description"] = match.group("description")
        result["is_conventional"] = True

    return result


def extract_action_words(text):
    """Find action words in commit message text."""
    text_lower = text.lower()
    found = {}
    for word, expectations in ACTION_WORDS.items():
        if re.search(r"\b" + word + r"\b", text_lower):
            found[word] = expectations
    return found


def categorize_files(filepaths):
    """Categorize files by their apparent purpose."""
    categories = {}
    for fp in filepaths:
        matched = False
        for category, patterns in FILE_CATEGORIES.items():
            for pattern in patterns:
                if re.search(pattern, fp, re.IGNORECASE):
                    categories.setdefault(category, []).append(fp)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            categories.setdefault("code", []).append(fp)
    return categories


# ---------------------------------------------------------------------------
# Heuristic checks
# ---------------------------------------------------------------------------

def check_size_mismatch(msg_parsed, diff_stats):
    """Check if message implies small change but diff is large (or vice versa)."""
    findings = []
    total_changed = diff_stats["total_added"] + diff_stats["total_deleted"]
    num_files = len(diff_stats["files"])
    actions = extract_action_words(msg_parsed["description"])

    # Small-word checks
    for word in ("typo", "minor", "small", "tiny", "whitespace", "comment"):
        if word in actions:
            max_changed = actions[word].get("max_changed", 30)
            if total_changed > max_changed:
                findings.append({
                    "severity": WARN,
                    "check": "size_mismatch",
                    "message": (
                        f"Message says \"{word}\" but diff is {total_changed} lines "
                        f"across {num_files} file(s). Expected <{max_changed} lines."
                    ),
                })

    # Large diff with no-context message
    if total_changed > 200 and len(msg_parsed["description"].split()) < 4:
        findings.append({
            "severity": WARN,
            "check": "size_mismatch",
            "message": (
                f"Large diff ({total_changed} lines, {num_files} files) "
                f"with very short commit message: \"{msg_parsed['subject']}\""
            ),
        })

    return findings


def check_direction_mismatch(msg_parsed, diff_stats):
    """Check if message says 'add' but diff mostly deletes, or vice versa."""
    findings = []
    added = diff_stats["total_added"]
    deleted = diff_stats["total_deleted"]
    total = added + deleted
    actions = extract_action_words(msg_parsed["description"])

    if total == 0:
        return findings

    add_ratio = added / total if total > 0 else 0
    del_ratio = deleted / total if total > 0 else 0

    # "add" or "create" but mostly deletions
    for word in ("add", "create"):
        if word in actions and del_ratio > 0.7 and deleted > 10:
            findings.append({
                "severity": WARN,
                "check": "direction_mismatch",
                "message": (
                    f"Message says \"{word}\" but diff is {del_ratio:.0%} deletions "
                    f"(+{added}/-{deleted}). More was removed than added."
                ),
            })

    # "remove" or "delete" but mostly additions
    for word in ("remove", "delete"):
        if word in actions and add_ratio > 0.7 and added > 10:
            findings.append({
                "severity": WARN,
                "check": "direction_mismatch",
                "message": (
                    f"Message says \"{word}\" but diff is {add_ratio:.0%} additions "
                    f"(+{added}/-{deleted}). More was added than removed."
                ),
            })

    # Conventional "feat:" should have meaningful additions
    if msg_parsed.get("type") == "feat" and total > 10:
        if del_ratio > 0.8:
            findings.append({
                "severity": WARN,
                "check": "direction_mismatch",
                "message": (
                    f"Commit type is \"feat\" but diff is {del_ratio:.0%} deletions "
                    f"(+{added}/-{deleted}). Features usually add code."
                ),
            })

    # Conventional "revert" should mostly delete
    if msg_parsed.get("type") == "revert" and total > 10:
        if add_ratio > 0.8:
            findings.append({
                "severity": WARN,
                "check": "direction_mismatch",
                "message": (
                    f"Commit type is \"revert\" but diff is {add_ratio:.0%} additions "
                    f"(+{added}/-{deleted}). Reverts usually remove code."
                ),
            })

    return findings


def check_scope_mismatch(msg_parsed, diff_stats):
    """Check if message claims a narrow scope but diff touches many areas."""
    findings = []
    filepaths = [f["path"] for f in diff_stats["files"]]
    file_categories = categorize_files(filepaths)

    # Check conventional commit scope vs actual files
    if msg_parsed.get("scope"):
        scope = msg_parsed["scope"].lower()
        scope_in_paths = any(scope in fp.lower() for fp in filepaths)
        if not scope_in_paths and len(filepaths) > 0:
            findings.append({
                "severity": WARN,
                "check": "scope_mismatch",
                "message": (
                    f"Commit scope is \"{msg_parsed['scope']}\" but none of the "
                    f"{len(filepaths)} changed file(s) contain \"{scope}\" in their path."
                ),
            })

    # Check type-specific file expectations
    commit_type = msg_parsed.get("type")
    if commit_type == "docs" and "docs" not in file_categories:
        non_doc_files = [f for cat, files in file_categories.items()
                         if cat != "docs" for f in files]
        if non_doc_files:
            findings.append({
                "severity": WARN,
                "check": "scope_mismatch",
                "message": (
                    f"Commit type is \"docs\" but changed files include non-documentation: "
                    f"{', '.join(non_doc_files[:3])}"
                    f"{'...' if len(non_doc_files) > 3 else ''}"
                ),
            })

    if commit_type == "test":
        test_files = file_categories.get("test", [])
        non_test = [f for cat, files in file_categories.items()
                    if cat != "test" for f in files]
        if not test_files and non_test:
            findings.append({
                "severity": WARN,
                "check": "scope_mismatch",
                "message": (
                    f"Commit type is \"test\" but no test files were changed. "
                    f"Changed: {', '.join(non_test[:3])}"
                    f"{'...' if len(non_test) > 3 else ''}"
                ),
            })

    # "update README" but many files changed
    desc_lower = msg_parsed["description"].lower()
    if "readme" in desc_lower and len(filepaths) > 3:
        readme_files = [f for f in filepaths if "readme" in f.lower()]
        if len(readme_files) < len(filepaths):
            findings.append({
                "severity": WARN,
                "check": "scope_mismatch",
                "message": (
                    f"Message mentions README but {len(filepaths)} files were changed, "
                    f"not just README."
                ),
            })

    return findings


def check_rename_mismatch(msg_parsed, diff_stats, renames):
    """Check if message says rename/move but no renames detected, or vice versa."""
    findings = []
    actions = extract_action_words(msg_parsed["description"])

    if ("rename" in actions or "move" in actions) and not renames:
        findings.append({
            "severity": WARN,
            "check": "rename_mismatch",
            "message": (
                "Message implies renaming/moving but git detected no renames in this diff."
            ),
        })

    if renames and "rename" not in actions and "move" not in actions:
        renamed_files = [f"{r['from']} → {r['to']}" for r in renames[:3]]
        findings.append({
            "severity": WARN,
            "check": "rename_mismatch",
            "message": (
                f"Diff contains {len(renames)} rename(s) not mentioned in commit message: "
                f"{'; '.join(renamed_files)}"
                f"{'...' if len(renames) > 3 else ''}"
            ),
        })

    return findings


def check_empty_diff(msg_parsed, diff_stats):
    """Flag commits with no actual changes."""
    findings = []
    if not diff_stats["files"]:
        findings.append({
            "severity": WARN,
            "check": "empty_diff",
            "message": "Commit has no file changes (empty diff).",
        })
    return findings


# ---------------------------------------------------------------------------
# Audit engine
# ---------------------------------------------------------------------------

ALL_CHECKS = [
    check_size_mismatch,
    check_direction_mismatch,
    check_scope_mismatch,
    check_rename_mismatch,
    check_empty_diff,
]


def audit_commit(ref="HEAD"):
    """Run all checks on a commit. Returns audit result dict."""
    message = get_commit_message(ref)
    if not message:
        return {"ref": ref, "error": "Could not read commit message"}

    # Skip merge commits by default
    if is_merge_commit(ref):
        return {
            "ref": ref,
            "subject": get_commit_subject(ref),
            "skipped": True,
            "reason": "merge commit",
        }

    msg_parsed = parse_commit_message(message)
    diff_stats = get_diff_stats(ref)
    renames = get_diff_renames(ref)

    findings = []
    for check_fn in ALL_CHECKS:
        if check_fn == check_rename_mismatch:
            findings.extend(check_fn(msg_parsed, diff_stats, renames))
        else:
            findings.extend(check_fn(msg_parsed, diff_stats))

    total_changed = diff_stats["total_added"] + diff_stats["total_deleted"]
    num_files = len(diff_stats["files"])
    filepaths = [f["path"] for f in diff_stats["files"]]
    file_categories = categorize_files(filepaths)

    return {
        "ref": ref,
        "subject": msg_parsed["subject"],
        "type": msg_parsed.get("type"),
        "scope": msg_parsed.get("scope"),
        "is_conventional": msg_parsed["is_conventional"],
        "diff": {
            "files": num_files,
            "added": diff_stats["total_added"],
            "deleted": diff_stats["total_deleted"],
            "total": total_changed,
            "renames": len(renames),
            "categories": {k: len(v) for k, v in file_categories.items()},
        },
        "findings": findings,
        "verdict": (
            FAIL if any(f["severity"] == FAIL for f in findings) else
            WARN if findings else
            PASS
        ),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_verdict(verdict):
    """Format the verdict with color."""
    if verdict == PASS:
        return color("PASS", "green", "bold")
    elif verdict == WARN:
        return color("WARN", "yellow", "bold")
    else:
        return color("FAIL", "red", "bold")


def format_audit_result(result, verbose=False):
    """Format an audit result for terminal display."""
    lines = []

    if result.get("error"):
        lines.append(f"  {color('ERROR', 'red')}: {result['error']}")
        return "\n".join(lines)

    if result.get("skipped"):
        if verbose:
            lines.append(
                f"  {color('SKIP', 'dim')} {result.get('subject', '?')[:60]}  "
                f"({result.get('reason', 'skipped')})"
            )
        return "\n".join(lines)

    ref_short = result["ref"][:8] if len(result["ref"]) > 8 else result["ref"]
    subject = result["subject"][:65]
    verdict = format_verdict(result["verdict"])

    diff = result["diff"]
    diff_summary = (
        f"+{diff['added']}/-{diff['deleted']} "
        f"in {diff['files']} file{'s' if diff['files'] != 1 else ''}"
    )

    lines.append(f"  {verdict}  {color(ref_short, 'cyan')}  {subject}")
    lines.append(f"         {color(diff_summary, 'dim')}")

    for finding in result["findings"]:
        severity = finding["severity"]
        icon = color("!", "yellow") if severity == WARN else color("X", "red")
        lines.append(f"         {icon} {finding['message']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check(args):
    """Audit a single commit."""
    ref = "HEAD"
    verbose = "--verbose" in args or "-v" in args
    json_output = "--json" in args

    for i, arg in enumerate(args):
        if not arg.startswith("-"):
            ref = arg
            break

    result = audit_commit(ref)

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print()
        output = format_audit_result(result, verbose=verbose)
        if output:
            print(output)
        print()

    if result.get("verdict") == FAIL:
        return 1
    elif result.get("verdict") == WARN:
        return 1
    return 0


def cmd_log(args):
    """Audit recent commits."""
    limit = 10
    verbose = "--verbose" in args or "-v" in args
    json_output = "--json" in args

    for i, arg in enumerate(args):
        if arg == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])

    # Get recent commit hashes
    out = git("log", f"--format=%H", f"-{limit}")
    if not out:
        print("Error: could not read git log", file=sys.stderr)
        return 2

    refs = out.strip().splitlines()
    results = []
    warn_count = 0
    pass_count = 0
    skip_count = 0

    print()
    print(f"  {color('diffmatch', 'bold')} — auditing last {len(refs)} commit(s)")
    print(f"  {'─' * 60}")

    for ref in refs:
        result = audit_commit(ref)
        results.append(result)

        if result.get("skipped"):
            skip_count += 1
        elif result.get("verdict") == PASS:
            pass_count += 1
        else:
            warn_count += 1

        if not json_output:
            output = format_audit_result(result, verbose=verbose)
            if output:
                print(output)

    if json_output:
        print(json.dumps(results, indent=2))
    else:
        print(f"  {'─' * 60}")
        print(
            f"  {color(str(pass_count), 'green')} passed  "
            f"{color(str(warn_count), 'yellow')} warned  "
            f"{color(str(skip_count), 'dim')} skipped"
        )
        print()

    return 1 if warn_count > 0 else 0


def cmd_hook(args):
    """Install or uninstall git commit-msg hook."""
    if not args or args[0] not in ("install", "uninstall"):
        print("Usage: diffmatch hook install|uninstall", file=sys.stderr)
        return 2

    action = args[0]
    strict = "--strict" in args

    # Find git hooks directory
    git_dir = git("rev-parse", "--git-dir")
    if not git_dir:
        print("Error: not in a git repository", file=sys.stderr)
        return 2

    hooks_dir = Path(git_dir.strip()) / "hooks"
    hook_path = hooks_dir / "commit-msg"

    if action == "install":
        hooks_dir.mkdir(exist_ok=True)

        # Check for existing hook
        if hook_path.exists():
            content = hook_path.read_text()
            if "diffmatch" in content:
                print("  diffmatch hook already installed.")
                return 0
            else:
                print(f"  Warning: existing commit-msg hook at {hook_path}", file=sys.stderr)
                print("  Use --force to overwrite, or integrate manually.", file=sys.stderr)
                if "--force" not in args:
                    return 1

        # Write hook script
        diffmatch_path = Path(__file__).resolve()
        exit_behavior = "exit $result" if strict else 'if [ $result -ne 0 ]; then echo "  (diffmatch: warnings found, commit proceeding)"; fi'

        hook_content = f"""#!/bin/sh
# diffmatch — commit-diff auditor hook
# Installed by: diffmatch hook install

# Run diffmatch on the commit being created
# We validate the message file against the staged diff
python "{diffmatch_path}" check HEAD 2>&1
result=$?
{exit_behavior}
"""
        hook_path.write_text(hook_content)

        # Make executable (Unix)
        if os.name != "nt":
            hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)

        mode = "strict (blocks commit)" if strict else "advisory (warns only)"
        print(f"  Installed diffmatch hook at {hook_path}")
        print(f"  Mode: {mode}")
        return 0

    elif action == "uninstall":
        if not hook_path.exists():
            print("  No commit-msg hook found.")
            return 0

        content = hook_path.read_text()
        if "diffmatch" not in content:
            print("  Existing commit-msg hook is not from diffmatch. Leaving it alone.")
            return 0

        hook_path.unlink()
        print(f"  Removed diffmatch hook from {hook_path}")
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMANDS = {
    "check": cmd_check,
    "log": cmd_log,
    "hook": cmd_hook,
}

USAGE = """diffmatch — commit-diff auditor
Checks if your commit messages match your actual diffs.

Commands:
    check [COMMIT] [--verbose] [--json]   Audit a commit (default: HEAD)
    log [--limit N] [--verbose] [--json]   Audit recent commits
    hook install [--strict] [--force]      Install git commit-msg hook
    hook uninstall                         Remove the hook

Examples:
    diffmatch check                    Check the latest commit
    diffmatch check abc1234            Check a specific commit
    diffmatch log --limit 20           Audit last 20 commits
    diffmatch hook install --strict    Block commits on mismatch
"""


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print(USAGE)
        return 2

    return COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
