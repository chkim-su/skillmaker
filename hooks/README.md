# Hooks Configuration

This directory contains hook configurations for automatic plugin validation.

## Automatic Hooks (hooks.json)

The `hooks.json` file defines automatic validation hooks:

| Hook | Trigger | Action |
|------|---------|--------|
| PostToolUse:Write | After marketplace.json/plugin.json modified | Validate schema |
| PreToolUse:Bash | Before `git push` | Block if validation fails |
| PreToolUse:Bash | Before `git commit` | Warn if validation issues |

### Enabled by Default

These hooks run automatically when the skillmaker plugin is active.

## Manual Setup (Optional)

For additional control, you can add hooks to `.claude/settings.json`:

```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "matcher": {
        "tool_name": "Bash",
        "query": "git push"
      },
      "command": "python3 scripts/validate_all.py",
      "run_in_background": false
    }
  ]
}
```

## What It Does

- **Post-Write Validation**: After modifying marketplace.json or plugin.json, schema is validated
- **Pre-Push Blocking**: Push is blocked if validation fails (errors exist)
- **Pre-Commit Warning**: Commit proceeds with warning if validation has issues

## Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| `owner` missing | ERROR | marketplace.json requires `owner.name` |
| `plugins` missing | ERROR | marketplace.json requires `plugins` array |
| `plugins[].name` missing | ERROR | Each plugin needs a name |
| `plugins[].source` missing | ERROR | Each plugin needs a source |
| Path format invalid | ERROR | Commands need `.md`, skills are directories |
| File not found | ERROR | Registered file doesn't exist |
| Unregistered file | ERROR | File exists but not in marketplace.json |

## Manual Validation

```bash
python3 scripts/validate_all.py              # Human-readable output
python3 scripts/validate_all.py --json       # JSON output
python3 scripts/validate_all.py --fix        # Auto-fix issues
python3 scripts/validate_all.py --fix --dry-run  # Preview fixes
```

## Hook Events

| Event | When | Use Case |
|-------|------|----------|
| PreToolUse | Before tool runs | Block dangerous operations |
| PostToolUse | After tool runs | Auto-validate, format output |
| Stop | Claude finishes | Final checks |
| Notification | Alert sent | Custom notifications |
