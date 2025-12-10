---
description: Validate plugin structure before deployment. Runs automated checks and parallel quality validation.
argument-hint: "[plugin-path]"
allowed-tools: ["Bash", "Read", "Task"]
---

# Deploy Checker

Validate that a Claude Code plugin is ready for deployment.

## Step 1: Automated Script Validation

```bash
python3 scripts/validate_all.py
```

**Decision:**
- Exit 0 → Continue to Step 2
- Exit 1 (errors) → STOP. Report errors from script output.
- Exit 2 (warnings) → Continue but note warnings

## Step 2: Parallel Subagent Quality Validation

Launch **3 Task subagents in parallel** for multi-step quality checks:

**Task 1 - Content Quality:**
```
Read references/deploy-checker/content-quality.md
Validate all description fields in commands/, agents/, skills/
Return JSON: {"task": "content", "status": "pass|fail", "issues": [...]}
```

**Task 2 - Expert Skill Completeness:**
```
Read references/deploy-checker/expert-skill-requirements.md
Analyze each skill in skills/ for completeness
Return JSON: {"task": "expert-skill", "status": "pass|fail", "issues": [...]}
```

**Task 3 - Cross-Reference Validation:**
```
Read references/deploy-checker/cross-reference-guide.md
Verify all internal links and file references
Return JSON: {"task": "cross-ref", "status": "pass|fail", "issues": [...]}
```

Wait for all 3 results.

## Step 3: Result Aggregation

Combine script output + 3 subagent results:

**All pass:**
```
STATUS: READY FOR DEPLOYMENT
- Script: passed
- Content Quality: passed
- Expert Skills: passed
- Cross-References: passed
```

**Any fail:**
```
STATUS: FIX REQUIRED

Errors:
1. [source] issue description
2. [source] issue description

See references/deploy-checker/common-errors.md for fix guidance.
```

## Hooks (Auto-Validation)

This plugin includes hooks that automatically run validation before `git push`.
See hooks/ directory for configuration.
