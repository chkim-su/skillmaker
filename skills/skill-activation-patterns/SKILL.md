---
name: skill-activation-patterns
description: Design patterns for automatic skill activation. Reference documentation for implementing your own activation system.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# Skill Activation Patterns

## Scope

This is **design pattern documentation**, not an implementation.

| What this is | What this is NOT |
|--------------|------------------|
| Reference patterns | Exclusive functionality |
| Implementation guide | The only way to do it |

**Any plugin or project can implement skill-activation independently.**

## Quick Start

1. Create `.claude/skills/skill-rules.json`
2. Add UserPromptSubmit hook to settings.json
3. Hook reads rules, matches triggers, suggests skills

## Core Concept

```
User Prompt → [Hook] → skill-rules.json → Match triggers → Suggest skills
```

## skill-rules.json (Minimal)

```json
{
  "version": "1.0",
  "skills": {
    "backend-patterns": {
      "type": "domain",
      "enforcement": "suggest",
      "promptTriggers": {
        "keywords": ["backend", "API"]
      }
    }
  }
}
```

## Skill Types

| Type | Purpose |
|------|---------|
| **domain** | Expertise/knowledge |
| **guardrail** | Enforce standards |

## Enforcement Levels

| Level | Behavior |
|-------|----------|
| **suggest** | Recommend |
| **warn** | Allow + warning |
| **block** | Must use skill |

## Best Practices

1. **Start with suggest** - Don't block until proven
2. **Specific keywords** - Avoid generic over-triggering
3. **Test regex** - Verify no false positives
4. **Use skipConditions** - Allow escape hatch

## References

- [Full Schema](references/full-schema.md) - Complete skill-rules.json spec
- [Hook Implementation](references/hook-implementation.md) - TypeScript/Bash code
- [Real Examples](references/skill-rules-examples.md) - Production configs
