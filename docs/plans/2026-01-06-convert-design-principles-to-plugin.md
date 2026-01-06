# Convert design-principles to Plugin with Slash Command

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the local `design-principles` skill into a Claude Code plugin with visible slash command `/design-principles`

**Architecture:** Migrate `~/.claude/skills/design-principles/skill.md` to `~/.claude/plugins/design-principles/` with proper plugin structure including `commands/`, `skills/`, `plugin.json`, and auto-discovery.

**Tech Stack:** Claude Code Plugin API, markdown frontmatter, YAML configuration, bash scripting for setup

---

## Context

**Current state:**
- `design-principles` skill exists at `~/.claude/skills/design-principles/skill.md`
- Skill works internally but has no visible slash command
- Only accessible via `Skill` tool invocation

**Desired state:**
- Plugin at `~/.claude/plugins/design-principles/`
- Slash command `/design-principles` visible globally
- Same functionality, discoverable via `/help`

**Why this works:**
- Plugin `commands/` directory creates slash commands automatically
- Plugin `skills/` directory works same as local skills
- Claude Code auto-discovers plugins from `~/.claude/plugins/`

---

## Task 1: Create Plugin Directory Structure

**Files:**
- Create: `~/.claude/plugins/design-principles/.claude-plugin/`
- Create: `~/.claude/plugins/design-principles/skills/design-principles/`
- Create: `~/.claude/plugins/design-principles/commands/`

**Step 1: Create base plugin directories**

```bash
# Create plugin root structure
mkdir -p ~/.claude/plugins/design-principles/.claude-plugin
mkdir -p ~/.claude/plugins/design-principles/skills/design-principles
mkdir -p ~/.claude/plugins/design-principles/commands
```

**Step 2: Verify directories created**

Run: `ls -la ~/.claude/plugins/design-principles/`
Expected:
```
drwxr-xr-x  4 user  staff   128 Jan  6 10:00 .
drwxr-xr-x  X user  staff   XXX Jan  6 09:00 ..
drwxr-xr-x  3 user  staff    96 Jan  6 10:00 .claude-plugin
drwxr-xr-x  3 user  staff    96 Jan  6 10:00 commands
drwxr-xr-x  3 user  staff    96 Jan  6 10:00 skills
```

**Step 3: Commit structure**

```bash
cd ~/.claude/plugins/design-principles
git init
git add .
git commit -m "feat: create plugin directory structure"
```

---

## Task 2: Create Plugin Manifest

**Files:**
- Create: `~/.claude/plugins/design-principles/.claude-plugin/plugin.json`

**Step 1: Write plugin.json**

```json
{
  "name": "design-principles",
  "version": "1.0.0",
  "description": "Jony Ive-level design precision for enterprise software, SaaS dashboards, and admin interfaces",
  "author": {
    "name": "Felipe Gonzalez"
  },
  "keywords": ["design", "ui", "ux", "frontend", "apple", "minimalism"]
}
```

**Step 2: Verify JSON syntax**

Run: `cat ~/.claude/plugins/design-principles/.claude-plugin/plugin.json | python3 -m json.tool`
Expected: Valid JSON output (no errors)

**Step 3: Commit manifest**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add plugin manifest"
```

---

## Task 3: Migrate Skill to Plugin Structure

**Files:**
- Source: `~/.claude/skills/design-principles/skill.md`
- Create: `~/.claude/plugins/design-principles/skills/design-principles/SKILL.md`

**Step 1: Copy skill.md to SKILL.md (uppercase required)**

```bash
cp ~/.claude/skills/design-principles/skill.md \
   ~/.claude/plugins/design-principles/skills/design-principles/SKILL.md
