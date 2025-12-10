#!/usr/bin/env python3
"""
Unified plugin validation script.

Runs all automated checks that can be done in a single pass:
- Registration integrity (marketplace.json ↔ files)
- Frontmatter validation (YAML syntax, required fields)
- Directory structure validation
- Settings.json validation

Usage:
    python3 scripts/validate_all.py [plugin-path]
    python3 scripts/validate_all.py --json  # JSON output for parsing

Exit codes:
    0 - All passed
    1 - Errors found (deployment will fail)
    2 - Warnings only (deployment may work)
"""

import json
import sys
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def add_error(self, msg: str):
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_pass(self, msg: str):
        self.passed.append(msg)

    def merge(self, other: 'ValidationResult'):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.passed.extend(other.passed)


def find_marketplace_json(start_path: Path) -> Path | None:
    """Find marketplace.json in .claude-plugin/ directory."""
    claude_plugin = start_path / ".claude-plugin"
    if claude_plugin.exists():
        marketplace = claude_plugin / "marketplace.json"
        if marketplace.exists():
            return marketplace
    plugin_json = start_path / "plugin.json"
    if plugin_json.exists():
        return plugin_json
    return None


def parse_frontmatter(content: str) -> Tuple[dict | None, str | None]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return None, "No frontmatter found"

    try:
        end_idx = content.index('---', 3)
        yaml_content = content[3:end_idx].strip()
        return yaml.safe_load(yaml_content), None
    except (ValueError, yaml.YAMLError) as e:
        return None, str(e)


def validate_registration(plugin_root: Path, plugin_data: dict) -> ValidationResult:
    """Validate marketplace.json entries match actual files."""
    result = ValidationResult()

    # Get registered items
    registered_commands = plugin_data.get("commands", [])
    registered_agents = plugin_data.get("agents", [])
    registered_skills = plugin_data.get("skills", [])

    # Validate commands
    commands_dir = plugin_root / "commands"
    if commands_dir.exists():
        actual_commands = {f.stem for f in commands_dir.glob("*.md")}
        registered_set = set()

        for cmd in registered_commands:
            # Normalize path: "./commands/foo" or "./commands/foo.md"
            name = cmd.replace("./commands/", "").replace(".md", "")
            registered_set.add(name)

            cmd_file = commands_dir / f"{name}.md"
            if cmd_file.exists():
                result.add_pass(f"commands/{name}.md registered and exists")
            else:
                result.add_error(f"commands/{name}.md NOT FOUND (registered in marketplace.json)")

        # Check for unregistered files
        for actual in actual_commands:
            if actual not in registered_set:
                result.add_error(f"commands/{actual}.md exists but NOT REGISTERED in marketplace.json")

    # Validate agents
    agents_dir = plugin_root / "agents"
    if agents_dir.exists():
        actual_agents = {f.stem for f in agents_dir.glob("*.md")}
        registered_set = set()

        for agent in registered_agents:
            name = agent.replace("./agents/", "").replace(".md", "")
            registered_set.add(name)

            agent_file = agents_dir / f"{name}.md"
            if agent_file.exists():
                result.add_pass(f"agents/{name}.md registered and exists")
            else:
                result.add_error(f"agents/{name}.md NOT FOUND")

        for actual in actual_agents:
            if actual not in registered_set:
                result.add_error(f"agents/{actual}.md exists but NOT REGISTERED")

    # Validate skills
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        actual_skills = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        registered_set = set()

        for skill in registered_skills:
            name = skill.replace("./skills/", "").rstrip("/")
            registered_set.add(name)

            skill_md = skills_dir / name / "SKILL.md"
            if skill_md.exists():
                result.add_pass(f"skills/{name}/SKILL.md registered and exists")
            elif (skills_dir / name).exists():
                result.add_error(f"skills/{name}/ exists but missing SKILL.md")
            else:
                result.add_error(f"skills/{name}/ NOT FOUND")

        for actual in actual_skills:
            if actual not in registered_set:
                skill_md = skills_dir / actual / "SKILL.md"
                if skill_md.exists():
                    result.add_error(f"skills/{actual}/ exists with SKILL.md but NOT REGISTERED")

    return result


def validate_frontmatter_fields(plugin_root: Path) -> ValidationResult:
    """Validate frontmatter in all markdown files."""
    result = ValidationResult()

    # Commands
    commands_dir = plugin_root / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            fm, error = parse_frontmatter(content)

            if error:
                result.add_error(f"{cmd_file.name}: Invalid frontmatter - {error}")
                continue

            if not fm:
                result.add_error(f"{cmd_file.name}: Missing frontmatter")
                continue

            if not fm.get("description"):
                result.add_error(f"{cmd_file.name}: Missing 'description' field")
            elif "TODO" in str(fm.get("description", "")):
                result.add_warning(f"{cmd_file.name}: description contains TODO")
            else:
                result.add_pass(f"{cmd_file.name}: frontmatter valid")

    # Agents
    agents_dir = plugin_root / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            fm, error = parse_frontmatter(content)

            if error:
                result.add_error(f"{agent_file.name}: Invalid frontmatter - {error}")
                continue

            if not fm:
                result.add_error(f"{agent_file.name}: Missing frontmatter")
                continue

            if not fm.get("name"):
                result.add_error(f"{agent_file.name}: Missing 'name' field")
            if not fm.get("description"):
                result.add_error(f"{agent_file.name}: Missing 'description' field")
            if not fm.get("tools"):
                result.add_warning(f"{agent_file.name}: Missing 'tools' field")

            if fm.get("description") and "TODO" not in str(fm.get("description", "")):
                result.add_pass(f"{agent_file.name}: frontmatter valid")

    # Skills
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            content = skill_md.read_text()
            fm, error = parse_frontmatter(content)

            if error:
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Invalid frontmatter - {error}")
                continue

            if not fm:
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Missing frontmatter")
                continue

            if not fm.get("name"):
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Missing 'name' field")
            if not fm.get("description"):
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Missing 'description' field")
            elif "TODO" in str(fm.get("description", "")):
                result.add_warning(f"skills/{skill_dir.name}/SKILL.md: description contains TODO")
            else:
                result.add_pass(f"skills/{skill_dir.name}/SKILL.md: frontmatter valid")

    return result


