# Skillmaker Plugin

> Create perfect skills and subagents that use them explicitly. Solve the context window problem with skill-based architecture.

## The Problem

**Skills** have all the capabilities of subagents, but lack one critical feature: **independent context windows**.

**Subagents** provide isolated context, preventing pollution of the main conversation.

## The Solution

**Skillmaker** helps you:

1. **Create perfect skills** with progressive disclosure and clear triggers
2. **Wrap existing code** into reusable skill format
3. **Build subagents** that explicitly use skills, combining isolated context with domain expertise

## Architecture Insight

```
Main Conversation (Context Window 1)
        ↓
        └─> Subagent (Context Window 2) [ISOLATED]
            └─> Skills (auto-loaded into Context 2)
                - skill-a: Domain expertise
                - skill-b: Domain expertise
                - skill-c: Domain expertise
```

**Result**: Isolated context + Expert knowledge = Perfect combination

## Commands

### `/skillmaker:skill-new` - Create New Skill

Create a brand new skill from scratch.

**Usage:**
```bash
/skillmaker:skill-new                              # Interactive mode
/skillmaker:skill-new Create a skill for AWS deployments   # With description
```

**Process:**
1. Understands your intent (3-5 questions)
2. Clarifies scope (3-5 questions)
3. Designs structure (progressive disclosure)
4. Generates complete skill in `.claude/skills/{name}/`

**Output:**
```
.claude/skills/{skill-name}/
├── SKILL.md           # Core skill (500-1000 words)
├── reference.md       # Detailed docs (optional)
├── examples.md        # Usage examples (optional)
└── scripts/           # Utilities (optional)
```

---

### `/skillmaker:skillization` - Convert Existing Code

Transform existing functionality into a reusable skill.

**Usage:**
```bash
/skillmaker:skillization                           # Interactive mode
/skillmaker:skillization our auth middleware       # Target specific code
```

**Process:**
1. Discovers target functionality (3-5 questions)
2. Analyzes existing code (uses Read, Grep, Glob)
3. Extracts patterns and knowledge
4. Creates skill that wraps/documents existing code

**Key principle**: Skills reference existing code, not duplicate it.

---

### `/skillmaker:skill-cover` - Create Skill-Using Subagent

Build a subagent that provides isolated context for skill usage.

**Usage:**
```bash
/skillmaker:skill-cover                            # Interactive mode
/skillmaker:skill-cover Create agent for data pipelines   # With purpose
```

**Process:**
1. Clarifies purpose (2-3 questions)
2. Scans available skills (categorized list)
3. Determines architecture:
   - **Single-Skill Consumer**: Specialized agent for one skill
   - **Multi-Skill Orchestrator**: Coordinates multiple skills
4. Creates subagent in `.claude/agents/{name}.md`

**Architecture Types:**

#### Single-Skill Consumer
```yaml
---
name: sql-agent
description: Handles SQL operations using sql-helper skill
skills: sql-helper
tools: Read, Write, Bash
---

You are a SQL specialist. Use sql-helper skill for all operations.
```

**Best for**: Focused, single-domain tasks

#### Multi-Skill Orchestrator
```yaml
---
name: fullstack-orchestrator
description: Coordinates frontend, backend, and database tasks
skills: frontend-design, api-generator, migration-patterns
tools: Read, Write, Bash, Task
---

You coordinate full-stack development:
- frontend-design: For UI
- api-generator: For APIs
- migration-patterns: For database

Choose skill(s) based on request domain.
```

**Best for**: Complex, multi-domain workflows

---

## Quick Start

### 1. Create Your First Skill

```bash
/skillmaker:skill-new
```

Follow the interactive questions to create a skill.

### 2. Wrap Existing Code

```bash
/skillmaker:skillization
```

Point it to existing functionality to skillize it.

### 3. Create a Subagent

```bash
/skillmaker:skill-cover
```

Build a subagent that uses your skills with isolated context.

### 4. Use Your Subagent

```bash
# In main conversation
/my-custom-agent [your request]
```

The subagent runs in isolated context, using auto-loaded skills.

---

## Examples

### Example 1: Specialized Single-Skill Agent

**Scenario**: You have a complex database migration pattern.

```bash
# Step 1: Create skill
/skillmaker:skill-new Create a skill for database migrations

# Step 2: Create specialized agent
/skillmaker:skill-cover Create an agent that only handles migrations

# Step 3: Use it
/migration-agent Create a migration to add user_preferences table
```

**Result**: Migration agent runs in isolated context, using migration-patterns skill exclusively.

### Example 2: Multi-Skill Orchestrator

**Scenario**: You work on full-stack features frequently.

```bash
# Step 1: Create/identify skills
# Assume you have: frontend-design, api-generator, migration-patterns

# Step 2: Create orchestrator
/skillmaker:skill-cover Create a full-stack orchestrator

# Agent shows categorized skill list:
📊 Data & Analysis:
- migration-patterns

🎨 Design & Frontend:
- frontend-design

📦 Code Generation:
- api-generator

# You select: frontend-design, api-generator, migration-patterns

# Step 3: Use orchestrator
/fullstack-orchestrator Add user profile feature with avatar upload
```

**Result**: Orchestrator coordinates all three skills, handling UI, API, and database in one workflow.

