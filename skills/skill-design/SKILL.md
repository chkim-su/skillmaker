---
name: skill-design
description: Best practices for skill structure, progressive disclosure, and trigger phrases. Use when creating or designing skills.
allowed-tools: Read, Write, Glob, Grep
---

# Skill Design Best Practices

This skill provides expert guidance on creating effective, production-ready skills.

## Core Principles

### 1. Progressive Disclosure

**SKILL.md should be concise** (~500-1000 words):
- Clear description and purpose
- 5-10 trigger phrases
- Core instructions
- Basic examples

**Supporting files for depth**:
- `reference.md`: Detailed API documentation
- `examples.md`: Comprehensive usage examples
- `patterns.md`: Advanced techniques
- `scripts/`: Utility scripts or validators

### 2. Trigger Phrases

Include 5-10 specific phrases that should activate the skill:

```yaml
Trigger phrases:
- "create a hook"
- "add a PreToolUse hook"
- "validate tool use"
- "implement prompt-based hooks"
- "block dangerous commands"
```

**Good triggers**:
- ✅ Specific actions: "create a database migration"
- ✅ Domain terms: "SQL query optimization"
- ✅ Tool references: "${CLAUDE_PLUGIN_ROOT}"

**Bad triggers**:
- ❌ Generic: "help me"
- ❌ Too broad: "write code"

### 3. YAML Frontmatter Structure

```yaml
---
name: skill-name                    # Kebab-case, descriptive
description: |                      # Clear, trigger-phrase rich
  What this skill does. Use when [specific scenarios].
  Trigger phrases: "phrase1", "phrase2", "phrase3"
allowed-tools: Read, Write, Bash    # Restrict tool access
---
```

### 4. Skill.md Content Structure

```markdown
# Skill Name

[2-3 sentence overview]

## When to Use

- Scenario 1
- Scenario 2
- Scenario 3

## Core Instructions

1. **Step 1**: Clear action
2. **Step 2**: Clear action
3. **Step 3**: Clear action

## Quick Examples

### Example 1
[Simple, common use case]

### Example 2
[Another common pattern]

## Key Principles

- Principle 1
- Principle 2

---

For advanced usage, see [reference.md](reference.md)
```

### 5. Tool Restrictions

Use `allowed-tools` to scope skills appropriately:

```yaml
# Read-only skill
allowed-tools: Read, Grep, Glob

# Code generation skill
allowed-tools: Read, Write, Edit

# Full automation skill
allowed-tools: Read, Write, Edit, Bash, Task
```

### 6. Skill Naming Conventions

- **Kebab-case**: `database-migration`, not `databaseMigration`
- **Descriptive**: `sql-query-optimizer`, not `sql-helper`
- **Domain-focused**: `frontend-design`, `security-auditor`

### 7. Testing Your Skill

After creation, test activation:

1. Use trigger phrases in prompts
2. Verify skill loads (check for markers/behavior)
3. Test with and without trigger phrases
4. Validate tool restrictions work

## Common Patterns

### Pattern 1: Analysis Skill
```yaml
---
name: code-analyzer
description: Analyze code quality, patterns, and potential issues
allowed-tools: Read, Grep, Glob
---
```

### Pattern 2: Generation Skill
```yaml
---
name: component-generator
description: Create UI components following project patterns
allowed-tools: Read, Write, Grep, Glob
---
```

### Pattern 3: Workflow Skill
```yaml
---
name: deployment-orchestrator
description: Coordinate multi-step deployment workflows
allowed-tools: Read, Write, Bash, Task
---
```

## Progressive Disclosure in Action

**User asks simple question** → SKILL.md provides answer

**User needs details** → Skill mentions "See reference.md" → Claude reads reference.md

**User wants examples** → Skill mentions examples.md → Claude reads examples

**This keeps context usage minimal by default.**

## Validation Checklist

Before finalizing a skill:

- ✅ SKILL.md under 1000 words
- ✅ 5-10 specific trigger phrases
- ✅ Clear allowed-tools restriction
- ✅ Supporting files for complex topics
- ✅ Real, working examples
- ✅ Tested activation
