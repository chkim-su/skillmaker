---
description: Create skills, agents, or commands with smart routing
argument-hint: "describe what to create (e.g., 'API skill', 'database agent')"
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob", "Task", "Skill", "AskUserQuestion"]
---

# Routing

Analyze input. Match first pattern:

| Pattern | Route |
|---------|-------|
| `skill.*create\|create.*skill\|스킬.*만들` | => SKILL |
| `convert\|from.*code\|skillization\|변환` | => SKILL_FROM_CODE |
| `agent\|에이전트\|subagent` | => AGENT |
| `command\|workflow\|명령어` | => COMMAND |
| `validate\|check\|검증\|분석\|상태\|status\|analyze` | => VALIDATE |
| `publish\|deploy\|배포` | => PUBLISH |
| `register\|local\|등록\|로컬` | => LOCAL_REGISTER |
| no match / empty | => MENU |

**CRITICAL RULE**: When routing to VALIDATE, you MUST execute the actual validation script.
DO NOT perform "visual analysis" or "manual inspection" - ALWAYS run the script.

---

# MENU

```yaml
AskUserQuestion:
  question: "What to create?"
  header: "Type"
  options:
    - label: "Skill"
      description: "Create new skill"
    - label: "Agent"
      description: "Create subagent with skills"
    - label: "Command"
      description: "Create workflow command"
    - label: "Validate"
      description: "Check for errors"
    - label: "Publish"
      description: "Deploy to marketplace (after testing)"
```

Route: Skill=>SKILL, Agent=>AGENT, Command=>COMMAND, Validate=>VALIDATE, Publish=>PUBLISH

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
| Edge Case | Null/empty source | Catches `source: null`, `source: ""`, `source: {}` |
| Edge Case | Wrong key names | Detects `"type"` instead of `"source"` |
| Pattern | Official patterns | Validates against official Claude plugin structure |
| CLI | Double-validation | Runs `claude plugin validate` if available |

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

**[!] CRITICAL FORMAT REQUIREMENTS - Review before deployment:**

### 1. GitHub Source Format
```json
// [PASS] CORRECT
"source": {"source": "github", "repo": "owner/repo"}

// [X] WRONG - "type" instead of "source"
"source": {"type": "github", "repo": "owner/repo"}
```

### 2. Skills Path Format
```json
// [PASS] CORRECT - skills are directories
"skills": ["./skills/my-skill"]

// [X] WRONG - skills are NOT .md files
"skills": ["./skills/my-skill.md"]
```

### 3. Commands/Agents Path Format
```json
// [PASS] CORRECT - commands and agents ARE .md files
"commands": ["./commands/my-cmd.md"],
"agents": ["./agents/my-agent.md"]
```

### 4. Agent Frontmatter Required Fields
```yaml
---
name: agent-name
description: What this agent does
tools: ["Read", "Write", "Bash"]  # ← REQUIRED!
---
```

---

## Deployment Steps

1. Check local registration:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_local_registration.py --path $(pwd)
```

2. If not registered locally:
```markdown
[!] 로컬 등록이 필요합니다.

먼저 `/wizard register`를 실행하여 로컬에서 테스트하세요.
```
=> Exit

3. Ask testing confirmation:
```yaml
AskUserQuestion:
  question: "로컬 테스트를 완료했나요?"
  header: "테스트"
  options:
    - label: "Yes - 테스트 완료"
      description: "정상 작동 확인함"
    - label: "No - 아직 테스트 중"
      description: "나중에 다시 진행"
```

4. If "No": Show testing guide, exit

5. **Clear Claude Code cache** (if reinstalling):
```bash
rm -rf ~/.claude/plugins/cache/{plugin-name}*
```

6. **MANDATORY: Run validation before any changes**:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
   - **If ANY errors exist => STOP and fix first**
   - Show user the exact errors and how to fix them
   - Do NOT proceed with errors

6. Find unregistered items:
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
