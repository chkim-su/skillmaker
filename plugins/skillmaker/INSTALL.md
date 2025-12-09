# Installation Guide

## Quick Install (Recommended)

### From GitHub (After Publishing)

```bash
# Add the marketplace
/plugin marketplace add chkim-su/skillmaker

# Install the plugin
/plugin install skillmaker@skillmaker-marketplace
```

---

## Manual Installation (Local Development)

### Option 1: Local Marketplace

```bash
# 1. Clone or copy this directory to your system
git clone https://github.com/chkim-su/skillmaker.git
# or
cp -r /path/to/skillmaker ~/.claude/plugins/skillmaker

# 2. Add as local marketplace
/plugin marketplace add ~/.claude/plugins/skillmaker

# 3. Install the plugin
/plugin install skillmaker@skillmaker-marketplace
```

### Option 2: Direct Copy

```bash
# Copy to Claude plugins directory
cp -r /path/to/skillmaker ~/.claude-plugins/skillmaker

# Restart Claude Code
```

---

## Verify Installation

After installation, verify the commands are available:

```bash
/help
```

You should see:
- `/skillmaker:skill-new`
- `/skillmaker:skillization`
- `/skillmaker:skill-cover`
- `/skillmaker:command-maker`

---

## Team Installation (Auto-setup)

For teams, add to `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "skillmaker": {
      "source": {
        "source": "github",
        "repo": "chkim-su/skillmaker"
      }
    }
  },
  "enabledPlugins": [
    "skillmaker@skillmaker"
  ]
}
```

Team members will automatically get the plugin when they trust the repository.

---

## Troubleshooting

### Commands not showing

```bash
# Reload Claude Code
# or
/plugin uninstall skillmaker@skillmaker-marketplace
/plugin install skillmaker@skillmaker-marketplace
```

### Debug mode

```bash
claude --debug
```

Check for loading errors or warnings.

### Verify marketplace

```bash
/plugin marketplace list
```

Should show `skillmaker-marketplace`.

---

## Uninstallation

```bash
/plugin uninstall skillmaker@skillmaker-marketplace
/plugin marketplace remove skillmaker-marketplace
```

---

## Next Steps

After installation, read the [README.md](README.md) for usage examples.

Quick start:

```bash
# Create your first skill
/skillmaker:skill-new

# Convert existing code
/skillmaker:skillization

# Create a subagent
/skillmaker:skill-cover
```
