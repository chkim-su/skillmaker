---
name: skill-activation-patterns
description: Skill auto-activation system using hooks and trigger configuration. Use when designing skills that should activate automatically.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# Skill Activation Patterns

## Problem

Claude Code skills don't activate automatically by default. Users must explicitly invoke skills, which means:
- Relevant skills are forgotten during work
- Best practices aren't enforced
- Domain expertise isn't applied when needed

## Solution: Hook + skill-rules.json

```
┌─────────────────────────────────────────────────────────┐
│                 AUTO-ACTIVATION SYSTEM                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  User Prompt → [UserPromptSubmit Hook]                  │
│                      ↓                                   │
│              Read skill-rules.json                       │
│                      ↓                                   │
│              Match triggers:                             │
│              • Keywords (case-insensitive)               │
│              • Intent patterns (regex)                   │
│              • File paths (glob)                         │
│              • Content patterns (code detection)         │
│                      ↓                                   │
│              Output skill suggestions                    │
│                      ↓                                   │
│              Claude uses Skill tool                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## skill-rules.json Schema

```json
{
  "version": "1.0",
  "skills": {
    "skill-name": {
      "type": "domain|guardrail",
      "enforcement": "suggest|warn|block",
      "priority": "critical|high|medium|low",
      "promptTriggers": {
        "keywords": ["keyword1", "keyword2"],
        "intentPatterns": ["regex pattern"]
      },
      "fileTriggers": {
        "pathPatterns": ["src/**/*.ts"],
        "pathExclusions": ["**/*.test.ts"],
        "contentPatterns": ["import.*Pattern"]
      },
      "blockMessage": "Custom message when blocked",
      "skipConditions": {
        "sessionSkillUsed": true,
        "fileMarkers": ["@skip-validation"]
      }
    }
  }
}
```

---

## Skill Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| **domain** | Expertise/knowledge | Backend patterns, API design, testing |
| **guardrail** | Enforce standards | Breaking changes, security, compatibility |

---

## Enforcement Levels

| Level | Behavior | Use Case |
|-------|----------|----------|
| **suggest** | Show recommendation | General best practices |
| **warn** | Show warning, allow proceed | Important but not critical |
| **block** | Must use skill first | Breaking changes, security |

---

## Trigger Types

### 1. Keyword Triggers
Simple case-insensitive matching:
```json
"keywords": ["backend", "API", "controller", "service"]
```

### 2. Intent Pattern Triggers
Regex for user intent:
```json
"intentPatterns": [
  "(create|add|implement).*?(route|endpoint|API)",
  "(how to|best practice).*?(backend|service)"
]
```

### 3. File Path Triggers
Glob patterns for file context:
```json
"pathPatterns": ["src/backend/**/*.ts", "api/**/*.ts"],
"pathExclusions": ["**/*.test.ts", "**/*.spec.ts"]
```

### 4. Content Pattern Triggers
Code content detection:
```json
"contentPatterns": ["import.*Prisma", "router\\.get"]
```

---

## Priority Levels

| Priority | When Triggered | Display |
|----------|----------------|---------|
| **critical** | Always | ⚠️ CRITICAL SKILLS (REQUIRED) |
| **high** | Most matches | 📚 RECOMMENDED SKILLS |
| **medium** | Clear matches | 💡 SUGGESTED SKILLS |
| **low** | Explicit only | 📌 OPTIONAL SKILLS |

---

## Implementation

See `references/` for detailed implementation:
- `hook-implementation.md` - TypeScript/Bash hook code
- `skill-rules-examples.md` - Real-world configuration examples
- `integration-guide.md` - Step-by-step setup

---

## Quick Start

1. Create `.claude/skills/skill-rules.json`
2. Add hook to `.claude/settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation.sh"
      }]
    }]
  }
}
```
3. Test: Edit a file matching pathPatterns → skill should activate

---

## Best Practices

1. **Start with suggest** - Don't block until pattern is proven
2. **Specific keywords** - Avoid generic words that over-trigger
3. **Test regex** - Verify intentPatterns don't have false positives
4. **Document blockMessage** - Clear guidance for blocked actions
5. **Use skipConditions** - Allow escape hatch for edge cases
