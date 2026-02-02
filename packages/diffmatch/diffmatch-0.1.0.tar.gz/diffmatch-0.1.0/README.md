# diffmatch

**commitlint checks format. diffmatch checks truth.**

diffmatch audits git commits to verify that commit messages actually match their diffs. It catches the lies we all tell in commit messages.

```
$ diffmatch log --limit 5

  diffmatch — auditing last 5 commit(s)
  ────────────────────────────────────────────────────────────
  PASS  a1b2c3d4  feat: add user authentication module
         +342/-12 in 8 files
  WARN  e5f6g7h8  fix typo in README
         +89/-34 in 6 files
         ! Message says "typo" but diff is 123 lines across 6 file(s). Expected <20 lines.
  WARN  i9j0k1l2  docs: update API reference
         +45/-12 in 4 files
         ! Commit type is "docs" but changed files include non-documentation: src/api.ts, src/handler.ts...
  PASS  m3n4o5p6  refactor: simplify error handling
         +28/-45 in 3 files
  WARN  q7r8s9t0  add new payment provider
         +2/-180 in 12 files
         ! Message says "add" but diff is 99% deletions (+2/-180). More was removed than added.
  ────────────────────────────────────────────────────────────
  2 passed  3 warned  0 skipped
```

## Why

[commitlint](https://github.com/conventional-changelog/commitlint) validates that your commit messages follow a **format** (e.g., `feat:`, `fix:`, `docs:`). It has 413K weekly downloads because developers care about commit quality.

But commitlint never checks whether the message is **true**.

- "fix typo" on a 200-line refactor? commitlint says OK.
- "add feature X" when the diff only deletes code? commitlint says OK.
- "docs: update README" when you also changed 5 source files? commitlint says OK.

diffmatch catches these. It reads the actual diff and compares it to what the message claims.

## Install

```bash
pip install diffmatch
```

Requires Python 3.8+ and git.

## Usage

### Check a single commit

```bash
diffmatch check              # Check HEAD
diffmatch check abc1234      # Check specific commit
diffmatch check --json       # JSON output for CI
```

### Audit recent history

```bash
diffmatch log                # Last 10 commits
diffmatch log --limit 50     # Last 50 commits
diffmatch log --verbose      # Show skipped merge commits
```

### Git hook

```bash
diffmatch hook install           # Advisory mode (warns, doesn't block)
diffmatch hook install --strict  # Strict mode (blocks commit on mismatch)
diffmatch hook uninstall         # Remove the hook
```

### pre-commit

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/diffmatch-dev/diffmatch
    rev: v0.1.0
    hooks:
      - id: diffmatch
```

## What it checks

| Check | What it catches | Example |
|-------|----------------|---------|
| **Size mismatch** | Minimizing words on large diffs | "fix typo" on 200+ line change |
| **Direction mismatch** | Add/delete claims vs. actual diff direction | "add feature" but 90% deletions |
| **Scope mismatch** | Narrow claims on broad changes | "docs: update" but source files changed |
| **Rename detection** | Unreported file renames | 78 renames not mentioned in message |
| **Empty diff** | Commits with no actual changes | Message exists but diff is empty |

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | Warnings found (mismatches detected) |
| `2` | Error (git not found, bad arguments) |

## JSON output

All commands support `--json` for CI integration:

```bash
diffmatch check --json | jq '.verdict'
```

```json
{
  "ref": "HEAD",
  "subject": "fix typo in config",
  "type": "fix",
  "is_conventional": true,
  "diff": {
    "files": 6,
    "added": 89,
    "deleted": 34,
    "total": 123,
    "renames": 0,
    "categories": {"code": 4, "config": 2}
  },
  "findings": [
    {
      "severity": "warn",
      "check": "size_mismatch",
      "message": "Message says \"typo\" but diff is 123 lines across 6 file(s). Expected <20 lines."
    }
  ],
  "verdict": "warn"
}
```

## Design principles

- **Zero dependencies.** Pure Python stdlib + git CLI. No npm, no cargo, no binary.
- **Single file.** The entire tool is one Python file. Read it, audit it, vendor it.
- **Heuristic, not AI.** Pattern matching, not vibes. Every check is deterministic and explainable.
- **Advisory by default.** Warns, doesn't block. Earn trust before enforcing.
- **Complements commitlint.** Format + truth > format alone.

## FAQ

**Won't this have false positives?**
Yes. Heuristics are imperfect. That's why the default mode is advisory (warn, don't block). Tune thresholds over time, and use `--strict` only when you trust the calibration.

**Why not just use an LLM to check commit messages?**
You could. But that requires API keys, network access, costs money, and is non-deterministic. diffmatch runs offline, instantly, for free, and gives the same answer every time.

**Does it support non-English commit messages?**
The action word matching is English-only. File type and size checks work regardless of language.

**Does it work with merge commits?**
Merge commits are skipped by default. Use `--verbose` to see them in the output.

## License

MIT
