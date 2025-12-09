---
description: Transform existing code into reusable skills. Analyzes code to determine skill type (knowledge/hybrid/tool), extracts scriptable operations, and documents patterns.
argument-hint: "[target code/functionality]"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill"]
---

# Skillization: Convert Existing Code to Skill

**FIRST: Load the skillmaker:skill-design skill** using the Skill tool.

Transform existing functionality into reusable skills by analyzing code and determining the appropriate skill type.

## Your Task

### Step 1: Identify Target

If user specified a target, search for it:

```bash
# Search for relevant code
Grep: pattern="{target_keyword}" type="py"
Glob: pattern="**/*{target}*.{py,ts,js}"
```

Ask if unclear:
- What functionality should become a skill?
- Where is it located? (files, modules)

### Step 2: Analyze Code for Skill Type

**Key Questions**:

1. **Is this code REUSED or REFERENCED?**
   - Same code copy-pasted → Extract to scripts (Tool)
   - Patterns followed → Document (Knowledge)
   - Both → Hybrid

2. **Does it manipulate files or call external tools?**
   - Yes → Likely Tool skill with scripts
   - No → Likely Knowledge skill

3. **Is reliability critical?**
   - Yes → Scripts for deterministic behavior
   - No → Documentation may suffice

### Step 3: Launch skill-converter Agent

Use the Task tool:

```
Task tool with:
- subagent_type: "skillmaker:skill-converter"
- description: "Convert code to skill"
- prompt: "Analyze and convert existing code to a skill:

Target: {user_specified_target}
Files found: {list of relevant files}

Your process:
1. Read and analyze the code
2. Identify scriptable operations vs documentable patterns
3. Determine skill type (knowledge/hybrid/tool)
4. Design the skill structure
5. Extract scripts (if tool/hybrid)
6. Document patterns and knowledge

Use scripts/init_skill.py to initialize and scripts/validate_skill.py to validate.

Return:
- Skill name and type with reasoning
- SKILL.md content
- Scripts (with full implementations if tool/hybrid)
- References content
- What code to REFERENCE (not duplicate)
"
```

### Step 4: Review Conversion Plan

Present to user:

```
🔄 Skillization Analysis Complete

Source Code:
- {file1.py} - {description}
- {file2.py} - {description}

Recommended Type: {Knowledge | Hybrid | Tool} Skill
Reason: {why this type}

Components:

Scripts to Extract (if tool/hybrid):
| Source | → Script | Purpose |
|--------|----------|---------|
| src/utils/x.py:func | scripts/x.py | {purpose} |

Knowledge to Document:
| Topic | Source | Content |
|-------|--------|---------|
| {topic} | {file:lines} | {what} |

Code to Reference (not duplicate):
- {file:lines} - {description}

Implicit Knowledge:
- {knowledge point 1}
- {knowledge point 2}

Ready to create this skill?
```

### Step 5: Create Skill

After confirmation:

```bash
# Initialize structure
python ${CLAUDE_PLUGIN_ROOT}/scripts/init_skill.py {skill-name} --type {type} --path .claude/skills
```

### Step 6: Implement Components

**For scripts/** (if tool/hybrid):
1. Extract functions from source code
2. Make standalone with argparse
3. Add error handling
4. Test with real inputs
5. Make executable: `chmod +x scripts/*.py`

**For SKILL.md**:
1. Document workflow
2. Link to existing code (don't duplicate)
3. Include script usage table
4. Add trigger phrases

**For references/**:
1. Detailed patterns
2. Edge cases and gotchas
3. Links to source implementation

### Step 7: Validate and Test

```bash
# Validate structure
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_skill.py .claude/skills/{skill-name}

# Test scripts (if tool/hybrid)
python .claude/skills/{skill-name}/scripts/example.py --help
```

### Step 8: Show Completion

```
✅ Created skill: {skill-name}

Type: {type}

Converted from:
- {source_file1}
- {source_file2}

Files created:
- .claude/skills/{skill-name}/SKILL.md
- .claude/skills/{skill-name}/scripts/{script}.py (if applicable)
- .claude/skills/{skill-name}/references/{ref}.md

References existing code:
- {file:lines} (linked, not duplicated)

Validation: ✅ Passed

Usage:
- Load: Use Skill tool with "{skill-name}"
- In agents: skills: {skill-name}

Next steps:
1. Test with requests that used the original code
2. Verify skill references existing code correctly
3. Create an agent: /skillmaker:skill-cover
```

## Scriptability Decision Matrix

| Code Characteristic | Action |
|---------------------|--------|
| Same function called repeatedly | → Script it |
| Complex algorithm | → Script it |
| File format manipulation | → Script it |
| External API calls | → Script it |
| Decision-making logic | → Document it |
| Context-dependent choices | → Document it |
| Tribal knowledge | → Document it |

## Example Conversion

```
User: Convert our auth middleware to a skill

[Grep for auth-related code]
Found: src/middleware/auth.ts, src/utils/jwt.ts

[Read files]

Analysis:
- JWT generation/validation: Deterministic, repeatable → Could script
- But: Already works in codebase, no need to extract
- Decision logic: Which routes need auth → Document
- Implicit knowledge: Token expiry strategy → Document

Recommendation: Knowledge Skill

Because:
- Code already works (no need to extract)
- Value is in DOCUMENTING the patterns
- Different contexts need different decisions

Structure:
auth-patterns/
├── SKILL.md          # When/how to apply auth
└── references/
    ├── implementation.md  # Links to actual code
    └── security.md        # Security guidelines

SKILL.md will REFERENCE auth.ts, not duplicate it.
```

## Important Notes

- **Reference, don't duplicate** - Link to existing code
- **Extract scripts only if needed** - Working code doesn't always need extraction
- **Capture implicit knowledge** - Document the WHY
- **Use init_skill.py** - Proper structure
- **Validate before done** - Catch issues early
