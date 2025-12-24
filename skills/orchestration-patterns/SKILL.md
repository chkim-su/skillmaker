---
name: orchestration-patterns
description: Single-skill vs multi-skill subagent architectures. Use when designing subagents.
allowed-tools: ["Read", "Write"]
---

# Two Patterns

## Pattern 1: Single-Skill Consumer

**Use when**: Focused, single-domain task

```yaml
---
name: sql-agent
skills: sql-helper
tools: [Read, Grep, Glob]
---
```

```
User → Subagent [isolated] → skill-x → Focused result
```

✅ Fast, focused, clear responsibility
❌ Limited to one domain

---

## Pattern 2: Multi-Skill Orchestrator

**Use when**: Multi-domain workflow

```yaml
---
name: fullstack-orchestrator
skills: frontend-design, api-generator, migration-patterns
tools: [Read, Write, Bash, Task]
---
```

```
User → Orchestrator [isolated]
         ├→ skill-a (if UI)
         ├→ skill-b (if API)
         └→ skill-c (if DB)
       → Coordinated result
```

✅ Handles complex workflows
❌ More decision-making overhead

---

# Decision Matrix

| Question | Single-Skill | Multi-Skill |
|----------|--------------|-------------|
| Scope? | Narrow | Broad |
| Skills needed? | 1 | 2+ |
| Coordination? | No | Yes |

---

# Auto-Loading

```yaml
skills: skill1, skill2
```

Skills load automatically when subagent starts. No explicit activation needed.

---

# Best Practices

**Single-Skill:**
- Name: `{domain}-agent`
- Minimal tools
- "Use {skill} for all operations"

**Multi-Skill:**
- Name: `{domain}-orchestrator`
- Include Task tool
- Document when to use each skill
- "Don't activate all skills for simple requests"
