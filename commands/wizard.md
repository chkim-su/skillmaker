---
description: Create skills, agents, or commands with smart routing
argument-hint: "describe what to create (e.g., 'API skill', 'database agent')"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill", "AskUserQuestion"]
---

# Routing

Analyze input. Match first pattern:

| Pattern | Route |
|---------|-------|
| `skill.*create\|create.*skill\|스킬.*만들` | → SKILL |
| `convert\|from.*code\|skillization\|변환` | → SKILL_FROM_CODE |
| `agent\|에이전트\|subagent` | → AGENT |
| `command\|workflow\|명령어` | → COMMAND |
| `validate\|check\|검증` | → VALIDATE |
| no match / empty | → MENU |

---

# MENU

```yaml
AskUserQuestion:
  question: "What to create?"
  header: "Type"
  options:
    - label: "Skill"
    - label: "Agent"
    - label: "Command"
    - label: "Validate"
```

Route: Skill→SKILL, Agent→AGENT, Command→COMMAND, Validate→VALIDATE

---

# SKILL

1. Load skill: `skill-design`

2. Ask type:
```yaml
AskUserQuestion:
  question: "Skill type?"
  header: "Type"
  options:
    - label: "Knowledge"
      description: "Guidelines, high freedom"
    - label: "Hybrid"
      description: "Guidance + scripts"
    - label: "Tool"
      description: "Script-driven, low freedom"
    - label: "Unsure"
```

3. If "Unsure": ask freedom level (High→Knowledge, Medium→Hybrid, Low→Tool)

4. Launch:
```
Task: skill-architect
Pass: description, skill_type
```

---

# SKILL_FROM_CODE

1. If no path specified:
```yaml
AskUserQuestion:
  question: "Target type?"
  header: "Target"
  options:
    - label: "File"
    - label: "Directory"
    - label: "Pattern"
```
Then ask for path.

2. Load skill: `skill-design`

3. Launch:
```
Task: skill-converter
Pass: target_path, description
```

---

# AGENT

1. Check: `Glob .claude/skills/*/SKILL.md`

2. If none: "No skills found. Create skill first?" → Yes: goto SKILL

3. List skills, ask selection:
```yaml
AskUserQuestion:
  question: "Which skills?"
  header: "Skills"
  multiSelect: true
  options: [discovered skills]
```

4. Load skill: `orchestration-patterns`

5. Launch:
```
Task: skill-orchestrator-designer
Pass: selected_skills, description
```

---

# COMMAND

1. Check: `Glob .claude/agents/*.md`

2. If none: "No agents found. Create agent first?" → Yes: goto AGENT

3. List agents, ask selection:
```yaml
AskUserQuestion:
  question: "Which agents?"
  header: "Agents"
  multiSelect: true
```

4. Ask flow:
```yaml
AskUserQuestion:
  question: "Coordination?"
  header: "Flow"
  options:
    - label: "Sequential"
    - label: "Parallel"
    - label: "Conditional"
```

5. Write `.claude/commands/{name}.md` with selected agents and flow pattern.

---

# VALIDATE

1. Run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py`

2. If errors, offer: "Auto-fix?" → Yes: run with `--fix`
