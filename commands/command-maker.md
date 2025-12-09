---
description: Create commands that orchestrate existing agents into workflows. Supports single or multiple command creation.
argument-hint: "[workflow description]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Command Maker: Create Agent-Orchestrating Commands

Create commands that orchestrate existing agents into structured workflows.

## Step 1: Initial Setup (COMMAND RESPONSIBILITY)

**CRITICAL**: This step MUST be done by the command, NOT the agent. The agent runs in isolated context and cannot interact with the user for selection.

### 1.1 Determine Scope

Ask user about creation scope:

```
Command Creation Scope:

1. Single command - Create one command that orchestrates agents
2. Multiple commands - Create a set of related commands (workflow suite)

Select option (1 or 2):
```

### 1.2 Scan for Available Agents

Use Glob tool to find all agents:
```
Pattern: .claude/agents/*.md
```

### 1.3 Extract Agent Information

For each agent file found, use Read tool to extract:
- Agent name (from frontmatter)
- Description (from frontmatter)
- Skills used (from frontmatter)
- Tools available (from frontmatter)

### 1.4 Present Agents to User

Display ACTUAL agents found (do NOT use hardcoded examples):

```
Available Agents in Your Project:

[For each agent found, display:]
- {agent-name}: {description}
  Skills: {skills}
  Tools: {tools}

Example output format:
- sql-specialist: SQL optimization specialist using sql-optimizer skill
  Skills: sql-optimizer
  Tools: Read, Write, Grep, Glob
- data-pipeline-runner: Runs ETL pipelines with monitoring
  Skills: data-pipeline, monitoring
  Tools: Read, Write, Bash, Task
```

If no agents found, inform user:
```
No agents found in .claude/agents/

Create agents first using:
- /skillmaker:skill-cover (create agent that uses skills)

Or create skills first:
- /skillmaker:skill-new (create new skill from scratch)
- /skillmaker:skillization (convert existing code to skill)
```

### 1.5 Get User Selection

**For Single Command:**
```
Which agents should this command orchestrate?

Enter agent name(s) separated by commas:
```

**For Multiple Commands:**
```
Which agents will be used across your command suite?

Enter all agent names that may be used (separated by commas):
```

### 1.6 Ask Workflow Questions

**For Single Command:**
```
Command Configuration:

1. Command name: (e.g., run-pipeline, optimize-db)
2. Command purpose: What workflow does this command execute?
3. Execution flow:
   - Sequential (agents run one after another)
   - Parallel (agents run simultaneously)
   - Conditional (agent selection based on input)
4. User interaction:
   - Fully automated (no prompts during execution)
   - Interactive (asks questions during workflow)
5. Argument hint: What arguments does this command accept?
```

**For Multiple Commands:**
```
Command Suite Configuration:

1. Suite name/prefix: (e.g., pipeline, data-ops)
2. How many commands: (number)
3. For each command, I'll ask:
   - Command name
   - Purpose
   - Which agents it uses
   - Execution flow
```

### 1.7 Confirm Configuration

**For Single Command:**
```
Command Configuration Summary:

Name: {command-name}
Purpose: {purpose}
Agents: {agent1, agent2, ...}
Execution: {sequential | parallel | conditional}
Interaction: {automated | interactive}
Arguments: {argument-hint}

Proceed with command design? (yes/no)
```

**For Multiple Commands:**
```
Command Suite Configuration Summary:

Suite: {suite-name}
Commands to create:
1. {command1-name}: {purpose} (uses: agent1, agent2)
2. {command2-name}: {purpose} (uses: agent3)
3. {command3-name}: {purpose} (uses: agent1, agent3)

Proceed with command design? (yes/no)
```

Wait for user confirmation before proceeding to Step 2.

## Step 2: Launch Designer Agent

After user confirms configuration, use the Task tool to launch the `command-workflow-designer` agent:

**For Single Command:**
```
Task tool with:
- subagent_type: "general-purpose"
- description: "Design agent-orchestrating command"
- prompt: "You are the command-workflow-designer agent from the skillmaker plugin.

Your role is to design a command that orchestrates agents into a workflow.

## Configuration (from command)
Command Name: {command-name}
Purpose: {purpose}
Agents to orchestrate: {agent1, agent2, ...}
Execution flow: {sequential | parallel | conditional}
Interaction mode: {automated | interactive}
Argument hint: {argument-hint}

## Agent Details
{For each agent, include:}
- {agent-name}: {description}
  Skills: {skills}
  Tools: {tools}

## Your Task

Design the command workflow. DO NOT create files - return the design only.

### Design Requirements:

1. **Clear workflow steps**: Define each step in the workflow
2. **Agent invocation**: How and when each agent is called
3. **Data flow**: How output from one agent feeds into another
4. **Error handling**: What happens if an agent fails
5. **User feedback**: Progress indicators and results presentation

## Output Format

Return design in this exact format:

=== COMMAND DESIGN ===
NAME: {command-name}
DESCRIPTION: {command description for frontmatter}
ARGUMENT_HINT: {argument-hint}
ALLOWED_TOOLS: [\"Read\", \"Write\", \"Bash\", \"Task\", \"Glob\", \"Grep\"]
AGENTS_USED: {agent1, agent2, agent3}

=== COMMAND.MD CONTENT ===
---
description: {description}
argument-hint: \"{argument-hint}\"
allowed-tools: [\"Read\", \"Write\", \"Bash\", \"Task\", \"Glob\", \"Grep\"]
---

# {Command Title}

{Full command markdown content with:}
- Purpose and overview
- Step-by-step workflow
- Agent invocation instructions (use Task tool)
- Data flow between agents
- Error handling
- Result presentation

=== END COMMAND.MD ===

This structured format allows the command to parse and create the command file.
"
```

