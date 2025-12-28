---
description: Create skills, agents, or commands with smart routing
argument-hint: "describe what to create (e.g., 'API skill', 'database agent')"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill", "AskUserQuestion"]
---

# Complexity-Based Skill Loading

Before routing, detect complexity level from input and load appropriate skills:

| Level | Keywords | Auto-Load Skills |
|-------|----------|------------------|
| **Simple** | simple, basic, 단순, 기본 | skill-design |
| **Standard** | standard, normal, 일반 | skill-design, orchestration-patterns, hook-templates |
| **Advanced** | advanced, complex, enhanced, serena, mcp, 고급 | ALL pattern skills |

If no complexity keyword found, ask:

```yaml
AskUserQuestion:
  question: "프로젝트 복잡도를 선택하세요"
  header: "Complexity"
  options:
    - label: "Simple"
      description: "단일 skill, 기본 agent"
    - label: "Standard (Recommended)"
      description: "Multi-skill, Hook 포함"
    - label: "Advanced"
      description: "Serena Gateway + claude-mem + workflow gates"
```

After selection, load skills using Skill tool:
- Simple: `Skill("skillmaker:skill-design")`
- Standard: + `Skill("skillmaker:orchestration-patterns")`, `Skill("skillmaker:hook-templates")`
- Advanced: + `Skill("skillmaker:mcp-gateway-patterns")`, `Skill("skillmaker:skill-activation-patterns")`

---

# Routing

Analyze input. Match first pattern:

| Pattern | Route |
|---------|-------|
| `init\|new.*project\|새.*프로젝트\|시작\|setup\|marketplace.*create\|마켓플레이스.*만들` | => PROJECT_INIT |
| `skill.*create\|create.*skill\|스킬.*만들` | => SKILL |
| `convert\|from.*code\|skillization\|변환` | => SKILL_FROM_CODE |
| `agent\|에이전트\|subagent` | => AGENT |
| `command\|workflow\|명령어` | => COMMAND |
| `analyze\|분석\|리뷰\|review` | => ANALYZE |
| `validate\|check\|검증\|상태\|status` | => VALIDATE |
| `publish\|deploy\|배포` | => PUBLISH |
| `register\|local\|등록\|로컬` | => LOCAL_REGISTER |
| no match / empty | => MENU |

**CRITICAL RULE**: When routing to VALIDATE, you MUST execute the actual validation script.
DO NOT perform "visual analysis" or "manual inspection" - ALWAYS run the script.

---

# MENU

```yaml
AskUserQuestion:
  question: "What would you like to do?"
  header: "Action"
  options:
    - label: "New Project"
      description: "Initialize new plugin/marketplace project"
    - label: "Skill"
      description: "Create new skill"
    - label: "Agent"
      description: "Create subagent with skills"
    - label: "Command"
      description: "Create workflow command"
    - label: "Analyze"
      description: "Comprehensive analysis (validation + design principles)"
    - label: "Validate"
      description: "Quick schema/path validation only"
    - label: "Publish"
      description: "Deploy to marketplace (after testing)"
```

Route: New Project=>PROJECT_INIT, Skill=>SKILL, Agent=>AGENT, Command=>COMMAND, Analyze=>ANALYZE, Validate=>VALIDATE, Publish=>PUBLISH

---

# PROJECT_INIT

**Purpose**: Initialize a new plugin project with clear intent understanding.

## Step 1: Understand Intent

```yaml
AskUserQuestion:
  question: "What is your goal?"
  header: "Purpose"
  options:
    - label: "Marketplace Distribution (Recommended)"
      description: "Create a marketplace that others can install via 'claude marketplace add'"
    - label: "Personal Use Only"
      description: "Local plugin for your own use (simpler setup)"
```

## Step 2a: If Marketplace Distribution

