# Skillmaker

Claude Code plugin for creating reusable skills, agents, and MCP integration systems.

## Features

### Skills
Structured, reusable domain knowledge with progressive disclosure:
- Core knowledge in `SKILL.md` (500-1000 words)
- Detailed references in `references/`
- Utility scripts in `scripts/`

### Agents
Subagents with isolated context windows that auto-load skills:
- Single-skill consumers for focused tasks
- Multi-skill orchestrators for complex workflows

### MCP Gateway Design
Design MCP integration systems with proper isolation:
- **Agent Gateway**: Native subagent as MCP access point (for frequently used MCPs)
- **Subprocess Isolation**: Separate Claude CLI process (for rarely used, large MCPs)
- **Workflow State Patterns**: Hook-based quality gates for multi-phase operations

### Skill Auto-Activation
Automatic skill activation system using hooks:
- **skill-rules.json**: Configure triggers (keywords, intent patterns, file paths)
- **Hook templates**: Production-tested UserPromptSubmit, PostToolUse, Stop hooks
- **Enforcement levels**: suggest, warn, block

## Installation

```bash
# Register as local marketplace
python3 scripts/register_local.py
```

## Quick Start

```
/skillmaker:wizard
```

The wizard routes to specialized agents:
- `skill-architect`: Design new skills
- `skill-converter`: Convert existing code to skills
- `skill-orchestrator-designer`: Create subagents that use skills
- `mcp-gateway-designer`: Design MCP integration systems
- `skill-rules-designer`: Create skill auto-activation rules

## Skills Reference

| Skill | Purpose |
|-------|---------|
| `skill-design` | Best practices for skill structure |
| `skill-catalog` | Categorize and list available skills |
| `orchestration-patterns` | Single vs multi-skill architecture |
| `mcp-gateway-patterns` | Agent Gateway and Subprocess isolation |
| `workflow-state-patterns` | Hook-based state machines |
| `skill-activation-patterns` | Auto-activation with hooks and triggers |
| `hook-templates` | Production-tested Claude Code hooks |

## Version

2.5.0

## License

MIT
