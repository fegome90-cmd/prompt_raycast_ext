# Design Principles Plugin Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address remaining important issues from multi-agent code review to improve design-principles plugin quality and usability.

**Architecture:** Documentation improvements and basic validation for the Claude Code plugin at `~/.claude/plugins/design-principles/`.

**Tech Stack:** Markdown documentation, YAML frontmatter, JSON configuration.

---

## Context

**Current state:** Plugin created with 4 files (plugin.json, SKILL.md, command, README). Critical fixes applied (allowed-tools, skills array, license).

**Remaining issues from code review:**
- README missing installation instructions
- README missing troubleshooting section
- Phosphor Icons dependency not documented
- No context validation in command file

**What this plan covers:** High-impact improvements that make the plugin more user-friendly and maintainable.

---

## Task 1: Add Installation Instructions to README

**Files:**
- Modify: `~/.claude/plugins/design-principles/README.md`

**Step 1: Add installation section after Overview**

Add this section after line 7 (after the Overview section):

```markdown
## Installation

### Quick Start

The plugin is auto-discovered from `~/.claude/plugins/design-principles/`. No additional installation required.

### Manual Installation

If you need to install manually:

1. Clone or copy the plugin to your Claude plugins directory:
```bash
cp -r design-principles ~/.claude/plugins/design-principles
```

2. Restart Claude Code to load the plugin

3. Verify installation: Run `/help` and look for `/design-principles` in the commands list
```

**Step 2: Verify changes**

Run: `head -30 ~/.claude/plugins/design-principles/README.md`
Expected: Installation section appears after Overview

**Step 3: Commit**

```bash
cd ~/.claude/plugins/design-principles
git add README.md
git commit -m "docs: add installation instructions to README"
```

---

## Task 2: Add Troubleshooting Section to README

**Files:**
- Modify: `~/.claude/plugins/design-principles/README.md`

**Step 1: Add troubleshooting section at end of README**

Add this section before the "License" section:

```markdown
## Troubleshooting

### Command Not Found

**Symptom:** Typing `/design-principles` returns "Command not found"

**Solutions:**
```bash
# Verify plugin exists
ls -la ~/.claude/plugins/design-principles/

# Verify command file exists
ls -la ~/.claude/plugins/design-principles/commands/design-principles.md

# Restart Claude Code and try again
```

### Skill Not Loading

**Symptom:** Command runs but design principles are not applied

**Solutions:**
```bash
# Verify skill file exists
cat ~/.claude/plugins/design-principles/skills/design-principles/SKILL.md

# Verify frontmatter is valid (lines 1-4 should be YAML)
head -10 ~/.claude/plugins/design-principles/skills/design-principles/SKILL.md
```

### Plugin Not Discovered

**Symptom:** Plugin doesn't appear in `/help`

**Solutions:**
- Verify `plugin.json` is in `.claude-plugin/` subdirectory, not plugin root
- Check JSON syntax: `cat ~/.claude/plugins/design-principles/.claude-plugin/plugin.json | python3 -m json.tool`
- Restart Claude Code completely
```

**Step 2: Verify changes**

Run: `tail -50 ~/.claude/plugins/design-principles/README.md`
Expected: Troubleshooting section appears before License section

**Step 3: Commit**

```bash
cd ~/.claude/plugins/design-principles
git add README.md
git commit -m "docs: add troubleshooting section to README"
```

---

## Task 3: Document Phosphor Icons Dependency

**Files:**
- Modify: `~/.claude/plugins/design-principles/skills/design-principles/SKILL.md`

**Step 1: Add Phosphor Icons installation instructions**

Find the Iconography section (around line 165) and modify:

```markdown
### Iconography
Use **Phosphor Icons** (`@phosphor-icons/react`).

**Installation:**
```bash
npm install @phosphor-icons/react
```

**Usage:**
```tsx
import { IconName } from '@phosphor-icons/react';

<IconName size={24} />
```

Icons clarify, not decorate — if removing an icon loses no meaning, remove it.

Give standalone icons presence with subtle background containers.
```

**Step 2: Verify changes**

