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

## Pattern 3: Enhanced Agent (with Codebase Bridge + Memory)

**Use when**: Complex tasks requiring codebase understanding and session continuity

```yaml
---
name: smart-orchestrator
skills: domain-skill-1, domain-skill-2
tools: [Read, Write, Bash, Task, Skill]
model: sonnet
---
```

```
Session Start
    ↓
claude-mem: load recent context
    ↓
User Request
    ↓
Serena Gateway: explore codebase (QUERY)
    ↓
Match findings → skill-rules.json
    ↓
Auto-call relevant skills
    ↓
Execute task
    ↓
claude-mem: store observation
```

✅ Smart skill discovery via codebase analysis
✅ Cross-session memory persistence
✅ Reduces manual skill selection
❌ Requires Serena + claude-mem setup

**Key Components:**
1. **Serena Gateway** - Codebase exploration bridge (see `mcp-gateway-patterns`)
2. **skill-rules.json** - Trigger patterns (see `skill-activation-patterns`)
3. **claude-mem** - Context persistence (see `references/enhanced-agent.md`)

---

# Decision Matrix

| Question | Single-Skill | Multi-Skill | Enhanced |
|----------|--------------|-------------|----------|
| Scope? | Narrow | Broad | Broad + Smart |
| Skills needed? | 1 | 2+ | 2+ (auto-discovered) |
| Coordination? | No | Yes | Yes + Auto |
| Memory? | No | No | Yes (claude-mem) |
| Codebase Aware? | No | No | Yes (Serena) |

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

**Enhanced:**
- Name: `{domain}-smart-agent`
- Include Task + Skill tools
- Add Serena Gateway for exploration
- Document claude-mem project name
- "Explore codebase before selecting skills"
