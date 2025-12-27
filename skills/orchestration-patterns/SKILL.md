---
name: orchestration-patterns
description: Single-skill vs multi-skill subagent architectures. Use when designing subagents.
allowed-tools: ["Read", "Write"]
---

# Subagent Architecture Patterns

Subagents provide **context isolation** - intermediate work stays in subagent's context, keeping main conversation clean.

---

# Skill Loading

Skills declared in YAML frontmatter load **automatically** from Claude Code's global registry:

```yaml
skills: skill1, skill2    # Auto-loaded at subagent start
```

Skills can come from any source (plugins, user, project) - all are globally available.

---

## Pattern 1: Single-Skill Consumer

**Use when**: Focused, single-domain task

```yaml
---
name: sql-agent
skills: sql-helper
tools: [Read, Grep, Glob]
model: sonnet
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
model: sonnet
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
Auto-call relevant skills (via Skill tool)
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
1. **Serena Gateway** - Codebase exploration with MCP isolation (see `mcp-gateway-patterns`)
2. **skill-rules.json** - Trigger patterns for auto-activation (see `skill-activation-patterns`)
3. **claude-mem** - Context persistence across sessions (see `references/enhanced-agent.md`)

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
- Minimal tools (Read, Grep, Glob)
- "Use {skill} for all operations"

**Multi-Skill:**
- Name: `{domain}-orchestrator`
- Include Task tool for sub-delegation
- Document when to use each skill
- "Don't activate all skills for simple requests"

**Enhanced:**
- Name: `{domain}-smart-agent`
- Include Task + Skill tools
- Configure Serena Gateway for exploration
- Set claude-mem project name
- "Explore codebase before selecting skills"
