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
| `publish\|deploy\|배포\|마켓` | → PUBLISH |
| `register\|local\|등록\|로컬` | → LOCAL_REGISTER |
| no match / empty | → MENU |

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

Route: Skill→SKILL, Agent→AGENT, Command→COMMAND, Validate→VALIDATE, Publish→PUBLISH

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

5. **Post-creation validation** (CRITICAL):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
- If errors: Show errors and offer `--fix`
- If warnings: Show warnings, continue
- If pass: Show success

6. After creation, show next steps:
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

4. **Post-creation validation** (CRITICAL):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
- If errors: Show errors and offer `--fix`

5. After creation, show next steps (same as SKILL step 6)

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

6. **Post-creation validation** (CRITICAL):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
- If errors: Show errors and offer `--fix`

7. After creation, show next steps (same as SKILL step 6)

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

6. **Post-creation validation** (CRITICAL):
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```
- If errors: Show errors and offer `--fix`

7. After creation, show next steps (same as SKILL step 6)

---

# VALIDATE

1. Run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py`

2. If errors, offer: "Auto-fix?" → Yes: run with `--fix`

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

1. Check local registration:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_local_registration.py --path $(pwd)
```

2. If not registered locally:
```markdown
⚠️ 로컬 등록이 필요합니다.

먼저 `/wizard register`를 실행하여 로컬에서 테스트하세요.
```
→ Exit

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

5. Find unregistered items:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py --json | grep "not_registered"
```

6. If unregistered items exist:
```yaml
AskUserQuestion:
  question: "어떤 항목을 마켓플레이스에 등록할까요?"
  header: "항목"
  multiSelect: true
  options: [list of unregistered items]
```

7. Register selected items to marketplace.json:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/register_marketplace.py --items {selected}
```

8. Run final validation:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_all.py
```

9. Show result:
```markdown
## 마켓플레이스 등록 완료

다음 항목이 marketplace.json에 등록되었습니다:
- {registered items}

**배포 방법:**
1. 변경사항 커밋: `git add . && git commit -m "Add new items"`
2. GitHub에 푸시: `git push`
3. 사용자들이 설치 가능: `/plugin install {plugin}@{marketplace}`
```
