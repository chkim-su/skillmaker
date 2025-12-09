---
description: Create a brand new skill from scratch based on conversation context or user goals. Uses 20-questions clarification approach.
argument-hint: "[skill description]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Create New Skill

**FIRST: Load the skillmaker:skill-design skill** using the Skill tool to understand skill structure, progressive disclosure, and trigger phrases.

Create a brand new skill from scratch based on conversation context or user goals.

## Your Task

After loading the skill-design skill, use the Task tool to launch the `skill-architect` agent to guide the user through creating a new skill:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Create new skill with 20-questions"
- prompt: "You are the skill-architect agent from the skillmaker plugin.

Your role is to create a perfect, production-ready skill through iterative clarification.

## Context
User request: {user_provided_description_if_any}
Conversation history: Available in context

## Your Process

1. **Understand Intent** (3-5 questions)
   - What problem does this skill solve?
   - What triggers should activate it?
   - What tools/knowledge does it need?

2. **Clarify Scope** (3-5 questions)
   - Single-purpose or multi-capability?
   - What are edge cases?
   - What should it NOT do?

3. **Design Structure**
   - SKILL.md with trigger phrases
   - Progressive disclosure (reference.md, examples.md if needed)
   - Allowed tools specification

4. **Present Skill Design**
   - DO NOT create files yourself
   - Return structured design to the command
   - Include complete SKILL.md content
   - Specify any references/ or examples/ files needed

## Key Principles

- **20-questions approach**: Ask focused questions, one at a time
- **Progressive disclosure**: Keep SKILL.md concise, detailed docs separate
- **Trigger phrases**: Include 5-10 specific phrases that should activate the skill
- **Tool restrictions**: Use allowed-tools to limit scope appropriately

## Output Format

After completing the design, return it in this format:

=== SKILL DESIGN ===
NAME: {skill-name}
DESCRIPTION: {full description with trigger phrases}
ALLOWED_TOOLS: ["Tool1", "Tool2", "Tool3"]

=== SKILL.MD CONTENT ===
---
name: {skill-name}
description: {description}
allowed-tools: ["Tool1", "Tool2"]
---

# {Skill Title}

{Full SKILL.md markdown content here}

=== END SKILL.MD ===

REFERENCES_NEEDED: {yes|no}
{If yes, for each reference file:}
REFERENCE_FILE: {filename}.md
{content}
END_REFERENCE_FILE

EXAMPLES_NEEDED: {yes|no}
{If yes, for each example file:}
EXAMPLE_FILE: {filename}.md
{content}
END_EXAMPLE_FILE

This structured format allows the command to parse and create all necessary files.
"
```

Note: If the user provided a description with the command (e.g., `/skillmaker:skill-new Create a skill for database migrations`), include it in the prompt.

## Step 2: Review Design and Confirm

After the skill-architect agent completes, you will receive a structured skill design.

1. **Parse the agent's output** to extract:
   - Skill name
   - Description
   - Allowed tools
   - SKILL.md content
   - References files (if any)
   - Examples files (if any)

2. **Present design summary to user**:
   ```
   ✨ Skill Design Complete

   Name: {skill-name}
   Description: {description}

   Trigger Phrases:
   - {phrase1}
   - {phrase2}
   - {phrase3}

   Allowed Tools: {tools}

   Structure:
   - SKILL.md (core skill)
   - references/{filename}.md (if needed)
   - examples/{filename}.md (if needed)
   ```

3. **Ask for confirmation**:
   "Ready to create this skill? This will create files in .claude/skills/{skill-name}/"

4. **Wait for user confirmation** before proceeding to Step 3.

## Step 3: Create Skill Files

**IMPORTANT**: Files must be created in the PROJECT's .claude directory (current working directory), NOT the plugin directory.

### 3.1 Create Directory Structure

Use Bash tool to create directories:

```bash
mkdir -p .claude/skills/{skill-name}
mkdir -p .claude/skills/{skill-name}/references  # if references needed
mkdir -p .claude/skills/{skill-name}/examples    # if examples needed
```

### 3.2 Write SKILL.md

Use Write tool:
- **Path**: `.claude/skills/{skill-name}/SKILL.md`
- **Content**: Extract the SKILL.md content from between `=== SKILL.MD CONTENT ===` and `=== END SKILL.MD ===`

The content must include YAML frontmatter:
```yaml
---
name: {skill-name}
description: {description with trigger phrases}
allowed-tools: ["Tool1", "Tool2"]
---
```

### 3.3 Write Supporting Files

**For each reference file** (if REFERENCES_NEEDED: yes):
- Extract content between `REFERENCE_FILE: {filename}.md` and `END_REFERENCE_FILE`
- Use Write tool
- Path: `.claude/skills/{skill-name}/references/{filename}.md`
- Content: Extracted reference content

**For each example file** (if EXAMPLES_NEEDED: yes):
- Extract content between `EXAMPLE_FILE: {filename}.md` and `END_EXAMPLE_FILE`
- Use Write tool
- Path: `.claude/skills/{skill-name}/examples/{filename}.md`
- Content: Extracted example content

### 3.4 Verify Creation

Use Glob tool to verify all files were created:
```
Pattern: .claude/skills/{skill-name}/**/*
```

Confirm all expected files exist.

### 3.5 Show Confirmation

Display to user:
```
✅ Created skill: {skill-name}

Files created:
- .claude/skills/{skill-name}/SKILL.md
- .claude/skills/{skill-name}/references/{filename}.md (if applicable)
- .claude/skills/{skill-name}/examples/{filename}.md (if applicable)

Skill is ready to use!

Usage:
- Load explicitly: Use Skill tool with "{skill-name}"
- In agents: Add to YAML frontmatter: skills: {skill-name}
- In commands: Add "FIRST: Load {skill-name} skill"

Example files for reference:
- Simple skill: /examples/example-skill-simple.md
- Skill with references: /examples/example-skill-with-references.md
- Single-skill agent: /examples/example-agent-single-skill.md

Next steps:
- Test the skill with a simple request
- Refine based on actual usage
- Create a specialized agent that uses this skill (use /skillmaker:skill-cover)
```

## Important Notes

- **File location**: Create files in PROJECT's `.claude/` directory (current working directory), NOT the plugin's `.claude/`
- **Path format**: Use relative paths like `.claude/skills/{name}/SKILL.md`
- **Verification**: Always verify files were created before confirming to user
- **Availability**: Skills are available immediately after creation (no restart needed)
- **Examples**: Reference the example files in `/examples/` directory for guidance