### Example 3: Skillizing Existing Code

**Scenario**: You have a well-tested auth middleware you want to reuse.

```bash
# Step 1: Skillize existing code
/skillmaker:skillization our auth middleware

# Analyzer asks questions, reads your code, creates skill
# Result: auth-patterns skill in .claude/skills/auth-patterns/

# Step 2: Create consumer agent
/skillmaker:skill-cover Create agent for auth implementations

# Step 3: Use it
/auth-agent Add JWT authentication to the API
```

**Result**: auth-agent uses auth-patterns skill, which references your existing, tested code.

---

## Plugin Structure

```
.claude-plugins/skillmaker/
├── .claude-plugin/
│   └── plugin.json                 # Plugin metadata
├── commands/
│   ├── skill-new.md                # Create new skill
│   ├── skillization.md             # Convert existing code
│   └── skill-cover.md              # Create subagent
└── skills/
    ├── skill-design/               # Skill best practices
    │   └── SKILL.md
    ├── skill-catalog/              # Skill categorization
    │   └── SKILL.md
    └── orchestration-patterns/     # Architecture patterns
        └── SKILL.md
```

---

## Key Concepts

### Progressive Disclosure

Skills use a layered approach:

1. **SKILL.md**: Concise core (~500-1000 words)
2. **reference.md**: Detailed documentation (loaded as needed)
3. **examples.md**: Comprehensive examples (loaded as needed)
4. **scripts/**: Utility tools (used as needed)

This keeps context usage minimal by default.

### Trigger Phrases

Each skill includes 5-10 specific phrases that activate it:

```yaml
Trigger phrases:
- "create a hook"
- "add a PreToolUse hook"
- "validate tool use"
```

These help Claude know when to activate the skill.

### Tool Restrictions

Skills can limit tool access:

```yaml
allowed-tools: Read, Grep, Glob  # Read-only skill
```

This prevents skills from overstepping their domain.

### Auto-Loading in Subagents

When you list skills in subagent YAML:

```yaml
skills: skill1, skill2, skill3
```

They're **automatically loaded** when the subagent starts. No explicit activation needed.

---

## Best Practices

### When to Create a Skill

✅ **Create a skill when:**
- You have specialized domain knowledge
- A pattern is used repeatedly
- The task needs specific tool restrictions
- Progressive disclosure would help

❌ **Don't create a skill for:**
- One-time tasks
- Generic operations
- Simple prompts

### When to Create a Subagent

✅ **Create a subagent when:**
- You need isolated context
- The task generates large intermediate results
- You want to prevent main conversation pollution
- You're building a specialized tool

❌ **Don't create a subagent for:**
- Simple, quick tasks
- When main context is fine
- Latency is critical

### Single-Skill vs Multi-Skill

| Use Case | Architecture |
|----------|--------------|
| Focused domain (SQL, migrations, auth) | Single-Skill Consumer |
| Multi-domain workflow (full-stack, data pipeline) | Multi-Skill Orchestrator |
| Frequently switching skills | Multi-Skill Orchestrator |
| One clear expertise area | Single-Skill Consumer |

---

## FAQ

### Q: How is this different from just creating a subagent?

**A**: Subagents alone don't have domain expertise built-in. Skills provide:
- Structured knowledge (progressive disclosure)
- Trigger phrases (automatic activation)
- Tool restrictions (scoped permissions)
- Reusability (multiple subagents can use the same skill)

### Q: Can I use skills without subagents?

**A**: Yes! Skills work in the main conversation too. But subagents provide isolated context, which prevents large intermediate results from polluting your main conversation.

### Q: How many skills should an orchestrator have?

**A**: Keep it focused. 3-5 related skills is ideal. More than 7 and you should consider splitting into multiple orchestrators.

### Q: Can skills call other skills?

**A**: No, skills don't call other skills. But orchestrator subagents can use multiple skills and coordinate between them.

### Q: What's the context cost?

**A**: Each SKILL.md is ~500-1000 words. A 3-skill orchestrator adds ~1500-3000 words to context—far less than loading entire codebases.

---

## Troubleshooting

### Skill not activating?

1. Check trigger phrases are specific
2. Verify skill description matches use case
3. Test with explicit trigger phrase in prompt

### Subagent not using skill?

1. Verify skill is listed in YAML `skills:` field
2. Check system prompt mentions the skill
3. Confirm skill files exist in `.claude/skills/`

### Too many skills loading?

Use single-skill consumers instead of orchestrators for focused tasks.

---

## Contributing

This plugin follows the official [claude-code plugin patterns](https://github.com/anthropics/claude-code/tree/main/plugins).

To extend:
1. Add new commands in `commands/`
2. Add supporting skills in `skills/`
3. Update `plugin.json` manifest

---

## License

MIT

---

## Credits

Inspired by:
- [hookify](https://github.com/anthropics/claude-code/tree/main/plugins/hookify) - Agent + skill pairing pattern
- [plugin-dev](https://github.com/anthropics/claude-code/tree/main/plugins/plugin-dev) - Progressive disclosure and multi-phase workflows
- [feature-dev](https://github.com/anthropics/claude-code/tree/main/plugins/feature-dev) - Orchestration patterns
