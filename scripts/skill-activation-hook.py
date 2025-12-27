#!/usr/bin/env python3
"""
Skillmaker UserPromptSubmit Hook
Suggests relevant skills based on user prompt keywords and complexity level.
"""

import json
import os
import sys
import re
from pathlib import Path

def load_skill_rules():
    """Load skill-rules.json from .claude/skills/"""
    # Try CLAUDE_PLUGIN_ROOT first, then script directory
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        rules_path = Path(plugin_root) / ".claude" / "skills" / "skill-rules.json"
    else:
        script_dir = Path(__file__).parent.parent
        rules_path = script_dir / ".claude" / "skills" / "skill-rules.json"

    if not rules_path.exists():
        return None

    with open(rules_path) as f:
        return json.load(f)

def match_keywords(prompt: str, keywords: list) -> bool:
    """Check if any keyword matches in prompt (case-insensitive)"""
    prompt_lower = prompt.lower()
    return any(kw.lower() in prompt_lower for kw in keywords)

def match_patterns(prompt: str, patterns: list) -> bool:
    """Check if any regex pattern matches in prompt"""
    prompt_lower = prompt.lower()
    for pattern in patterns:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return True
    return False

def detect_complexity(prompt: str, complexity_levels: dict) -> str:
    """Detect complexity level from prompt"""
    prompt_lower = prompt.lower()

    # Check in order: advanced -> standard -> simple
    for level in ["advanced", "standard", "simple"]:
        if level in complexity_levels:
            keywords = complexity_levels[level].get("keywords", [])
            if any(kw.lower() in prompt_lower for kw in keywords):
                return level

    return None

def find_matching_skills(prompt: str, rules: dict) -> list:
    """Find skills that match the prompt"""
    matched = []
    skills = rules.get("skills", {})

    for skill_name, config in skills.items():
        triggers = config.get("promptTriggers", {})
        keywords = triggers.get("keywords", [])
        patterns = triggers.get("intentPatterns", [])

        if match_keywords(prompt, keywords) or match_patterns(prompt, patterns):
            matched.append({
                "name": skill_name,
                "priority": config.get("priority", "low"),
                "type": config.get("type", "domain")
            })

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    matched.sort(key=lambda x: priority_order.get(x["priority"], 99))

    return matched

def main():
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Silent exit on invalid input

    prompt = input_data.get("prompt", "")
    if not prompt:
        sys.exit(0)

    # Load rules
    rules = load_skill_rules()
    if not rules:
        sys.exit(0)

    # Detect complexity level
    complexity = detect_complexity(prompt, rules.get("complexity_levels", {}))

    # Find matching skills
    matched_skills = find_matching_skills(prompt, rules)

    # If complexity detected, add those skills too
    if complexity:
        complexity_skills = rules.get("complexity_levels", {}).get(complexity, {}).get("auto_skills", [])
        for skill_name in complexity_skills:
            if not any(s["name"] == skill_name for s in matched_skills):
                matched_skills.append({
                    "name": skill_name,
                    "priority": "medium",
                    "type": "complexity-based"
                })

    # Output suggestions if any
    if matched_skills:
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📚 RECOMMENDED SKILLS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        if complexity:
            print(f"Complexity: {complexity.upper()}")
            print("")

        for skill in matched_skills[:5]:  # Max 5 suggestions
            priority_icon = {"high": "⚡", "medium": "💡", "low": "📌"}.get(skill["priority"], "•")
            print(f"  {priority_icon} skillmaker:{skill['name']}")

        print("")
        print("Use: Skill(\"skillmaker:{name}\") to load")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")

if __name__ == "__main__":
    main()
