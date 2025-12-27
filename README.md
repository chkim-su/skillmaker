# Skillmaker

Claude Code plugin for creating reusable skills, agents, and MCP integration systems.

## Core Concepts

### Skills
Structured, reusable domain knowledge loaded into Claude's context on demand.
- **Global Registry**: All skills (plugin, user, project) are globally available via `Skill` tool
- **Progressive Disclosure**: Core knowledge in SKILL.md, detailed docs in references/
- **Auto-Loading**: Skills in agent YAML frontmatter load automatically at start

### Agents (Subagents)
Isolated context windows that run skills without polluting main conversation.
- **Context Isolation**: Intermediate work stays in subagent, main context stays clean
- **Three Architectures**: Single-Skill, Multi-Skill Orchestrator, Enhanced Agent
- **Skill Inheritance**: Agents can load any globally registered skill

### MCP Gateway
Design patterns for MCP integration with proper isolation.
- **Agent Gateway**: Native subagent as MCP access point (frequent use, workflow state)
- **Subprocess Isolation**: Separate Claude CLI process (rare use, token efficiency)
- **2-Layer Protocol**: Intent Layer (QUERY/MODIFY) + Action Layer (MCP-specific)

## Features

### Skill Design (`skill-design`)
Best practices for creating skills:
- SKILL.md structure and frontmatter
- Skill types: Knowledge, Hybrid, Tool, Expert
- Tool restrictions and allowed-tools configuration

### Skill Catalog (`skill-catalog`)
Global skill system documentation:
- How Claude Code's `<available_skills>` registry works
- Skill sources: plugins, user, project (all globally accessible)
- Category-based skill organization

### Orchestration Patterns (`orchestration-patterns`)
Subagent architecture decision guide:
| Pattern | Use When | Key Feature |
|---------|----------|-------------|
| Single-Skill | Focused domain task | 1 skill, minimal tools |
| Multi-Skill | Multi-domain workflow | 2+ skills, Task tool |
| Enhanced | Codebase aware + memory | Serena Gateway + claude-mem |

### MCP Gateway Patterns (`mcp-gateway-patterns`)
MCP isolation strategies:
- **Agent Gateway**: Fast, stateful, for frequent MCP calls
- **Subprocess**: Token-efficient, for rare/large MCP responses
- Request/Response JSON schema with effect/artifact fields

### Workflow State Patterns (`workflow-state-patterns`)
Hook-based state machines for multi-phase workflows:
- File-based state markers (.analysis-done, .plan-approved)
- PreToolUse hooks for quality gates
- PostToolUse hooks for state progression
- Claude Code 1.0.40+ hook schema

### Skill Activation Patterns (`skill-activation-patterns`)
Automatic skill activation system:
- **skill-rules.json**: Configure triggers (keywords, patterns, files)
- **Hook Integration**: UserPromptSubmit hook for prompt analysis
- **Enforcement Levels**: suggest, warn, block

### Hook Templates (`hook-templates`)
Production-tested Claude Code hooks:
- UserPromptSubmit, PreToolUse, PostToolUse, Stop
- Schema requirements for 1.0.40+
- Common patterns and best practices

## Agents

| Agent | Purpose |
|-------|---------|
| `skill-architect` | Design new skills through iterative questioning |
| `skill-converter` | Convert existing code into reusable skills |
| `skill-orchestrator-designer` | Create subagents (Single/Multi/Enhanced) |
| `mcp-gateway-designer` | Design MCP Gateway systems |
| `skill-rules-designer` | Create skill-rules.json configurations |

## Installation

```bash
# Register as local marketplace
python3 scripts/register_local.py
```

## Quick Start

```
/skillmaker:wizard
```

The wizard routes to specialized agents based on your needs.

## Version

2.6.0

## License

MIT