```

**Step 2: Verify content migrated**

Run: `head -20 ~/.claude/plugins/design-principles/skills/design-principles/SKILL.md`
Expected: Should start with frontmatter containing `name: design-principles`

**Step 3: Commit skill migration**

```bash
git add skills/design-principles/SKILL.md
git commit -m "feat: migrate design-principles skill to plugin"
```

---

## Task 4: Create Slash Command

**Files:**
- Create: `~/.claude/plugins/design-principles/commands/design-principles.md`

**Step 1: Write command file with frontmatter**

Create `~/.claude/plugins/design-principles/commands/design-principles.md`:

```markdown
---
description: Enforce Jony Ive-level design precision - clean, modern, minimalist with taste
argument-hint: Optional design context or question
allowed-tools: ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
disable-model-invocation: false
---

# Design Principles Command

Invoke the design-principles skill and follow it exactly as presented to you.

## Usage

This command loads the design-principles skill which provides:
- Design direction selection (Precision & Density, Warmth & Approachability, etc.)
- Core craft principles (4px grid, symmetrical padding, border radius consistency)
- Typography hierarchy, iconography, animation timing
- Color strategy, contrast hierarchy, anti-patterns

## When to Use

Use this skill when building dashboards, admin interfaces, or any UI that needs Apple-like precision. Every pixel matters.

**Examples:**
- "Design a data table for analytics"
- "Create a settings page with form controls"
- "Build a card-based dashboard"

## What Happens

1. Skill is loaded automatically
2. You'll be asked to commit to a design direction
3. Follow the skill's guidance for pixel-perfect implementation

---

**Begin by loading the design-principles skill and applying its principles to the current task.**
```

**Step 2: Verify command file exists**

Run: `cat ~/.claude/plugins/design-principles/commands/design-principles.md | head -10`
Expected: Should show frontmatter with `description:` field

**Step 3: Commit command**

```bash
git add commands/design-principles.md
git commit -m "feat: add /design-principles slash command"
```

---

## Task 5: Create README Documentation

**Files:**
- Create: `~/.claude/plugins/design-principles/README.md`

**Step 1: Write README.md**

Create `~/.claude/plugins/design-principles/README.md`:

```markdown
# Design Principles Plugin

Jony Ive-level design precision for Claude Code UI development.

## Overview

Enforces precise, crafted design for enterprise software, SaaS dashboards, admin interfaces, and web applications. Every interface should look designed by a team that obsesses over 1-pixel differences.

## Features

- **Design Direction Guidance**: Choose the right aesthetic for your product context
- **Core Craft Principles**: 4px grid, symmetrical padding, border radius consistency
- **Typography System**: Font weights, tracking, scale hierarchy
- **Color Strategy**: Foundations, accents, semantic usage
- **Animation Standards**: 150ms micro-interactions, easing curves
- **Anti-Patterns**: What to avoid in enterprise UI

## Installation

This plugin is auto-discovered from `~/.claude/plugins/design-principles/`

## Usage

### Slash Command

```
/design-principles
```

### Skill Invocation

The skill also auto-loads when you ask about:
- Design direction for dashboards/UI
- Spacing, typography, or color choices
- Apple-like design precision
- Visual hierarchy and polish

## Design Directions

The skill helps you choose from:
- **Precision & Density**: Linear, Raycast aesthetics
- **Warmth & Approachability**: Notion, Coda style
- **Sophistication & Trust**: Stripe, Mercury feel
- **Boldness & Clarity**: Vercel, minimal dashboards
- **Utility & Function**: GitHub, developer tools
- **Data & Analysis**: Analytics, metrics focus

## Examples

**Ask:**
> "Create a data table for user analytics"

**Result:**
- Guidance on density vs whitespace
- Typography hierarchy for data
- Border strategy (borders-only vs shadows)
- Monospace for numbers, tabular-nums

**Ask:**
> "Design a settings page"

**Result:**
- Form control isolation (custom selects, not native)
- Section grouping with consistent padding
- Visual hierarchy through typography
- Minimalist decoration, functional focus

## Principles

### The 4px Grid
All spacing uses 4px base: 4, 8, 12, 16, 24, 32