```yaml
AskUserQuestion:
  question: "Do you have a GitHub account/organization?"
  header: "GitHub"
  options:
    - label: "Yes - Use GitHub"
      description: "Deploy via GitHub repository (recommended for sharing)"
    - label: "No - Local Path"
      description: "Users will need to clone/download manually"
```

**If GitHub**: Ask for owner/repo format:
```yaml
AskUserQuestion:
  question: "GitHub repository name? (format: owner/repo)"
  header: "Repo"
```

## Step 3: Create Project Structure

### For Marketplace Distribution (GitHub):

```
{project-name}/
├── .claude-plugin/
│   ├── marketplace.json    ← Registry file
│   └── plugin.json         ← Plugin metadata
├── .claude/
│   └── skills/
│       └── skill-rules.json  ← (Optional) Plugin-level skill activation
├── skills/                 ← Skill directories
├── commands/              ← Command .md files
├── agents/                ← Agent .md files
├── hooks/
│   └── hooks.json         ← Hook file (including UserPromptSubmit for skill-activation)
└── scripts/               ← Hook scripts
```

**Note**: Plugins with 2+ related skills **SHOULD** include skill-activation to help users discover relevant skills. See `skill-activation-patterns` for details.

**marketplace.json** (GitHub source):
```json
{
  "name": "{project-name}-marketplace",
  "owner": {"name": "{user}"},
  "metadata": {
    "description": "...",
    "version": "1.0.0"
  },
  "plugins": [{
    "name": "{plugin-name}",
    "description": "...",
    "source": {"source": "github", "repo": "{owner/repo}"},
    "version": "1.0.0",
    "skills": ["./skills/{skill-name}"],
    "commands": ["./commands/{command-name}.md"],
    "agents": ["./agents/{agent-name}.md"]
  }]
}
```

### For Personal Use:

**marketplace.json** (local source):
```json
{
  "name": "{project-name}-marketplace",
  "owner": {"name": "{user}"},
  "plugins": [{
    "name": "{plugin-name}",
    "source": "./",
    "skills": ["./skills/{skill-name}"],
    "agents": ["./agents/{agent-name}.md"]
  }]
}
```

## Step 4: Critical Explanation

Show this explanation to user:

```markdown
## 프로젝트 구조 이해하기

### 마켓플레이스 vs 플러그인
- **마켓플레이스**: 플러그인 목록을 제공하는 레지스트리
- **플러그인**: 실제 기능이 있는 코드

### Source 설정의 의미
| Source 타입 | 의미 | 사용 시점 |
|------------|------|----------|
| `"./"` | 로컬 파일 사용 | 개발/테스트 중 |
| `{"source": "github", ...}` | GitHub에서 다운로드 | 배포 후 |

### ⚠️ 주의사항
- **GitHub source 사용 시**: 반드시 GitHub 리포지토리에 파일을 푸시해야 함
- **로컬 테스트 시**: `source: "./"` 권장
- **배포 시**: GitHub source로 변경 후 푸시
```

## Step 5: Post-Init Validation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

**MUST pass before proceeding.**

## Step 6: Next Steps

```markdown
## 다음 단계

1. **컴포넌트 생성**:
   - `/wizard skill` - 스킬 생성
   - `/wizard agent` - 에이전트 생성
   - `/wizard command` - 커맨드 생성

2. **(Optional) Skill Auto-Activation 설정** (2개 이상 스킬이 있는 경우):
   - `Skill("skillmaker:skill-activation-patterns")` 참고
   - `.claude/skills/skill-rules.json` 생성
   - `hooks/hooks.json`에 UserPromptSubmit hook 추가
   - 플러그인이 자체 스킬을 키워드 기반으로 추천

3. **로컬 테스트**:
   - `/wizard register` - 로컬 등록
   - Claude Code 재시작
   - 기능 테스트

4. **배포** (GitHub source 사용 시):
   - `git push origin main`
   - `/wizard publish`
```

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

