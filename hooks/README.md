# Hooks Configuration (BLOCKING)

This directory contains **BLOCKING** hook configurations for mandatory plugin validation.

## ⚠️ CRITICAL: All Hooks Are BLOCKING

| Hook | Trigger | Behavior |
|------|---------|----------|
| PreToolUse:Bash | Before `git commit` | **BLOCK** if validation fails |
| PreToolUse:Bash | Before `git push` | **BLOCK** if validation fails |
| PostToolUse:Write | After marketplace.json modified | **BLOCK** if schema invalid |
| PostToolUse:Write | After plugin.json modified | **BLOCK** if schema invalid |

## Installation (REQUIRED)

Copy hooks from `hooks.json` to your Claude Code settings:

**Linux/macOS:**
```bash
# View current settings
cat ~/.claude/settings.json

# Add hooks manually - see hooks.json for full configuration
```

**Windows:**
```powershell
# View current settings
type %USERPROFILE%\.claude\settings.json
```

### settings.json Example

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": {
        "tool_name": "Bash",
        "query": "git commit"
      },
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py",
      "blocking": true
    },
    {
      "event": "PreToolUse",
      "matcher": {
        "tool_name": "Bash",
        "query": "git push"
      },
      "command": "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py",
      "blocking": true
    }
  ]
}
```

## Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| `owner` missing | **BLOCK** | marketplace.json requires `owner.name` |
| `plugins` missing | **BLOCK** | marketplace.json requires `plugins` array |
| `plugins[].name` missing | **BLOCK** | Each plugin needs a name |
| `plugins[].source` missing | **BLOCK** | Each plugin needs a source |
| URL in source | **BLOCK** | URLs not allowed; use `{type: "github", repo: "..."}` |
| Unrecognized fields | **BLOCK** | Only allowed fields permitted |
| Path format invalid | **BLOCK** | Commands need `.md`, skills are directories |
| File not found | **BLOCK** | Registered file doesn't exist |
| Unregistered file | **BLOCK** | File exists but not in marketplace.json |

## Manual Validation

```bash
# Run validation (exit code 1 = errors, 2 = warnings, 0 = pass)
python3 scripts/validate_all.py

# JSON output for programmatic use
python3 scripts/validate_all.py --json

# Auto-fix issues
python3 scripts/validate_all.py --fix

# Preview fixes without applying
python3 scripts/validate_all.py --fix --dry-run
```

## Error Handling

When validation fails:

1. **DO NOT proceed** - fix the errors first
2. Run `--fix` to auto-repair common issues
3. Re-run validation until it passes
4. Only then continue with commit/push

## Wizard Integration

The `/wizard` command enforces validation automatically:

1. After creating skill/agent/command, validation runs
2. If errors exist, wizard **BLOCKS** and shows fix options
3. User must fix errors or run `--fix` before proceeding
4. Wizard **LOOPS** until validation passes