### Symmetrical Padding
TLBR must match. Top 16px = all sides 16px (unless content creates balance)

### Border Radius Consistency
Pick a system: Sharp (4/6/8), Soft (8/12), Minimal (2/4/6). Commit.

### Depth Strategy
Borders-only OR subtle shadows OR layered shadows. Choose ONE, commit.

## Anti-Patterns

Never:
- Dramatic drop shadows (`0 25px 50px...`)
- Large border radius (16px+) on small elements
- Asymmetric padding without clear reason
- Pure white cards on colored backgrounds
- Spring/bouncy animations in enterprise UI

## Inspired By

- [Linear](https://linear.app) - Precision & Density
- [Notion](https://notion.so) - Warmth & Approachability
- [Stripe](https://stripe.com) - Sophistication & Trust
- [Vercel](https://vercel.com) - Boldness & Clarity
- [Raycast](https://raycast.com) - Utility & Function

## License

MIT

## Author

Felipe Gonzalez
```

**Step 2: Commit README**

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Task 6: Test Plugin Locally

**Files:** None (manual testing)

**Step 1: Test plugin discovery**

```bash
# Verify plugin structure
ls -la ~/.claude/plugins/design-principles/

# Check manifest
cat ~/.claude/plugins/design-principles/.claude-plugin/plugin.json
```

Expected: All files in place, valid JSON

**Step 2: Restart Claude Code to load plugin**

Quit and reopen Claude Code, or run:
```bash
# If using CLI, restart the process
# Claude Code will auto-discover the plugin on startup
```

**Step 3: Verify slash command appears**

In Claude Code, run:
```
/help
```

Expected: `/design-principles` should appear in available commands list

**Step 4: Test slash command invocation**

Run:
```
/design-principles
```

Expected: Command loads design-principles skill and presents guidance

**Step 5: Test skill auto-loading**

Ask in Claude Code:
```
What's the right spacing for a data table?
```

Expected: design-principles skill should auto-load based on trigger phrases

**Step 6: Document test results**

Create test notes:
```bash
echo "Test Results $(date)" > ~/.claude/plugins/design-principles/test-notes.md
echo "- Plugin discovered: ✓" >> ~/.claude/plugins/design-principles/test-notes.md
echo "- Slash command visible: ✓" >> ~/.claude/plugins/design-principles/test-notes.md
echo "- Command invocation works: ✓" >> ~/.claude/plugins/design-principles/test-notes.md
echo "- Skill auto-loading works: ✓" >> ~/.claude/plugins/design-principles/test-notes.md
```

**Step 7: Commit test notes**

```bash
git add test-notes.md
git commit -m "test: document plugin verification results"
```

---

## Task 7: Cleanup Old Skill Location

**Files:**
- Remove: `~/.claude/skills/design-principles/` (after verification)

**Step 1: Backup old skill (optional but recommended)**

```bash
# Create backup
cp -r ~/.claude/skills/design-principles \
      ~/.claude/skills/design-principles.backup.$(date +%Y%m%d)
```

**Step 2: Remove old skill location**

```bash
# Remove after plugin is verified working
rm -rf ~/.claude/skills/design-principles
```

**Step 3: Verify no conflicts**

Run: `ls ~/.claude/skills/`
Expected: Should NOT see `design-principles/` directory

**Step 4: Test plugin still works without old skill**

Repeat tests from Task 6:
1. `/design-principles` command works
2. Skill auto-loads on trigger phrases

**Step 5: Commit cleanup**

```bash
cd ~/.claude/plugins/design-principles
echo "# Migration Notes

## Original Location
- ~/.claude/skills/design-principles/skill.md

## Migrated To
- ~/.claude/plugins/design-principles/
  - skills/design-principles/SKILL.md
  - commands/design-principles.md

## Migration Date
$(date)

## Verified
- Plugin auto-discovery works
- Slash command visible
- Skill invocation works
- Old location removed" > MIGRATION.md

git add MIGRATION.md
git commit -m "docs: add migration notes and cleanup confirmation"
```

---

## Task 8: Optional - Create Marketplace Entry

**Files:**
- Modify: `~/.claude/plugins/design-principles/.claude-plugin/marketplace.json` (create if publishing)

**Step 1: Determine if publishing**

Ask: "Should this plugin be published to the Claude Code marketplace?"

If yes, continue. If no, skip this task.

**Step 2: Create marketplace.json**

Create `~/.claude/plugins/design-principles/.claude-plugin/marketplace.json`:

```json
{
  "name": "design-principles",
  "description": "Jony Ive-level design precision for enterprise UI - Apple-inspired design principles for dashboards, admin interfaces, and web applications",
  "category": "developer-tools",
  "version": "1.0.0",
  "author": "Felipe Gonzalez",
  "repository": "https://github.com/felipegonzalez/design-principles-plugin",
  "homepage": "https://github.com/felipegonzalez/design-principles-plugin#readme",
  "license": "MIT",
  "keywords": ["design", "ui", "ux", "frontend", "apple", "minimalism", "dashboard", "admin"],
  "icon": "🎨"
}
```

**Step 3: Create GitHub repository (if publishing)**

```bash
# Create repo on GitHub first, then:
cd ~/.claude/plugins/design-principles
git remote add origin git@github.com:felipegonzalez/design-principles-plugin.git
git push -u origin main
```

**Step 4: Submit to marketplace**

Follow Claude Code marketplace submission process with repository URL.

**Step 5: Commit marketplace config**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: add marketplace configuration"
```

---

## Final Verification

**All tasks complete?**
- [x] Plugin directory structure created
- [x] Plugin manifest (plugin.json) created
- [x] Skill migrated to plugin structure (SKILL.md)
- [x] Slash command created (design-principles.md)
- [x] README documentation added
- [x] Plugin tested locally
- [x] Old skill location cleaned up
- [ ] Marketplace entry (optional)

**Expected commits:**
1. "feat: create plugin directory structure"
2. "feat: add plugin manifest"
3. "feat: migrate design-principles skill to plugin"
4. "feat: add /design-principles slash command"
5. "docs: add comprehensive README"
6. "test: document plugin verification results"
7. "docs: add migration notes and cleanup confirmation"
8. "feat: add marketplace configuration" (optional)

---

## Success Criteria

- ✅ Plugin auto-discovers from `~/.claude/plugins/`
- ✅ `/design-principles` slash command visible in `/help`
- ✅ Command invokes skill correctly
- ✅ Skill auto-loads on trigger phrases
- ✅ Old skill location removed
- ✅ No conflicts or errors
- ✅ Documentation complete

---

## Troubleshooting

**Plugin not discovered:**
- Verify `plugin.json` is in `.claude-plugin/` subdirectory
- Check JSON syntax is valid
- Restart Claude Code completely

**Slash command not visible:**
- Verify command file is in `commands/` directory at plugin root
- Check frontmatter has `description:` field
- Verify filename is `design-principles.md`

**Skill not loading:**
- Verify SKILL.md is uppercase (not skill.md)
- Check skill directory name matches plugin name: `skills/design-principles/`
- Verify frontmatter has `name:` and `description:` fields

**Old skill still loading:**
- Verify old location was removed: `ls ~/.claude/skills/design-principles`
- Check for backup directory and remove if confirmed working
- Restart Claude Code after cleanup

---

## Related Documentation

- **Plugin Dev Guide:** `~/.claude/plugins/cache/claude-plugins-official/plugin-dev/`
- **Plugin Structure Skill:** `plugin-dev/skills/plugin-structure/skill.md`
- **Command Development:** `plugin-dev/skills/command-development/skill.md`
- **Original Skill:** `~/.claude/skills/design-principles/skill.md` (before migration)