3. If "Unsure": ask freedom level (High=>Knowledge, Medium=>Hybrid, Low=>Tool)

4. Launch:
```
Task: skill-architect
Pass: description, skill_type
```

5. **Post-creation validation** (MANDATORY - BLOCKING):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --json
```

**CRITICAL: This step MUST pass before proceeding. DO NOT skip.**

- **If status="fail"**:
  1. Show ALL errors to user
  2. Ask: "자동 수정을 실행할까요?" (Run auto-fix?)
  3. If yes: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --fix`
  4. Re-run validation after fix
  5. **LOOP until status != "fail"** - DO NOT proceed with errors
  6. If user declines fix: **STOP HERE** - show "검증 실패. 수동으로 오류를 수정한 후 다시 시도하세요."

- **If status="warn"**: Show warnings, ask to continue (user may proceed)

- **If status="pass"**: Show "[PASS] 검증 통과" and continue

6. After validation passes, show next steps:
```markdown
## Next Steps

1. **로컬 등록** (테스트용):
   `/wizard register` 실행하여 로컬 플러그인으로 등록

2. **테스트**:
   - Claude Code 재시작
   - 백그라운드 에이전트로 기능 테스트
   - 정상 작동 확인

3. **마켓플레이스 배포** (테스트 완료 후):
   `/wizard publish` 실행
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

4. **Post-creation validation** (MANDATORY - BLOCKING):
   Same as SKILL step 5. **MUST pass before proceeding.**

5. After validation passes, show next steps (same as SKILL step 6)

---

# AGENT

1. Check: `Glob .claude/skills/*/SKILL.md`

2. If none: "No skills found. Create skill first?" => Yes: goto SKILL

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

6. **Post-creation validation** (MANDATORY - BLOCKING):
   Same as SKILL step 5. **MUST pass before proceeding.**

7. After validation passes, show next steps (same as SKILL step 6)

---

# COMMAND

1. Check: `Glob .claude/agents/*.md`

2. If none: "No agents found. Create agent first?" => Yes: goto AGENT

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

6. **Post-creation validation** (MANDATORY - BLOCKING):
   Same as SKILL step 5. **MUST pass before proceeding.**

7. After validation passes, show next steps (same as SKILL step 6)

---

# ANALYZE

**Purpose**: Context-aware project analysis combining validation with design principles review.

## Approach: Adaptive Analysis

Do NOT follow a fixed checklist. Instead:

1. **Understand Context First**
   - What type of project is this? (plugin, skill library, agent suite)
   - What is its primary purpose?
   - What complexity level? (simple/standard/advanced)

2. **Run Base Validation**
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
   ```

3. **Run Functional Tests** (MANDATORY)

   After validation passes, run context-aware functional tests:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/functional-test.py      # Auto-detect changes
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/functional-test.py --all  # Test everything
   ```

   | Context | Test Scope | Command |
   |---------|------------|---------|
   | **New plugin** | All components | `--all` |
   | **Modified** | Changed files only | (auto-detect) |
   | **Debugging** | Specific component | `--component skills/my-skill` |

   **Static tests** (automated):
   - Skill structure & registration
   - Agent dependency resolution
   - Frontmatter validation

   **Runtime tests** (require Claude Code session):
   - `Skill("plugin:skill-name")` load test
   - `Task` agent execution with dependencies
   - Hook trigger verification

   **[!] CRITICAL**: If functional tests fail, fix issues before proceeding.

4. **Analyze Based on Project Type**

   | Project Type | Focus Areas |
   |--------------|-------------|
   | **Skill library** | Skill design principles, SKILL.md quality, references separation |
   | **Agent suite** | Orchestration patterns, context isolation, Skill() tool usage |
   | **Full plugin** | All above + hookify compliance, deployment readiness |
   | **MCP integration** | Gateway patterns, isolation strategy, subprocess safety |

5. **Check Relevant Principles Only**

   Load skills dynamically based on what's relevant:
   - If has skills/ directory → `Skill("skillmaker:skill-design")` analysis
   - If has agents/ directory → `Skill("skillmaker:orchestration-patterns")` analysis
   - If has hooks/ directory → Hookify compliance check
   - If uses MCP → `Skill("skillmaker:mcp-gateway-patterns")` analysis

6. **Critical Analysis (철학적 분석)** - NEW

   After technical validation, load critical analysis:
   ```
   Skill("skillmaker:critical-analysis-patterns")
   ```

   Apply the **5 Core Questions** to each component:

   | Question | What to Ask |
   |----------|-------------|
   | 존재 정당성 | "이것이 왜 여기 있는가? 제거하면 뭐가 깨지나?" |
   | 의도-구현 정합성 | "이름과 역할이 일치하는가? 문서와 코드가 동기화되어 있는가?" |
   | 일관성 | "비슷한 것들이 다르게 처리되고 있지 않은가?" |
   | 미사용 기능 | "선언했지만 안 쓰는 것이 있는가?" |
   | 복잡성 정당화 | "이 복잡성이 정말 필요한가? 더 단순한 대안은?" |

   **Red Flags to Detect**:
   - agents/에 있지만 tools: [] → "에이전트인가 문서인가?"
   - 90%+ 유사한 워크플로우 분리 → "통합 안 하는 이유가 있는가?"
   - 책임이 중복되는 컴포넌트 → "경계가 명확한가?"
   - 구 아키텍처 문서 잔재 → "현재 아키텍처를 반영하는가?"

   **Output Format**:
   ```markdown
   ### 철학적 분석

   | 발견 | 질문 | 제안 |
   |-----|-----|-----|
   | {무엇을 발견했는가} | {왜?} | {대안} |
   ```

7. **Contextual Improvement Suggestions**

   Based on actual findings, suggest:
   - Architecture improvements specific to this project
   - Missing patterns that would benefit this use case
   - Complexity reduction opportunities

## Output Format

```markdown
## 프로젝트 분석: {project-name}

### 프로젝트 이해
- 타입: {detected type}
- 복잡도: {simple/standard/advanced}
- 주요 목적: {purpose}

### 검증 결과
{validation output}

### 설계 원칙 분석
{context-specific analysis based on project type}

### 개선 제안
{specific, actionable suggestions based on actual findings}
```

## Key Difference from VALIDATE

| VALIDATE | ANALYZE |
|----------|---------|
| Fixed script execution | Adaptive to project type |
| Schema/path checking only | Design principles included |
| Pass/fail binary | Nuanced insights |
| Technical correctness | Architectural quality |

---

# VALIDATE

**[!] MANDATORY: You MUST execute the actual validation script. NO exceptions.**
**DO NOT perform "visual analysis", "manual inspection", or "eye-check". ALWAYS run the script.**

## Validation Checks Performed

The validation script performs **comprehensive multi-layer checking**:

| Layer | Check | Description |
|-------|-------|-------------|
| Schema | Required fields | `name`, `owner`, `plugins` exist |
| Schema | Source format | `{"source": "github", ...}` NOT `{"type": "github", ...}` |
| Schema | Path formats | Skills=directories, Commands/Agents=.md files |
| **Path Resolution** | **E016** | **Path mismatch - file exists but Claude looks elsewhere** |
| **Path Resolution** | **E017** | **marketplace.json location causes path issues** |
| **Source Mismatch** | **E016** | **GitHub source used but local files exist** |
| **Remote Mismatch** | **E018** | **Git remote ≠ marketplace.json source repo** |
| **Remote Access** | **E019** | **External GitHub repo not accessible** |
| **Remote Files** | **E020** | **External repo missing required files** |
| **Hookify** | **W028** | **Enforcement keywords (MUST/REQUIRED/CRITICAL) without hooks** |
| **Skill Design** | **W029** | **Skill missing frontmatter (name, description, allowed-tools)** |
| **Skill Design** | **W031** | **Skill content exceeds 500 words (progressive disclosure)** |
| **Skill Design** | **W032** | **Skill has long sections but no references/ directory** |
| **Agent Patterns** | **W030** | **Agent missing frontmatter (name, description, tools, skills)** |
| **Skill Calling** | **W033** | **Agent/command declares skills but no Skill() usage found** |
| **Workflow** | **W034** | **Multi-stage workflow without per-stage skill loading** |
| Edge Case | Null/empty source | Catches `source: null`, `source: ""`, `source: {}` |
| Edge Case | Wrong key names | Detects `"type"` instead of `"source"` |
| Pattern | Official patterns | Validates against official Claude plugin structure |
| CLI | Double-validation | Runs `claude plugin validate` if available |

## Critical Error Codes (E016-E020)

### E016: Path Resolution Mismatch

**증상**: 마켓플레이스는 설치되지만 플러그인이 로드되지 않음

**원인 1**: marketplace.json이 비표준 위치에 있어서 경로 해석이 잘못됨
```
marketplace.json 위치: some-dir/marketplace.json
경로: ./commands/foo.md
Claude가 찾는 위치: some-dir/commands/foo.md (존재하지 않음)
실제 파일 위치: commands/foo.md (프로젝트 루트)
```

**원인 2**: GitHub source를 사용하지만 로컬 파일만 존재
```
source: {"source": "github", "repo": "owner/repo"}
로컬에 파일 존재: commands/foo.md, agents/bar.md
문제: Claude가 GitHub에서 다운로드하려 하지만 리포지토리가 비어있거나 없음
```

**해결 방법**:
- marketplace.json을 `.claude-plugin/` 또는 프로젝트 루트로 이동
- 또는 GitHub 리포지토리에 파일 푸시
- 또는 source를 `"./"` 로 변경 (로컬 개발용)

### E017: marketplace.json Location Issue

**증상**: 경로 해석이 예상과 다르게 동작

**해결 방법**:
```bash
# 자동 수정 실행
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --fix
```

### E018: Git Remote ≠ Source Mismatch

**증상**: 현재 Git 리모트와 marketplace.json의 source 리포지토리가 다름

**원인**:
```
현재 리모트: github.com/user-a/my-plugin
marketplace.json source: {"source": "github", "repo": "user-b/other-repo"}
```

**해결 방법**:
1. marketplace.json의 source를 현재 리모트와 일치시키기
2. 또는 다른 리포지토리로 푸시하려면 리모트 변경

### E019: External Repo Not Accessible

**증상**: marketplace.json에서 참조하는 외부 GitHub 리포지토리에 접근 불가

**원인**:
- 리포지토리가 존재하지 않음
- 리포지토리가 private이고 접근 권한 없음
- GitHub CLI (`gh`)가 인증되지 않음

**해결 방법**:
```bash
# 리포지토리 존재 확인
gh repo view owner/repo

# 리포지토리 생성 (필요시)
gh repo create owner/repo --public

# GitHub CLI 인증 (필요시)
gh auth login
```

### E020: External Repo Missing Files

**증상**: 외부 리포지토리에 marketplace.json에서 선언한 파일이 없음

**원인**:
```
marketplace.json에 선언: ./commands/analyze.md
외부 리포지토리: commands/analyze.md 파일 없음
```

**해결 방법**:
1. 외부 리포지토리에 누락된 파일 푸시
2. 또는 marketplace.json에서 해당 경로 제거
3. Multi Repo 대신 Single Repo 모델 사용 고려

### W028: Hookify Required (Warning)

**증상**: 스킬/에이전트 파일에 강제 키워드(MUST, REQUIRED, CRITICAL)가 있지만 hooks.json이 없음

**원인**:
```
skills/my-skill/SKILL.md: "MUST use Skill() tool"
agents/my-agent.md: "CRITICAL: Never read files directly"
→ hooks/hooks.json 없음
```

**문제**: 문서 기반 강제는 **무의미**합니다. 에이전트는 이를 무시합니다.

**해결 방법**:
1. `hooks/hooks.json` 생성
2. PreToolUse/PostToolUse 훅으로 행동 강제
3. 또는 강제 키워드를 "should", "recommend"로 변경

**예시**:
- ❌ SKILL.md: "MUST use Skill() tool" → 에이전트가 무시함
- ✅ PreToolUse hook: Read/Grep/Glob 시 skill 파일 접근 경고

### W029: Skill Frontmatter Missing (Warning)

**증상**: 스킬의 SKILL.md에 필수 frontmatter 필드가 누락됨

**필수 필드**:
```yaml
---
name: skill-name
description: What this skill does
allowed-tools: ["Read", "Write", "Bash"]
---
```

**문제**: frontmatter가 없으면 Claude Code가 스킬을 올바르게 로드하지 못할 수 있음

**해결 방법**: SKILL.md 상단에 YAML frontmatter 추가

### W030: Agent Frontmatter Missing (Warning)

**증상**: 에이전트 .md 파일에 필수 frontmatter 필드가 누락됨

**필수 필드**:
```yaml
---
name: agent-name
description: What this agent does
tools: ["Read", "Write", "Task"]
skills: skill-name, other-skill
---
```

**문제**: frontmatter가 없으면 Task 에이전트로 사용 시 올바르게 작동하지 않음

**해결 방법**: 에이전트 .md 상단에 YAML frontmatter 추가

### W031: Skill Content Too Long (Warning)

**증상**: SKILL.md 핵심 콘텐츠가 500단어를 초과함

**원인**: Progressive disclosure 패턴 위반
```
SKILL.md: 1200 words (권장: <500)
```

**문제**: 긴 스킬은 컨텍스트를 과도하게 소비하고 핵심 지침이 묻힘

**해결 방법**:
1. 핵심 지침만 SKILL.md에 유지
2. 상세 내용을 `references/` 디렉토리로 이동
3. SKILL.md에서 `Read("references/details.md")` 로 참조

### W032: Missing references/ Directory (Warning)

**증상**: SKILL.md에 긴 섹션이 있지만 references/ 디렉토리가 없음

**패턴**: skill-design은 상세 내용 분리를 권장
```
skill-name/
├── SKILL.md         # 핵심 지침 (<500 words)
└── references/      # 상세 문서 (on-demand 로드)
    ├── details.md
    └── examples.md
```

**해결 방법**: `references/` 디렉토리 생성 후 상세 내용 이동

### W033: Missing Skill() Tool Usage (Warning)

**증상**: 에이전트/커맨드가 스킬을 선언하거나 참조하지만 Skill() 호출이 없음

**원인 1**: Frontmatter에 skills 선언했지만 본문에 Skill() 패턴 없음
```yaml
---
skills: skill-design, orchestration-patterns  # 선언됨
---
# Agent Body
에이전트가 스킬을 사용하는 방법에 대한 언급 없음  # Skill() 없음
```

**원인 2**: 커맨드가 스킬 이름을 언급하지만 로딩 패턴 없음

**해결 방법**:
1. **선언적 (frontmatter)**: 이미 `skills:` 선언 시 자동 로딩됨 - 경고 무시 가능
2. **명령적 (body)**: 명시적 로딩 추가
   ```
   Load skill: `Skill("skillmaker:skill-design")`
   ```

**참고**: frontmatter의 `skills:` 선언은 에이전트 시작 시 자동 로딩되므로 명시적 Skill() 불필요할 수 있음.

### W034: Multi-Stage Workflow Without Per-Stage Skill Loading (Warning)

**증상**: 다단계 워크플로우(3개 이상)가 있지만 단계별 Skill() 호출이 부족함

**원인**:
```markdown
## Phase 1: 탐색
...코드 탐색 로직...

## Phase 2: 분석
...분석 로직...

## Phase 3: 수정
...수정 로직...

## Phase 4: 검증
...검증 로직...
```
→ 4단계 워크플로우이지만 Skill() 호출 0개

**문제**:
- 각 단계마다 다른 컨텍스트가 필요할 수 있음
- 모든 스킬이 한번에 로딩되면 컨텍스트 비효율

**해결 방법**:
1. **단계별 스킬 로딩**:
   ```markdown
   ## Phase 1: 탐색
   Load: `Skill("skillmaker:orchestration-patterns")`

   ## Phase 2: 분석
   Load: `Skill("skillmaker:skill-design")`
   ```

2. **또는 Hookify**:
   - PreToolUse hook으로 단계 전환 시 스킬 자동 로딩
   - 워크플로우 상태 추적 후 적절한 스킬 제안

## Execution Steps

1. **ALWAYS execute this command first** (NO SKIPPING):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

2. **Show the ACTUAL output** from the script to the user.
   - DO NOT paraphrase or summarize without showing actual output
   - Include: errors, warnings, passed checks, and summary

3. **If status="fail" (errors exist)**:
   - Show ALL errors from script output
   - Ask: "자동 수정을 실행할까요?" (Run auto-fix?)
   - If yes: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --fix`
   - Re-run validation and show results

4. **If status="warn" (warnings only)**: Show warnings, explain they won't block deployment

5. **If status="pass"**: Show "[PASS] 검증 통과 - 배포 준비 완료"

## Error Handling

모든 스키마 오류는 **자동 수정** 가능:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --fix
```

자동 수정 항목:
- 잘못된 `source` 형식 => 올바른 형식으로 변환
- 잘못된 `repository` 객체 => 문자열로 변환
- 금지된 필드 (`components`, `repo` at plugin level) => 제거
- 누락된 `.md` 확장자 => 추가
- 잘못된 `.md` 확장자 (skills) => 제거

**FORBIDDEN BEHAVIORS:**
- [X] Reading files manually and reporting "looks good"
- [X] Checking file existence without running the script
- [X] Saying "based on previous analysis" without running script NOW
- [X] Skipping the script execution for any reason

---

# LOCAL_REGISTER

Register current project as local plugin for testing.

1. Get current project path: `pwd`

2. Check if `.claude-plugin/marketplace.json` exists
   - If not: "Not a plugin project. Create marketplace.json first?"

3. Run registration script:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/register_local.py --path $(pwd)
```

4. Show result:
```markdown
## 로컬 등록 완료

플러그인이 로컬에 등록되었습니다.

**다음 단계:**
1. Claude Code 재시작 (변경사항 적용)
2. 기능 테스트 진행
3. 테스트 완료 후: `/wizard publish`
```

---

# PUBLISH

Deploy to marketplace after testing.

## Pre-Deployment Checklist

**[!] CRITICAL: Understand the deployment model before proceeding**

### Deployment Models

| Model | Source Setting | 마켓플레이스 리포지토리 | 플러그인 리포지토리 |
|-------|---------------|----------------------|-------------------|
| **Single Repo** | `"./"` | GitHub에 푸시 | 마켓플레이스와 동일 |
| **Multi Repo** | `{"source": "github", ...}` | GitHub에 푸시 | 별도 리포지토리 필요 |

### Single Repo (Recommended for most cases)
- 마켓플레이스와 플러그인 코드가 같은 리포지토리
- `source: "./"` 사용
- 설치: `claude marketplace add owner/repo`

### Multi Repo (Advanced)
- 마켓플레이스와 플러그인 코드가 별도 리포지토리
- `source: {"source": "github", "repo": "owner/plugin-repo"}` 사용
- **주의**: 마켓플레이스와 플러그인 리포지토리 모두 푸시 필요!

---

## Step 1: Determine Deployment Type

```yaml
AskUserQuestion:
  question: "배포 방식을 선택하세요"
  header: "배포 방식"
  options:
    - label: "Single Repo (Recommended)"
      description: "하나의 GitHub 리포지토리에 모든 코드 포함"
    - label: "Multi Repo (Advanced)"
      description: "마켓플레이스와 플러그인을 별도 리포지토리로 분리"
```

## Step 2: Run Validation

**MANDATORY - NO EXCEPTIONS**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

**If E016 (GitHub source with local files) is detected**:
```markdown
⚠️ 현재 GitHub source를 사용하지만 파일이 GitHub에 푸시되지 않았습니다.

**해결 방법 선택:**
1. **Single Repo로 변경** (권장): source를 "./"로 변경
2. **파일 푸시**: GitHub 리포지토리에 파일 푸시 후 재시도
```

## Step 3: Configure Source Based on Choice

### If Single Repo:
1. Update marketplace.json:
```json
"source": "./"
```

2. Ensure GitHub repo exists:
```bash
gh repo view $(git remote get-url origin) || gh repo create
```

3. Push all files:
```bash
git add -A && git commit -m "Prepare for deployment" && git push
```

### If Multi Repo:
1. Verify plugin repo exists and has files:
```bash
gh api repos/{owner}/{plugin-repo}/contents --jq '.[].name'
```

2. Update marketplace.json:
```json
"source": {"source": "github", "repo": "{owner}/{plugin-repo}"}
```

3. Push marketplace repo:
```bash
git push origin main
```

## Step 4: Final Validation

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

**MUST pass with status="pass" before proceeding.**

## Step 5: Test Installation

```markdown
## 설치 테스트

다른 터미널에서 테스트:
\`\`\`bash
claude marketplace add {owner}/{marketplace-repo}
\`\`\`

플러그인 확인:
\`\`\`bash
claude /plugin
# {plugin-name}@{marketplace-name} 이 표시되어야 함
\`\`\`
```

## Step 6: Success Message

```markdown
## 배포 완료!

**사용자 설치 방법:**
\`\`\`bash
claude marketplace add {owner}/{marketplace-repo}
\`\`\`

**활성화:**
\`\`\`bash
claude /plugin
# → {plugin-name}@{marketplace-name} 선택
\`\`\`
```

---

## Legacy Deployment Steps (for reference)

1. Check local registration:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --json | grep "not_registered"
```

7. If unregistered items exist:
```yaml
AskUserQuestion:
  question: "어떤 항목을 마켓플레이스에 등록할까요?"
  header: "항목"
  multiSelect: true
  options: [list of unregistered items]
```

8. Register selected items to marketplace.json:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/register_marketplace.py --items {selected}
```

9. Run final validation (MANDATORY):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
   - **MUST pass with no errors before proceeding**

10. If GitHub deployment, verify source format:
```yaml
AskUserQuestion:
  question: "GitHub 리포지토리를 사용하나요?"
  header: "Source"
  options:
    - label: "Yes - GitHub 배포"
      description: "GitHub에 푸시하여 배포"
    - label: "No - 로컬 경로 유지"
      description: "./ 형식 유지"
```

11. If GitHub: Update source in marketplace.json:
```json
"source": {"source": "github", "repo": "OWNER/REPO"}
```
**WARNING**: Use `"source": "github"`, NOT `"type": "github"`!

12. Show result:
```markdown
## 마켓플레이스 등록 완료

다음 항목이 marketplace.json에 등록되었습니다:
- {registered items}

**배포 방법:**
1. 변경사항 커밋: `git add . && git commit -m "Add new items"`
2. GitHub에 푸시: `git push`
3. Claude Code 검증: `claude plugin validate .`
4. 사용자들이 설치 가능: `/plugin install {plugin}@{marketplace}`
```
