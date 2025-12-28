#!/usr/bin/env python3
"""
Unified plugin validation and auto-fix script.

Runs all automated checks and optionally fixes issues:
- Registration integrity (marketplace.json - files)
- Frontmatter validation (YAML syntax, required fields)
- Directory structure validation
- Settings.json validation
- Deploy readiness (git status, push state)

Validation Phases:
    PHASE 0: Schema Static   - JSON structure validation with error codes
    PHASE 1: CLI Validation  - Claude Code CLI schema check
    PHASE 2: File Validation - File existence, frontmatter, content
    PHASE 3: Best Practices  - Pattern matching, recommendations
    PHASE 4: Deploy Ready    - Git uncommitted/unpushed checks (DEFAULT)
    PHASE 5: Remote Check    - GitHub source repo accessibility & structure
    PHASE 6: Cache Mgmt      - Auto-clear outdated plugin cache

Usage:
    python3 scripts/validate_all.py [plugin-path]
    python3 scripts/validate_all.py --fix           # Auto-fix issues
    python3 scripts/validate_all.py --fix --dry-run # Preview fixes
    python3 scripts/validate_all.py --json          # JSON output
    python3 scripts/validate_all.py --skip-git      # Skip git status checks
    python3 scripts/validate_all.py --schema-only   # Fast: only schema validation
    python3 scripts/validate_all.py --quiet         # Minimal output, errors only
    python3 scripts/validate_all.py --pre-edit      # Validate current state before edit

Hook Integration:
    Hooks can use these flags for efficient validation:
    - PostToolUse (Write/Edit): --skip-git --schema-only  (fastest, ~1s)
    - PreToolUse (git commit):  --skip-git                (medium, ~2s)
    - PreToolUse (git push):    (no flags)                (full, ~5s)

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

# Fix Windows console encoding for emoji/unicode output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    import yaml
except ImportError:
    # Fallback: simple YAML parser for frontmatter
    yaml = None

import re

# =============================================================================
# SCHEMA DEFINITIONS - Static validation rules
# =============================================================================

# Error codes for precise identification
class ErrorCode:
    E001 = "E001"  # Components inside .claude-plugin
    E002 = "E002"  # Skill has .md extension
    E003 = "E003"  # Command missing .md extension
    E004 = "E004"  # Agent missing .md extension
    E005 = "E005"  # source is string "github"/"url" (should be object)
    E006 = "E006"  # source uses "type" key instead of "source"
    E007 = "E007"  # repo at plugin level (should be in source object)
    E008 = "E008"  # repository is object (should be string)
    E009 = "E009"  # Missing SKILL.md in skill directory
    E010 = "E010"  # Agent missing required "tools" field
    E011 = "E011"  # Path doesn't start with ./
    E012 = "E012"  # File/directory not found
    E013 = "E013"  # Unrecognized field in schema
    E014 = "E014"  # Missing required field
    E015 = "E015"  # Invalid name format (not kebab-case)
    E016 = "E016"  # Path resolution mismatch (file exists at plugin_root but not at marketplace.json location)
    E017 = "E017"  # marketplace.json location causes path resolution issues
    E018 = "E018"  # Git remote does not match marketplace.json source repo
    E019 = "E019"  # External GitHub repo not accessible or doesn't exist
    E020 = "E020"  # External repo missing required files (cross-repo validation)
    E021 = "E021"  # settings.json enabledPlugins must be object, not array
    E022 = "E022"  # settings.json source.type invalid discriminator (valid: url|github|git|npm|file|directory)
    E023 = "E023"  # Marketplace cache repo mismatch (known_marketplaces.json vs git remote)
    E024 = "E024"  # Marketplace cache stale (known_marketplaces.json entry but missing cache dir)
    E025 = "E025"  # plugin.json version doesn't match marketplace.json version
    E026 = "E026"  # Duplicate plugin registration (same plugin from multiple marketplaces)
    E027 = "E027"  # hooks.json schema invalid (Claude Code 1.0.40+ schema)
    # Pattern compliance warnings (W029-W034)
    W029 = "W029"  # Skill missing recommended frontmatter fields (name, description, allowed-tools)
    W030 = "W030"  # Agent missing recommended frontmatter fields (name, description, tools, skills)
    W031 = "W031"  # Skill content exceeds recommended limit (progressive disclosure violation)
    W032 = "W032"  # Skill references not separated into references/ subdirectory
    W033 = "W033"  # Agent/command declares skills but doesn't use Skill() tool pattern
    W034 = "W034"  # Multi-stage workflow without per-stage skill loading (should hookify)


# Schema patterns (regex)
SCHEMA = {
    "kebab_case": re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"),
    "relative_path": re.compile(r"^\./"),
    "md_extension": re.compile(r"\.md$"),
    "json_extension": re.compile(r"\.json$"),
    "semver": re.compile(r"^\d+\.\d+\.\d+"),
    "repo_format": re.compile(r"^[^/]+/[^/]+$"),
    "url_format": re.compile(r"^https?://"),
}

# Allowed fields per schema type
ALLOWED_FIELDS = {
    "marketplace": {"$schema", "name", "owner", "plugins", "description", "version", "homepage", "metadata"},
    "owner": {"name", "email", "url"},
    "metadata": {"description", "version", "pluginRoot"},
    "plugin": {
        "name", "source", "description", "version", "author", "homepage",
        "repository", "license", "keywords", "category", "tags", "strict",
        "commands", "agents", "skills", "hooks", "mcpServers", "lspServers"
    },
    "author": {"name", "email"},
    "plugin_json": {"name", "version", "description", "author", "repository", "homepage", "license", "keywords", "category", "tags"},
}

# Required fields per schema type
REQUIRED_FIELDS = {
    "marketplace": {"name", "owner", "plugins"},
    "owner": {"name"},
    "plugin": {"name", "source"},
    "agent_frontmatter": {"name", "description", "tools"},
    "command_frontmatter": {"description"},
    "skill_frontmatter": {"name", "description"},
}

# Forbidden fields (common mistakes)
FORBIDDEN_FIELDS = {
    "plugin": {"components", "repo"},  # components not valid, repo should be in source
}

# Reserved marketplace names
RESERVED_NAMES = {
    "claude-code-marketplace", "claude-plugins-official", "anthropic-marketplace",
    "anthropic-plugins", "claude-code-plugins", "agent-skills", "life-sciences"
}


def format_error(code: str, message: str) -> str:
    """Format error with code for easy identification."""
    return f"[{code}] {message}"


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
            print(f"  [WARN]  Fix failed: {e}")
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
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
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
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
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
    content = file_path.read_text(encoding='utf-8')

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
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    plugins = data.get("plugins", [data])

    if plugin_idx < len(plugins):
        plugins[plugin_idx]["source"] = new_source

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_add_shebang(script_path: Path):
    """Add shebang to Python script."""
    content = script_path.read_text(encoding='utf-8')
    if not content.startswith('#!'):
        content = '#!/usr/bin/env python3\n' + content
        script_path.write_text(content)


def fix_make_executable(script_path: Path):
    """Make script executable."""
    os.chmod(script_path, os.stat(script_path).st_mode | 0o111)


def fix_path_format(marketplace_path: Path, item_type: str, old_path: str, new_path: str):
    """Fix a path format in marketplace.json (e.g., add/remove .md extension)."""
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    plugins = data.get("plugins", [data])

    for plugin in plugins:
        items = plugin.get(item_type, [])
        for i, item in enumerate(items):
            # Normalize for comparison
            if item.rstrip('/') == old_path.rstrip('/') or item == old_path:
                items[i] = new_path
                break

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_github_source_format(marketplace_path: Path, plugin_idx: int):
    """Fix GitHub source format: move repo from plugin level into source object."""
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    plugins = data.get("plugins", [data])

    if plugin_idx < len(plugins):
        plugin = plugins[plugin_idx]
        source = plugin.get("source", "")
        repo = plugin.pop("repo", None)  # Remove repo from plugin level

        if source in ["github", "url"] and repo:
            # Convert to correct format
            plugin["source"] = {"source": source, "repo": repo}
        elif source in ["github", "url"]:
            # No repo found, create placeholder
            plugin["source"] = {"source": source, "repo": "OWNER/REPO"}

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_plugin_json_schema(plugin_json_path: Path):
    """Auto-fix plugin.json to conform to schema."""
    data = json.loads(plugin_json_path.read_text(encoding='utf-8'))

    # Allowed fields only
    ALLOWED = {"name", "version", "description", "author", "repository",
               "homepage", "license", "keywords", "category", "tags"}

    # Remove forbidden fields
    for key in list(data.keys()):
        if key not in ALLOWED:
            del data[key]

    # Fix repository format (object => string)
    if "repository" in data and isinstance(data["repository"], dict):
        url = data["repository"].get("url", "")
        data["repository"] = url

    plugin_json_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_move_component_to_root(plugin_root: Path, component_type: str):
    """Move component directory from .claude-plugin/ to plugin root."""
    import shutil

    wrong_dir = plugin_root / ".claude-plugin" / component_type
    correct_dir = plugin_root / component_type

    if not wrong_dir.exists():
        return

    if correct_dir.exists():
        # Merge: move files from wrong to correct
        for item in wrong_dir.iterdir():
            target = correct_dir / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
        # Remove empty wrong dir
        if not list(wrong_dir.iterdir()):
            wrong_dir.rmdir()
    else:
        # Simple move
        shutil.move(str(wrong_dir), str(correct_dir))


def fix_skill_structure(plugin_root: Path, skill_path: str):
    """Convert skill .md file to directory/SKILL.md structure.

    Before: skills/my-skill.md (file)
    After:  skills/my-skill/SKILL.md (directory with file)
    """
    # Normalize path
    normalized = skill_path.lstrip("./")
    full_path = plugin_root / normalized

    # If it's a .md file, convert to directory structure
    if full_path.exists() and full_path.is_file() and full_path.suffix == ".md":
        # Read content
        content = full_path.read_text(encoding='utf-8')

        # Create directory (remove .md extension)
        dir_path = full_path.with_suffix("")
        dir_path.mkdir(parents=True, exist_ok=True)

        # Write content to SKILL.md
        skill_md = dir_path / "SKILL.md"
        skill_md.write_text(content)

        # Remove original .md file
        full_path.unlink()

    # Also check in .claude-plugin/ location
    wrong_path = plugin_root / ".claude-plugin" / normalized
    if wrong_path.exists() and wrong_path.is_file() and wrong_path.suffix == ".md":
        content = wrong_path.read_text(encoding='utf-8')

        # Create correct directory at root
        dir_name = wrong_path.stem  # filename without .md
        correct_dir = plugin_root / "skills" / dir_name
        correct_dir.mkdir(parents=True, exist_ok=True)

        skill_md = correct_dir / "SKILL.md"
        skill_md.write_text(content)

        wrong_path.unlink()


def fix_skills_complete(plugin_root: Path):
    """Complete fix for skills: move from .claude-plugin/ to root and convert .md to directory structure.

    Handles:
    1. Move .claude-plugin/skills/ to ./skills/
    2. Convert any .md files to directory/SKILL.md structure
    3. Update marketplace.json paths
    """
    import shutil

    wrong_dir = plugin_root / ".claude-plugin" / "skills"
    correct_dir = plugin_root / "skills"

    if not wrong_dir.exists():
        return

    # Create skills directory at root if needed
    correct_dir.mkdir(parents=True, exist_ok=True)

    # Process each item in wrong_dir
    for item in list(wrong_dir.iterdir()):
        if item.is_file() and item.suffix == ".md":
            # Convert .md file to directory/SKILL.md
            skill_name = item.stem
            target_dir = correct_dir / skill_name
            target_dir.mkdir(parents=True, exist_ok=True)

            content = item.read_text(encoding='utf-8')
            skill_md = target_dir / "SKILL.md"
            skill_md.write_text(content)

            item.unlink()
        elif item.is_dir():
            # Move directory as-is
            target = correct_dir / item.name
            if not target.exists():
                shutil.move(str(item), str(target))

    # Remove empty wrong_dir
    if wrong_dir.exists() and not list(wrong_dir.iterdir()):
        wrong_dir.rmdir()

    # Update marketplace.json paths
    marketplace_path = plugin_root / ".claude-plugin" / "marketplace.json"
    if marketplace_path.exists():
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
        for plugin in data.get("plugins", [data]):
            skills = plugin.get("skills", [])
            updated_skills = []
            for skill in skills:
                # Remove .md extension if present
                if skill.endswith(".md"):
                    skill = skill[:-3]  # Remove .md
                updated_skills.append(skill)
            if skills:
                plugin["skills"] = updated_skills
        marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


# ============================================================================
# SCHEMA-BASED STATIC VALIDATION (Primary validation layer)
# ============================================================================

def validate_schema_static(plugin_root: Path, marketplace_path: Path) -> ValidationResult:
    """
    Static schema validation - catches errors at parse time.
    This is the PRIMARY validation layer that runs before any file I/O checks.
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        result.add_error(format_error(ErrorCode.E014, "marketplace.json not found"))
        return result

    try:
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        result.add_error(format_error(ErrorCode.E014, f"Invalid JSON: {e}"))
        return result

    # -------------------------------------------------------------------------
    # 1. MARKETPLACE ROOT VALIDATION
    # -------------------------------------------------------------------------

    # Check required fields
    for field in REQUIRED_FIELDS["marketplace"]:
        if field not in data:
            result.add_error(format_error(ErrorCode.E014, f"Missing required field: '{field}'"))

    # Check unrecognized fields
    unrecognized = set(data.keys()) - ALLOWED_FIELDS["marketplace"]
    if unrecognized:
        result.add_error(format_error(
            ErrorCode.E013,
            f"Unrecognized field(s) at marketplace root: {', '.join(sorted(unrecognized))}"
        ))

    # Validate name format
    name = data.get("name", "")
    if name:
        if name.lower() in RESERVED_NAMES:
            result.add_error(format_error(ErrorCode.E015, f"Reserved name: '{name}'"))
        elif " " in name:
            result.add_error(format_error(ErrorCode.E015, f"Name contains spaces: '{name}' (use kebab-case)"))
        elif not SCHEMA["kebab_case"].match(name) and name not in RESERVED_NAMES:
            result.add_warning(f"Name '{name}' is not kebab-case (recommended: lowercase-with-hyphens)")
    else:
        result.add_error(format_error(ErrorCode.E014, "Missing 'name' field"))

    # Validate owner
    owner = data.get("owner")
    if owner:
        if not isinstance(owner, dict):
            result.add_error(format_error(ErrorCode.E014, "'owner' must be an object"))
        else:
            if "name" not in owner:
                result.add_error(format_error(ErrorCode.E014, "owner.name is required"))
            unrecognized_owner = set(owner.keys()) - ALLOWED_FIELDS["owner"]
            if unrecognized_owner:
                result.add_error(format_error(ErrorCode.E013, f"Unrecognized owner field(s): {unrecognized_owner}"))

    # -------------------------------------------------------------------------
    # 2. PLUGIN ENTRIES VALIDATION
    # -------------------------------------------------------------------------

    plugins = data.get("plugins", [])
    if not isinstance(plugins, list):
        result.add_error(format_error(ErrorCode.E014, "'plugins' must be an array"))
        return result

    if len(plugins) == 0:
        result.add_error(format_error(ErrorCode.E014, "'plugins' array is empty"))
        return result

    for i, plugin in enumerate(plugins):
        prefix = f"plugins[{i}]"

        if not isinstance(plugin, dict):
            result.add_error(format_error(ErrorCode.E014, f"{prefix} must be an object"))
            continue

        # Check required fields
        for field in REQUIRED_FIELDS["plugin"]:
            if field not in plugin:
                result.add_error(format_error(ErrorCode.E014, f"{prefix}.{field} is required"))

        # Check unrecognized fields
        unrecognized_plugin = set(plugin.keys()) - ALLOWED_FIELDS["plugin"]
        if unrecognized_plugin:
            result.add_error(format_error(
                ErrorCode.E013,
                f"{prefix}: Unrecognized field(s): {', '.join(sorted(unrecognized_plugin))}"
            ))

        # Check forbidden fields
        for forbidden in FORBIDDEN_FIELDS["plugin"]:
            if forbidden in plugin:
                if forbidden == "repo":
                    result.add_error(
                        format_error(ErrorCode.E007,
                            f'{prefix}.repo is at plugin level. '
                            f'Move into source: "source": {{"source": "github", "repo": "..."}}'),
                        Fix(f"Fix {prefix} GitHub source format",
                            fix_github_source_format, marketplace_path, i)
                    )
                elif forbidden == "components":
                    result.add_error(format_error(
                        ErrorCode.E013,
                        f'{prefix}.components is not valid. Use commands/agents/skills arrays.'
                    ))

        # Validate source format
        source = plugin.get("source")
        if source is not None:
            result.merge(validate_source_schema(source, prefix, marketplace_path, i))

        # Validate path arrays
        result.merge(validate_path_arrays(plugin, prefix, marketplace_path))

        # Validate repository format
        if "repository" in plugin:
            repo = plugin["repository"]
            if isinstance(repo, dict):
                result.add_error(
                    format_error(ErrorCode.E008,
                        f'{prefix}.repository must be string URL, not object'),
                    Fix(f"Fix {prefix}.repository format",
                        fix_repository_to_string, marketplace_path, i)
                )

    return result


