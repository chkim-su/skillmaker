# Skillization: Convert Existing Code to Skill

Transform existing functionality, projects, or functions into reusable skills.

## Your Task

Use the Task tool to launch the `skill-converter` agent to analyze existing code and convert it to skill format:

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

5. **Skill Creation**
   - Create SKILL.md with:
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

## Output

Create skill structure in .claude/skills/{skill-name}/ that wraps or documents the existing functionality.
"
```

Note: If the user specified a target (e.g., `/skillmaker:skillization our auth middleware`), include it in the prompt.