def validate_source_path(plugin_data: dict) -> ValidationResult:
    """Validate source path format."""
    result = ValidationResult()
    source = plugin_data.get("source", "")

    if isinstance(source, str):
        if source and source not in [".", "./"] and not source.startswith("./"):
            result.add_error(f'source "{source}" must start with "./" (e.g., "./{source}")')
        else:
            result.add_pass("source path format valid")
    elif isinstance(source, dict):
        if "source" not in source or "repo" not in source:
            result.add_error('GitHub source format requires {"source": "github", "repo": "user/repo"}')
        else:
            result.add_pass("GitHub source format valid")

    return result


def validate_settings_json() -> ValidationResult:
    """Check for common settings.json misconfigurations."""
    result = ValidationResult()
    home = Path.home()

    settings_paths = [
        home / ".claude" / "settings.json",
        home / ".config" / "claude-code" / "settings.json",
    ]

    for settings_path in settings_paths:
        if not settings_path.exists():
            continue

        try:
            settings = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, IOError):
            continue

        # Check plugins array
        plugins = settings.get("plugins", [])
        for i, plugin in enumerate(plugins):
            if isinstance(plugin, dict):
                source = plugin.get("source", "")
                if isinstance(source, str) and source:
                    if not source.startswith("./") and not source.startswith("/"):
                        result.add_error(
                            f'settings.json plugins[{i}].source "{source}" must start with "./"'
                        )

        # Check extraKnownMarketplaces
        marketplaces = settings.get("extraKnownMarketplaces", {})
        for name, config in marketplaces.items():
            source = config.get("source", "")
            if isinstance(source, str) and source and not source.startswith("./"):
                result.add_error(
                    f'settings.json extraKnownMarketplaces.{name}.source must start with "./"'
                )

    return result


def main():
    # Parse arguments
    json_output = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    plugin_root = Path(args[0]).resolve() if args else Path.cwd()

    # Find marketplace.json
    marketplace_path = find_marketplace_json(plugin_root)
    if not marketplace_path:
        if json_output:
            print(json.dumps({"status": "error", "message": "No marketplace.json found"}))
        else:
            print("ERROR: No .claude-plugin/marketplace.json or plugin.json found")
        sys.exit(1)

    # Parse marketplace.json
    try:
        data = json.loads(marketplace_path.read_text())
    except json.JSONDecodeError as e:
        if json_output:
            print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        else:
            print(f"ERROR: Invalid JSON in {marketplace_path}: {e}")
        sys.exit(1)

    # Get plugins
    plugins = data.get("plugins", [data])

    # Run all validations
    total_result = ValidationResult()

    # Settings.json validation
    total_result.merge(validate_settings_json())

    for plugin in plugins:
        # Determine effective root
        source = plugin.get("source", "./")
        if source in [".", "./"]:
            effective_root = plugin_root
        else:
            effective_root = plugin_root / source.lstrip("./")

        # Run validations
        total_result.merge(validate_source_path(plugin))
        total_result.merge(validate_registration(effective_root, plugin))
        total_result.merge(validate_frontmatter_fields(effective_root))

    # Output results
    if json_output:
        output = {
            "status": "fail" if total_result.errors else ("warn" if total_result.warnings else "pass"),
            "errors": total_result.errors,
            "warnings": total_result.warnings,
            "passed": len(total_result.passed)
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 60)
        print("PLUGIN VALIDATION")
        print("=" * 60)
        print(f"Plugin: {plugin_root}")
        print()

        if total_result.errors:
            print("ERRORS:")
            for e in total_result.errors:
                print(f"  ❌ {e}")
            print()

        if total_result.warnings:
            print("WARNINGS:")
            for w in total_result.warnings:
                print(f"  ⚠️  {w}")
            print()

        print("SUMMARY:")
        print(f"  Errors:   {len(total_result.errors)}")
        print(f"  Warnings: {len(total_result.warnings)}")
        print(f"  Passed:   {len(total_result.passed)}")
        print()

        if total_result.errors:
            print("STATUS: ❌ DEPLOYMENT WILL FAIL")
        elif total_result.warnings:
            print("STATUS: ⚠️  DEPLOYMENT MAY HAVE ISSUES")
        else:
            print("STATUS: ✅ READY FOR DEPLOYMENT")

    # Exit code
    if total_result.errors:
        sys.exit(1)
    elif total_result.warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
