#!/usr/bin/env python3
"""
Unified plugin validation and auto-fix script.

Runs all automated checks and optionally fixes issues:
- Registration integrity (marketplace.json ↔ files)
- Frontmatter validation (YAML syntax, required fields)
- Directory structure validation
- Settings.json validation

Usage:
    python3 scripts/validate_all.py [plugin-path]
    python3 scripts/validate_all.py --fix           # Auto-fix issues
    python3 scripts/validate_all.py --fix --dry-run # Preview fixes
    python3 scripts/validate_all.py --json          # JSON output

Exit codes:
    0 - All passed (or all fixed with --fix)
    1 - Errors found (deployment will fail)
    2 - Warnings only (deployment may work)
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import yaml
except ImportError:
    # Fallback: simple YAML parser for frontmatter
    yaml = None


class Fix:
    """Represents a fixable issue."""
    def __init__(self, description: str, fix_func, *args):
        self.description = description
        self.fix_func = fix_func
        self.args = args

    def apply(self) -> bool:
        """Apply the fix. Returns True if successful."""
        try:
            self.fix_func(*self.args)
            return True
        except Exception as e:
            print(f"  ⚠️  Fix failed: {e}")
            return False


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
        self.fixes: List[Fix] = []  # Auto-fixable issues

    def add_error(self, msg: str, fix: Optional[Fix] = None):
        self.errors.append(msg)
        if fix:
            self.fixes.append(fix)

    def add_warning(self, msg: str, fix: Optional[Fix] = None):
        self.warnings.append(msg)
        if fix:
            self.fixes.append(fix)

    def add_pass(self, msg: str):
        self.passed.append(msg)

    def merge(self, other: 'ValidationResult'):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.passed.extend(other.passed)
        self.fixes.extend(other.fixes)


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
        if yaml:
            return yaml.safe_load(yaml_content), None
        else:
            # Simple fallback parser
            result = {}
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip().strip('"').strip("'")
            return result, None
    except (ValueError, Exception) as e:
        return None, str(e)


# ============================================================================
# FIX FUNCTIONS
# ============================================================================

def fix_add_to_marketplace(marketplace_path: Path, item_type: str, item_path: str):
    """Add an item to marketplace.json."""
    data = json.loads(marketplace_path.read_text())
    plugins = data.get("plugins", [data])

    for plugin in plugins:
        if item_type not in plugin:
            plugin[item_type] = []

        # Normalize path format
        if not item_path.startswith("./"):
            item_path = f"./{item_path}"

        if item_path not in plugin[item_type]:
            plugin[item_type].append(item_path)

    # Write back with proper formatting
    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_remove_from_marketplace(marketplace_path: Path, item_type: str, item_path: str):
    """Remove an item from marketplace.json."""
    data = json.loads(marketplace_path.read_text())
    plugins = data.get("plugins", [data])

    for plugin in plugins:
        items = plugin.get(item_type, [])
        # Try both formats
        for fmt in [item_path, f"./{item_path}", item_path.lstrip("./")]:
            if fmt in items:
                items.remove(fmt)
                break
        plugin[item_type] = items

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_create_command_stub(cmd_path: Path, name: str):
    """Create a stub command file with proper frontmatter."""
    content = f'''---
description: TODO: Add description for {name}
argument-hint: "[optional args]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
---

# {name.replace('-', ' ').title()}

TODO: Add command instructions here.
'''
    cmd_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_path.write_text(content)


def fix_create_agent_stub(agent_path: Path, name: str):
    """Create a stub agent file with proper frontmatter."""
    content = f'''---
name: {name}
description: TODO: Add description for {name}
tools: ["Read", "Write", "Bash", "Grep", "Glob"]
model: sonnet
---

# {name.replace('-', ' ').title()} Agent

TODO: Add agent instructions here.
'''
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(content)


def fix_create_skill_stub(skill_dir: Path, name: str):
    """Create a stub SKILL.md file."""
    skill_md = skill_dir / "SKILL.md"
    content = f'''---
name: {name}
description: TODO: Add description for {name}
allowed-tools: ["Read", "Grep", "Glob"]
---

# {name.replace('-', ' ').title()}

TODO: Add skill instructions here.

## When to Use

- TODO: Add trigger scenarios

## How to Use

TODO: Add usage instructions
'''
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md.write_text(content)


def fix_add_frontmatter(file_path: Path, frontmatter: dict):
    """Add or replace frontmatter in a markdown file."""
    content = file_path.read_text()

    # Build YAML frontmatter
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            fm_lines.append(f'{key}: {json.dumps(value)}')
        elif isinstance(value, str) and '\n' in value:
            fm_lines.append(f'{key}: |')
            for line in value.split('\n'):
                fm_lines.append(f'  {line}')
        else:
            fm_lines.append(f'{key}: {value}')
    fm_lines.append("---\n")
    fm_str = '\n'.join(fm_lines)

    # Remove existing frontmatter if present
    if content.startswith('---'):
        try:
            end_idx = content.index('---', 3)
            content = content[end_idx + 3:].lstrip('\n')
        except ValueError:
            pass

    file_path.write_text(fm_str + content)


def fix_source_path(marketplace_path: Path, plugin_idx: int, new_source: str):
    """Fix source path in marketplace.json."""
    data = json.loads(marketplace_path.read_text())
    plugins = data.get("plugins", [data])

    if plugin_idx < len(plugins):
        plugins[plugin_idx]["source"] = new_source

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_add_shebang(script_path: Path):
    """Add shebang to Python script."""
    content = script_path.read_text()
    if not content.startswith('#!'):
        content = '#!/usr/bin/env python3\n' + content
        script_path.write_text(content)


def fix_make_executable(script_path: Path):
    """Make script executable."""
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)


def fix_path_format(marketplace_path: Path, item_type: str, old_path: str, new_path: str):
    """Fix a path format in marketplace.json (e.g., add/remove .md extension)."""
    data = json.loads(marketplace_path.read_text())
    plugins = data.get("plugins", [data])

    for plugin in plugins:
        items = plugin.get(item_type, [])
        for i, item in enumerate(items):
            # Normalize for comparison
            if item.rstrip('/') == old_path.rstrip('/') or item == old_path:
                items[i] = new_path
                break

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_registration(plugin_root: Path, plugin_data: dict, marketplace_path: Path) -> ValidationResult:
    """Validate marketplace.json entries match actual files."""
    result = ValidationResult()

    registered_commands = plugin_data.get("commands", [])
    registered_agents = plugin_data.get("agents", [])
    registered_skills = plugin_data.get("skills", [])

    # Validate commands
    commands_dir = plugin_root / "commands"
    if commands_dir.exists():
        actual_commands = {f.stem for f in commands_dir.glob("*.md")}
        registered_set = set()

        for cmd in registered_commands:
            # CRITICAL: Validate path format - commands MUST end with .md
            if not cmd.endswith(".md"):
                correct_path = cmd + ".md"
                result.add_error(
                    f'Command path "{cmd}" missing .md extension (plugin system will fail to load)',
                    Fix(f'Fix path to "{correct_path}"', fix_path_format, marketplace_path, "commands", cmd, correct_path)
                )
                # Still check if the file would exist with correct extension
                name = cmd.replace("./commands/", "").replace("commands/", "")
            else:
                name = cmd.replace("./commands/", "").replace("commands/", "").replace(".md", "")

            registered_set.add(name)

            cmd_file = commands_dir / f"{name}.md"
            if cmd_file.exists():
                if cmd.endswith(".md"):
                    result.add_pass(f"commands/{name}.md registered and exists")
            else:
                result.add_error(
                    f"commands/{name}.md NOT FOUND (registered in marketplace.json)",
                    Fix(f"Create stub commands/{name}.md", fix_create_command_stub, cmd_file, name)
                )

        for actual in actual_commands:
            if actual not in registered_set:
                result.add_error(
                    f"commands/{actual}.md exists but NOT REGISTERED in marketplace.json",
                    Fix(f"Add commands/{actual}.md to marketplace.json",
                        fix_add_to_marketplace, marketplace_path, "commands", f"commands/{actual}.md")
                )

    # Validate agents
    agents_dir = plugin_root / "agents"
    if agents_dir.exists():
        actual_agents = {f.stem for f in agents_dir.glob("*.md")}
        registered_set = set()

        for agent in registered_agents:
            # CRITICAL: Validate path format - agents MUST end with .md
            if not agent.endswith(".md"):
                correct_path = agent + ".md"
                result.add_error(
                    f'Agent path "{agent}" missing .md extension (plugin system will fail to load)',
                    Fix(f'Fix path to "{correct_path}"', fix_path_format, marketplace_path, "agents", agent, correct_path)
                )
                name = agent.replace("./agents/", "").replace("agents/", "")
            else:
                name = agent.replace("./agents/", "").replace("agents/", "").replace(".md", "")

            registered_set.add(name)

            agent_file = agents_dir / f"{name}.md"
            if agent_file.exists():
                if agent.endswith(".md"):
                    result.add_pass(f"agents/{name}.md registered and exists")
            else:
                result.add_error(
                    f"agents/{name}.md NOT FOUND",
                    Fix(f"Create stub agents/{name}.md", fix_create_agent_stub, agent_file, name)
                )

        for actual in actual_agents:
            if actual not in registered_set:
                result.add_error(
                    f"agents/{actual}.md exists but NOT REGISTERED",
                    Fix(f"Add agents/{actual}.md to marketplace.json",
                        fix_add_to_marketplace, marketplace_path, "agents", f"agents/{actual}.md")
                )

    # Validate skills
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        actual_skills = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        registered_set = set()

        for skill in registered_skills:
            # CRITICAL: Validate path format - skills are directories, must NOT end with .md
            if skill.endswith(".md"):
                correct_path = skill.replace(".md", "").rstrip("/")
                result.add_error(
                    f'Skill path "{skill}" has .md extension but skills are directories',
                    Fix(f'Fix path to "{correct_path}"', fix_path_format, marketplace_path, "skills", skill, correct_path)
                )
                name = skill.replace("./skills/", "").replace("skills/", "").replace(".md", "").rstrip("/")
            else:
                name = skill.replace("./skills/", "").replace("skills/", "").rstrip("/")

            registered_set.add(name)

            skill_md = skills_dir / name / "SKILL.md"
            if skill_md.exists():
                if not skill.endswith(".md"):
                    result.add_pass(f"skills/{name}/SKILL.md registered and exists")
            elif (skills_dir / name).exists():
                result.add_error(
                    f"skills/{name}/ exists but missing SKILL.md",
                    Fix(f"Create skills/{name}/SKILL.md", fix_create_skill_stub, skills_dir / name, name)
                )
            else:
                result.add_error(
                    f"skills/{name}/ NOT FOUND",
                    Fix(f"Create skills/{name}/ with SKILL.md", fix_create_skill_stub, skills_dir / name, name)
                )

        for actual in actual_skills:
            if actual not in registered_set:
                skill_md = skills_dir / actual / "SKILL.md"
                if skill_md.exists():
                    result.add_error(
                        f"skills/{actual}/ exists with SKILL.md but NOT REGISTERED",
                        Fix(f"Add skills/{actual} to marketplace.json",
                            fix_add_to_marketplace, marketplace_path, "skills", f"skills/{actual}")
                    )

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

            if error or not fm:
                default_fm = {
                    "description": f"TODO: Add description for {cmd_file.stem}",
                    "argument-hint": "[optional args]",
                    "allowed-tools": ["Read", "Write", "Bash", "Grep", "Glob"]
                }
                result.add_error(
                    f"{cmd_file.name}: {error or 'Missing frontmatter'}",
                    Fix(f"Add frontmatter to {cmd_file.name}", fix_add_frontmatter, cmd_file, default_fm)
                )
                continue

            if not fm.get("description"):
                fm["description"] = f"TODO: Add description for {cmd_file.stem}"
                result.add_error(
                    f"{cmd_file.name}: Missing 'description' field",
                    Fix(f"Add description to {cmd_file.name}", fix_add_frontmatter, cmd_file, fm)
                )
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

            if error or not fm:
                default_fm = {
                    "name": agent_file.stem,
                    "description": f"TODO: Add description for {agent_file.stem}",
                    "tools": ["Read", "Write", "Bash", "Grep", "Glob"],
                    "model": "sonnet"
                }
                result.add_error(
                    f"{agent_file.name}: {error or 'Missing frontmatter'}",
                    Fix(f"Add frontmatter to {agent_file.name}", fix_add_frontmatter, agent_file, default_fm)
                )
                continue

            needs_fix = False
            if not fm.get("name"):
                fm["name"] = agent_file.stem
                needs_fix = True
                result.add_error(f"{agent_file.name}: Missing 'name' field")
            if not fm.get("description"):
                fm["description"] = f"TODO: Add description for {agent_file.stem}"
                needs_fix = True
                result.add_error(f"{agent_file.name}: Missing 'description' field")
            if not fm.get("tools"):
                result.add_warning(f"{agent_file.name}: Missing 'tools' field")

            if needs_fix:
                result.fixes.append(Fix(f"Fix frontmatter in {agent_file.name}", fix_add_frontmatter, agent_file, fm))
            elif fm.get("description") and "TODO" not in str(fm.get("description", "")):
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

            if error or not fm:
                default_fm = {
                    "name": skill_dir.name,
                    "description": f"TODO: Add description for {skill_dir.name}",
                    "allowed-tools": ["Read", "Grep", "Glob"]
                }
                result.add_error(
                    f"skills/{skill_dir.name}/SKILL.md: {error or 'Missing frontmatter'}",
                    Fix(f"Add frontmatter to skills/{skill_dir.name}/SKILL.md", fix_add_frontmatter, skill_md, default_fm)
                )
                continue

            needs_fix = False
            if not fm.get("name"):
                fm["name"] = skill_dir.name
                needs_fix = True
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Missing 'name' field")
            if not fm.get("description"):
                fm["description"] = f"TODO: Add description for {skill_dir.name}"
                needs_fix = True
                result.add_error(f"skills/{skill_dir.name}/SKILL.md: Missing 'description' field")
            elif "TODO" in str(fm.get("description", "")):
                result.add_warning(f"skills/{skill_dir.name}/SKILL.md: description contains TODO")
            else:
                if not needs_fix:
                    result.add_pass(f"skills/{skill_dir.name}/SKILL.md: frontmatter valid")

            if needs_fix:
                result.fixes.append(Fix(f"Fix frontmatter in skills/{skill_dir.name}/SKILL.md",
                                       fix_add_frontmatter, skill_md, fm))

    return result


def validate_source_path(plugin_data: dict, marketplace_path: Path, plugin_idx: int) -> ValidationResult:
    """Validate source path format."""
    result = ValidationResult()
    source = plugin_data.get("source", "")

    if isinstance(source, str):
        if source and source not in [".", "./"] and not source.startswith("./"):
            fixed_source = f"./{source}"
            result.add_error(
                f'source "{source}" must start with "./" (e.g., "{fixed_source}")',
                Fix(f'Fix source path to "{fixed_source}"', fix_source_path, marketplace_path, plugin_idx, fixed_source)
            )
        else:
            result.add_pass("source path format valid")
    elif isinstance(source, dict):
        if "source" not in source or "repo" not in source:
            result.add_error('GitHub source format requires {"source": "github", "repo": "user/repo"}')
        else:
            result.add_pass("GitHub source format valid")

    return result


def validate_scripts(plugin_root: Path) -> ValidationResult:
    """Validate script files have shebang and are executable."""
    result = ValidationResult()

    scripts_dir = plugin_root / "scripts"
    if not scripts_dir.exists():
        return result

    for script in scripts_dir.glob("*.py"):
        content = script.read_text()

        # Check shebang
        if not content.startswith('#!'):
            result.add_warning(
                f"scripts/{script.name}: Missing shebang",
                Fix(f"Add shebang to {script.name}", fix_add_shebang, script)
            )
        else:
            result.add_pass(f"scripts/{script.name}: has shebang")

        # Check executable (Unix only)
        if os.name != 'nt':
            if not os.access(script, os.X_OK):
                result.add_warning(
                    f"scripts/{script.name}: Not executable",
                    Fix(f"Make {script.name} executable", fix_make_executable, script)
                )

    return result


def validate_hookify_compliance(plugin_root: Path) -> ValidationResult:
    """
    W028: Check if MUST/CRITICAL/REQUIRED keywords exist without corresponding hooks.
    W035: Check for 'NOT YET HOOKIFIED' markers indicating known unhookified items.

    Per skillmaker's own principle: "문서 기반 강제는 무의미합니다"
    """
    result = ValidationResult()

    # Enforcement keywords that should be hookified
    enforcement_keywords = [
        r'\bMUST\b',
        r'\bCRITICAL\b',
        r'\bREQUIRED\b',
        r'\bMANDATORY\b',
        r'\b강제\b',
        r'\b반드시\b'
    ]

    # Unhookified markers
    unhookified_markers = [
        'NOT YET HOOKIFIED',
        'NOT HOOKIFIED',
        '⚠️ **NOT YET HOOKIFIED**'
    ]

    import re

    # Check if hooks.json exists
    hooks_json = plugin_root / "hooks" / "hooks.json"
    has_hooks = hooks_json.exists()

    # Collect files to check
    files_to_check = []

    # Skills
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    files_to_check.append(skill_md)

    # Agents
    agents_dir = plugin_root / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            files_to_check.append(agent_file)

    # Commands
    commands_dir = plugin_root / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            files_to_check.append(cmd_file)

    # Track findings
    files_with_enforcement = []
    unhookified_found = []

    for file_path in files_to_check:
        try:
            content = file_path.read_text()
        except Exception:
            continue

        rel_path = file_path.relative_to(plugin_root)

        # Check for enforcement keywords
        for pattern in enforcement_keywords:
            if re.search(pattern, content):
                files_with_enforcement.append(str(rel_path))
                break

        # Check for unhookified markers (W035)
        for marker in unhookified_markers:
            if marker in content:
                # Count occurrences
                count = content.count(marker)
                unhookified_found.append((str(rel_path), count))
                break

    # W028: Enforcement keywords without hooks
    if files_with_enforcement and not has_hooks:
        result.add_warning(
            f"W028: {len(files_with_enforcement)} file(s) contain enforcement keywords "
            f"(MUST/CRITICAL/REQUIRED) but no hooks/hooks.json exists. "
            f"Document-based enforcement is ineffective."
        )
    elif files_with_enforcement and has_hooks:
        # hooks.json exists, that's good
        result.add_pass(f"W028: Enforcement keywords found in {len(files_with_enforcement)} files, hooks.json exists")

    # W035: Unhookified markers found
    for rel_path, count in unhookified_found:
        result.add_warning(
            f"W035: {rel_path}: Contains {count} 'NOT YET HOOKIFIED' marker(s) - "
            f"known limitation awaiting hookification"
        )

    if not unhookified_found and files_to_check:
        result.add_pass("W035: No unhookified markers found")

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

        plugins = settings.get("plugins", [])
        for i, plugin in enumerate(plugins):
            if isinstance(plugin, dict):
                source = plugin.get("source", "")
                if isinstance(source, str) and source:
                    if not source.startswith("./") and not source.startswith("/"):
                        result.add_error(
                            f'settings.json plugins[{i}].source "{source}" must start with "./"'
                        )

        marketplaces = settings.get("extraKnownMarketplaces", {})
        for name, config in marketplaces.items():
            source = config.get("source", "")
            if isinstance(source, str) and source and not source.startswith("./"):
                result.add_error(
                    f'settings.json extraKnownMarketplaces.{name}.source must start with "./"'
                )

    return result


def apply_fixes(fixes: List[Fix], dry_run: bool = False) -> Tuple[int, int]:
    """Apply all fixes. Returns (success_count, fail_count)."""
    success = 0
    fail = 0

    print("\n" + "=" * 60)
    print("APPLYING FIXES" if not dry_run else "FIXES PREVIEW (dry-run)")
    print("=" * 60)

    for fix in fixes:
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}→ {fix.description}")

        if dry_run:
            success += 1
        else:
            if fix.apply():
                print(f"  ✅ Done")
                success += 1
            else:
                fail += 1

    return success, fail


def main():
    # Parse arguments
    json_output = "--json" in sys.argv
    fix_mode = "--fix" in sys.argv
    dry_run = "--dry-run" in sys.argv
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

    # Check for marketplace.json and plugin.json conflict
    # This causes "no context" error in Claude Code runtime
    claude_plugin_dir = plugin_root / ".claude-plugin"
    if claude_plugin_dir.exists():
        has_marketplace = (claude_plugin_dir / "marketplace.json").exists()
        has_plugin_json = (claude_plugin_dir / "plugin.json").exists()
        if has_marketplace and has_plugin_json:
            error_msg = (
                "CONFLICT: .claude-plugin/ contains both marketplace.json and plugin.json\n"
                "  This causes 'no context' error during plugin installation.\n"
                "  Solution: Remove plugin.json when using marketplace.json for distribution."
            )
            if json_output:
                print(json.dumps({"status": "error", "message": error_msg}))
            else:
                print(f"ERROR: {error_msg}")
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

    for i, plugin in enumerate(plugins):
        source = plugin.get("source", "./")
        if source in [".", "./"]:
            effective_root = plugin_root
        else:
            effective_root = plugin_root / source.lstrip("./")

        total_result.merge(validate_source_path(plugin, marketplace_path, i))
        total_result.merge(validate_registration(effective_root, plugin, marketplace_path))
        total_result.merge(validate_frontmatter_fields(effective_root))
        total_result.merge(validate_scripts(effective_root))
        total_result.merge(validate_hookify_compliance(effective_root))

    # Output results
    if json_output:
        output = {
            "status": "fail" if total_result.errors else ("warn" if total_result.warnings else "pass"),
            "errors": total_result.errors,
            "warnings": total_result.warnings,
            "passed": len(total_result.passed),
            "fixable": len(total_result.fixes)
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
        print(f"  Fixable:  {len(total_result.fixes)}")
        print()

        if total_result.errors:
            print("STATUS: ❌ DEPLOYMENT WILL FAIL")
        elif total_result.warnings:
            print("STATUS: ⚠️  DEPLOYMENT MAY HAVE ISSUES")
        else:
            print("STATUS: ✅ READY FOR DEPLOYMENT")

    # Apply fixes if requested
    if fix_mode and total_result.fixes:
        success, fail = apply_fixes(total_result.fixes, dry_run)
        print(f"\nFixes applied: {success}, Failed: {fail}")

        if not dry_run and success > 0:
            print("\n💡 Re-run validation to verify fixes:")
            print(f"   python3 {sys.argv[0]}")
    elif fix_mode and not total_result.fixes:
        print("\n✨ Nothing to fix!")
    elif total_result.fixes and not json_output:
        print(f"\n💡 {len(total_result.fixes)} issues can be auto-fixed. Run with --fix:")
        print(f"   python3 {sys.argv[0]} --fix")
        print(f"   python3 {sys.argv[0]} --fix --dry-run  # Preview only")

    # Exit code
    if total_result.errors and not (fix_mode and not dry_run):
        sys.exit(1)
    elif total_result.warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
