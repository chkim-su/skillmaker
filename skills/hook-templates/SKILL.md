---
name: hook-templates
description: Production-tested Claude Code hook templates for common automation patterns. Use when implementing hooks.
allowed-tools: ["Read", "Write", "Grep", "Glob"]
---

# Hook Templates

## Hook Types

| Type | Trigger Point | Common Use |
|------|---------------|------------|
| **UserPromptSubmit** | Every user prompt | Skill activation, context injection |
| **PreToolUse** | Before tool execution | Validation, blocking |
| **PostToolUse** | After tool execution | Tracking, state updates |
| **Stop** | Session end | Cleanup, reminders |

---

## settings.json Registration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/my-hook.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-edit.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post-edit.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Hook Input (stdin JSON)

All hooks receive JSON on stdin:

```json
{
  "session_id": "abc123",
  "prompt": "user prompt text",
  "cwd": "/project/path",
  "tool_name": "Edit",
  "tool_input": { ... }
}
```

---

## Template 1: Skill Activation (UserPromptSubmit)

See `references/skill-activation.md` for full implementation.

**Purpose**: Suggest skills based on user prompt keywords.

```bash
#!/bin/bash
# Quick keyword check
INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""' | tr '[:upper:]' '[:lower:]')

if [[ "$PROMPT" == *"backend"* ]] || [[ "$PROMPT" == *"api"* ]]; then
    echo "📚 RECOMMENDED: Use 'backend-patterns' skill"
fi
```

---

## Template 2: File Modification Tracker (PostToolUse)

**Purpose**: Track which files were modified during session.

```bash
#!/bin/bash
INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // ""')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""')

if [[ -n "$FILE_PATH" ]]; then
    CACHE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/cache"
    mkdir -p "$CACHE_DIR"
    echo "$FILE_PATH" >> "$CACHE_DIR/modified-files.txt"
fi
```

---

## Template 3: Pre-Edit Validation (PreToolUse)

**Purpose**: Block edits without required checks.

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // ""')

# Example: Block edits to protected files
if [[ "$FILE_PATH" == *"config/production"* ]]; then
    echo "⚠️ BLOCKED: Cannot edit production config directly"
    echo "Use configuration management workflow instead"
    exit 1  # Non-zero exits block the operation
fi

exit 0
```

---

## Template 4: Session End Reminder (Stop)

**Purpose**: Remind about uncommitted work or pending tasks.

```bash
#!/bin/bash
# Check for uncommitted changes
if git status --porcelain | grep -q '^'; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️ UNCOMMITTED CHANGES DETECTED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Consider committing your work before ending session."
    echo ""
fi

# Check for workflow state files
if ls .*.done 2>/dev/null | grep -q .; then
    echo ""
    echo "📋 WORKFLOW IN PROGRESS"
    echo "State files found - workflow may be incomplete"
    echo ""
fi
```

---

## Exit Codes

| Exit Code | Behavior |
|-----------|----------|
| 0 | Success, continue |
| 1+ | For PreToolUse: blocks operation |
| 1+ | For others: logged but doesn't block |

---

## Schema Requirements (Claude Code 1.0.40+)

**Required Structure:**
```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolName",      // String OR object (see below)
        "hooks": [                   // REQUIRED: nested hooks array
          {
            "type": "command",       // REQUIRED: "command" or "prompt"
            "command": "...",        // Required when type is "command"
            "timeout": 5000          // Optional: milliseconds
          }
        ]
      }
    ]
  }
}
```

**Matcher Formats (BOTH valid):**

1. **String matcher** - Simple tool name matching:
```json
"matcher": "Task"
"matcher": "Edit|Write|MultiEdit"
```

2. **Object matcher** - Advanced conditional matching:
```json
"matcher": {
  "tool_name": "Task",
  "input_contains": ["serena-refactor-executor"],
  "output_contains": ["VERDICT: PASS"]
}
```

**Common Mistakes to Avoid:**
- ❌ `"command": "..."` at top level - must be inside `hooks` array
- ❌ Missing `"type": "command"` - type field is required
- ❌ `"pattern": "..."` - pattern field doesn't exist, use matcher
- ❌ `"behavior": "block"` - behavior field doesn't exist

---

## Best Practices

1. **Always read from stdin** - Hook input is JSON on stdin
2. **Use jq for parsing** - Reliable JSON extraction
3. **Exit 0 on success** - Non-zero may block operations
4. **Keep hooks fast** - Slow hooks degrade UX
5. **Log errors to stderr** - stdout goes to Claude
6. **Use $CLAUDE_PROJECT_DIR** - Reliable project path

---

## Detailed Templates

See `references/` for complete implementations:
- `user-prompt-submit.md` - Prompt analysis patterns
- `post-tool-use.md` - Modification tracking
- `pre-tool-use.md` - Validation gates
- `stop.md` - Session cleanup