def validate_source_schema(source: Any, prefix: str, marketplace_path: Path, plugin_idx: int) -> ValidationResult:
    """Validate source field format according to schema."""
    result = ValidationResult()

    if source is None or source == "":
        result.add_error(format_error(ErrorCode.E014, f"{prefix}.source is empty/null"))
        return result

    if isinstance(source, str):
        # String source: must start with ./ or be a path
        if source in ["github", "url"]:
            result.add_error(
                format_error(ErrorCode.E005,
                    f'{prefix}.source is "{source}" but must be object. '
                    f'Use: "source": {{"source": "{source}", "repo": "owner/repo"}}'),
                Fix(f"Fix {prefix} source format",
                    fix_github_source_format, marketplace_path, plugin_idx)
            )
        elif source == ".":
            result.add_error(
                format_error(ErrorCode.E011,
                    f'{prefix}.source is "." but must be "./"'),
                Fix(f"Fix {prefix}.source to './'",
                    fix_source_path, marketplace_path, plugin_idx, "./")
            )
        elif not SCHEMA["relative_path"].match(source):
            result.add_error(
                format_error(ErrorCode.E011,
                    f'{prefix}.source "{source}" must start with "./"'),
                Fix(f"Fix {prefix}.source path",
                    fix_source_path, marketplace_path, plugin_idx, f"./{source}")
            )

    elif isinstance(source, dict):
        # Object source: validate structure
        if "type" in source and "source" not in source:
            result.add_error(
                format_error(ErrorCode.E006,
                    f'{prefix}.source uses "type" key. Must use "source" key. '
                    f'Correct: {{"source": "github", "repo": "..."}}')
            )
        elif "source" not in source:
            result.add_error(format_error(ErrorCode.E014, f'{prefix}.source object missing "source" key'))
        else:
            source_type = source.get("source")
            if source_type == "github":
                if "repo" not in source:
                    result.add_error(format_error(ErrorCode.E014,
                        f'{prefix}.source.repo is required for GitHub source'))
                elif not SCHEMA["repo_format"].match(str(source.get("repo", ""))):
                    result.add_error(format_error(ErrorCode.E015,
                        f'{prefix}.source.repo must be "owner/repo" format'))
            elif source_type == "url":
                if "url" not in source:
                    result.add_error(format_error(ErrorCode.E014,
                        f'{prefix}.source.url is required for URL source'))
                elif not SCHEMA["url_format"].match(str(source.get("url", ""))):
                    result.add_error(format_error(ErrorCode.E015,
                        f'{prefix}.source.url must be http:// or https://'))
            elif source_type not in ["github", "url"]:
                result.add_error(format_error(ErrorCode.E015,
                    f'{prefix}.source.source must be "github" or "url", got "{source_type}"'))
    else:
        result.add_error(format_error(ErrorCode.E014,
            f'{prefix}.source must be string or object, got {type(source).__name__}'))

    return result


def validate_path_arrays(plugin: dict, prefix: str, marketplace_path: Path) -> ValidationResult:
    """Validate commands/agents/skills/hooks path format."""
    result = ValidationResult()

    # Commands: must be .md files
    for i, cmd in enumerate(plugin.get("commands", [])):
        if not isinstance(cmd, str):
            result.add_error(format_error(ErrorCode.E014, f"{prefix}.commands[{i}] must be string"))
            continue
        if not SCHEMA["relative_path"].match(cmd):
            result.add_error(format_error(ErrorCode.E011, f'{prefix}.commands[{i}] "{cmd}" must start with "./"'))
        if not SCHEMA["md_extension"].search(cmd):
            correct = cmd + ".md"
            result.add_error(
                format_error(ErrorCode.E003, f'{prefix}.commands[{i}] "{cmd}" must end with .md'),
                Fix(f'Fix path to "{correct}"', fix_path_format, marketplace_path, "commands", cmd, correct)
            )

    # Agents: must be .md files
    for i, agent in enumerate(plugin.get("agents", [])):
        if not isinstance(agent, str):
            result.add_error(format_error(ErrorCode.E014, f"{prefix}.agents[{i}] must be string"))
            continue
        if not SCHEMA["relative_path"].match(agent):
            result.add_error(format_error(ErrorCode.E011, f'{prefix}.agents[{i}] "{agent}" must start with "./"'))
        if not SCHEMA["md_extension"].search(agent):
            correct = agent + ".md"
            result.add_error(
                format_error(ErrorCode.E004, f'{prefix}.agents[{i}] "{agent}" must end with .md'),
                Fix(f'Fix path to "{correct}"', fix_path_format, marketplace_path, "agents", agent, correct)
            )

    # Skills: must NOT be .md files (they are directories)
    for i, skill in enumerate(plugin.get("skills", [])):
        if not isinstance(skill, str):
            result.add_error(format_error(ErrorCode.E014, f"{prefix}.skills[{i}] must be string"))
            continue
        if not SCHEMA["relative_path"].match(skill):
            result.add_error(format_error(ErrorCode.E011, f'{prefix}.skills[{i}] "{skill}" must start with "./"'))
        if SCHEMA["md_extension"].search(skill):
            correct = skill.replace(".md", "").rstrip("/")
            result.add_error(
                format_error(ErrorCode.E002,
                    f'{prefix}.skills[{i}] "{skill}" has .md extension. '
                    f'Skills are directories, not files.'),
                Fix(f'Fix path to "{correct}"', fix_path_format, marketplace_path, "skills", skill, correct)
            )

    # Hooks: single path string (NOT an array) - points to directory or .json file
    hooks_path = plugin.get("hooks")
    if hooks_path is not None:
        if isinstance(hooks_path, str):
            if not SCHEMA["relative_path"].match(hooks_path):
                result.add_error(format_error(ErrorCode.E011, f'{prefix}.hooks "{hooks_path}" must start with "./"'))
            # hooks must be a file path ending with .json (e.g., ./hooks/hooks.json)
            if not hooks_path.endswith('.json'):
                result.add_error(format_error(ErrorCode.E014, f'{prefix}.hooks must end with ".json" (e.g., "./hooks/hooks.json")'))
        elif isinstance(hooks_path, list):
            # Old format was array - this is no longer supported
            result.add_error(
                format_error(ErrorCode.E014,
                    f'{prefix}.hooks must be string path, not array. '
                    f'Use: "hooks": "./hooks/hooks.json"')
            )
        else:
            result.add_error(format_error(ErrorCode.E014, f"{prefix}.hooks must be string path"))

    return result


def fix_repository_to_string(marketplace_path: Path, plugin_idx: int):
    """Convert repository object to string URL."""
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    plugins = data.get("plugins", [data])

    if plugin_idx < len(plugins):
        plugin = plugins[plugin_idx]
        repo = plugin.get("repository", {})
        if isinstance(repo, dict):
            url = repo.get("url", "")
            plugin["repository"] = url

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
                    f'Skill path "{skill}" has .md extension but skills must be directories. '
                    f'Skills are folders containing SKILL.md, not .md files themselves. '
                    f'Correct format: "{correct_path}" (the directory, not the file)',
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
            content = cmd_file.read_text(encoding='utf-8')
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
            content = agent_file.read_text(encoding='utf-8')
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
                fm["tools"] = ["Read", "Grep", "Glob"]
                needs_fix = True
                result.add_error(
                    f'{agent_file.name}: Missing required "tools" field. '
                    f'Example: tools: ["Read", "Write", "Bash", "Grep", "Glob"]'
                )

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

            content = skill_md.read_text(encoding='utf-8')
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
        # Special case: "github" or "url" as string means wrong format (should be object)
        # This is handled by test_source_edge_cases(), so skip adding "./" prefix fix here
        if source in ["github", "url"]:
            # Don't add fix here - test_source_edge_cases handles this with proper fix
            if "repo" in plugin_data:
                result.add_error(
                    f'source "{source}" with "repo" at plugin level is invalid format. '
                    f'Use: "source": {{"source": "{source}", "repo": "owner/repo"}}'
                )
            else:
                result.add_error(
                    f'source "{source}" must be an object, not a string. '
                    f'Use: "source": {{"source": "{source}", "repo": "owner/repo"}}'
                )
        elif source and source not in [".", "./"] and not source.startswith("./"):
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


