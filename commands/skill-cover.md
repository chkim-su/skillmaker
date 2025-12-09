---
description: Create a subagent that explicitly uses one or multiple skills. Determines if single-skill consumer or multi-skill orchestrator.
argument-hint: "[subagent purpose]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Skill Cover: Create Subagent for Skills

**FIRST: Load the skillmaker:orchestration-patterns skill** using the Skill tool to understand single-skill vs multi-skill architectures.

Create a subagent that explicitly uses one or multiple skills, providing isolated context window.

## Step 1: Discover Available Skills (COMMAND RESPONSIBILITY)

**CRITICAL**: This step MUST be done by the command, NOT the agent. The agent runs in isolated context and cannot interact with the user for selection.

### 1.1 Scan for Skills

Use Glob tool to find all skills:
```
Pattern: .claude/skills/*/SKILL.md
```

### 1.2 Extract Skill Information

For each SKILL.md found, use Read tool to extract:
- Skill name (from frontmatter)
- Description (from frontmatter)
- Allowed tools (from frontmatter)

### 1.3 Present Skills to User

Display ACTUAL skills found (do NOT use hardcoded examples):

```
Available Skills in Your Project:

[For each skill found, display:]
- {skill-name}: {description}

Example output format:
- sql-optimizer: Optimize SQL queries for performance
- api-client: REST API client patterns and error handling
- data-pipeline: ETL pipeline design and implementation
```

If no skills found, inform user:
```
No skills found in .claude/skills/

Create skills first using:
- /skillmaker:skill-new (create new skill from scratch)
- /skillmaker:skillization (convert existing code to skill)
```

### 1.4 Get User Selection

Ask user which skills to include in the agent:

```
Which skills should this agent use?

Options:
1. Single skill (specialized agent for one task)
2. Multiple skills (orchestrator for complex workflows)

Enter skill name(s) separated by commas, or type number(s) to select:
```

### 1.5 Ask Follow-up Questions

After skill selection, gather configuration:

```
Agent Configuration:

1. Agent name: (e.g., sql-specialist, data-pipeline-runner)
2. Agent purpose: What should this agent do?
3. Model: sonnet (default) / opus / haiku
4. Color: blue / green / yellow / cyan / magenta
5. Additional tools needed: (Read, Write, Grep, Glob, Bash, Task)
```

### 1.6 Confirm Configuration

Present final configuration to user:

```
Agent Configuration Summary:

Name: {agent-name}
Purpose: {purpose}
Architecture: {single-skill-consumer | multi-skill-orchestrator}
Skills: {skill1, skill2, ...}
Tools: {tools}
Model: {model}
Color: {color}

Proceed with agent design? (yes/no)
```

Wait for user confirmation before proceeding to Step 2.

## Step 2: Launch Designer Agent

After user confirms configuration, use the Task tool to launch the `skill-orchestrator-designer` agent:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Design skill-using subagent"
- prompt: "You are the skill-orchestrator-designer agent from the skillmaker plugin.

Your role is to design a subagent definition based on the provided configuration.

## Configuration (from command)
Agent Name: {agent-name}
Purpose: {purpose}
Architecture: {single-skill-consumer | multi-skill-orchestrator}
Selected Skills: {skill1, skill2, ...}
Tools: {tools}
Model: {model}
Color: {color}

## Your Task

Design the agent system prompt and structure. DO NOT create files - return the design only.

### For Single-Skill Consumer:

Design a focused agent that uses ONE skill exclusively:
- Clear role definition
- Skill usage patterns
- Response format
- Scope limitations

### For Multi-Skill Orchestrator:

Design a coordinator agent that:
- Analyzes user requests
- Selects appropriate skill(s)
- Coordinates multi-skill workflows
- Returns unified results

## Output Format

Return design in this exact format:

=== AGENT DESIGN ===
NAME: {agent-name}
DESCRIPTION: {agent description for frontmatter}
ARCHITECTURE: {single-skill-consumer | multi-skill-orchestrator}
SKILLS: {skill1, skill2, skill3}
TOOLS: {tools array}
MODEL: {model}
COLOR: {color}

=== AGENT.MD CONTENT ===
---
name: {agent-name}
description: {description}
tools: {tools array}
skills: {skill-list}
model: {model}
color: {color}
---

# {Agent Title}

{Full agent system prompt with:}
- Role definition
- Available skills and their purposes
- Behavior guidelines
- Response patterns
- Key principles
- Scope limitations

=== END AGENT.MD ===

This structured format allows the command to parse and create the agent file.
"
```

## Step 3: Review Agent Design and Confirm

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
   Agent Design Complete

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

4. **Wait for user confirmation** before proceeding to Step 4.

## Step 4: Create Agent File

**IMPORTANT**: File must be created in the PROJECT's .claude directory (current working directory), NOT the plugin directory.

### 4.1 Create Directory if Needed

Use Bash tool to ensure agents directory exists:

```bash
mkdir -p .claude/agents
```

### 4.2 Write Agent Definition

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

### 4.3 Verify Creation

Use Read tool to verify the agent file was created correctly:
- Read `.claude/agents/{agent-name}.md`
- Confirm YAML frontmatter is valid
- Confirm skills are properly listed

### 4.4 Show Confirmation

Display to user:
```
Created agent: {agent-name}

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
- Create commands to orchestrate this agent (use /skillmaker:command-maker)
```

## Important Notes

- **Scanning location**: Scan skills from PROJECT's `.claude/skills/` directory
- **File creation location**: Create agent file in PROJECT's `.claude/agents/` directory
- **Path format**: Use relative path `.claude/agents/{agent-name}.md`
- **Verification**: Verify the file was created and has valid YAML frontmatter
- **Availability**: Agents are available immediately as slash commands (no restart needed)
- **Context isolation**: Each agent invocation runs in separate context window
- **Example reference**: See `/examples/example-agent-single-skill.md` for single-skill consumer pattern
