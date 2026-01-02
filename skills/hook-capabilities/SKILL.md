---
name: hook-capabilities
description: Claude Code Hook system reference for capabilities, possibilities, and limitations. Use when you want to know what hooks can do.
allowed-tools: ["Read"]
---

# Claude Code Hook Capabilities

Reference for **what hooks can do** in Claude Code.

## Why Hooks Matter: The Only Guarantee

```
Hook = 100% execution guarantee (event-based)
Skill/Agent/MCP = ~20-80% (Claude's judgment)
```

**Key insight**: Hooks are the ONLY mechanism that executes without Claude's decision.
See [orchestration-patterns.md](references/orchestration-patterns.md) for forcing skill/agent activation.

## 5 Hook Roles

| 역할 | 설명 | 예시 |
|------|------|------|
| **Gate** | 도구 실행 차단/허용 | 위험한 명령 방지, 워크플로우 전제조건 검사 |
| **Side Effect** | 도구 실행 후 자동 작업 | 포맷터, 린터, 자동 커밋 |
| **State Manager** | 워크플로우 상태 관리 | 상태 파일 생성/삭제, phase 추적 |
| **External Integrator** | 외부 시스템 연동 | MCP 호출, HTTP API, WebSocket, Slack |
| **Context Injector** | 세션 컨텍스트 주입 | 프로젝트 설정 로드, 서비스 활성화 |

## Event 종류 및 특성

| Event | Block | 특수 기능 | 검증 상태 |
|-------|-------|----------|-----------|
| SessionStart | ❌ | source (compact/new) | ✅ 검증됨 |
| UserPromptSubmit | ✅ | **stdout → Claude 컨텍스트 자동 주입** | ✅ 검증됨 |
| PreToolUse | ✅ | **updatedInput으로 입력 수정**, tool_use_id | ✅ 검증됨 |
| PermissionRequest | ✅ | **allow/deny/ask + 입력 수정** | 미검증 |
| PostToolUse | ❌ | **tool_response** (결과 접근) | ✅ 검증됨 |
| Stop | ✅ | **stop_hook_active** (루프 방지) | ✅ 검증됨 |
| SubagentStop | ✅ | tool_use_id로 부모-자식 상관관계 | 미검증 |
| Notification | ❌ | notification_type 포함 | ✅ 검증됨 |
| PreCompact | ❌ | trigger (auto/manual) | ✅ 검증됨 |
| SessionEnd | ❌ | 세션 종료 시 | 미검증 |

## 범용 접근법 (22가지)

### 제어 패턴 (Control)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Iteration Control** | 반복 횟수 추적 + 최대 제한 | Stop |
| **Force Continuation** | exit 2로 Claude 작업 계속 유도 | Stop |
| **Promise Detection** | Claude 응답 패턴 감지 → 조건부 종료 | Stop |
| **Infinite Loop Prevention** | parent_tool_use_id로 재귀 방지 | UserPromptSubmit |
| **Threshold Branching** | 에러/경고 수 기반 분기 | Stop |

### 입력 조작 (Input Manipulation)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Input Modification** | updatedInput으로 도구 입력 수정 | PreToolUse, PermissionRequest |
| **Path Normalization** | 상대 경로 → 절대 경로 자동 변환 | PreToolUse |
| **Environment Injection** | 환경 변수 자동 주입 | PreToolUse |
| **Dry-run Enforcement** | 위험 명령에 --dry-run 자동 추가 | PreToolUse |

### 컨텍스트 관리 (Context)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Context Injection** | stdout → Claude 컨텍스트 자동 주입 | UserPromptSubmit |
| **Progressive Loading** | 필요시 컨텍스트/스킬 로드 | UserPromptSubmit |
| **Skill Auto-Activation** | 키워드 → 스킬 제안 | UserPromptSubmit |
| **Transcript Parsing** | 이전 응답 읽기 + 분석 | Stop |
| **Transcript Backup** | 세션 트랜스크립트 백업 | PreCompact |

### 상태 관리 (State)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Session Cache** | 세션별 상태 누적 + 결과 집계 | PostToolUse |
| **Session Lifecycle** | SessionStart/End로 상태 초기화/정리 | SessionStart/End |
| **Checkpoint Commit** | 모든 변경마다 checkpoint → squash | PostToolUse, Stop |
| **Session Branching** | 세션별 Git 브랜치 자동 격리 | Pre/PostToolUse |

### 외부 연동 (Integration)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Notification Forwarding** | 알림 → Slack/Discord/외부 서비스 | Notification |
| **Desktop/Audio Alert** | osascript, notify-send, TTS | Notification |
| **Subagent Correlation** | tool_use_id로 부모-자식 추적 | SubagentStop |

