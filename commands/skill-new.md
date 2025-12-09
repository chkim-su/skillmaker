---
description: Create a brand new skill from scratch. Guides through skill type selection (knowledge/hybrid/tool) and uses init_skill.py for proper structure.
argument-hint: "[skill description]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Create New Skill

**FIRST: Load the skillmaker:skill-design skill** using the Skill tool.

Create a brand new skill with proper structure based on its type.

## Your Task

### Step 1: Quick Assessment

If user provided a description, ask 2-3 focused questions:

1. **Is this primarily about KNOWLEDGE or AUTOMATION?**
   - Guidelines, patterns, best practices → Knowledge skill
   - File manipulation, data processing → Tool skill
   - Both → Hybrid skill

2. **Will the same operations be performed repeatedly?**
   - Yes → Likely needs scripts (Tool/Hybrid)
   - No → Likely Knowledge skill

3. **What file formats or external tools involved?**
   - PDF, XLSX, images, APIs → Tool skill with scripts

### Step 2: Determine Skill Type

Based on answers, classify:

| Type | When to Use | Structure |
|------|-------------|-----------|
| **Knowledge** | Guidelines, patterns, decisions depend on context | SKILL.md + references/ |
| **Hybrid** | Mix of guidance + helper scripts | SKILL.md + scripts/ + references/ |
| **Tool** | File manipulation, same operations repeatedly | SKILL.md + scripts/ |

### Step 3: Launch skill-architect Agent

Use the Task tool to launch the `skill-architect` agent:

```
Task tool with:
- subagent_type: "skillmaker:skill-architect"
- description: "Design new skill"
- prompt: "Design a new skill based on:

User request: {description_from_user}
Preliminary type: {knowledge | hybrid | tool}

Follow your process:
1. Ask clarifying questions (one at a time)
2. Determine final skill type with reasoning
3. Design complete structure
4. Present design for approval

Use scripts/init_skill.py to initialize and scripts/validate_skill.py to validate.

Return the complete skill design including:
- Skill name and type
- SKILL.md content
- Scripts needed (if tool/hybrid) with implementations
- References needed with content
- Assets needed (if any)
"
```

### Step 4: Review and Create

After agent completes:

1. **Parse the design output**
2. **Present summary to user**:

```
✨ Skill Design Complete

Name: {skill-name}
Type: {Knowledge | Hybrid | Tool} Skill

Trigger Phrases:
- {phrase1}
- {phrase2}

Structure:
{skill-name}/
├── SKILL.md
├── scripts/        # if applicable
├── references/     # if applicable
└── assets/         # if applicable

Scripts: {list if any}
References: {list if any}

Ready to create?
```

3. **Wait for confirmation**

### Step 5: Create Skill Files

**Use init_skill.py for proper structure:**

```bash
# Create skill structure
python ${CLAUDE_PLUGIN_ROOT}/scripts/init_skill.py {skill-name} --type {type} --path .claude/skills
```

Then customize the generated files with actual content from the design.

### Step 6: Implement Content

**For SKILL.md**:
- Replace TODO placeholders with real content
- Add trigger phrases to description
- Document available scripts (if any)

**For scripts/** (if tool/hybrid):
- Implement actual functionality
- Test each script
- Make executable: `chmod +x scripts/*.py`

**For references/**:
- Add detailed patterns and documentation

### Step 7: Validate and Confirm

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_skill.py .claude/skills/{skill-name}
```

Show results to user:

```
✅ Created skill: {skill-name}

Type: {type}

Files created:
- .claude/skills/{skill-name}/SKILL.md
- .claude/skills/{skill-name}/scripts/{script}.py (if applicable)
- .claude/skills/{skill-name}/references/{ref}.md (if applicable)

Validation: ✅ Passed

Usage:
- Load: Use Skill tool with "{skill-name}"
- In agents: skills: {skill-name}

Next steps:
{if tool/hybrid}
1. Test scripts with real inputs
{endif}
2. Try the skill with a sample request
3. Create an agent: /skillmaker:skill-cover
```

## Quick Path for Simple Skills

If user just wants a knowledge skill quickly:

```bash
# Initialize
python ${CLAUDE_PLUGIN_ROOT}/scripts/init_skill.py {name} --type knowledge --path .claude/skills

# Edit SKILL.md with actual content
# Validate
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_skill.py .claude/skills/{name}
```

## Important Notes

- **Always use init_skill.py** - Don't create structure manually
- **Determine type early** - It shapes everything
- **Test scripts** - Tool skills need working scripts
- **Validate before done** - Catch issues early
- **File location**: PROJECT's `.claude/skills/` directory
