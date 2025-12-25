#!/usr/bin/env python3
"""
Register a plugin project as a local marketplace for testing.

Usage:
    python register_local.py --path /path/to/plugin/project

This script:
1. Reads the user's ~/.claude/settings.json
2. Adds the plugin path to extraKnownMarketplaces
3. Enables the plugin in enabledPlugins
4. Saves the updated settings
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_settings_path() -> Path:
    """Get the path to Claude settings.json."""
    if sys.platform == "win32":
        base = Path(os.environ.get("USERPROFILE", ""))
    else:
        base = Path.home()
    return base / ".claude" / "settings.json"


def read_settings(settings_path: Path) -> dict:
    """Read existing settings or return empty dict."""
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {settings_path}, starting fresh")
            return {}
    return {}


def get_marketplace_name(plugin_path: Path) -> str:
    """Extract marketplace name from marketplace.json."""
    marketplace_json = plugin_path / ".claude-plugin" / "marketplace.json"
    if marketplace_json.exists():
        try:
            with open(marketplace_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("name", plugin_path.name)
        except (json.JSONDecodeError, KeyError):
            pass
    return plugin_path.name


def get_plugin_name(plugin_path: Path) -> str:
    """Extract first plugin name from marketplace.json."""
    marketplace_json = plugin_path / ".claude-plugin" / "marketplace.json"
    if marketplace_json.exists():
        try:
            with open(marketplace_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                plugins = data.get("plugins", [])
                if plugins:
                    return plugins[0].get("name", "plugin")
        except (json.JSONDecodeError, KeyError):
            pass
    return "plugin"


def register_local(plugin_path: Path, settings_path: Path) -> dict:
    """Register plugin as local marketplace."""
    settings = read_settings(settings_path)

    # Get names
    marketplace_name = get_marketplace_name(plugin_path)
    plugin_name = get_plugin_name(plugin_path)
    local_key = f"{marketplace_name}-local"

    # Ensure extraKnownMarketplaces exists
    if "extraKnownMarketplaces" not in settings:
        settings["extraKnownMarketplaces"] = {}

    # Add local marketplace
    # Use forward slashes for cross-platform compatibility
    plugin_path_str = str(plugin_path).replace("\\", "/")

    # CRITICAL: Use "type": "directory" - valid discriminator values are:
    # 'url' | 'github' | 'git' | 'npm' | 'file' | 'directory'
    settings["extraKnownMarketplaces"][local_key] = {
        "source": {
            "type": "directory",
            "path": plugin_path_str
        }
    }

    # Ensure enabledPlugins exists and is an OBJECT (not array!)
    # Claude Code expects: {"plugin@marketplace": true}
    if "enabledPlugins" not in settings:
        settings["enabledPlugins"] = {}
    elif isinstance(settings["enabledPlugins"], list):
        # Convert list format to object format
        # Old format: ["plugin@marketplace"]
        # Correct format: {"plugin@marketplace": true}
        old_plugins = settings["enabledPlugins"]
        settings["enabledPlugins"] = {p: True for p in old_plugins}

    # Add plugin to enabled plugins (object format)
    plugin_ref = f"{plugin_name}@{local_key}"
    settings["enabledPlugins"][plugin_ref] = True

    return {
        "settings": settings,
        "marketplace_key": local_key,
        "plugin_ref": plugin_ref
    }


def save_settings(settings: dict, settings_path: Path) -> None:
    """Save settings to file."""
    # Ensure directory exists
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Register a plugin project as a local marketplace for testing"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the plugin project directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )

    args = parser.parse_args()

    plugin_path = Path(args.path).resolve()
    settings_path = get_settings_path()

    # Validate plugin path
    marketplace_json = plugin_path / ".claude-plugin" / "marketplace.json"
    if not marketplace_json.exists():
        error = f"Error: Not a plugin project. Missing {marketplace_json}"
        if args.json:
            print(json.dumps({"success": False, "error": error}))
        else:
            print(error, file=sys.stderr)
        sys.exit(1)

    # Register
    result = register_local(plugin_path, settings_path)

    if args.dry_run:
        if args.json:
            print(json.dumps({
                "success": True,
                "dry_run": True,
                "marketplace_key": result["marketplace_key"],
                "plugin_ref": result["plugin_ref"],
                "settings_path": str(settings_path),
                "settings_preview": result["settings"]
            }, indent=2))
        else:
            print("Dry run - would make the following changes:")
            print(f"  Settings file: {settings_path}")
            print(f"  Marketplace key: {result['marketplace_key']}")
            print(f"  Plugin reference: {result['plugin_ref']}")
            print(f"\nSettings preview:")
            print(json.dumps(result["settings"], indent=2))
    else:
        save_settings(result["settings"], settings_path)

        if args.json:
            print(json.dumps({
                "success": True,
                "marketplace_key": result["marketplace_key"],
                "plugin_ref": result["plugin_ref"],
                "settings_path": str(settings_path)
            }, indent=2))
        else:
            print(f"Successfully registered local plugin!")
            print(f"  Marketplace: {result['marketplace_key']}")
            print(f"  Plugin: {result['plugin_ref']}")
            print(f"  Settings: {settings_path}")
            print()
            print("Next steps:")
            print("  1. Restart Claude Code to apply changes")
            print("  2. Test your plugin functionality")
            print("  3. Run '/wizard publish' after testing")


if __name__ == "__main__":
    main()
