---
name: orchestration-patterns
description: Patterns for single-skill vs multi-skill subagent architectures. Use when designing subagents that consume skills.
allowed-tools: ["Read", "Write"]
---

# Orchestration Patterns

This skill provides architectural patterns for subagents that use skills.

## Two Core Patterns

### Pattern 1: Single-Skill Consumer

**When to use:**
- Specialized, focused task
- One skill provides all necessary knowledge
- Need isolated context for that specific skill

**Architecture:**
```
User Request
    ↓
Single-Skill Consumer Subagent [Isolated Context]
    ↓
    Uses: skill-x (auto-loaded)
    ↓
Focused Result
```

**Example YAML:**
```yaml
---
name: database-migration-agent
description: Handles database schema migrations using migration-patterns skill
tools: Read, Write, Bash
skills: migration-patterns
model: sonnet
---

You are a database migration specialist.

Your ONLY task: Create and manage database migrations using the migration-patterns skill.

Process:
1. Activate migration-patterns skill (auto-loaded)
2. Understand schema change request
3. Generate migration files following patterns
4. Validate migration safety
5. Return migration code

IMPORTANT: All migrations must follow the patterns in migration-patterns skill.
```

**Benefits:**
- ✅ Focused expertise
- ✅ Isolated context (no pollution)
- ✅ Clear responsibility
- ✅ Fast execution

**Drawbacks:**
- ❌ Limited to one domain
- ❌ Can't coordinate across skills

---

### Pattern 2: Multi-Skill Orchestrator

**When to use:**
- Complex workflow spanning multiple domains
- Need to coordinate different skills
- Task requires decision-making about which skill to use

**Architecture:**
```
User Request
    ↓
Multi-Skill Orchestrator [Isolated Context]
    ↓
    Skills Available: skill-a, skill-b, skill-c (all auto-loaded)
    ↓
    Decision: Which skill(s) for this request?
    ↓
    Execution: May use 1+ skills
    ↓
Coordinated Result
```

**Example YAML:**
```yaml
---
name: fullstack-orchestrator
description: Coordinates frontend, backend, and database tasks across multiple skills
tools: Read, Write, Bash, Grep, Glob, Task
skills: frontend-design, api-generator, migration-patterns, deployment-tool
model: sonnet
---

You are a full-stack development orchestrator.

Available skills (auto-loaded):
- **frontend-design**: UI components and styling
- **api-generator**: REST API endpoints
- **migration-patterns**: Database schemas
- **deployment-tool**: Deployment workflows

Your role:
1. Analyze user request
2. Determine which skill(s) to activate based on task:
   - UI change? → Use frontend-design
   - API endpoint? → Use api-generator
   - Schema change? → Use migration-patterns
   - Deploy? → Use deployment-tool
   - Full feature? → Use multiple skills in sequence

3. Coordinate workflow:
   - For complex features, activate skills in order
   - Pass results between skills
   - Ensure consistency across layers

4. Return unified implementation

IMPORTANT: Choose skills based on request domain. Don't activate all skills for simple requests.
```

**Benefits:**
- ✅ Handles complex workflows
- ✅ Coordinates multiple domains
- ✅ Flexible skill selection
- ✅ Still has isolated context

**Drawbacks:**
- ⚠️ More complex decision-making
- ⚠️ May load unnecessary skills
- ⚠️ Requires clear orchestration logic

---

## Decision Matrix

| Question | Single-Skill | Multi-Skill |
|----------|--------------|-------------|
| Task scope? | Narrow, focused | Broad, multi-domain |
| Skill count needed? | 1 | 2+ |
| Coordination needed? | No | Yes |
| Context size concern? | Low | Medium |
| Execution speed? | Fast | Moderate |

## Advanced Pattern: Hierarchical Orchestration

For very complex workflows:

```
User Request
    ↓
Top-Level Orchestrator [Context 1]
    ↓
    Spawns → Specialized Consumer 1 [Context 2] → skill-a
           → Specialized Consumer 2 [Context 3] → skill-b
           → Specialized Consumer 3 [Context 4] → skill-c
    ↓
Aggregated Result
```

**Example:**
```yaml
---
name: feature-orchestrator
description: Breaks down features and delegates to specialized agents
tools: Task  # Only Task tool to spawn sub-agents
skills: project-analysis  # Only for understanding request
model: sonnet
---

You are a feature development orchestrator.

Your role:
1. Use project-analysis skill to understand feature request
2. Break down into sub-tasks:
   - UI → Spawn frontend-agent (uses frontend-design skill)
   - API → Spawn backend-agent (uses api-generator skill)
   - DB → Spawn database-agent (uses migration-patterns skill)
3. Each sub-agent has isolated context + their specific skill
4. Aggregate results from all sub-agents
5. Return complete feature

This pattern provides MAXIMUM context isolation.
```

## Skill Auto-Loading Behavior

When you list skills in YAML frontmatter:

```yaml
skills: skill1, skill2, skill3
```

**What happens:**
1. Subagent starts with clean context
2. Each SKILL.md is loaded into context
3. Skills are immediately available (no explicit activation needed)
4. Subagent can use any/all skills based on task

**Context usage:**
- Each SKILL.md: ~500-1000 words
- 3 skills ≈ 1500-3000 words added to context
- Still much smaller than full codebase

## Best Practices

### For Single-Skill Consumers

1. **Name clearly**: `{domain}-agent`, e.g., `sql-agent`
2. **Restrict tools**: Only what the skill needs
3. **Clear mandate**: "You MUST use {skill} for all operations"
4. **Fast model**: Use `sonnet` for speed

### For Multi-Skill Orchestrators

1. **Name for domain**: `{domain}-orchestrator`, e.g., `data-orchestrator`
2. **Include Task tool**: For spawning sub-agents if needed
3. **Document skills**: List each skill with its purpose in prompt
4. **Decision logic**: Explain when to use each skill
5. **Prevent overuse**: "Don't activate all skills for simple requests"

## Example: Converting Single to Multi

**Before (Single-Skill):**
```yaml
name: frontend-agent
skills: frontend-design
```

**After (Multi-Skill):**
```yaml
name: ui-orchestrator
skills: frontend-design, theme-factory, component-library
tools: Read, Write, Task  # Added Task
```

**System prompt changes:**
```diff
- You are a frontend specialist using frontend-design skill.
+ You are a UI orchestrator with access to multiple design skills:
+ - frontend-design: Create new components
+ - theme-factory: Apply theming
+ - component-library: Use existing components
+
+ Choose the appropriate skill(s) based on the request.
```

## Testing Your Pattern

After creating a subagent:

1. **Test with simple request**: Should use minimal skills
2. **Test with complex request**: Should coordinate appropriately
3. **Check context usage**: Use `/tasks` to see context size
4. **Verify isolation**: Main conversation should stay clean

## Key Takeaway

**Single-Skill Consumer** = Specialized tool (like a screwdriver)
**Multi-Skill Orchestrator** = Versatile toolkit (like a multi-tool)

Choose based on task complexity and domain scope.
