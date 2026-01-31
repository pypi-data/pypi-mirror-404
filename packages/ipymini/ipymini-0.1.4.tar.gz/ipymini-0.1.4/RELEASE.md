# Release Process Guide (Onboarding)

## Overview

We use **fastship** for releases. The key philosophy: **bump after release**. The version in the repo is always the *next* release, not the last one.

After releasing v0.0.5, immediately bump to v0.0.6. This means:
- Dev code is always ahead of released code
- No confusion about whether you're running released or dev code
- The version number tells you what's *coming*, not what *was*

---

## When to Use PRs vs Direct Commits

| Change Type | Method | Example |
|-------------|--------|---------|
| New features | `ship_pr` | Adding a new command |
| Bug fixes | `ship_pr --label bug` | Fixing a crash |
| Breaking changes | `ship_pr --label breaking` | Changing API |
| README updates | Direct commit + push | Typo fixes |
| Internal refactoring | Direct commit + push | Code cleanup |

**Rule of thumb**: If it should appear in release notes, use a PR.

---

## The Commands

### `ship_pr "title"` - Create and merge a PR

Creates branch, commits staged changes, pushes, creates PR, merges it, cleans up.

```bash
ship_pr "Add new feature"           # label: enhancement (default)
ship_pr "Fix bug" --label bug       # label: bug
ship_pr "Breaking change" --label breaking
```

### `ship_changelog` - Generate changelog

Creates/updates CHANGELOG.md from closed GitHub issues since last release.

```bash
ship_changelog
```

### `ship_release` - Full release workflow

Does everything: GitHub release, PyPI upload, version bump.

```bash
ship_release
```

### Individual commands (rarely needed)

```bash
ship_bump              # bump patch (default)
ship_bump --part 1     # bump minor
ship_bump --part 0     # bump major
ship_pypi              # build and upload to PyPI
ship_release_gh        # interactive: changelog + editor + release
```

---

## Complete Release Workflow

### Step 1: Make changes via PRs

```bash
# Make your changes, then:
ship_pr "Add feature X"
ship_pr "Fix issue Y" --label bug
```

### Step 2: Generate and review changelog

```bash
ship_changelog
```

**Review CHANGELOG.md carefully.** Edit if needed. The format should be:

```markdown
## 0.0.5

### New Features

- Feature one ([#1](url))
- Feature two ([#2](url))


## 0.0.4
```

Note: One blank line after headings, NO blank lines between list items, TWO blank lines before next version.

### Step 3: Release

```bash
ship_release
```

This runs:
1. Commits changelog, pushes, creates GitHub release
2. Uploads to PyPI
3. Bumps patch version
4. Commits and pushes "bump"

**Done.** The repo is now ready for the next dev cycle.

---

## Key Principles

1. **Slow down** - Don't rush through releases. Review changelogs carefully.
2. **Ask questions** - If unsure about the process, ask rather than assume.
3. **Fix, don't workaround** - If something is broken, fix the root cause.
4. **Version tells the future** - After release, the repo version is always the *next* release.

---

## Quick Reference

```bash
# Daily development
ship_pr "Description"              # Feature PR
ship_pr "Fix X" --label bug        # Bug fix PR

# Release day
ship_changelog                     # Generate changelog
# ... review and edit CHANGELOG.md ...
ship_release                       # Release everything
```