**For Multiple Commands:**

Launch the designer agent once for each command, or use a batch prompt:

```
Task tool with:
- subagent_type: "general-purpose"
- description: "Design command suite"
- prompt: "You are the command-workflow-designer agent from the skillmaker plugin.

Your role is to design a suite of related commands that orchestrate agents.

## Suite Configuration
Suite name: {suite-name}
Commands to design: {count}

## Commands to Create:
{For each command:}
Command {n}:
- Name: {command-name}
- Purpose: {purpose}
- Agents: {agents}
- Execution: {flow}

## Available Agents:
{For each agent, include:}
- {agent-name}: {description}
  Skills: {skills}
  Tools: {tools}

## Your Task

Design each command in the suite. DO NOT create files - return all designs.

## Output Format

For EACH command, return:

=== COMMAND DESIGN {n} ===
NAME: {command-name}
DESCRIPTION: {description}
ARGUMENT_HINT: {argument-hint}
ALLOWED_TOOLS: [tools]

=== COMMAND.MD CONTENT ===
---
description: {description}
argument-hint: \"{argument-hint}\"
allowed-tools: [tools]
---

# {Command Title}

{Full command content}

=== END COMMAND.MD ===

Repeat for each command in the suite.
"
```

## Step 3: Review Command Design and Confirm

After the command-workflow-designer agent completes:

1. **Parse the agent's output** to extract:
   - Command name(s)
   - Description(s)
   - Allowed tools
   - Command.md content(s)

2. **Present design summary to user:**

**For Single Command:**
```
Command Design Complete

Name: {command-name}
Description: {description}

Workflow:
{Brief workflow description}

Agents orchestrated:
- {agent1}: {role in workflow}
- {agent2}: {role in workflow}

Execution: {sequential | parallel | conditional}
```

**For Multiple Commands:**
```
Command Suite Design Complete

Suite: {suite-name}

Commands designed:
1. {command1-name}: {description}
2. {command2-name}: {description}
3. {command3-name}: {description}

Ready to create {n} command files.
```

3. **Ask for confirmation:**
   "Ready to create command file(s)? This will create .claude/commands/{command-name}.md"

4. **Wait for user confirmation** before proceeding to Step 4.

## Step 4: Create Command File(s)

**IMPORTANT**: Files must be created in the PROJECT's .claude directory (current working directory), NOT the plugin directory.

### 4.1 Create Directory if Needed

Use Bash tool to ensure commands directory exists:

```bash
mkdir -p .claude/commands
```

### 4.2 Write Command Definition(s)

**For Single Command:**

Use Write tool:
- **Path**: `.claude/commands/{command-name}.md`
- **Content**: Extract from between `=== COMMAND.MD CONTENT ===` and `=== END COMMAND.MD ===`

**For Multiple Commands:**

For each command in the suite:
- Extract content between `=== COMMAND.MD CONTENT ===` and `=== END COMMAND.MD ===`
- Use Write tool with path `.claude/commands/{command-name}.md`

### 4.3 Verify Creation

Use Glob tool to verify all files were created:
```
Pattern: .claude/commands/*.md
```

For each created file, use Read tool to verify:
- YAML frontmatter is valid
- Description is present
- Allowed tools are specified

### 4.4 Show Confirmation

**For Single Command:**
```
Created command: {command-name}

File created: .claude/commands/{command-name}.md

Orchestrates agents: {agents}
Execution flow: {flow}

Usage: /{command-name} {argument-hint}

Example:
  /{command-name} {example usage}

The command will:
1. Execute the defined workflow
2. Orchestrate the specified agents
3. Handle data flow between agents
4. Present unified results

Next steps:
- Test the command with a sample request
- Refine the workflow if needed (edit the .md file)
- Add error handling for edge cases
```

**For Multiple Commands:**
```
Created command suite: {suite-name}

Files created:
- .claude/commands/{command1-name}.md
- .claude/commands/{command2-name}.md
- .claude/commands/{command3-name}.md

Usage:
- /{command1-name} {hint}
- /{command2-name} {hint}
- /{command3-name} {hint}

Next steps:
- Test each command individually
- Refine workflows as needed
- Consider creating a master orchestrator command
```

## Important Notes

- **Scanning location**: Scan agents from PROJECT's `.claude/agents/` directory
- **File creation location**: Create command files in PROJECT's `.claude/commands/` directory
- **Path format**: Use relative paths like `.claude/commands/{name}.md`
- **Verification**: Always verify files were created before confirming to user
- **Availability**: Commands are available immediately (no restart needed)
- **Agent invocation**: Commands use Task tool to invoke agents
- **Workflow patterns**: Sequential for dependent steps, Parallel for independent operations, Conditional for branching logic