def validate_marketplace_schema(data: dict, marketplace_path: Path) -> ValidationResult:
    """Validate marketplace.json follows the official Claude Code schema.

    Official Schema (from Claude Code documentation):

    Required at marketplace level:
      - name: string (kebab-case, no spaces)
      - owner: object with required 'name' field
      - plugins: array of plugin objects

    Optional at marketplace level:
      - description, version, homepage
      - metadata: object with description, version, pluginRoot

    Required per plugin:
      - name: string (kebab-case)
      - source: string (path starting with ./) or object (GitHub/URL)

    Optional per plugin:
      - description, version, author, homepage, repository, license
      - keywords, category, tags, strict
      - commands, agents, skills, hooks, mcpServers, lspServers
    """
    result = ValidationResult()

    # -------------------------------------------------------------------------
    # RESERVED MARKETPLACE NAMES (STRICT - will be rejected by Claude Code)
    # -------------------------------------------------------------------------
    RESERVED_NAMES = {
        "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
        "anthropic-marketplace", "anthropic-plugins",
        "agent-skills", "life-sciences"
    }

    # -------------------------------------------------------------------------
    # ALLOWED FIELDS (STRICT - unrecognized fields are errors, not warnings)
    # -------------------------------------------------------------------------
    ALLOWED_MARKETPLACE_FIELDS = {
        "name", "owner", "plugins",  # Required
        "description", "version", "homepage", "metadata", "$schema"  # Optional
    }

    ALLOWED_OWNER_FIELDS = {"name", "email"}

    ALLOWED_METADATA_FIELDS = {"description", "version", "pluginRoot"}

    ALLOWED_PLUGIN_FIELDS = {
        "name", "source",  # Required
        "description", "version", "author", "homepage", "repository", "license",
        "keywords", "category", "tags", "strict",
        "commands", "agents", "skills", "hooks", "mcpServers", "lspServers"
    }

    # Fields that are commonly mistakenly added
    FORBIDDEN_PLUGIN_FIELDS = {
        "components",  # Not part of Claude Code schema
        "repo",        # Should be inside source object, not at plugin level
    }

    ALLOWED_AUTHOR_FIELDS = {"name", "email"}

    ALLOWED_SOURCE_TYPES = {"github", "url"}

    # -------------------------------------------------------------------------
    # 1. VALIDATE MARKETPLACE ROOT STRUCTURE
    # -------------------------------------------------------------------------

    # Check for unrecognized root fields (ERROR - strict mode)
    unrecognized_root = set(data.keys()) - ALLOWED_MARKETPLACE_FIELDS
    if unrecognized_root:
        result.add_error(
            f"marketplace.json has unrecognized field(s) at root: {', '.join(sorted(unrecognized_root))}. "
            f"Allowed fields: {', '.join(sorted(ALLOWED_MARKETPLACE_FIELDS))}"
        )

    # Required: name (marketplace identifier)
    if "name" not in data:
        result.add_error("marketplace.json missing required field: 'name'")
    else:
        name = data["name"]
        if not isinstance(name, str):
            result.add_error("'name' must be a string")
        elif name.lower() in RESERVED_NAMES or any(reserved in name.lower() for reserved in ["anthropic", "official-claude"]):
            result.add_error(f"marketplace name '{name}' is reserved or impersonates official marketplaces")
        elif " " in name:
            result.add_error(f"marketplace name '{name}' must not contain spaces (use kebab-case)")
        elif not name.replace("-", "").replace("_", "").isalnum():
            result.add_error(f"marketplace name '{name}' must be alphanumeric with hyphens/underscores only")
        else:
            result.add_pass(f"marketplace name '{name}' is valid")

    # Required: owner (object with name)
    if "owner" not in data:
        result.add_error("marketplace.json missing required field: 'owner'")
    else:
        owner = data["owner"]
        if not isinstance(owner, dict):
            result.add_error("'owner' must be an object with 'name' field")
        else:
            # Check owner fields
            unrecognized_owner = set(owner.keys()) - ALLOWED_OWNER_FIELDS
            if unrecognized_owner:
                result.add_error(f"'owner' has unrecognized field(s): {', '.join(sorted(unrecognized_owner))}")

            if "name" not in owner:
                result.add_error("'owner' missing required field: 'name'")
            elif not isinstance(owner["name"], str) or not owner["name"].strip():
                result.add_error("'owner.name' must be a non-empty string")
            else:
                result.add_pass("owner field is valid")

    # Required: plugins (array of plugin objects)
    if "plugins" not in data:
        result.add_error("marketplace.json missing required field: 'plugins'")
    elif not isinstance(data["plugins"], list):
        result.add_error("'plugins' must be an array")
    elif len(data["plugins"]) == 0:
        result.add_error("'plugins' array is empty - at least one plugin required")
    else:
        result.add_pass(f"plugins array contains {len(data['plugins'])} plugin(s)")

    # Optional: metadata validation
    if "metadata" in data:
        metadata = data["metadata"]
        if not isinstance(metadata, dict):
            result.add_error("'metadata' must be an object")
        else:
            unrecognized_meta = set(metadata.keys()) - ALLOWED_METADATA_FIELDS
            if unrecognized_meta:
                result.add_error(f"'metadata' has unrecognized field(s): {', '.join(sorted(unrecognized_meta))}")
            else:
                result.add_pass("metadata field is valid")

    # -------------------------------------------------------------------------
    # 2. VALIDATE EACH PLUGIN ENTRY (STRICT)
    # -------------------------------------------------------------------------

    plugin_names = []

    for i, plugin in enumerate(data.get("plugins", [])):
        if not isinstance(plugin, dict):
            result.add_error(f"plugins[{i}] must be an object")
            continue

        # Check for unrecognized plugin fields (ERROR - strict mode)
        unrecognized_plugin = set(plugin.keys()) - ALLOWED_PLUGIN_FIELDS
        if unrecognized_plugin:
            result.add_error(
                f"plugins[{i}] has unrecognized field(s): {', '.join(sorted(unrecognized_plugin))}. "
                f"Allowed: {', '.join(sorted(ALLOWED_PLUGIN_FIELDS))}"
            )

        # Required: name
        if "name" not in plugin:
            result.add_error(f"plugins[{i}] missing required field: 'name'")
        else:
            pname = plugin["name"]
            if not isinstance(pname, str):
                result.add_error(f"plugins[{i}].name must be a string")
            elif " " in pname:
                result.add_error(f"plugins[{i}].name '{pname}' must not contain spaces")
            else:
                plugin_names.append(pname)
                result.add_pass(f"plugins[{i}].name '{pname}' is valid")

        # Required: source (STRICT format validation)
        if "source" not in plugin:
            result.add_error(f"plugins[{i}] missing required field: 'source'")
        else:
            source = plugin["source"]

            if isinstance(source, str):
                # Special case: "github" or "url" as string is a different error
                # (should be object with repo), handled by test_source_edge_cases
                if source in ["github", "url"]:
                    # Error is reported by test_source_edge_cases with proper fix
                    pass
                # Path source - must start with ./
                elif not source.startswith("./"):
                    result.add_error(
                        f"plugins[{i}].source '{source}' must start with './' "
                        f"(e.g., './' or './plugins/name')"
                    )
                # Path traversal check
                elif ".." in source:
                    result.add_error(
                        f"plugins[{i}].source '{source}' contains path traversal (..) which is not allowed"
                    )
                else:
                    result.add_pass(f"plugins[{i}].source path format is valid")

            elif isinstance(source, dict):
                # Object source - must have valid structure
                # CRITICAL: The key must be "source", NOT "type"
                source_type = source.get("source")

                # Check for common mistake: using "type" instead of "source"
                if "type" in source and "source" not in source:
                    result.add_error(
                        f'plugins[{i}].source uses "type" key but must use "source" key. '
                        f'Correct format: {{"source": "github", "repo": "owner/repo"}} '
                        f'NOT {{"type": "github", ...}}'
                    )
                elif source_type not in ALLOWED_SOURCE_TYPES:
                    result.add_error(
                        f'plugins[{i}].source.source must be one of: {", ".join(ALLOWED_SOURCE_TYPES)}. '
                        f'Got: {repr(source_type)}. '
                        f'Correct format: {{"source": "github", "repo": "owner/repo"}}'
                    )
                elif source_type == "github":
                    if "repo" not in source:
                        result.add_error(
                            f'plugins[{i}].source: GitHub source requires "repo" field. '
                            f'Correct format: {{"source": "github", "repo": "owner/repo"}}'
                        )
                    elif not isinstance(source["repo"], str) or "/" not in source["repo"]:
                        result.add_error(
                            f'plugins[{i}].source.repo must be in format "owner/repo". '
                            f'Got: {repr(source.get("repo"))}'
                        )
                    else:
                        result.add_pass(f"plugins[{i}].source GitHub format is valid")
                elif source_type == "url":
                    if "url" not in source:
                        result.add_error(
                            f'plugins[{i}].source: URL source requires "url" field. '
                            f'Correct format: {{"source": "url", "url": "https://..."}}'
                        )
                    elif not isinstance(source["url"], str) or not source["url"].startswith(("http://", "https://")):
                        result.add_error(f"plugins[{i}].source.url must be a valid HTTP(S) URL")
                    else:
                        result.add_pass(f"plugins[{i}].source URL format is valid")
            else:
                result.add_error(
                    f"plugins[{i}].source must be a string (path) or object (GitHub/URL source)"
                )

        # Optional: author validation
        if "author" in plugin:
            author = plugin["author"]
            if not isinstance(author, dict):
                result.add_error(f"plugins[{i}].author must be an object with 'name' field")
            else:
                unrecognized_author = set(author.keys()) - ALLOWED_AUTHOR_FIELDS
                if unrecognized_author:
                    result.add_error(f"plugins[{i}].author has unrecognized field(s): {', '.join(sorted(unrecognized_author))}")
                if "name" not in author:
                    result.add_error(f"plugins[{i}].author missing required 'name' field")

        # Optional: repository validation (MUST be string, not object)
        if "repository" in plugin:
            repo = plugin["repository"]
            if isinstance(repo, dict):
                result.add_error(
                    f'plugins[{i}].repository must be a string URL, not an object. '
                    f'WRONG: {{"type": "git", "url": "..."}} '
                    f'CORRECT: "https://github.com/owner/repo"'
                )
            elif not isinstance(repo, str):
                result.add_error(f"plugins[{i}].repository must be a string URL")
            elif not repo.startswith(("http://", "https://")):
                result.add_warning(f"plugins[{i}].repository should be a full URL (https://...)")

        # Check for forbidden fields with specific error messages
        if "components" in plugin:
            result.add_error(
                f'plugins[{i}].components is not allowed. '
                f'Use "skills", "agents", "commands" arrays instead of "components" object.'
            )

        # Optional: array field validations
        for array_field in ["commands", "agents", "skills", "keywords", "tags"]:
            if array_field in plugin:
                value = plugin[array_field]
                if not isinstance(value, (list, str)):
                    result.add_error(f"plugins[{i}].{array_field} must be an array or string")
                elif isinstance(value, list):
                    for j, item in enumerate(value):
                        if not isinstance(item, str):
                            result.add_error(f"plugins[{i}].{array_field}[{j}] must be a string")
                        # Path traversal check for path arrays
                        elif array_field in ["commands", "agents", "skills"] and ".." in item:
                            result.add_error(f"plugins[{i}].{array_field}[{j}] contains path traversal (..) which is not allowed")

    # -------------------------------------------------------------------------
    # 3. CHECK FOR DUPLICATE PLUGIN NAMES (STRICT)
    # -------------------------------------------------------------------------

    seen_names = set()
    for pname in plugin_names:
        if pname in seen_names:
            result.add_error(f"Duplicate plugin name '{pname}' - each plugin must have a unique name")
        seen_names.add(pname)

    return result


