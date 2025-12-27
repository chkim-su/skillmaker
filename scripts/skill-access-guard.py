#!/usr/bin/env python3
"""
Skill Access Guard - Warns when skill files are read directly instead of using Skill() tool.
"""

import json
import sys
import re

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Get path from different tool input formats
    path = ""
    if tool_name == "Read":
        path = tool_input.get("file_path", "")
    elif tool_name == "Grep":
        path = tool_input.get("path", "")
    elif tool_name == "Glob":
        path = tool_input.get("path", "") or tool_input.get("pattern", "")

    if not path:
        sys.exit(0)

    # Detect skill file access patterns
    skill_patterns = [
        r'/skills/[^/]+/SKILL\.md',       # Direct SKILL.md read
        r'/skills/[^/]+/references/',      # Skill references
        r'\.claude/skills/[^/]+/',         # .claude/skills directory
        r'plugins/.*/skills/[^/]+/'        # Plugin skills
    ]

    for pattern in skill_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            # Extract skill name if possible
            skill_match = re.search(r'/skills/([^/]+)/', path)
            skill_name = skill_match.group(1) if skill_match else "unknown"

            print("")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("⚠️ SKILL FILE DIRECT ACCESS DETECTED")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"  Path: {path}")
            print("")
            print("  ❌ Reading skill files directly is discouraged")
            print(f"  ✅ Use: Skill(\"plugin:{skill_name}\")")
            print("")
            print("  The Skill() tool loads skill content properly")
            print("  and ensures correct skill activation.")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("")
            break

if __name__ == "__main__":
    main()