### 보안/규정 (Security)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **Auto-Approval** | 특정 도구/명령 자동 승인 | PermissionRequest |
| **Secret Scanning** | API 키/비밀 정보 감지 차단 | PreToolUse |
| **Compliance Audit** | 규정 준수 로깅 + 위반 감지 | PostToolUse |

### 구현 기법 (Implementation)

| 접근법 | 설명 | Event |
|--------|------|-------|
| **TypeScript Delegation** | 복잡한 로직 .ts 위임 | Any |
| **Hook Chaining** | 여러 Hook 순서대로 실행 | Any |
| **Background Execution** | run_in_background로 비동기 | Any |
| **Argument Pattern Matching** | `Bash(npm test*)` 인자 매칭 | PreToolUse |
| **MCP Tool Matching** | `mcp__memory__.*` MCP 매칭 | PreToolUse |
| **Prompt-Type Hook** | type: "prompt" LLM 평가 | Any |

## 가능 vs 불가능

| ✅ 가능 | ❌ 불가능 |
|---------|----------|
| 파일 생성/삭제/수정 | PostToolUse에서 차단 |
| MCP/HTTP/WebSocket 호출 | Claude 컨텍스트 직접 수정 |
| UserPromptSubmit stdout → 컨텍스트 | 기존 컨텍스트 삭제 |
| PreToolUse/PermissionRequest → 입력 수정 | 이미 실행된 도구 취소 |
| Stop에서 작업 계속 유도 | 무제한 강제 (무한 루프 위험) |

## 데이터 전달 방식 (⚠️ 중요)

### stdin JSON (검증됨)
모든 세션/프로젝트 정보는 **stdin JSON**으로 전달:
- `session_id` - 세션 UUID
- `cwd` - 프로젝트 디렉토리
- `transcript_path` - 세션 로그 파일 경로
- `tool_use_id` - 도구 호출 ID (PreToolUse/PostToolUse)

### 이벤트별 stdin JSON 구조

```bash
# UserPromptSubmit
{"prompt": "user message", "session_id": "...", "cwd": "/path"}

# PreToolUse / PostToolUse
{"tool_name": "Bash", "tool_input": {"command": "npm test"}, "session_id": "..."}

# PermissionRequest
{"tool_name": "Bash", "tool_input": {...}, "permission_type": "execute"}

# Stop
{"stop_reason": "end_turn", "session_id": "..."}

# SubagentStop
{"agent_name": "backend-dev", "result": "...", "session_id": "..."}
```

### 환경변수 (검증됨)
`CLAUDE_PROJECT_DIR`, `CLAUDE_SESSION_ID` 등은 **환경변수가 아님**!

실제 설정되는 환경변수:
```bash
CLAUDE_CODE_ENABLE_CFC="false"
CLAUDE_CODE_ENTRYPOINT="cli"
```

### 설정 리로드
- `settings.json` 변경은 **새 세션에서만 적용**됨

## Exit 코드 완전 정리

| Exit 코드 | 의미 | 동작 |
|-----------|------|------|
| **0** | 성공/허용 | 정상 진행 |
| **1** | 에러 | Hook 실패, 경고 표시 |
| **2** | 차단/계속 | 이벤트별 다름 |

**이벤트별 exit 2 동작**:

| Event | exit 2 동작 |
|-------|------------|
| **PreToolUse** | 도구 실행 차단 |
| **PostToolUse** | 결과 무시 (재시도 유도) |
| **PermissionRequest** | 권한 요청 거부 |
| **Stop** | Claude 작업 계속 강제 |
| **UserPromptSubmit** | 프롬프트 처리 중단 |

## Hook 실행 순서

```
동일 이벤트의 여러 Hook → 순차 실행 (정의 순서)
하나의 Hook이 exit 2 → 이후 Hook 미실행
```

## timeout 설정

```json
{"type": "command", "command": "script.sh", "timeout": 10000}
```

기본값: 60000ms (1분)

## 일반적인 실수

| 실수 | 문제점 | 해결책 |
|------|--------|--------|
| stdin 미읽기 | JSON 입력 누락 | `INPUT=$(cat)` 필수 |
| stdout 디버그 출력 | 컨텍스트 오염 | stderr (`>&2`) 사용 |
| exit 1 vs exit 2 혼동 | 의도와 다른 동작 | exit 1=에러, exit 2=차단 |
| jq 없이 파싱 | 불안정 | jq 설치 및 사용 |

## References

- [Event Details](references/event-details.md) - 10 event specifications
- [Pattern Details](references/patterns-detailed.md) - Role, usage, examples
- [Orchestration Patterns](references/orchestration-patterns.md) - **Force skill/agent activation**
- [Real-World Examples](references/real-world-examples.md) - Implementation case studies
- [Advanced Patterns](references/advanced-patterns.md) - Complex combinations
