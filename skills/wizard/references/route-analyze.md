# ANALYZE Route

Context-aware project analysis combining validation with design principles.

## Approach: Adaptive Analysis

Do NOT follow a fixed checklist. Adapt to project type.

## Step 1: Understand Context

- Project type: plugin, skill library, agent suite?
- Primary purpose?
- Complexity level: simple/standard/advanced?

## Step 2: Run Base Validation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

## Step 3: Run Functional Tests

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/functional-test.py      # Auto-detect
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/functional-test.py --all  # Test all
```

**CRITICAL**: Fix failures before proceeding.

## Step 4: Analyze Based on Project Type

| Project Type | Focus Areas |
|--------------|-------------|
| **Skill library** | Skill design, SKILL.md quality, references separation |
| **Agent suite** | Orchestration patterns, context isolation, Skill() usage |
| **Full plugin** | All above + hookify, deployment readiness |
| **MCP integration** | Gateway patterns, isolation strategy |

## Step 5: Load Relevant Principles

- skills/ directory → `Skill("skillmaker:skill-design")`
- agents/ directory → `Skill("skillmaker:orchestration-patterns")`
- hooks/ directory → Hookify compliance check
- MCP usage → `Skill("skillmaker:mcp-gateway-patterns")`

## Step 6: Critical Analysis

Load: `Skill("skillmaker:critical-analysis-patterns")`

### 6a: Apply 6 Core Questions

| Question | What to Ask |
|----------|-------------|
| 존재 정당성 | "이것이 왜 여기 있는가?" |
| 의도-구현 정합성 | "이름과 역할이 일치하는가?" |
| 일관성 | "비슷한 것들이 다르게 처리되는가?" |
| 미사용 기능 | "선언했지만 안 쓰는가?" |
| 복잡성 정당화 | "이 복잡성이 필요한가?" |
| Fundamental Redesign | "시스템 자체가 잘못된 것은 아닌가?" |

### 6b: Canonical Pattern Comparison

| Domain | Skill | Compare Against |
|--------|-------|-----------------|
| MCP | mcp-gateway-patterns | daemon-shared-server.md |
| Skill | skill-design | structure-rules.md |
| Agent | orchestration-patterns | context-isolation.md |
| Hooks | hook-templates | full-examples.md |

**Verdict**: Deficient → Recommend | Respectable → Acknowledge | Superior → Learn

## Step 7: Solution Synthesis (PROACTIVE)

> HOOKIFIED: `PostToolUse:Task → solution-synthesis-gate.py`

### 7a: Load Skills for Problems Found

| Problem | Action |
|---------|--------|
| MCP/Gateway issues | `Skill("mcp-gateway-patterns")` → Read daemon-shared-server.md |
| Skill design issues | `Skill("skill-design")` → Read structure-rules.md |
| Agent context issues | `Skill("orchestration-patterns")` → Read context-isolation.md |

### 7b: Extract and Present Solutions

**DO**: Load skill → Read references → Extract concrete solution
**DON'T**: Just say "load this skill"

### 7c: Known Solutions

| Problem | Solution | Command |
|---------|----------|---------|
| Subagent cannot access MCP | Daemon SSE | `python -m mcp_server --sse` |
| Long SKILL.md | Progressive disclosure | Create `references/` |
| Document enforcement fails | Hookify | PreToolUse hooks |

### 7d: Radical Solutions 🔥

When conservative solutions feel like band-aids:
- "Is the system structure wrong?"
- "If there's a 10x better method, what is it?"

### 7e: Execution Proposal

```yaml
AskUserQuestion:
  question: "Apply extracted solutions?"
  header: "Execute"
  multiSelect: true
  options:
    - label: "Apply All (Recommended)"
    - label: "Analysis only"
```

## Output Format

```markdown
## 프로젝트 분석: {project-name}

### 프로젝트 이해
- 타입: {type}
- 복잡도: {level}
- 주요 목적: {purpose}

### 검증 결과
{validation output}

### 철학적 분석
| # | 발견 | 질문 | 심각도 |
|---|------|------|--------|

### 해결책 종합
[Concrete solutions with implementation steps]

### 실행 제안
[Actionable items with commands]
```

## Key Difference from VALIDATE

| VALIDATE | ANALYZE |
|----------|---------|
| Fixed script | Adaptive |
| Schema only | Design principles |
| Pass/fail | Nuanced insights |
