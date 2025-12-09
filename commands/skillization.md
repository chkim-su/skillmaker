---
description: Transform existing functionality, projects, or functions into reusable skills. Analyzes existing code with 20-questions approach.
argument-hint: "[target code/functionality]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Skillization: Convert Existing Code to Skill

**FIRST: Load the skillmaker:skill-design skill** using the Skill tool to understand how to structure skills properly.

Transform existing functionality, projects, or functions into reusable skills.

## Your Task

After loading the skill-design skill, use the Task tool to launch the `skill-converter` agent to analyze existing code and convert it to skill format:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Convert existing code to skill"
- prompt: "You are the skill-converter agent from the skillmaker plugin.

Your role is to analyze existing code/functionality and transform it into a reusable skill.

## Context
User request: {user_provided_target_if_any}
Codebase: Available via Read, Grep, Glob tools

## Your Process

1. **Discovery** (3-5 questions)
   - What functionality should be skillized?
   - Where is it located? (files, functions, modules)
   - What's the current usage pattern?

2. **Analysis** (Use tools to explore)
   - Read relevant code files
   - Understand dependencies and patterns
   - Identify core logic vs boilerplate

3. **Clarification** (3-5 questions)
   - Should the skill wrap existing code or document it?
   - What variations/options exist?
   - What context does a user need to provide?

4. **Extraction**
   - Identify the core knowledge/pattern
   - Determine trigger phrases
   - Design progressive disclosure structure

5. **Present Skill Design**
   - DO NOT create files yourself
   - Return structured design to the command
   - SKILL.md should include:
     - Clear description of the functionality
     - When to use it
     - How it wraps/uses existing code
     - Trigger phrases based on current usage
   - Add reference.md if complex patterns exist
   - Include examples.md with actual usage from codebase

## Key Principles

- **Preserve existing code**: Skills should reference/use existing code, not duplicate it
- **Document patterns**: Extract the "how" and "when", not just the "what"
- **Real examples**: Use actual code from the project as examples
- **Clear triggers**: Base trigger phrases on how the functionality is currently used

## Output Format

After completing the analysis and design, return it in this format:

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

{Full SKILL.md markdown content that references existing code}

=== END SKILL.MD ===

REFERENCES_NEEDED: {yes|no}
{If yes, for each reference file:}
REFERENCE_FILE: {filename}.md
{content with code patterns from codebase}
END_REFERENCE_FILE

EXAMPLES_NEEDED: {yes|no}
{If yes, for each example file:}
EXAMPLE_FILE: {filename}.md
{content with actual usage examples from codebase}
END_EXAMPLE_FILE

This structured format allows the command to parse and create all necessary files.
"
```

Note: If the user specified a target (e.g., `/skillmaker:skillization our auth middleware`), include it in the prompt.

## Step 2: Review Design and Confirm

After the skill-converter agent completes, you will receive a structured skill design.

1. **Parse the agent's output** to extract:
   - Skill name
   - Description
   - Allowed tools
   - SKILL.md content
   - References files (if any)
   - Examples files (if any)

2. **Present design summary to user**:
   ```
   ✨ Skillization Complete

   Name: {skill-name}
   Description: {description}

   Wraps existing code: {file paths or modules}

   Trigger Phrases:
   - {phrase1}
   - {phrase2}
   - {phrase3}

   Allowed Tools: {tools}

   Structure:
   - SKILL.md (wraps existing functionality)
   - references/{filename}.md (code patterns, if needed)
   - examples/{filename}.md (actual usage examples from codebase)
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
- Content: Extracted reference content (should include code patterns from existing codebase)

**For each example file** (if EXAMPLES_NEEDED: yes):
- Extract content between `EXAMPLE_FILE: {filename}.md` and `END_EXAMPLE_FILE`
- Use Write tool
- Path: `.claude/skills/{skill-name}/examples/{filename}.md`
- Content: Extracted example content (should include actual usage from existing code)

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

This skill wraps your existing code in: {file paths}

Usage:
- Load explicitly: Use Skill tool with "{skill-name}"
- In agents: Add to YAML frontmatter: skills: {skill-name}
- In commands: Add "FIRST: Load {skill-name} skill"

Next steps:
- Test the skill with requests that previously used the original code
- Verify the skill properly references existing functionality
- Create a specialized agent using this skill (use /skillmaker:skill-cover)
- Share with your team to standardize usage patterns
```

## Important Notes

- **File location**: Create files in PROJECT's `.claude/` directory (current working directory), NOT the plugin's `.claude/`
- **Path format**: Use relative paths like `.claude/skills/{name}/SKILL.md`
- **Verification**: Always verify files were created before confirming to user
- **Preserve code**: Skills should reference existing code, not duplicate it
- **Examples**: Use actual code examples from the project in the examples/ directory
