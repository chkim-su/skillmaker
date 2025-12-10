---
description: Validate plugin structure before deployment. Checks marketplace.json, skills, agents, commands for errors and completeness.
argument-hint: "[plugin-path]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
---

# Deploy Checker: Plugin Deployment Validation

Validate that a Claude Code plugin is ready for deployment.

## Your Task

Run comprehensive checks on the plugin structure and report any issues.

### Step 1: Locate Plugin

If path provided, use it. Otherwise, check current directory:

```bash
# Look for plugin markers
ls -la .claude-plugin/ 2>/dev/null || ls -la plugin.json 2>/dev/null
```

If no plugin found:
```
❌ No plugin found in current directory.

Expected one of:
- .claude-plugin/marketplace.json
- plugin.json

Run from plugin root directory or provide path:
  /deploy-checker /path/to/plugin
```

### Step 2: Run Validation Checks

Execute all checks and collect results:

#### Check 1: Plugin Metadata
```bash
# Read marketplace.json or plugin.json
Read: .claude-plugin/marketplace.json
```

Verify:
- [ ] `name` field exists and is valid
- [ ] `description` field exists and is meaningful (not TODO)
- [ ] `version` field exists (if applicable)
- [ ] No JSON syntax errors

#### Check 2: Required Directories

```bash
Glob: pattern="**/*" (to see structure)
```

Check existence of expected directories:
- [ ] `commands/` - At least one .md file
- [ ] `agents/` - At least one .md file (if agents declared)
- [ ] `skills/` - Each skill has SKILL.md (if skills declared)
- [ ] `scripts/` - If referenced, must exist

#### Check 3: Command Files

For each command in `commands/*.md`:
- [ ] Has valid YAML frontmatter
- [ ] `description` field present and not TODO
- [ ] `allowed-tools` field present
- [ ] No broken internal references

#### Check 4: Agent Files

For each agent in `agents/*.md`:
- [ ] Has valid YAML frontmatter
- [ ] `name` field matches filename
- [ ] `description` field present and not TODO
- [ ] `tools` field present
- [ ] Referenced skills exist (if `skills:` specified)

#### Check 5: Skill Directories

For each skill in `skills/*/`:
- [ ] `SKILL.md` exists
- [ ] YAML frontmatter valid
- [ ] `name` and `description` present
- [ ] No TODO in description
- [ ] Referenced files exist (scripts/, references/, assets/)
- [ ] If `references/` linked, files exist

#### Check 6: Script Files

For each script in `scripts/*.py` or `scripts/*.sh`:
- [ ] File is executable or has shebang
- [ ] No syntax errors (basic check)
- [ ] Has docstring/usage info

#### Check 7: Cross-References

- [ ] All `skills:` in agents reference existing skills
- [ ] All `[references/xxx.md]` links point to existing files
- [ ] All `scripts/xxx.py` references point to existing files

### Step 3: Generate Report

Present results in this format:

```
╔══════════════════════════════════════════════════════════════╗
║                    PLUGIN DEPLOY CHECKER                      ║
╠══════════════════════════════════════════════════════════════╣
║ Plugin: {plugin-name}                                         ║
║ Path: {plugin-path}                                           ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ METADATA                                                     │
├─────────────────────────────────────────────────────────────┤
│ ✅ marketplace.json valid                                    │
│ ✅ name: skillmaker                                          │
│ ✅ description: present                                      │
│ ⚠️  version: not specified                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ COMMANDS ({count} files)                                     │
├─────────────────────────────────────────────────────────────┤
│ ✅ skill-new.md - valid                                      │
│ ✅ skillization.md - valid                                   │
│ ❌ deploy-checker.md - missing description                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ AGENTS ({count} files)                                       │
├─────────────────────────────────────────────────────────────┤
│ ✅ skill-architect.md - valid                                │
│ ⚠️  skill-converter.md - TODO in description                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SKILLS ({count} directories)                                 │
├─────────────────────────────────────────────────────────────┤
│ ✅ skill-design/ - valid                                     │
│    ├── SKILL.md ✅                                           │
│    ├── references/ ✅ (1 file)                               │
│    └── scripts/ ❌ (referenced but missing)                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ SCRIPTS ({count} files)                                      │
├─────────────────────────────────────────────────────────────┤
│ ✅ init_skill.py - executable, has docstring                 │
│ ✅ validate_skill.py - executable, has docstring             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CROSS-REFERENCES                                             │
├─────────────────────────────────────────────────────────────┤
│ ✅ All skill references valid                                │
│ ❌ Broken link: references/missing.md in skill-design        │
└─────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
                         SUMMARY
═══════════════════════════════════════════════════════════════

  Errors:   2 ❌
  Warnings: 1 ⚠️
  Passed:   15 ✅

  Status: NOT READY FOR DEPLOYMENT

  Fix these issues:
  1. [ERROR] commands/deploy-checker.md: Add description
  2. [ERROR] skills/skill-design: Create referenced scripts/
  3. [WARN] agents/skill-converter.md: Remove TODO from description

═══════════════════════════════════════════════════════════════
```

### Step 4: Detailed Error Output

For each error, provide actionable fix:

```
┌─────────────────────────────────────────────────────────────┐
│ ERROR DETAILS                                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. commands/deploy-checker.md:2                              │
│    Missing or empty 'description' in frontmatter             │
│                                                              │
│    Fix: Add description field:                               │
│    ---                                                       │
│    description: Your command description here                │
│    ---                                                       │
│                                                              │
│ 2. skills/skill-design/SKILL.md:215                          │
│    Broken reference: [scripts/example.py]                    │
│                                                              │
│    Fix: Either create the file or remove the reference       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Step 5: Success Output

If all checks pass:

```
╔══════════════════════════════════════════════════════════════╗
║                    ✅ READY FOR DEPLOYMENT                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Plugin: skillmaker                                           ║
║  Commands: 4                                                  ║
║  Agents: 3                                                    ║
║  Skills: 3                                                    ║
║  Scripts: 2                                                   ║
║                                                               ║
║  All checks passed! Plugin is ready for deployment.           ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝
```

## Validation Rules

### Frontmatter Requirements

**Commands**:
```yaml
---
description: Required, non-empty, no TODO
argument-hint: Optional
allowed-tools: Required, array
---
```

**Agents**:
```yaml
---
name: Required, must match filename (without .md)
description: Required, non-empty, no TODO
tools: Required, array
skills: Optional, but if present must reference existing skills
model: Optional (sonnet, opus, haiku)
---
```

**Skills (SKILL.md)**:
```yaml
---
name: Required
description: Required, non-empty, no TODO, should include trigger phrases
allowed-tools: Optional but recommended
---
```

### File Naming

- Commands: `kebab-case.md`
- Agents: `kebab-case.md`
- Skills: `kebab-case/SKILL.md`
- Scripts: `snake_case.py` or `kebab-case.sh`

### Content Quality

**Errors** (must fix):
- Missing required fields
- Broken references
- Invalid YAML syntax
- Missing SKILL.md in skill directories

**Warnings** (should fix):
- TODO in content
- Empty directories
- Scripts without docstrings
- Very short descriptions (<20 chars)

## Quick Fix Mode

If user requests, offer to auto-fix simple issues:

```
Found 3 auto-fixable issues:
1. Add missing shebang to scripts/example.py
2. Make scripts/example.py executable
3. Remove empty references/ directory

Auto-fix these? (y/n)
```

## Important Notes

- Run from plugin root directory
- Check ALL files, not just a sample
- Report line numbers for errors when possible
- Distinguish errors (blocking) from warnings (advisable)
- Provide actionable fix suggestions