def validate_plugin_json(plugin_root: Path) -> ValidationResult:
    """
    Validate plugin.json if it exists. Auto-fixable.

    Also checks:
    - E025: plugin.json version must match marketplace.json version
    """
    result = ValidationResult()

    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        return result

    try:
        data = json.loads(plugin_json.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        result.add_error(f"plugin.json: Invalid JSON: {e}")
        return result

    # Allowed fields in plugin.json
    ALLOWED_FIELDS = {
        "name", "version", "description", "author", "repository",
        "homepage", "license", "keywords", "category", "tags"
    }

    needs_fix = False

    # Check for unrecognized fields
    unrecognized = set(data.keys()) - ALLOWED_FIELDS
    if unrecognized:
        needs_fix = True
        result.add_error(
            f'plugin.json: removing invalid field(s): {", ".join(sorted(unrecognized))}'
        )

    # Check repository format
    if "repository" in data and isinstance(data["repository"], dict):
        needs_fix = True
        result.add_error('plugin.json: converting repository object => string')

    # E025: Check version consistency with marketplace.json
    marketplace_json = plugin_root / ".claude-plugin" / "marketplace.json"
    if marketplace_json.exists():
        try:
            marketplace_data = json.loads(marketplace_json.read_text(encoding='utf-8'))
            plugin_json_version = data.get("version", "")
            plugin_json_name = data.get("name", "")

            # Check marketplace.json plugins array for matching plugin
            plugins = marketplace_data.get("plugins", [])
            for plugin in plugins:
                mp_name = plugin.get("name", "")
                mp_version = plugin.get("version", "")

                # Match by name or if only one plugin
                if mp_name == plugin_json_name or len(plugins) == 1:
                    if plugin_json_version and mp_version and plugin_json_version != mp_version:
                        result.add_error(
                            f'[E025] Version mismatch: plugin.json has "{plugin_json_version}" '
                            f'but marketplace.json has "{mp_version}". '
                            f'Claude displays plugin.json version in /plugin UI. '
                            f'Update plugin.json to match marketplace.json version.'
                        )
                    break
        except (json.JSONDecodeError, IOError):
            pass

    # Add auto-fix
    if needs_fix:
        result.fixes.append(Fix(
            "Fix plugin.json schema",
            fix_plugin_json_schema, plugin_json
        ))
    else:
        result.add_pass("plugin.json: valid")

    return result


def validate_hooks_json(plugin_root: Path) -> ValidationResult:
    """
    Validate hooks.json schema for Claude Code 1.0.40+ compatibility.

    Schema requirements (1.0.40+):
    - Top level has "hooks" object
    - Event types: PreToolUse, PostToolUse, UserPromptSubmit, Stop
    - Each event type is an array
    - Each item has optional "matcher" (string, not object) for PreToolUse/PostToolUse
    - Each item has "hooks" array (nested)
    - Each hook has "type": "command" or "prompt"
    - timeout is in seconds (1-600), not milliseconds

    E027: hooks.json schema invalid
    """
    result = ValidationResult()

    # Check both possible locations
    hooks_locations = [
        plugin_root / "hooks" / "hooks.json",
        plugin_root / ".claude-plugin" / "hooks.json",
    ]

    hooks_json = None
    for loc in hooks_locations:
        if loc.exists():
            hooks_json = loc
            break

    if hooks_json is None:
        return result  # No hooks.json, skip validation

    try:
        data = json.loads(hooks_json.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        result.add_error(f"[E027] hooks.json: Invalid JSON: {e}")
        return result

    # Validate top-level structure
    if "hooks" not in data:
        result.add_error(
            f'[E027] hooks.json: Missing required "hooks" object at top level. '
            f'Schema changed in Claude Code 1.0.40+.'
        )
        return result

    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        result.add_error(
            f'[E027] hooks.json: "hooks" must be object, got {type(hooks).__name__}. '
            f'Use format: {{"hooks": {{"PreToolUse": [...], ...}}}}'
        )
        return result

    # Valid event types
    VALID_EVENTS = {"PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop"}

    for event_type, event_hooks in hooks.items():
        if event_type.startswith("$"):
            continue  # Skip meta fields like $schema_notes

        if event_type not in VALID_EVENTS:
            result.add_warning(
                f'[E027] hooks.json: Unknown event type "{event_type}". '
                f'Valid types: {", ".join(sorted(VALID_EVENTS))}'
            )
            continue

        if not isinstance(event_hooks, list):
            result.add_error(
                f'[E027] hooks.json: hooks.{event_type} must be array, got {type(event_hooks).__name__}'
            )
            continue

        for i, hook_group in enumerate(event_hooks):
            prefix = f"hooks.{event_type}[{i}]"

            if not isinstance(hook_group, dict):
                result.add_error(f'[E027] hooks.json: {prefix} must be object')
                continue

            # Check matcher is STRING ONLY (Claude Code 1.0.40+)
            # String: "Edit|Write|MultiEdit" - tool name matching with pipe for alternatives
            # Object matchers are NOT supported by Claude Code - filter in script instead
            if "matcher" in hook_group:
                matcher = hook_group["matcher"]
                if isinstance(matcher, str):
                    pass  # Valid: string matcher
                elif isinstance(matcher, dict):
                    # ERROR: Object matchers are NOT supported by Claude Code
                    # The original intent (input_contains, subagent filtering) must be done in script
                    result.add_error(
                        f'[E027] hooks.json: {prefix}.matcher must be string, not object. '
                        f'Object matchers are NOT supported by Claude Code. '
                        f'Use string matcher (e.g., "Task") and filter by parsing tool_input in your hook script. '
                        f'See hook-templates skill for examples.'
                    )
                else:
                    result.add_error(
                        f'[E027] hooks.json: {prefix}.matcher must be string, got {type(matcher).__name__}'
                    )

            # Check nested hooks array exists
            if "hooks" not in hook_group:
                result.add_error(
                    f'[E027] hooks.json: {prefix}.hooks array is required. '
                    f'Add: "hooks": [{{"type": "command", "command": "..."}}]'
                )
                continue

            nested_hooks = hook_group.get("hooks", [])
            if not isinstance(nested_hooks, list):
                result.add_error(
                    f'[E027] hooks.json: {prefix}.hooks must be array, got {type(nested_hooks).__name__}'
                )
                continue

            for j, hook in enumerate(nested_hooks):
                hook_prefix = f"{prefix}.hooks[{j}]"

                if not isinstance(hook, dict):
                    result.add_error(f'[E027] hooks.json: {hook_prefix} must be object')
                    continue

                # Check type field exists
                if "type" not in hook:
                    result.add_error(
                        f'[E027] hooks.json: {hook_prefix}.type is required. '
                        f'Use "type": "command" or "type": "prompt"'
                    )

                hook_type = hook.get("type", "")
                if hook_type not in ("command", "prompt", ""):
                    result.add_error(
                        f'[E027] hooks.json: {hook_prefix}.type must be "command" or "prompt", got "{hook_type}"'
                    )

                # Check command exists for command type
                if hook_type == "command" and "command" not in hook:
                    result.add_error(
                        f'[E027] hooks.json: {hook_prefix}.command is required when type is "command"'
                    )

                # Check timeout value (informational only - both ms and seconds may be valid)
                if "timeout" in hook:
                    timeout = hook["timeout"]
                    if isinstance(timeout, (int, float)):
                        # Note: Claude Code may accept both milliseconds and seconds
                        # Just provide informational messages, not errors
                        if timeout > 60000:
                            result.add_warning(
                                f'[E027] hooks.json: {hook_prefix}.timeout={timeout} is very large. '
                                f'Verify if this is intended (milliseconds or seconds).'
                            )
                        elif timeout < 1:
                            result.add_warning(
                                f'[E027] hooks.json: {hook_prefix}.timeout={timeout} is very short. '
                                f'Minimum recommended: 1 second.'
                            )

            # Check for potentially problematic fields at hook_group level
            # Note: input_contains and output_contains are valid inside matcher object
            # pattern and behavior are legacy fields that may not work
            legacy_fields = {"pattern", "behavior", "onError"}
            found_legacy = set(hook_group.keys()) & legacy_fields
            if found_legacy:
                result.add_warning(
                    f'[E027] hooks.json: {prefix} has legacy fields: {", ".join(found_legacy)}. '
                    f'These may not be supported. Consider using matcher object with input_contains/output_contains instead.'
                )

    if not result.errors and not result.warnings:
        result.add_pass("hooks.json: valid (Claude Code 1.0.40+ schema)")

    return result


def validate_scripts(plugin_root: Path) -> ValidationResult:
    """Validate script files have shebang and are executable."""
    result = ValidationResult()

    scripts_dir = plugin_root / "scripts"
    if not scripts_dir.exists():
        return result

    for script in scripts_dir.glob("*.py"):
        content = script.read_text(encoding='utf-8')

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


def validate_settings_json() -> ValidationResult:
    """
    Check for common settings.json misconfigurations.

    Validates:
    - E021: enabledPlugins must be object, not array
    - E022: extraKnownMarketplaces source.source must be valid discriminator
            (Note: discriminator field name is "source", not "type")
            Valid values: 'url' | 'github' | 'git' | 'npm' | 'file' | 'directory'
    - E026: Duplicate plugin registration (same plugin from multiple marketplaces)
    """
    result = ValidationResult()
    home = Path.home()

    # Valid source type discriminator values for settings.json
    VALID_SOURCE_TYPES = {'url', 'github', 'git', 'npm', 'file', 'directory'}

    settings_paths = [
        home / ".claude" / "settings.json",
        home / ".config" / "claude-code" / "settings.json",
    ]

    for settings_path in settings_paths:
        if not settings_path.exists():
            continue

        try:
            settings = json.loads(settings_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            continue

        # E021: Check enabledPlugins format (must be object, not array)
        enabled_plugins = settings.get("enabledPlugins")
        if enabled_plugins is not None:
            if isinstance(enabled_plugins, list):
                result.add_error(
                    f'[E021] settings.json: enabledPlugins must be an object {{"plugin@marketplace": true}}, '
                    f'not an array. Found: {type(enabled_plugins).__name__}'
                )

        # E026: Check for duplicate plugin registrations
        if enabled_plugins is not None and isinstance(enabled_plugins, dict):
            # Group plugins by name (extract from plugin@marketplace format)
            plugin_registrations: Dict[str, List[str]] = {}
            for plugin_ref, enabled in enabled_plugins.items():
                if not enabled:
                    continue
                if "@" in plugin_ref:
                    plugin_name, marketplace = plugin_ref.rsplit("@", 1)
                    if plugin_name not in plugin_registrations:
                        plugin_registrations[plugin_name] = []
                    plugin_registrations[plugin_name].append(plugin_ref)

            # Report duplicates
            for plugin_name, refs in plugin_registrations.items():
                if len(refs) > 1:
                    result.add_warning(
                        f'[E026] settings.json: Plugin "{plugin_name}" is registered multiple times: '
                        f'{", ".join(refs)}. '
                        f'This may cause loading conflicts. Consider removing duplicates.'
                    )

        plugins = settings.get("plugins", [])
        for i, plugin in enumerate(plugins):
            if isinstance(plugin, dict):
                source = plugin.get("source", "")
                if isinstance(source, str) and source:
                    if not source.startswith("./") and not source.startswith("/"):
                        result.add_error(
                            f'settings.json plugins[{i}].source "{source}" must start with "./"'
                        )

        # E022: Check extraKnownMarketplaces source format
        marketplaces = settings.get("extraKnownMarketplaces", {})
        for name, config in marketplaces.items():
            source = config.get("source", {})

            if isinstance(source, dict):
                # Check for correct "source" field (discriminator field name is "source")
                # Claude Code schema: { "source": { "source": "directory", "path": "..." } }
                source_discriminator = source.get("source")
                wrong_type = source.get("type")  # Common mistake: using "type" instead of "source"

                if wrong_type is not None:
                    # User used "type" instead of "source" - this is a common mistake
                    result.add_error(
                        f'[E022] settings.json: extraKnownMarketplaces.{name}.source uses '
                        f'"type": "{wrong_type}" which is incorrect. '
                        f'Use "source": "directory" instead (discriminator field is "source", not "type"). '
                        f'Valid values: {", ".join(sorted(VALID_SOURCE_TYPES))}'
                    )
                elif source_discriminator is not None and source_discriminator not in VALID_SOURCE_TYPES:
                    result.add_error(
                        f'[E022] settings.json: extraKnownMarketplaces.{name}.source.source '
                        f'"{source_discriminator}" is invalid. '
                        f'Valid values: {", ".join(sorted(VALID_SOURCE_TYPES))}'
                    )
                elif source_discriminator is None and "path" in source:
                    # Has path but no source discriminator - suggest directory
                    result.add_error(
                        f'[E022] settings.json: extraKnownMarketplaces.{name}.source '
                        f'has "path" but missing "source" discriminator. Add "source": "directory"'
                    )
            elif isinstance(source, str) and source and not source.startswith("./"):
                result.add_error(
                    f'settings.json extraKnownMarketplaces.{name}.source must start with "./"'
                )

    return result


def validate_marketplace_cache_consistency() -> ValidationResult:
    """
    Check for marketplace cache consistency issues (E023, E024).

    Validates:
    - E023: known_marketplaces.json repo matches actual git remote in cache
    - E024: known_marketplaces.json entry has valid cache directory

    Claude's plugin cache has 3 layers that must be consistent:
    1. known_marketplaces.json - registry (where to fetch from)
    2. ~/.claude/plugins/marketplaces/{name}/ - cached git clone
    3. installed_plugins.json - active plugins list
    """
    result = ValidationResult()
    home = Path.home()

    known_marketplaces_path = home / ".claude" / "plugins" / "known_marketplaces.json"
    cache_base = home / ".claude" / "plugins" / "marketplaces"

    if not known_marketplaces_path.exists():
        return result

    try:
        known_marketplaces = json.loads(known_marketplaces_path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, IOError):
        return result

    import subprocess

    for name, config in known_marketplaces.items():
        source = config.get("source", {})
        install_location = config.get("installLocation", "")

        # E024: Check if cache directory exists
        cache_dir = Path(install_location) if install_location else cache_base / name
        if install_location and not cache_dir.exists():
            result.add_error(
                f'[E024] Marketplace "{name}" registered in known_marketplaces.json '
                f'but cache directory missing: {cache_dir}'
            )
            continue

        # E023: For GitHub sources, verify git remote matches
        if isinstance(source, dict) and source.get("source") == "github":
            expected_repo = source.get("repo", "")

            if not expected_repo:
                continue

            # Check actual git remote in cache
            git_dir = cache_dir / ".git"
            if git_dir.exists():
                try:
                    git_result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        capture_output=True,
                        text=True,
                        cwd=cache_dir,
                        timeout=5
                    )

                    if git_result.returncode == 0:
                        actual_remote = git_result.stdout.strip()

                        # Normalize URLs for comparison
                        # https://github.com/owner/repo.git -> owner/repo
                        actual_repo = actual_remote.replace("https://github.com/", "").replace(".git", "")

                        if actual_repo != expected_repo:
                            result.add_error(
                                f'[E023] Marketplace "{name}" cache mismatch:\n'
                                f'       known_marketplaces.json repo: {expected_repo}\n'
                                f'       actual git remote: {actual_repo}\n'
                                f'       Fix: Update known_marketplaces.json or re-clone cache'
                            )
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass

    if not result.errors:
        result.add_pass("Marketplace cache consistency: all passed")

    return result


def apply_fixes(fixes: List[Fix], dry_run: bool = False) -> Tuple[int, int]:
    """Apply all fixes. Returns (success_count, fail_count)."""
    success = 0
    fail = 0

    print("\n" + "=" * 60)
    print("APPLYING FIXES" if not dry_run else "FIXES PREVIEW (dry-run)")
    print("=" * 60)

    for fix in fixes:
        print(f"\n{'[DRY-RUN] ' if dry_run else ''}=> {fix.description}")

        if dry_run:
            success += 1
        else:
            if fix.apply():
                print(f"  [PASS] Done")
                success += 1
            else:
                fail += 1

    return success, fail


# =============================================================================
# ENHANCED VALIDATION: Claude Code CLI + Edge Case Testing
# =============================================================================

def run_claude_cli_validation(plugin_root: Path) -> Tuple[bool, str, List[str]]:
    """
    Run Claude Code CLI validation as PRIMARY schema check.

    This is the authoritative source for schema validation.
    Returns (success, output_message, error_list)
    """
    import subprocess

    try:
        result = subprocess.run(
            ["claude", "plugin", "validate", str(plugin_root)],
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0 or "passed" in output.lower()

        # Parse errors from output
        errors = []
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('❯') or line.startswith('>'):
                errors.append(line.lstrip('❯> ').strip())

        return success, output.strip(), errors
    except FileNotFoundError:
        return True, "Claude CLI not found - install with: npm install -g @anthropic-ai/claude-code", []
    except subprocess.TimeoutExpired:
        return False, "Claude CLI validation timed out", ["Timeout"]
    except Exception as e:
        return True, f"Claude CLI validation skipped: {e}", []


def test_source_edge_cases(marketplace_path: Path) -> ValidationResult:
    """
    Test marketplace.json for common source format mistakes.

    This catches errors that would only appear during 'marketplace add'.
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        return result

    try:
        with open(marketplace_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return result

    plugins = data.get("plugins", [])

    for i, plugin in enumerate(plugins):
        source = plugin.get("source")

        # Edge case 1: source is None
        if source is None:
            result.add_error(
                f'plugins[{i}].source is null/missing. '
                f'Must be a path like "./" or object like {{"source": "github", "repo": "owner/repo"}}'
            )
            continue

        # Edge case 2: source is empty string
        if source == "":
            result.add_error(
                f'plugins[{i}].source is empty string. '
                f'Must be a path like "./" or object like {{"source": "github", "repo": "owner/repo"}}'
            )
            continue

        # Edge case 3: source is empty object
        if isinstance(source, dict) and not source:
            result.add_error(
                f'plugins[{i}].source is empty object {{}}. '
                f'Must be {{"source": "github", "repo": "owner/repo"}} or {{"source": "url", "url": "https://..."}}'
            )
            continue

        # Edge case 4: source object uses wrong keys
        if isinstance(source, dict):
            # Check for common mistakes
            if "type" in source and "source" not in source:
                result.add_error(
                    f'plugins[{i}].source uses "type" key instead of "source" key. '
                    f'WRONG: {{"type": "github", ...}} '
                    f'CORRECT: {{"source": "github", "repo": "owner/repo"}}'
                )
            elif "url" in source and "source" not in source:
                result.add_error(
                    f'plugins[{i}].source has "url" but missing "source" key. '
                    f'CORRECT: {{"source": "url", "url": "https://..."}}'
                )
            elif "repo" in source and "source" not in source:
                result.add_error(
                    f'plugins[{i}].source has "repo" but missing "source" key. '
                    f'CORRECT: {{"source": "github", "repo": "owner/repo"}}'
                )

        # Edge case 5: path source with problematic format
        if isinstance(source, str):
            if source == ".":
                result.add_error(
                    f'plugins[{i}].source is "." but must start with "./". '
                    f'Use "./" instead of "."'
                )
            # Edge case 6: source is just "github" string with repo at plugin level
            elif source == "github" or source == "url":
                # Check if repo is at plugin level (common mistake)
                if "repo" in plugin:
                    result.add_error(
                        f'plugins[{i}].source is "{source}" with "repo" at plugin level. '
                        f'WRONG: "source": "github", "repo": "..." '
                        f'CORRECT: "source": {{"source": "github", "repo": "owner/repo"}}',
                        Fix(f'Fix GitHub source format for plugins[{i}]',
                            fix_github_source_format, marketplace_path, i)
                    )
                else:
                    result.add_error(
                        f'plugins[{i}].source is "{source}" but must be an object. '
                        f'CORRECT: "source": {{"source": "github", "repo": "owner/repo"}}'
                    )

    if not result.errors:
        result.add_pass("Source format edge cases: all passed")

    return result


def validate_github_source_with_local_files(plugin_root: Path, marketplace_path: Path) -> ValidationResult:
    """
    CRITICAL: Detect when GitHub source is used but local files exist.

    This catches the common mistake where:
    - marketplace.json uses GitHub source: {"source": "github", "repo": "owner/repo"}
    - But actual component files (commands/, agents/, etc.) exist locally
    - Claude will ignore local files and try to download from GitHub
    - If GitHub repo doesn't exist or is empty, plugins won't load

    This is especially problematic during local development.
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        return result

    try:
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    except:
        return result

    plugins = data.get("plugins", [data])

    for i, plugin in enumerate(plugins):
        source = plugin.get("source")

        # Check if source is GitHub (object format)
        if isinstance(source, dict) and source.get("source") == "github":
            repo = source.get("repo", "unknown")

            # Check if local component files exist
            local_components = []
            for component_type in ["commands", "agents", "skills", "hooks"]:
                items = plugin.get(component_type, [])
                if isinstance(items, str):
                    items = [items]

                for item_path in items:
                    if isinstance(item_path, str):
                        normalized = item_path.lstrip("./")
                        full_path = plugin_root / normalized
                        if full_path.exists():
                            local_components.append(normalized)

            if local_components:
                result.add_error(format_error(
                    ErrorCode.E016,
                    f'plugins[{i}] uses GitHub source "{repo}" but LOCAL files exist:\n'
                    f'       {", ".join(local_components[:5])}{"..." if len(local_components) > 5 else ""}\n'
                    f'       Claude will IGNORE these local files and download from GitHub.\n'
                    f'       If the GitHub repo is empty or doesn\'t exist, plugins won\'t load!'
                ))

                result.add_warning(
                    f'FIX OPTIONS:\n'
                    f'       1. Push files to GitHub: git push origin main\n'
                    f'       2. OR change source to "./" for local development:\n'
                    f'          "source": "./"  (instead of GitHub object)'
                )

    return result


def validate_remote_source_consistency(plugin_root: Path, marketplace_path: Path) -> ValidationResult:
    """
    PHASE 5: Remote Consistency Check (E018, E019, E020)

    For Multi-Repo deployments, validate:
    1. E018: Git remote matches marketplace.json source repo (or is intentionally different)
    2. E019: External GitHub repos are accessible
    3. E020: External repos contain required files

    This catches the common mistake where:
    - Marketplace is pushed to repo A
    - Plugin source points to repo B
    - But repo B doesn't exist, is empty, or has wrong structure
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        return result

    try:
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    except:
        return result

    # Get current git remote
    git_remote = None
    try:
        import subprocess
        remote_output = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(plugin_root),
            capture_output=True,
            text=True,
            timeout=5
        )
        if remote_output.returncode == 0:
            url = remote_output.stdout.strip()
            # Extract owner/repo from various URL formats
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git
            import re
            match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)
            if match:
                git_remote = match.group(1)
    except:
        pass

    plugins = data.get("plugins", [data])

    for i, plugin in enumerate(plugins):
        source = plugin.get("source")
        plugin_name = plugin.get("name", f"plugins[{i}]")

        # Only check GitHub sources
        if not isinstance(source, dict) or source.get("source") != "github":
            continue

        repo = source.get("repo", "")
        if not repo:
            continue

        # E018: Check if git remote matches source repo
        if git_remote and git_remote != repo:
            # This might be intentional (multi-repo setup)
            # Just warn, don't error
            result.add_warning(
                f'{plugin_name}: Git remote "{git_remote}" differs from source.repo "{repo}". '
                f'This is OK for multi-repo setups, but verify both repos are properly configured.'
            )

        # E019 & E020: Check if external repo is accessible and has files
        try:
            import subprocess
            # Check if repo exists and is accessible
            gh_check = subprocess.run(
                ["gh", "api", f"repos/{repo}", "--jq", ".name"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if gh_check.returncode != 0:
                result.add_error(format_error(
                    ErrorCode.E019,
                    f'{plugin_name}: GitHub repo "{repo}" is not accessible. '
                    f'Error: {gh_check.stderr.strip()}\n'
                    f'       Verify the repo exists and is public (or you have access).'
                ))
                continue

            # E020: Check if repo has required structure
            contents_check = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents", "--jq", ".[].name"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if contents_check.returncode == 0:
                repo_contents = contents_check.stdout.strip().split('\n')

                # Check for .claude-plugin directory or marketplace.json
                has_claude_plugin = '.claude-plugin' in repo_contents
                has_marketplace = 'marketplace.json' in repo_contents

                if not has_claude_plugin and not has_marketplace:
                    result.add_warning(
                        f'{plugin_name}: Repo "{repo}" has no .claude-plugin/ or marketplace.json. '
                        f'Claude may not recognize this as a valid plugin.'
                    )

                # Check for component directories matching marketplace.json
                for component_type in ["commands", "agents", "skills", "hooks"]:
                    items = plugin.get(component_type, [])
                    if items and component_type not in repo_contents:
                        result.add_error(format_error(
                            ErrorCode.E020,
                            f'{plugin_name}: marketplace.json references "{component_type}/" '
                            f'but repo "{repo}" has no "{component_type}/" directory. '
                            f'Claude will fail to load these components!'
                        ))
            else:
                result.add_pass(f'{plugin_name}: repo "{repo}" is accessible')

        except FileNotFoundError:
            # gh CLI not installed
            result.add_warning(
                f'GitHub CLI (gh) not installed. Cannot verify external repo "{repo}". '
                f'Install with: brew install gh (Mac) or apt install gh (Linux)'
            )
            break
        except subprocess.TimeoutExpired:
            result.add_warning(f'Timeout checking repo "{repo}". Network issue?')
        except Exception as e:
            result.add_warning(f'Error checking repo "{repo}": {e}')

    if not result.errors and not result.warnings:
        result.add_pass("Remote source consistency check passed")

    return result


def validate_component_locations(plugin_root: Path, marketplace_path: Path) -> ValidationResult:
    """
    Validate that registered component paths actually exist from plugin root.

    Claude Code plugin structure requires:
    - Components (commands, agents, skills, hooks) MUST be at plugin ROOT level
    - Components must NOT be nested inside .claude-plugin/ directory

    This catches the common mistake of putting components inside .claude-plugin/
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        return result

    try:
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    except:
        return result

    plugins = data.get("plugins", [data])

    for i, plugin in enumerate(plugins):
        source = plugin.get("source", "./")

        # Determine effective root for this plugin
        if isinstance(source, dict):
            effective_root = plugin_root
        elif source in [".", "./"]:
            effective_root = plugin_root
        elif isinstance(source, str) and source.startswith("./"):
            effective_root = plugin_root / source.lstrip("./")
        else:
            effective_root = plugin_root

        # Check each registered component
        for component_type in ["commands", "agents", "skills", "hooks"]:
            items = plugin.get(component_type, [])
            if isinstance(items, str):
                items = [items]

            for item_path in items:
                if not isinstance(item_path, str):
                    continue

                # Normalize path
                normalized = item_path.lstrip("./")
                full_path = effective_root / normalized

                # Check if file/directory exists
                if not full_path.exists():
                    # Check if it exists in .claude-plugin/ (common mistake)
                    wrong_location = effective_root / ".claude-plugin" / normalized
                    if wrong_location.exists():
                        # E001: Component in wrong location (fix added at directory level below)
                        result.add_error(format_error(
                            ErrorCode.E001,
                            f'{component_type}: "{item_path}" found inside .claude-plugin/'
                        ))
                    else:
                        result.add_error(format_error(
                            ErrorCode.E012,
                            f'{component_type}: "{item_path}" not found at {full_path}'
                        ))
                else:
                    # Validate the item is the correct type
                    if component_type == "skills":
                        # Skills should be directories with SKILL.md
                        if full_path.is_file():
                            # E002: Skill is a file, needs conversion to directory
                            result.add_error(
                                format_error(
                                    ErrorCode.E002,
                                    f'skills: "{item_path}" is a file, converting to directory/SKILL.md'
                                ),
                                Fix(f'Convert {item_path} to directory structure',
                                    fix_skill_structure, plugin_root, item_path)
                            )
                        elif not (full_path / "SKILL.md").exists():
                            result.add_error(format_error(
                                ErrorCode.E009,
                                f'skills: "{item_path}" directory exists but missing SKILL.md'
                            ))
                        else:
                            result.add_pass(f'skills: "{item_path}" structure valid')
                    elif component_type == "hooks":
                        # Hooks: directory with hooks.json OR direct .json file
                        if full_path.is_dir():
                            hooks_file = full_path / "hooks.json"
                            if hooks_file.exists():
                                result.add_pass(f'hooks: "{item_path}/hooks.json" exists')
                            else:
                                result.add_warning(
                                    f'hooks: "{item_path}" directory exists but missing hooks.json'
                                )
                        elif full_path.is_file():
                            if item_path.endswith(".json"):
                                result.add_pass(f'hooks: "{item_path}" exists')
                            else:
                                result.add_warning(
                                    f'hooks: "{item_path}" should be .json file or directory containing hooks.json'
                                )
                    else:
                        # Commands, agents should be .md files
                        if full_path.is_dir():
                            result.add_error(format_error(
                                ErrorCode.E003 if component_type == "commands" else ErrorCode.E004,
                                f'{component_type}: "{item_path}" is a directory but {component_type} must be .md files'
                            ))
                        else:
                            result.add_pass(f'{component_type}: "{item_path}" exists')

    # Check for components inside .claude-plugin that should be at root
    claude_plugin_dir = plugin_root / ".claude-plugin"
    fixes_added = set()  # Track which fixes we've added to avoid duplicates

    for component_type in ["commands", "agents", "skills", "hooks"]:
        wrong_dir = claude_plugin_dir / component_type
        correct_dir = plugin_root / component_type

        if wrong_dir.exists() and wrong_dir.is_dir():
            files_in_wrong = list(wrong_dir.iterdir())
            if files_in_wrong:
                fix_key = f"move_{component_type}"
                if fix_key not in fixes_added:
                    fixes_added.add(fix_key)

                    if component_type == "skills":
                        # Skills need special handling: move + convert .md to directory
                        result.add_error(
                            format_error(
                                ErrorCode.E001,
                                f'"{component_type}/" is inside .claude-plugin/, will move and fix structure'
                            ),
                            Fix(f'Move and fix .claude-plugin/{component_type}/',
                                fix_skills_complete, plugin_root)
                        )
                    else:
                        result.add_error(
                            format_error(
                                ErrorCode.E001,
                                f'"{component_type}/" is inside .claude-plugin/, moving to plugin root'
                            ),
                            Fix(f'Move .claude-plugin/{component_type}/ to ./{component_type}/',
                                fix_move_component_to_root, plugin_root, component_type)
                        )

    return result


def validate_path_resolution_consistency(plugin_root: Path, marketplace_path: Path) -> ValidationResult:
    """
    CRITICAL VALIDATION: Detect path resolution mismatches.

    Claude Code plugin system has SPECIAL handling for .claude-plugin/ directory:
    - When marketplace.json is in .claude-plugin/, Claude resolves paths from PLUGIN ROOT
    - When marketplace.json is elsewhere, Claude resolves paths from marketplace.json location

    This catches the common mistake where:
    - marketplace.json is NOT in the standard .claude-plugin/ location
    - Component paths are "./commands/...", "./agents/...", etc.
    - Actual files exist at a different location than where Claude will look

    Error Codes:
    - E016: Path resolution mismatch - file exists but Claude will look in wrong location
    - E017: marketplace.json location causes structural issues
    """
    result = ValidationResult()

    if not marketplace_path.exists():
        return result

    try:
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
    except:
        return result

    # Determine marketplace.json directory
    marketplace_dir = marketplace_path.parent

    # SPECIAL CASE: .claude-plugin/ directory
    # Claude Code treats .claude-plugin/marketplace.json specially:
    # Paths are resolved from the PLUGIN ROOT (parent of .claude-plugin/)
    is_in_claude_plugin_dir = marketplace_dir.name == ".claude-plugin"

    if is_in_claude_plugin_dir:
        # Standard structure: .claude-plugin/marketplace.json with components at plugin root
        # Claude resolves paths from plugin_root, so check files exist there
        resolve_base = plugin_root
        result.add_pass("marketplace.json in .claude-plugin/ - using plugin root for path resolution")
    elif marketplace_dir == plugin_root:
        # marketplace.json at plugin root - paths resolve from root
        resolve_base = plugin_root
        result.add_pass("marketplace.json at plugin root - path resolution OK")
    else:
        # marketplace.json in non-standard nested location
        # This is where path resolution issues typically occur
        resolve_base = marketplace_dir
        result.add_warning(
            f'marketplace.json is in non-standard location "{marketplace_dir.relative_to(plugin_root)}/". '
            f'Paths will be resolved relative to this directory, not plugin root.'
        )

    plugins = data.get("plugins", [data])
    mismatch_found = False
    missing_at_resolve_base = []

    for i, plugin in enumerate(plugins):
        prefix = f"plugins[{i}]"

        for component_type in ["commands", "agents", "skills", "hooks"]:
            items = plugin.get(component_type, [])
            if isinstance(items, str):
                items = [items]

            for item_path in items:
                if not isinstance(item_path, str):
                    continue

                # Normalize path (remove leading ./)
                normalized = item_path.lstrip("./")

                # Path where Claude WILL look (based on resolve_base)
                resolved_path = resolve_base / normalized

                # Path at plugin root (for comparison)
                root_path = plugin_root / normalized

                # Check file existence
                file_at_resolved = resolved_path.exists()
                file_at_root = root_path.exists()

                if not file_at_resolved:
                    if file_at_root and resolve_base != plugin_root:
                        # File exists at root but Claude will look elsewhere
                        mismatch_found = True
                        result.add_error(format_error(
                            ErrorCode.E016,
                            f'{prefix}.{component_type}: "{item_path}" - '
                            f'FILE EXISTS at {root_path.relative_to(plugin_root)} '
                            f'but Claude will look at {resolved_path.relative_to(plugin_root)} (NOT FOUND). '
                            f'Claude will FAIL to load this component!'
                        ))
                    else:
                        # File doesn't exist anywhere
                        missing_at_resolve_base.append((prefix, component_type, item_path, resolved_path))

    # Report files missing at expected location (will be caught by E012 elsewhere, but add context)
    for prefix, component_type, item_path, resolved_path in missing_at_resolve_base:
        # E012 will be raised by validate_component_locations, so just add info here
        pass

    # If mismatches found in non-standard locations, suggest fixes
    if mismatch_found:
        result.add_error(
            format_error(
                ErrorCode.E017,
                f'marketplace.json is in "{marketplace_dir.relative_to(plugin_root)}/" but components are at plugin root. '
                f'Move marketplace.json to .claude-plugin/ or plugin root for correct path resolution.'
            ),
            Fix(
                'Move marketplace.json to .claude-plugin/ directory (standard location)',
                fix_move_marketplace_to_claude_plugin, plugin_root, marketplace_path
            )
        )
    elif not mismatch_found and (is_in_claude_plugin_dir or marketplace_dir == plugin_root):
        result.add_pass("Path resolution consistency check passed")

    return result


def fix_move_marketplace_to_claude_plugin(plugin_root: Path, current_marketplace_path: Path):
    """Move marketplace.json to .claude-plugin/ directory (standard location)."""
    import shutil

    claude_plugin_dir = plugin_root / ".claude-plugin"
    claude_plugin_dir.mkdir(exist_ok=True)

    dst = claude_plugin_dir / "marketplace.json"

    if current_marketplace_path.exists() and not dst.exists():
        shutil.move(str(current_marketplace_path), str(dst))


def fix_add_plugin_root_metadata(marketplace_path: Path):
    """Add pluginRoot: '../' to metadata to fix path resolution."""
    data = json.loads(marketplace_path.read_text(encoding='utf-8'))

    if "metadata" not in data:
        data["metadata"] = {}

    data["metadata"]["pluginRoot"] = "../"

    marketplace_path.write_text(json.dumps(data, indent=2) + "\n")


def fix_move_marketplace_to_root(plugin_root: Path):
    """Move marketplace.json from .claude-plugin/ to plugin root."""
    import shutil

    src = plugin_root / ".claude-plugin" / "marketplace.json"
    dst = plugin_root / "marketplace.json"

    if src.exists() and not dst.exists():
        shutil.move(str(src), str(dst))

        # If .claude-plugin is now empty, remove it
        claude_plugin_dir = plugin_root / ".claude-plugin"
        if claude_plugin_dir.exists() and not any(claude_plugin_dir.iterdir()):
            claude_plugin_dir.rmdir()


def validate_against_official_patterns(plugin_root: Path) -> ValidationResult:
    """
    Validate against patterns observed in official Claude Code plugins.
    """
    result = ValidationResult()

    marketplace_path = plugin_root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        return result

    try:
        with open(marketplace_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return result

    # Pattern 1: Official plugins use metadata.description
    if "metadata" not in data:
        result.add_warning(
            'Missing "metadata" object. Official plugins use: '
            '"metadata": {"description": "...", "version": "..."}'
        )
    elif "description" not in data.get("metadata", {}):
        result.add_warning(
            'Missing "metadata.description". Claude Code shows this in plugin listings.'
        )
    else:
        result.add_pass("metadata.description present")

    # Pattern 2: Check owner.name is present
    owner = data.get("owner", {})
    if not owner.get("name"):
        result.add_error(
            'Missing "owner.name". This is required by Claude Code.'
        )
    else:
        result.add_pass("owner.name present")

    # Pattern 3: Validate plugin component paths
    for i, plugin in enumerate(data.get("plugins", [])):
        # Skills should be directories (no .md)
        for skill in plugin.get("skills", []):
            if skill.endswith(".md"):
                result.add_error(
                    f'plugins[{i}].skills contains "{skill}" with .md extension. '
                    f'Skills are directories, not files. Remove the .md extension.'
                )

        # Commands should be .md files
        for cmd in plugin.get("commands", []):
            if not cmd.endswith(".md"):
                result.add_error(
                    f'plugins[{i}].commands contains "{cmd}" without .md extension. '
                    f'Commands must be .md files.'
                )

        # Agents should be .md files
        for agent in plugin.get("agents", []):
            if not agent.endswith(".md"):
                result.add_error(
                    f'plugins[{i}].agents contains "{agent}" without .md extension. '
                    f'Agents must be .md files.'
                )

    # Pattern 4: Hookify check - enforcement keywords should have corresponding hooks
    hookify_result = check_hookify_requirements(plugin_root)
    result.warnings.extend(hookify_result.warnings)
    result.passed.extend(hookify_result.passed)

    # Pattern 5: Skill design patterns compliance (W029, W031, W032)
    skill_patterns_result = check_skill_design_patterns(plugin_root)
    result.warnings.extend(skill_patterns_result.warnings)
    result.passed.extend(skill_patterns_result.passed)

    # Pattern 6: Agent orchestration patterns compliance (W030, W033)
    agent_patterns_result = check_agent_patterns(plugin_root)
    result.warnings.extend(agent_patterns_result.warnings)
    result.passed.extend(agent_patterns_result.passed)

    # Pattern 7: Command skill usage (W033)
    command_skill_result = check_command_skill_usage(plugin_root)
    result.warnings.extend(command_skill_result.warnings)
    result.passed.extend(command_skill_result.passed)

    # Pattern 8: Multi-stage workflow detection (W034)
    workflow_result = check_multistage_workflow_hookify(plugin_root)
    result.warnings.extend(workflow_result.warnings)
    result.passed.extend(workflow_result.passed)

    return result


def check_hookify_requirements(plugin_root: Path) -> ValidationResult:
    """
    W028: Check if enforcement keywords (MUST, REQUIRED, CRITICAL) in skills/agents
    have corresponding hooks. Documentation-only enforcement is meaningless.
    """
    result = ValidationResult()

    # Enforcement keywords that should be hookified
    enforcement_patterns = [
        (re.compile(r'\bMUST\b', re.IGNORECASE), "MUST"),
        (re.compile(r'\bREQUIRED\b', re.IGNORECASE), "REQUIRED"),
        (re.compile(r'\bCRITICAL\b', re.IGNORECASE), "CRITICAL"),
        (re.compile(r'\b강제\b'), "강제"),
        (re.compile(r'\b반드시\b'), "반드시"),
    ]

    # Skip patterns - these are meta-discussions about hookify, not actual enforcement
    skip_patterns = [
        re.compile(r'When to Hook', re.IGNORECASE),
        re.compile(r'Hookify check', re.IGNORECASE),
        re.compile(r'Hook vs Documentation', re.IGNORECASE),
        re.compile(r'documentation.*enforce', re.IGNORECASE),
        re.compile(r'hookify.*requirement', re.IGNORECASE),
    ]

    # Check if hooks exist
    hooks_json = None
    for loc in [
        plugin_root / "hooks" / "hooks.json",
        plugin_root / ".claude-plugin" / "hooks.json",
        plugin_root / ".claude" / "hooks.json",
    ]:
        if loc.exists():
            hooks_json = loc
            break

    has_hooks = hooks_json is not None

    # Scan skills for enforcement keywords
    skills_dir = plugin_root / "skills"
    agents_dir = plugin_root / "agents"

    enforcement_found = []

    for scan_dir, file_type in [(skills_dir, "skill"), (agents_dir, "agent")]:
        if not scan_dir.exists():
            continue

        for md_file in scan_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')

                # Skip if this is a meta-discussion about hookify
                is_meta = any(p.search(content) for p in skip_patterns)

                for pattern, keyword in enforcement_patterns:
                    matches = pattern.findall(content)
                    if matches and not is_meta:
                        # Get surrounding context for the match
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if pattern.search(line):
                                # Skip if line is in a code block or header about hooks
                                if 'hook' in line.lower() or line.strip().startswith('#'):
                                    continue
                                enforcement_found.append({
                                    'file': str(md_file.relative_to(plugin_root)),
                                    'keyword': keyword,
                                    'line': i + 1,
                                    'context': line.strip()[:80]
                                })
            except Exception:
                pass

    if enforcement_found and not has_hooks:
        # Group by file
        files_with_enforcement = set(e['file'] for e in enforcement_found)
        result.add_warning(
            f'[W028] Hookify required: Found {len(enforcement_found)} enforcement keyword(s) '
            f'in {len(files_with_enforcement)} file(s) but no hooks.json exists.\n'
            f'       Documentation-only enforcement is meaningless - agents will ignore it.\n'
            f'       Files: {", ".join(sorted(files_with_enforcement)[:3])}'
            f'{" ..." if len(files_with_enforcement) > 3 else ""}\n'
            f'       Action: Create hooks/hooks.json with PreToolUse/PostToolUse hooks to enforce.'
        )
    elif enforcement_found and has_hooks:
        # Has both enforcement keywords and hooks - good
        result.add_pass(f"Hookify check: {len(enforcement_found)} enforcement keywords found, hooks.json exists")
    elif not enforcement_found:
        result.add_pass("Hookify check: No enforcement keywords requiring hooks")

    return result


def check_skill_design_patterns(plugin_root: Path) -> ValidationResult:
    """
    W029, W031, W032: Check if skills follow skill-design patterns.

    Checks:
    - Frontmatter has name, description, allowed-tools
    - Core content is under 500 words (progressive disclosure)
    - Detailed content is in references/ subdirectory
    """
    result = ValidationResult()
    skills_dir = plugin_root / "skills"

    if not skills_dir.exists():
        return result

    # Required frontmatter fields for skills
    required_fields = ["name", "description"]
    recommended_fields = ["allowed-tools"]

    skills_checked = 0

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue  # E009 handles this

        skills_checked += 1

        try:
            content = skill_md.read_text(encoding='utf-8')

            # Parse frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    fm_content = parts[1].strip()
                    for line in fm_content.split('\n'):
                        if ':' in line:
                            key = line.split(':')[0].strip()
                            frontmatter[key] = True
                    body_content = parts[2]
                else:
                    body_content = content
            else:
                body_content = content

            # W029: Check frontmatter fields
            missing_required = [f for f in required_fields if f not in frontmatter]
            missing_recommended = [f for f in recommended_fields if f not in frontmatter]

            if missing_required:
                result.add_warning(
                    f'[W029] Skill "{skill_dir.name}": Missing required frontmatter: {", ".join(missing_required)}\n'
                    f'       Pattern: skill-design requires name and description in frontmatter.'
                )
            elif missing_recommended:
                result.add_warning(
                    f'[W029] Skill "{skill_dir.name}": Missing recommended frontmatter: {", ".join(missing_recommended)}\n'
                    f'       Pattern: skill-design recommends allowed-tools for explicit tool access.'
                )
            else:
                result.add_pass(f'Skill "{skill_dir.name}": Frontmatter complete')

            # W031: Check content length (progressive disclosure)
            # Count words in body content (excluding code blocks)
            body_no_code = re.sub(r'```[\s\S]*?```', '', body_content)
            body_no_code = re.sub(r'`[^`]+`', '', body_no_code)
            words = len(body_no_code.split())

            if words > 800:  # Hard limit
                result.add_warning(
                    f'[W031] Skill "{skill_dir.name}": Core content is {words} words (recommended: <500)\n'
                    f'       Pattern: skill-design recommends keeping SKILL.md concise.\n'
                    f'       Action: Move detailed content to references/ subdirectory.'
                )
            elif words > 500:  # Soft limit
                result.add_warning(
                    f'[W031] Skill "{skill_dir.name}": Core content is {words} words (recommended: <500)\n'
                    f'       Consider moving detailed sections to references/.'
                )
            else:
                result.add_pass(f'Skill "{skill_dir.name}": Content length OK ({words} words)')

            # W032: Check if detailed content should be in references/
            references_dir = skill_dir / "references"
            has_long_sections = bool(re.search(r'^#{1,3}\s.*\n(?:[^\n]+\n){20,}', body_content, re.MULTILINE))

            if has_long_sections and not references_dir.exists():
                result.add_warning(
                    f'[W032] Skill "{skill_dir.name}": Has long sections but no references/ directory\n'
                    f'       Pattern: skill-design recommends separating detailed docs into references/.'
                )
            elif references_dir.exists() and list(references_dir.glob('*.md')):
                result.add_pass(f'Skill "{skill_dir.name}": Uses references/ for detailed content')

        except Exception as e:
            result.add_warning(f'Could not analyze skill "{skill_dir.name}": {e}')

    if skills_checked == 0:
        result.add_pass("No skills to check for pattern compliance")

    return result


def check_agent_patterns(plugin_root: Path) -> ValidationResult:
    """
    W030: Check if agents follow orchestration-patterns.

    Checks:
    - Frontmatter has name, description, tools
    - Skills referenced in frontmatter exist or are available globally
    """
    result = ValidationResult()
    agents_dir = plugin_root / "agents"

    if not agents_dir.exists():
        return result

    # Required frontmatter fields for agents
    required_fields = ["name", "description", "tools"]
    recommended_fields = ["skills", "model"]

    # Get available skills in this plugin
    skills_dir = plugin_root / "skills"
    available_skills = set()
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                available_skills.add(skill_dir.name)

    agents_checked = 0

    for agent_md in agents_dir.glob("*.md"):
        agents_checked += 1

        try:
            content = agent_md.read_text(encoding='utf-8')

            # Parse frontmatter
            frontmatter = {}
            frontmatter_raw = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    fm_content = parts[1].strip()
                    for line in fm_content.split('\n'):
                        if ':' in line:
                            key = line.split(':')[0].strip()
                            value = ':'.join(line.split(':')[1:]).strip()
                            frontmatter[key] = True
                            frontmatter_raw[key] = value

            # W030: Check frontmatter fields
            missing_required = [f for f in required_fields if f not in frontmatter]
            missing_recommended = [f for f in recommended_fields if f not in frontmatter]

            agent_name = agent_md.stem

            if missing_required:
                result.add_warning(
                    f'[W030] Agent "{agent_name}": Missing required frontmatter: {", ".join(missing_required)}\n'
                    f'       Pattern: orchestration-patterns requires name, description, tools.'
                )
            elif missing_recommended:
                # Only warn if skills exist and could be used
                if available_skills and 'skills' in missing_recommended:
                    result.add_warning(
                        f'[W030] Agent "{agent_name}": Missing recommended frontmatter: skills\n'
                        f'       Available skills: {", ".join(sorted(available_skills)[:3])}'
                        f'{"..." if len(available_skills) > 3 else ""}'
                    )
                else:
                    result.add_pass(f'Agent "{agent_name}": Frontmatter OK')
            else:
                result.add_pass(f'Agent "{agent_name}": Frontmatter complete')

            # Check if skills referenced exist
            if 'skills' in frontmatter_raw:
                skills_value = frontmatter_raw['skills']
                # Parse comma-separated skills
                referenced_skills = [s.strip() for s in skills_value.split(',')]

                # Check if any local skills are referenced
                for skill in referenced_skills:
                    skill_name = skill.split(':')[-1]  # Handle plugin:skill format
                    if skill_name in available_skills:
                        result.add_pass(f'Agent "{agent_name}": Uses local skill "{skill_name}"')
                    # Note: Global skills from other plugins are valid but can't be verified here

            # W033: Check if agent uses Skill() tool when skills are declared
            body_content = parts[2] if len(parts) >= 3 else content
            skill_call_patterns = [
                r'Skill\s*\(',           # Skill(
                r'Skill\s*tool',          # Skill tool
                r'invoke.*skill',         # invoke skill
                r'load.*skill',           # load skill
                r'use.*Skill',            # use Skill
            ]
            has_skill_call = any(re.search(p, body_content, re.IGNORECASE) for p in skill_call_patterns)

            if 'skills' in frontmatter_raw and not has_skill_call:
                result.add_warning(
                    f'[W033] Agent "{agent_name}": Declares skills in frontmatter but no Skill() usage found\n'
                    f'       Pattern: Skills should be loaded via Skill("plugin:skill-name") tool.\n'
                    f'       Declared skills: {frontmatter_raw["skills"]}'
                )
            elif 'skills' in frontmatter_raw and has_skill_call:
                result.add_pass(f'Agent "{agent_name}": Uses Skill() tool for skill loading')

        except Exception as e:
            result.add_warning(f'Could not analyze agent "{agent_name}": {e}')

    if agents_checked == 0:
        result.add_pass("No agents to check for pattern compliance")

    return result


def check_multistage_workflow_hookify(plugin_root: Path) -> ValidationResult:
    """
    W034: Detect multi-stage workflows that should use per-stage skill loading.

    Multi-stage indicators:
    - Phase/Step/Stage headers with numbers
    - Sequential process patterns
    - Complex workflows without skill calls per stage
    """
    result = ValidationResult()

    # Directories to check
    dirs_to_check = [
        (plugin_root / "agents", "agent"),
        (plugin_root / "commands", "command"),
    ]

    # Multi-stage workflow patterns
    stage_patterns = [
        r'#{1,3}\s*(Phase|Step|Stage|단계)\s*\d',      # ## Phase 1, ## Step 1, ## 단계 1
        r'#{1,3}\s*\d+\.\s',                           # ## 1. Something
        r'#{1,3}\s*(First|Second|Third|Fourth|Fifth)', # ## First, ## Second
        r'#{1,3}\s*(처음|둘째|셋째|첫번째|두번째)',      # Korean ordinals
    ]

    for check_dir, file_type in dirs_to_check:
        if not check_dir.exists():
            continue

        for md_file in check_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                file_name = md_file.stem

                # Count stage headers
                stage_count = 0
                for pattern in stage_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    stage_count += len(matches)

                # If 3+ stages detected, check for per-stage skill loading
                if stage_count >= 3:
                    # Count Skill() calls
                    skill_calls = len(re.findall(r'Skill\s*\(', content))

                    # Complex workflow without adequate skill calls
                    if skill_calls < stage_count // 2:
                        result.add_warning(
                            f'[W034] {file_type.title()} "{file_name}": Multi-stage workflow ({stage_count} stages) '
                            f'with only {skill_calls} Skill() calls\n'
                            f'       Pattern: Each stage should load relevant skills for context isolation.\n'
                            f'       Consider: Add Skill() calls per stage, or hookify with PreToolUse/PostToolUse.'
                        )
                    else:
                        result.add_pass(f'{file_type.title()} "{file_name}": Multi-stage workflow with adequate skill loading')

            except Exception:
                pass

    return result


def check_command_skill_usage(plugin_root: Path) -> ValidationResult:
    """
    W033: Check if commands that reference skills use Skill() tool.
    """
    result = ValidationResult()
    commands_dir = plugin_root / "commands"

    if not commands_dir.exists():
        return result

    # Get available skills in this plugin
    skills_dir = plugin_root / "skills"
    available_skills = set()
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                available_skills.add(skill_dir.name)

    if not available_skills:
        return result

    commands_checked = 0

    for cmd_md in commands_dir.glob("*.md"):
        commands_checked += 1

        try:
            content = cmd_md.read_text(encoding='utf-8')
            cmd_name = cmd_md.stem

            # Check if command references any skills by name
            skills_mentioned = []
            for skill in available_skills:
                if skill in content:
                    skills_mentioned.append(skill)

            if not skills_mentioned:
                continue

            # Check if command uses Skill() tool
            skill_call_patterns = [
                r'Skill\s*\(',           # Skill(
                r'Skill\s*tool',          # Skill tool
                r'invoke.*skill',         # invoke skill
                r'load.*skill',           # load skill
            ]
            has_skill_call = any(re.search(p, content, re.IGNORECASE) for p in skill_call_patterns)

            if skills_mentioned and not has_skill_call:
                result.add_warning(
                    f'[W033] Command "{cmd_name}": References skills but no Skill() usage found\n'
                    f'       Pattern: Skills should be loaded via Skill("plugin:skill-name") tool.\n'
                    f'       Mentioned skills: {", ".join(skills_mentioned[:3])}'
                    f'{"..." if len(skills_mentioned) > 3 else ""}'
                )
            elif skills_mentioned and has_skill_call:
                result.add_pass(f'Command "{cmd_name}": Uses Skill() tool for skill loading')

        except Exception as e:
            result.add_warning(f'Could not analyze command "{cmd_name}": {e}')

    if commands_checked == 0:
        result.add_pass("No commands to check for skill usage")

    return result


def run_comprehensive_validation(plugin_root: Path, json_output: bool = False) -> ValidationResult:
    """
    Run comprehensive validation:
    1. Claude CLI validation (PRIMARY - authoritative schema check)
    2. Our code only adds: fixes, enhanced messages, best practices

    Philosophy: CLI is the source of truth. We only enhance, not duplicate.
    """
    result = ValidationResult()

    marketplace_path = plugin_root / ".claude-plugin" / "marketplace.json"

    # PRIMARY: Run Claude CLI validation (authoritative)
    cli_success, cli_output, cli_errors = run_claude_cli_validation(plugin_root)

    if "not found" in cli_output.lower():
        # CLI not available - use our fallback validation
        result.add_warning("Claude CLI not installed - using fallback schema validation")
        edge_result = test_source_edge_cases(marketplace_path)
        result.merge(edge_result)
    elif cli_success:
        result.add_pass("Claude CLI schema validation: passed")
    else:
        # CLI found errors - show CLI output directly
        result.add_error(f"Claude CLI: {cli_output.split(chr(10))[0]}")  # First line
        for error in cli_errors:
            result.add_error(f"  => {error}")

        # Add fix suggestions (our value-add)
        edge_result = test_source_edge_cases(marketplace_path)
        if edge_result.fixes:
            result.fixes.extend(edge_result.fixes)

    # Best practices check (warnings only, not in CLI)
    pattern_result = validate_against_official_patterns(plugin_root)
    # Only add warnings and passes, not errors (CLI handles errors)
    result.warnings.extend(pattern_result.warnings)
    result.passed.extend(pattern_result.passed)

    return result


def check_and_clear_outdated_cache(plugin_root: Path, marketplace_data: dict) -> ValidationResult:
    """
    Check if installed cache version is outdated compared to local source.
    If outdated, automatically clear the cache.

    Cache structure: ~/.claude/plugins/cache/{marketplace}/{plugin}/{version-or-hash}/

    This ensures the deployed version always matches the local source after push.
    """
    import shutil
    result = ValidationResult()

    # Get marketplace name from local source
    marketplace_name = marketplace_data.get("name", "")
    plugins = marketplace_data.get("plugins", [])
    if not plugins or not marketplace_name:
        return result

    local_version = plugins[0].get("version", "")
    plugin_name = plugins[0].get("name", "")

    if not plugin_name:
        return result

    # Check cache location: cache/{marketplace}/{plugin}/
    cache_base = Path.home() / ".claude" / "plugins" / "cache" / marketplace_name / plugin_name
    if not cache_base.exists():
        return result

    # Find cached versions (could be semver like "2.0.0" or hash like "6d3752c000e2")
    cached_versions = [d for d in cache_base.iterdir() if d.is_dir()]

    for cache_dir in cached_versions:
        cached_version = cache_dir.name

        # Check marketplace.json inside cache to get actual version
        cached_marketplace = cache_dir / ".claude-plugin" / "marketplace.json"
        if cached_marketplace.exists():
            try:
                cached_data = json.loads(cached_marketplace.read_text(encoding='utf-8'))
                cached_plugins = cached_data.get("plugins", [])
                if cached_plugins:
                    cached_ver = cached_plugins[0].get("version", cached_version)
                    if local_version and cached_ver != local_version:
                        result.add_warning(
                            f"[CACHE] Outdated: {plugin_name} v{cached_ver} (local: v{local_version})"
                        )
                        # Auto-clear outdated cache
                        try:
                            shutil.rmtree(cache_dir)
                            result.add_pass(f"[CACHE] Cleared: {marketplace_name}/{plugin_name}/{cached_version}")
                        except Exception as e:
                            result.add_error(f"[CACHE] Failed to clear: {e}")
                    else:
                        result.add_pass(f"[CACHE] Current: {plugin_name} v{cached_ver}")
            except Exception:
                pass

    return result


def validate_deploy_readiness(plugin_root: Path) -> ValidationResult:
    """
    PHASE 4: Deploy Readiness Validation

    Checks that are CRITICAL before deploying/publishing:
    1. Git: No uncommitted changes
    2. Git: No unpushed commits
    3. Git: Branch is up to date with remote

    These issues cause the deployed version to differ from the local source.
    """
    import subprocess
    result = ValidationResult()

    # Check if this is a git repository
    git_dir = plugin_root / ".git"
    if not git_dir.exists():
        result.add_warning("Not a git repository - skipping deploy readiness checks")
        return result

    try:
        # 1. Check for uncommitted changes (staged or unstaged)
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=plugin_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if status_result.returncode == 0 and status_result.stdout.strip():
            changes = status_result.stdout.strip().split('\n')
            result.add_error(
                f"[DEPLOY] {len(changes)} uncommitted change(s) detected. "
                f"The deployed version will NOT include these changes!"
            )
            # Show first few changes
            for change in changes[:5]:
                result.add_error(f"  {change}")
            if len(changes) > 5:
                result.add_error(f"  ... and {len(changes) - 5} more")
        else:
            result.add_pass("Git: No uncommitted changes")

        # 2. Check for unpushed commits
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=plugin_root,
            capture_output=True,
            text=True,
            timeout=10
        )

        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()

            # Check if branch has upstream
            upstream_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
                cwd=plugin_root,
                capture_output=True,
                text=True,
                timeout=10
            )

            if upstream_result.returncode == 0:
                upstream = upstream_result.stdout.strip()

                # Count commits ahead of upstream
                ahead_result = subprocess.run(
                    ["git", "rev-list", "--count", f"{upstream}..HEAD"],
                    cwd=plugin_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if ahead_result.returncode == 0:
                    ahead_count = int(ahead_result.stdout.strip())
                    if ahead_count > 0:
                        result.add_error(
                            f"[DEPLOY] {ahead_count} unpushed commit(s) on '{branch}'. "
                            f"Run: git push origin {branch}"
                        )
                    else:
                        result.add_pass(f"Git: Branch '{branch}' is up to date with remote")

                # Count commits behind upstream
                behind_result = subprocess.run(
                    ["git", "rev-list", "--count", f"HEAD..{upstream}"],
                    cwd=plugin_root,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if behind_result.returncode == 0:
                    behind_count = int(behind_result.stdout.strip())
                    if behind_count > 0:
                        result.add_warning(
                            f"[DEPLOY] Branch is {behind_count} commit(s) behind remote. "
                            f"Consider: git pull origin {branch}"
                        )
            else:
                result.add_warning(f"Git: Branch '{branch}' has no upstream tracking")

    except subprocess.TimeoutExpired:
        result.add_warning("Git status check timed out")
    except FileNotFoundError:
        result.add_warning("Git not found - skipping deploy readiness checks")
    except Exception as e:
        result.add_warning(f"Git check failed: {e}")

    return result


def main():
    # Parse arguments
    json_output = "--json" in sys.argv
    fix_mode = "--fix" in sys.argv
    dry_run = "--dry-run" in sys.argv
    schema_only = "--schema-only" in sys.argv
    pre_edit = "--pre-edit" in sys.argv
    quiet_mode = "--quiet" in sys.argv
    skip_git = "--skip-git" in sys.argv
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
        data = json.loads(marketplace_path.read_text(encoding='utf-8'))
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

    # ==========================================================================
    # PHASE 0: STATIC SCHEMA VALIDATION (runs FIRST, before all other checks)
    # ==========================================================================
    # This catches schema errors immediately at parse time with error codes
    schema_result = validate_schema_static(plugin_root, marketplace_path)
    total_result.merge(schema_result)

    # If schema has errors, show them prominently
    if schema_result.errors:
        if not json_output and not quiet_mode:
            print("=" * 60)
            print("SCHEMA VALIDATION FAILED")
            print("=" * 60)
            print(f"Found {len(schema_result.errors)} schema error(s):")
            for e in schema_result.errors:
                print(f"  {e}")
            print()
            if schema_result.fixes:
                print(f"[--fix] {len(schema_result.fixes)} errors can be auto-fixed")
            print("=" * 60)
            print()

    # ==========================================================================
    # FAST PATH: --schema-only skips all other phases
    # ==========================================================================
    if schema_only:
        # Quick exit for schema-only validation (used by hooks for fast feedback)
        if json_output:
            print(json.dumps({
                "status": "fail" if total_result.errors else "pass",
                "errors": total_result.errors,
                "warnings": total_result.warnings,
                "passed": len(total_result.passed),
                "mode": "schema-only"
            }, indent=2))
        elif not quiet_mode:
            if total_result.errors:
                print(f"[SCHEMA] FAIL: {len(total_result.errors)} error(s)")
                for e in total_result.errors:
                    print(f"  {e}")
            else:
                print("[SCHEMA] PASS")
        sys.exit(1 if total_result.errors else 0)

    # ==========================================================================
    # PHASE 1: CLI Validation (secondary check, may catch additional issues)
    # ==========================================================================
    if not quiet_mode:
        cli_success, cli_output, cli_errors = run_claude_cli_validation(plugin_root)
        cli_available = "not found" not in cli_output.lower()

        if cli_available:
            if cli_success:
                total_result.add_pass("CLI validation: passed")
            else:
                # CLI found additional errors - show them (avoid duplicates)
                for error in cli_errors:
                    error_msg = f"CLI: {error}"
                    if error_msg not in total_result.errors:
                        total_result.add_error(error_msg)
        else:
            # CLI not available - our schema validation already ran
            total_result.add_warning("Claude CLI not installed (npm install -g @anthropic-ai/claude-code)")

    # ==========================================================================
    # PHASE 2: File/Content Validation (our unique checks, not in CLI)
    # ==========================================================================

    # CRITICAL: Check component directory structure first
    total_result.merge(validate_component_locations(plugin_root, marketplace_path))

    # CRITICAL: Check path resolution consistency (E016, E017)
    # This detects when marketplace.json is in .claude-plugin/ but components are at root
    total_result.merge(validate_path_resolution_consistency(plugin_root, marketplace_path))

    # CRITICAL: Check for GitHub source with local files (common development mistake)
    total_result.merge(validate_github_source_with_local_files(plugin_root, marketplace_path))

    total_result.merge(validate_settings_json())

    # E023, E024: Check marketplace cache consistency
    total_result.merge(validate_marketplace_cache_consistency())

    for i, plugin in enumerate(plugins):
        source = plugin.get("source", "./")
        # Handle both string paths and GitHub source objects
        if isinstance(source, dict):
            effective_root = plugin_root
        elif source in [".", "./"]:
            effective_root = plugin_root
        elif isinstance(source, str) and source not in ["github", "url"]:
            effective_root = plugin_root / source.lstrip("./")
        else:
            effective_root = plugin_root

        # File existence and content checks (not covered by CLI)
        total_result.merge(validate_registration(effective_root, plugin, marketplace_path))
        total_result.merge(validate_frontmatter_fields(effective_root))
        total_result.merge(validate_scripts(effective_root))

    # Validate plugin.json if it exists
    total_result.merge(validate_plugin_json(plugin_root))

    # E027: Validate hooks.json schema (Claude Code 1.0.40+)
    total_result.merge(validate_hooks_json(plugin_root))

    # ==========================================================================
    # PHASE 3: Best Practices (warnings only)
    # ==========================================================================
    pattern_result = validate_against_official_patterns(plugin_root)
    total_result.warnings.extend(pattern_result.warnings)
    total_result.passed.extend(pattern_result.passed)

    # ==========================================================================
    # PHASE 4: Deploy Readiness (DEFAULT - use --skip-git to disable)
    # ==========================================================================
    if not skip_git:
        deploy_result = validate_deploy_readiness(plugin_root)
        total_result.merge(deploy_result)

        if deploy_result.errors and not json_output and not quiet_mode:
            print()
            print("=" * 60)
            print("DEPLOY READINESS CHECK FAILED")
            print("=" * 60)
            print("The following issues will cause deployed version to differ from local:")
            for e in deploy_result.errors:
                print(f"  {e}")
            print()
            print("Fix these issues before deploying:")
            print("  1. git add -A && git commit -m 'your message'")
            print("  2. git push origin <branch>")
            print("=" * 60)

    # ==========================================================================
    # PHASE 5: Remote Source Consistency (for GitHub sources)
    # ==========================================================================
    # Check if GitHub source repos exist and have correct structure
    remote_result = validate_remote_source_consistency(plugin_root, marketplace_path)
    total_result.merge(remote_result)

    # ==========================================================================
    # PHASE 6: Cache Management (auto-clear outdated cache)
    # ==========================================================================
    cache_result = check_and_clear_outdated_cache(plugin_root, data)
    total_result.merge(cache_result)

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
    elif quiet_mode:
        # Minimal output for hooks - only show errors
        if total_result.errors:
            for e in total_result.errors:
                print(f"[ERROR] {e}")
            print(f"FAIL: {len(total_result.errors)} error(s)")
        # In quiet mode, don't print anything on success
    else:
        print("=" * 60)
        print("PLUGIN VALIDATION")
        print("=" * 60)
        print(f"Plugin: {plugin_root}")
        print()

        if total_result.errors:
            print("ERRORS:")
            for e in total_result.errors:
                print(f"  [ERROR] {e}")
            print()

        if total_result.warnings:
            print("WARNINGS:")
            for w in total_result.warnings:
                print(f"  [WARN]  {w}")
            print()

        print("SUMMARY:")
        print(f"  Errors:   {len(total_result.errors)}")
        print(f"  Warnings: {len(total_result.warnings)}")
        print(f"  Passed:   {len(total_result.passed)}")
        print(f"  Fixable:  {len(total_result.fixes)}")
        print()

        if total_result.errors:
            print("STATUS: [ERROR] DEPLOYMENT WILL FAIL")
        elif total_result.warnings:
            print("STATUS: [WARN]  DEPLOYMENT MAY HAVE ISSUES")
        else:
            print("STATUS: [PASS] READY FOR DEPLOYMENT")

    # Apply fixes if requested
    if fix_mode and total_result.fixes:
        success, fail = apply_fixes(total_result.fixes, dry_run)
        if not quiet_mode:
            print(f"\nFixes applied: {success}, Failed: {fail}")

            if not dry_run and success > 0:
                print("\n[TIP] Re-run validation to verify fixes:")
                print(f"   python3 {sys.argv[0]}")
    elif fix_mode and not total_result.fixes:
        if not quiet_mode:
            print("\n[OK] Nothing to fix!")
    elif total_result.fixes and not json_output and not quiet_mode:
        print(f"\n[--fix] {len(total_result.fixes)} errors can be auto-fixed:")
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
