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
- [ ] `source` path format is correct (see Source Path Validation below)

**Source Path Validation** (CRITICAL):
- [ ] Local plugins: `source` must start with `./` (e.g., `"./plugins/my-plugin"`)
- [ ] GitHub plugins: must use object format `{"source": "github", "repo": "user/repo"}`
- [ ] No bare paths like `"source": "my-plugin"` (will cause "must start with ./" error)

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

**Expert Skill Detection** (CRITICAL):
If skill has `scripts/validation/` OR 4+ reference files → Treat as expert skill:
- [ ] `references/` contains format/structure docs
- [ ] `references/troubleshooting.md` exists
- [ ] `references/` contains library limitation docs
- [ ] `scripts/validation/` has validation scripts
- [ ] `assets/templates/` or `assets/examples/` present
- [ ] Reference files have actual content (not just TODOs)

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

## Common Mistakes (from Experience)

### ❌ Mistake 1: Skills Only Create MD Files
```
# Wrong: Skill with no scripts for file manipulation
pdf-processor/
├── SKILL.md              # Just documentation
└── references/
    └── usage.md

# Correct: Tool skill with actual scripts
pdf-processor/
├── SKILL.md
├── scripts/
│   ├── extract_text.py   # Working, tested script
│   └── rotate_page.py
└── references/
    └── troubleshooting.md
```

### ❌ Mistake 2: Expert Skills Without Comprehensive Docs
```
# Wrong: Complex format skill with minimal docs
pptx-builder/
├── SKILL.md
└── scripts/
    └── create.py         # Script, but no workaround docs

# Correct: Expert skill with full documentation
pptx-builder/
├── SKILL.md
├── scripts/
│   ├── create_slide.py
│   └── validation/
│       └── validate_pptx.py
├── references/
│   ├── ooxml-structure.md        # Internal format docs
│   ├── troubleshooting.md        # Known issues
│   ├── library-limitations.md    # What doesn't work
│   └── edge-cases.md             # Gotchas
└── assets/
    ├── templates/
    └── examples/
```

### ❌ Mistake 3: TODO in Production Descriptions
```yaml
# Wrong
---
description: TODO: Add description
---

# Correct
---
description: |
  Create PowerPoint presentations programmatically.
  Supports: slides, tables, charts. Handles OOXML complexities.
  Trigger phrases: "create PowerPoint", "make slides", "add table"
---
```

### ❌ Mistake 4: Broken Cross-References
```markdown
# Wrong: References non-existent file
See [references/advanced.md](references/advanced.md) for details.
# But references/advanced.md doesn't exist!

# Correct: Only reference existing files
See [references/patterns.md](references/patterns.md) for details.
# And references/patterns.md exists with actual content
```

### ❌ Mistake 5: Scripts Without Docstrings
```python
# Wrong
def main():
    # No usage info, no help
    pass

# Correct
#!/usr/bin/env python3
"""
Extract text from PDF files.

Usage:
    python extract_text.py <input.pdf> <output.txt>

Examples:
    python extract_text.py report.pdf report.txt
"""
import argparse
# ... proper implementation
```

### ❌ Mistake 6: Agent Skills Reference Doesn't Exist
```yaml
# Wrong: skill doesn't exist
---
name: my-agent
skills: non-existent-skill
---

# Correct: skill exists in skills/ directory
---
name: my-agent
skills: skill-design
---
```

### ❌ Mistake 7: Missing Skill Type Classification
```
# Wrong: No clear structure, unclear purpose
ambiguous-skill/
├── SKILL.md
├── scripts/              # Has scripts...
└── references/           # Has references...
# But no clear type, inconsistent structure

# Correct: Clear type with appropriate structure
# Knowledge skill: SKILL.md + references/
# Tool skill: SKILL.md + scripts/
# Hybrid skill: SKILL.md + scripts/ + references/
# Expert skill: SKILL.md + scripts/ + scripts/validation/ + references/ (4+ files) + assets/
```

### ❌ Mistake 8: Invalid Plugin Source Path
```json
// Wrong: Bare path (causes "must start with ./" error)
{
  "plugins": [
    {"source": "my-plugin"}
  ]
}

// Wrong: Missing ./ prefix for local path
{
  "plugins": [
    {"source": "plugins/skillmaker"}
  ]
}

// Correct: Local plugin with ./ prefix
{
  "plugins": [
    {"source": "./plugins/skillmaker"}
  ]
}

// Correct: GitHub plugin with object format
{
  "extraKnownMarketplaces": {
    "skillmaker": {
      "source": {
        "source": "github",
        "repo": "chkim-su/skillmaker"
      }
    }
  }
}
```

### ❌ Mistake 9: Marketplace JSON Path Mismatch
```json
// Wrong: marketplace.json source doesn't match actual location
// File at: ./plugins/skillmaker/
// But marketplace.json says:
{
  "source": "./skillmaker"  // Path doesn't exist!
}

// Correct: Path matches actual plugin location
{
  "source": "./plugins/skillmaker"
}
```

### ❌ Mistake 10: Multi-Plugin Marketplace Structure Wrong
```
# Wrong: Multi-plugin marketplace with files at root
my-marketplace/
├── .claude-plugin/
│   ├── marketplace.json    # marketplace 정의
│   └── plugin.json         # plugin 정의 (혼동 유발!)
├── commands/               # 루트에 직접
├── agents/
└── skills/

# Correct: Multi-plugin marketplace with plugins/ subdirectory
my-marketplace/
├── .claude-plugin/
│   └── marketplace.json    # 마켓플레이스만 정의
└── plugins/
    └── my-plugin/
        ├── .claude-plugin/
        │   └── plugin.json # 플러그인만 정의
        ├── commands/
        ├── agents/
        └── skills/
```

**규칙:**
- 마켓플레이스 루트: `.claude-plugin/marketplace.json`만
- 각 플러그인: `plugins/{name}/.claude-plugin/plugin.json`
- `source: "./plugins/{name}"` 형식 사용

### ❌ Mistake 11: Commands/Skills/Agents Not Recognized
```
# 원인: marketplace.json에서 source 경로와 실제 파일 위치 불일치

# 증상
- /skillmaker:skill-new 명령어가 안 뜸
- 스킬이 Available Skills에 안 보임
- 에이전트가 Task tool에서 사용 불가

# 진단 방법
1. marketplace.json의 source 경로 확인
2. 해당 경로에 실제로 commands/, agents/, skills/ 존재 확인
3. Claude Code 재시작 후 재확인

# 해결
- source 경로가 실제 플러그인 파일 위치와 일치하도록 수정
- 또는 플러그인 파일을 source 경로로 이동
```

## Important Notes

- Run from plugin root directory
- Check ALL files, not just a sample
- Report line numbers for errors when possible
- Distinguish errors (blocking) from warnings (advisable)
- Provide actionable fix suggestions
- **Detect skill type** and validate accordingly
- **Expert skills** require comprehensive documentation - flag if incomplete
