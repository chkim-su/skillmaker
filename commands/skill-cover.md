---
description: Create a subagent that explicitly uses one or multiple skills. Determines if single-skill consumer or multi-skill orchestrator.
argument-hint: "[subagent purpose]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Skill Cover: Create Subagent for Skills

**FIRST: Load the skillmaker:orchestration-patterns skill** using the Skill tool to understand single-skill vs multi-skill architectures.

Create a subagent that explicitly uses one or multiple skills, providing isolated context window.

## Your Task

After loading the orchestration-patterns skill, use the Task tool to launch the `skill-orchestrator-designer` agent to create a subagent wrapper:

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

4. **Present Agent Design**
   - DO NOT create files yourself
   - Return structured agent definition to the command
   - Include appropriate skills in YAML frontmatter
   - Write clear system prompt explaining skill usage
   - Add usage examples

## Key Principles

- **Context isolation**: Subagent provides independent context window
- **Explicit skill usage**: Skills listed in YAML frontmatter auto-load
- **Clear responsibility**: Single-purpose consumers vs orchestrators
- **Tool access**: Include Task tool for orchestrators that may spawn sub-agents

## Output Format

After completing the design, return it in this format:

=== AGENT DESIGN ===
NAME: {agent-name}
DESCRIPTION: {agent description}
ARCHITECTURE: {single-skill-consumer | multi-skill-orchestrator}
SKILLS: {skill1, skill2, skill3}
TOOLS: ["Read", "Write", "Grep", "Glob", "Bash", "Task"]
MODEL: sonnet
COLOR: {blue|green|yellow|cyan|magenta}

=== AGENT.MD CONTENT ===
---
name: {agent-name}
description: {description}
tools: ["Read", "Write", "Grep"]
skills: {skill-list}
model: sonnet
color: {color}
---

# {Agent Title}

{Full agent markdown content with system prompt}

=== END AGENT.MD ===

This structured format allows the command to parse and create the agent file.
"
```

Note: If the user specified a purpose (e.g., `/skillmaker:skill-cover Create agent for data pipeline tasks`), include it in the prompt.

## Step 2: Review Agent Design and Confirm

After the skill-orchestrator-designer agent completes, you will receive a structured agent design.

1. **Parse the agent's output** to extract:
   - Agent name
   - Description
   - Architecture type (single-skill-consumer or multi-skill-orchestrator)
   - Skills list
   - Tools list
   - Model and color
   - Agent.md content

2. **Present design summary to user**:
   ```
   🤖 Agent Design Complete

   Name: {agent-name}
   Description: {description}

   Architecture: {single-skill-consumer | multi-skill-orchestrator}

   Skills auto-loaded:
   - {skill1}
   - {skill2}
   - {skill3}

   Tools available: {tools}

   Purpose:
   {Brief explanation of what this agent does}

   Context isolation: This agent runs in its own context window,
   keeping your main conversation clean.
   ```

3. **Ask for confirmation**:
   "Ready to create this agent? This will create .claude/agents/{agent-name}.md"

4. **Wait for user confirmation** before proceeding to Step 3.

## Step 3: Create Agent File

**IMPORTANT**: File must be created in the PROJECT's .claude directory (current working directory), NOT the plugin directory.

### 3.1 Create Directory if Needed

Use Bash tool to ensure agents directory exists:

```bash
mkdir -p .claude/agents
```

### 3.2 Write Agent Definition

Use Write tool:
- **Path**: `.claude/agents/{agent-name}.md`
- **Content**: Extract the agent content from between `=== AGENT.MD CONTENT ===` and `=== END AGENT.MD ===`

The content must include YAML frontmatter:
```yaml
---
name: {agent-name}
description: {description}
tools: ["Read", "Write", "Grep"]
skills: {skill1, skill2}
model: sonnet
color: blue
---
```

### 3.3 Verify Creation

Use Read tool to verify the agent file was created correctly:
- Read `.claude/agents/{agent-name}.md`
- Confirm YAML frontmatter is valid
- Confirm skills are properly listed

### 3.4 Show Confirmation

Display to user:
```
✅ Created agent: {agent-name}

File created: .claude/agents/{agent-name}.md

Architecture: {architecture}
Skills auto-loaded: {skills}

This agent provides isolated context - your main conversation stays clean!

Usage: /{agent-name} [your request]

Example:
  /{agent-name} {example request relevant to agent's purpose}

The agent will:
1. Run in its own context window
2. Auto-load all specified skills
3. Have access to all configured tools
4. Return results to you without polluting main context

Next steps:
- Test the agent with a sample request
- Refine the agent's system prompt if needed (edit the .md file)
- Share with your team for collaborative workflows
```

## Important Notes

- **File location**: Create agent file in PROJECT's `.claude/agents/` directory (current working directory), NOT the plugin's directory
- **Path format**: Use relative path `.claude/agents/{agent-name}.md`
- **Verification**: Verify the file was created and has valid YAML frontmatter
- **Availability**: Agents are available immediately as slash commands (no restart needed)
- **Context isolation**: Each agent invocation runs in separate context window
- **Example reference**: See `/examples/example-agent-single-skill.md` for single-skill consumer pattern