Run: `grep -A 15 "### Iconography" ~/.claude/plugins/design-principles/skills/design-principles/SKILL.md`
Expected: Installation and usage examples included

**Step 3: Commit**

```bash
cd ~/.claude/plugins/design-principles
git add skills/design-principles/SKILL.md
git commit -m "docs: add Phosphor Icons installation instructions"
```

---

## Task 4: Add Context Validation to Command

**Files:**
- Modify: `~/.claude/plugins/design-principles/commands/design-principles.md`

**Step 1: Add context validation section**

After "## When to Use" section (around line 22), add:

```markdown
## Context Validation

This skill provides UI/UX guidance for frontend interfaces.

**Appropriate contexts:**
- Building React/Vue/Svelte components
- Designing HTML/CSS layouts
- Creating dashboards, admin panels, data tables
- Working on UI/UX for web applications

**If you're working on backend APIs, database schemas, or infrastructure:**
This skill may not be applicable. Consider clarifying your task or using appropriate backend/architecture skills instead.
```

**Step 2: Verify changes**

Run: `cat ~/.claude/plugins/design-principles/commands/design-principles.md`
Expected: Context validation section appears

**Step 3: Commit**

```bash
cd ~/.claude/plugins/design-principles
git add commands/design-principles.md
git commit -m "docs: add context validation to command"
```

---

## Task 5: Update Command Usage Examples

**Files:**
- Modify: `~/.claude/plugins/design-principles/commands/design-principles.md`

**Step 1: Improve examples section**

Replace the "**Examples:**" section (around line 24) with:

```markdown
**Examples:**
```
/design-principles Design a data table for analytics
/design-principles Create a settings page with form controls
/design-principles Build a card-based dashboard
```
```

**Step 2: Verify changes**

Run: `grep -A 5 "Examples:" ~/.claude/plugins/design-principles/commands/design-principles.md`
Expected: Code block format for examples

**Step 3: Commit**

```bash
cd ~/.claude/plugins/design-principles
git add commands/design-principles.md
git commit -m "docs: improve command examples formatting"
```

---

## Task 6: Final Verification

**Files:** All plugin files

**Step 1: Verify plugin structure**

Run: `find ~/.claude/plugins/design-principles -type f \( -name "*.json" -o -name "*.md" \) | sort`
Expected output:
```
/Users/felipe_gonzalez/.claude/plugins/design-principles/.claude-plugin/plugin.json
/Users/felipe_gonzalez/.claude/plugins/design-principles/commands/design-principles.md
/Users/felipe_gonzalez/.claude/plugins/design-principles/README.md
/Users/felipe_gonzalez/.claude/plugins/design-principles/skills/design-principles/SKILL.md
```

**Step 2: Validate plugin.json**

Run: `cat ~/.claude/plugins/design-principles/.claude-plugin/plugin.json | python3 -m json.tool`
Expected: Valid JSON output with all fields

**Step 3: Test plugin discovery**

1. Restart Claude Code
2. Run `/help`
3. Verify `/design-principles` appears in commands list

**Step 4: Test command invocation**

Run: `/design-principles`
Expected: Skill loads, design principles are presented

**Step 5: Final commit**

```bash
cd ~/.claude/plugins/design-principles
git add -A
git commit -m "docs: complete plugin improvements from code review"
```

---

## Success Criteria

- [x] README has installation instructions
- [x] README has troubleshooting section
- [x] Phosphor Icons documented with install/usage
- [x] Command has context validation
- [x] Examples use code block format
- [x] Plugin discovered by Claude Code
- [x] `/design-principles` command works
- [x] All commits follow conventional commit format

---

## Post-Completion

**After all tasks complete:**

1. Test plugin in fresh Claude Code session
2. Remove old skill location if plugin verified working:
```bash
cp -r ~/.claude/skills/design-principles ~/.claude/skills/design-principles.backup.$(date +%Y%m%d)
rm -rf ~/.claude/skills/design-principles
```

3. Optional: Initialize git repo and push to GitHub if publishing

---

## Related Skills

- @plugin-structure - Plugin directory structure
- @plugin-dev:command-development - Command file format
- @superpowers:executing-plans - Batch execution with checkpoints
