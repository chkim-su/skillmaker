---
name: hook-templates
description: Production-tested Claude Code hook templates for common automation patterns. Use when implementing hooks.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# Hook Templates

Production-tested templates for Claude Code hooks (1.0.40+ schema).

## Quick Start

1. Create hook script (bash/python)
2. Register in settings.json under `hooks.{EventName}`
3. Script receives JSON on stdin, outputs to stdout

## Hook Types

| Type | Trigger | Use Case |
|------|---------|----------|
| UserPromptSubmit | Every prompt | Skill activation |
| PreToolUse | Before tool | Validation, blocking |
| PostToolUse | After tool | Tracking, state |
| Stop | Session end | Cleanup, reminders |

## Basic Registration

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "script.sh",
        "timeout": 5
      }]
    }]
  }
}
```

## Exit Codes

| Code | PreToolUse | Others |
|------|------------|--------|
| 0 | Continue | Continue |
| 1+ | **Blocks** | Logged only |

## Best Practices

1. **Read stdin** - Input is JSON
2. **Use jq** - Reliable parsing
3. **Exit 0** - Non-zero may block
4. **Keep fast** - Slow hooks degrade UX
5. **Use $CLAUDE_PROJECT_DIR** - Project path

## Common Mistakes

- Missing nested `hooks` array
- Missing `"type": "command"`
- Using non-existent `pattern` or `behavior` fields

## Advanced Patterns

- **Subagent filtering**: Parse `tool_input.subagent_type` for Task hooks
- **Workflow gates**: Combine with `workflow-state-patterns` for state files
- **Skill auto-activation**: Use `skill-activation-patterns` with UserPromptSubmit

## References

- [Full Examples](references/full-examples.md) - All templates with detailed code
