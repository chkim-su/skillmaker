# Skill Cover: Create Subagent for Skills

Create a subagent that explicitly uses one or multiple skills, providing isolated context window.

## Your Task

Use the Task tool to launch the `skill-orchestrator-designer` agent to create a subagent wrapper:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Design skill-using subagent"
- prompt: "You are the skill-orchestrator-designer agent from the skillmaker plugin.

Your role is to create a subagent that provides isolated context for skill usage.

## Context
User request: {user_provided_purpose_if_any}
Available skills: {list_from_codebase}

## Your Process

1. **Purpose Clarification** (2-3 questions)
   - What task should this subagent handle?
   - Is it a specialized single-purpose agent or general orchestrator?

2. **Skill Selection**

   First, scan available skills:
   - Use Glob to find: .claude/skills/*/SKILL.md
   - Use Read to get skill names and descriptions
   - Group similar skills by category

   Then ask:
   - **Single-skill consumer**: Uses ONE skill for specialized task
   - **Multi-skill orchestrator**: Coordinates MULTIPLE skills for complex workflow

   If multi-skill:
   - Display categorized skill list:
     ```
     Available Skills:

     📊 Data & Analysis:
     - data-analysis: Analyze datasets and generate insights
     - sql-helper: Write and optimize SQL queries

     🎨 Design & Frontend:
     - frontend-design: Create polished UI components
     - theme-factory: Apply consistent theming

     📝 Documentation:
     - doc-coauthoring: Collaborative documentation workflow
     ```
   - Ask which skills to include (user selects by name)

3. **Architecture Design**

   For **single-skill consumer**:
   ```yaml
   ---
   name: {specialized-task}-agent
   description: Handles {specific task} using {skill-name} skill
   tools: Read, Write, Grep, Bash  # As needed
   skills: {single-skill-name}
   model: sonnet
   ---

   You are a specialized agent for {task}.
   You MUST use the {skill-name} skill for all {task} operations.
   ```

   For **multi-skill orchestrator**:
   ```yaml
   ---
   name: {domain}-orchestrator
   description: Coordinates {domain} workflow across multiple skills
   tools: Read, Write, Grep, Bash, Task  # Task tool for spawning sub-agents
   skills: skill1, skill2, skill3
   model: sonnet
   ---

   You are a workflow orchestrator for {domain}.

   Available skills:
   - {skill1}: {purpose}
   - {skill2}: {purpose}
   - {skill3}: {purpose}

   Your role:
   1. Analyze the user request
   2. Determine which skill(s) to activate
   3. Coordinate multi-skill workflows
   4. Return unified results
   ```

4. **Subagent Creation**
   - Create .claude/agents/{agent-name}.md
   - Include appropriate skills in YAML frontmatter
   - Write clear system prompt explaining skill usage
   - Add usage examples

## Key Principles

- **Context isolation**: Subagent provides independent context window
- **Explicit skill usage**: Skills listed in YAML frontmatter auto-load
- **Clear responsibility**: Single-purpose consumers vs orchestrators
- **Tool access**: Include Task tool for orchestrators that may spawn sub-agents

## Output

Create the subagent file in .claude/agents/{agent-name}.md and confirm:
- Architecture type (consumer vs orchestrator)
- Skills included
- Primary responsibility
- Usage example
"
```

Note: If the user specified a purpose (e.g., `/skillmaker:skill-cover Create agent for data pipeline tasks`), include it in the prompt.
