# Complete Workflow Example: Refactoring Pipeline

## Overview

This example shows a complete 4-phase refactoring workflow with:
- State file management
- Hook-based quality gates
- MCP Gateway integration
- Failure recovery

---

## Workflow Phases

```
┌─────────────────────────────────────────────────────────┐
│               REFACTORING WORKFLOW                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  [1] ANALYZE ──→ solid-analyzer agent                   │
│      └─ Creates: .refactor-analysis-done                 │
│                                                          │
│  [2] PLAN ─────→ refactor-planner agent                 │
│      └─ Creates: .refactor-plan-approved                 │
│                                                          │
│  [USER GATE] ──→ User reviews and approves plan         │
│                                                          │
│  [3] EXECUTE ──→ refactor-executor agent                │
│      └─ Pre-check: .analysis-done + .plan-approved      │
│      └─ Creates: .refactor-execution-done               │
│                                                          │
│  [4] VERIFY ───→ refactor-auditor agent                 │
│      └─ PASS: cleanup all, create .audit-passed         │
│      └─ FAIL: preserve .execution-done for retry        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Hooks Configuration

`hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "type": "preToolUse",
      "matcher": "Task",
      "pattern": "refactor-executor",
      "command": "test -f .refactor-analysis-done && test -f .refactor-plan-approved",
      "behavior": "block",
      "message": "❌ Workflow violation: Cannot execute without completed analysis and approved plan.\n\nRequired files:\n  - .refactor-analysis-done (run analyzer first)\n  - .refactor-plan-approved (run planner and approve)",
      "timeout": 5000
    },
    {
      "type": "preToolUse",
      "matcher": "Task",
      "pattern": "refactor-planner",
      "command": "test -f .refactor-analysis-done || echo '⚠️ Warning: Planning without analysis may miss issues'",
      "behavior": "notify",
      "timeout": 3000
    },
    {
      "type": "postToolUse",
      "matcher": "Task",
      "pattern": "solid-analyzer",
      "command": "touch .refactor-analysis-done && echo '✓ Analysis complete. State: .refactor-analysis-done created'",
      "behavior": "notify",
      "timeout": 3000
    },
    {
      "type": "postToolUse",
      "matcher": "Task",
      "pattern": "refactor-planner",
      "command": "touch .refactor-plan-approved && echo '✓ Plan created. State: .refactor-plan-approved created'",
      "behavior": "notify",
      "timeout": 3000
    },
    {
      "type": "postToolUse",
      "matcher": "Task",
      "pattern": "refactor-executor",
      "command": "touch .refactor-execution-done && echo '✓ Execution complete. State: .refactor-execution-done created'",
      "behavior": "notify",
      "timeout": 3000
    },
    {
      "type": "postToolUse",
      "matcher": "Task",
      "pattern": "refactor-auditor.*PASS",
      "command": "touch .refactor-audit-passed && rm -f .refactor-analysis-done .refactor-plan-approved .refactor-execution-done && echo '✓ Audit passed. Workflow complete. All state files cleaned.'",
      "behavior": "notify",
      "timeout": 5000
    },
    {
      "type": "postToolUse",
      "matcher": "Task",
      "pattern": "refactor-auditor.*FAIL",
      "command": "echo '⚠️ Audit failed. Fix issues and re-run executor. State preserved for retry.'",
      "behavior": "notify",
      "timeout": 3000
    },
    {
      "type": "stop",
      "command": "if [ -f .refactor-execution-done ] && [ ! -f .refactor-audit-passed ]; then echo '\\n📋 Workflow Status: Execution done, audit pending.\\nNext session: Run auditor to verify changes.'; fi",
      "behavior": "notify",
      "timeout": 5000
    }
  ]
}
```

---

## Agent Definitions

### 1. Solid Analyzer Agent

```yaml
---
name: solid-analyzer
description: Analyzes codebase for SOLID violations
tools: [Task, Read, Glob, Grep]
skills: solid-design-rules
model: sonnet
---
```

Calls gateway:
```json
{
  "intent": "ANALYZE",
  "action": "find_refs",
  "effect": "READ_ONLY",
  "artifact": "JSON",
  "params": { "target": "src/" }
}
```

### 2. Refactor Planner Agent

```yaml
---
name: refactor-planner
description: Creates step-by-step refactoring plans
tools: [Task, Read, Glob, Grep]
skills: solid-design-rules, refactoring-patterns
model: sonnet
---
```

### 3. Refactor Executor Agent

```yaml
---
name: refactor-executor
description: Executes refactoring operations via gateway
tools: [Task, Read, Glob, Grep, Bash]
skills: refactoring-patterns
model: sonnet
---
```

Calls gateway with MODIFY:
```json
{
  "intent": "MODIFY",
  "action": "rename_symbol",
  "effect": "MUTATING",
  "artifact": "PATCH",
  "params": { "old_name": "foo", "new_name": "bar" }
}
```

### 4. Refactor Auditor Agent

```yaml
---
name: refactor-auditor
description: Verifies refactoring quality
tools: [Task, Read, Glob, Grep, Bash]
skills: solid-design-rules
model: sonnet
---
```

---

## Command Entry Points

### Full Workflow Command

`commands/refactor.md`:
```markdown
---
name: refactor
description: Full refactoring workflow (analyze → plan → execute → verify)
---

# Refactoring Workflow

Execute complete refactoring pipeline:

1. Run solid-analyzer on target
2. Run refactor-planner to create plan
3. Present plan for user approval
4. Run refactor-executor (blocked until plan approved)
5. Run refactor-auditor to verify
6. Report results
```

### Individual Phase Commands

`commands/analyze.md`, `commands/plan.md`, etc.

---

## State File Lifecycle

```
Session 1:
  /analyze → .refactor-analysis-done created
  /plan → .refactor-plan-approved created
  (session ends)

Session 2:
  (state files persist)
  /execute → PRE HOOK checks files → PASS → executes
  .refactor-execution-done created
  /audit → runs verification
  PASS → all state files deleted
  FAIL → .refactor-execution-done preserved

Session 3 (if audit failed):
  (fix issues)
  /execute → runs again (state still valid)
  /audit → PASS → cleanup
```

---

## Debugging State

Check current workflow state:
```bash
ls -la .refactor-*
```

Reset workflow:
```bash
rm -f .refactor-*
```

Skip to specific phase (dangerous):
```bash
touch .refactor-analysis-done .refactor-plan-approved
```

---

## Integration Points

### With MCP Gateway

All MODIFY operations go through gateway with workflow state checks.

### With Git

Recommend:
1. Stash before workflow: `git stash`
2. After audit pass: `git commit`
3. On failure: `git checkout .` to reset

Add to `.gitignore`:
```
.refactor-*
```
