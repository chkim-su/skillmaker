---
name: hook-sdk-integration
description: LLM invocation patterns from hooks via SDK. Use when you need background agents, CLI calls, or cost optimization.
allowed-tools: ["Read", "Grep", "Glob"]
---

# Hook SDK Integration

Hook에서 u-llm-sdk/claude-only-sdk를 사용하여 LLM 호출하는 패턴.

## IMPORTANT: SDK 상세 가이드

**SDK 구현 시 반드시 로드**:
```
Skill("skillmaker:llm-sdk-guide")
```

이 스킬은 SDK 호출 패턴의 **인터페이스**를 다루고,
`llm-sdk-guide`는 SDK의 **상세 API와 타입**을 다룹니다.

## Quick Start

```bash
# Background agent 패턴 (비차단)
(python3 sdk-agent.py "$INPUT" &)
echo '{"status": "started"}'
exit 0
```

## 핵심 발견 (검증됨: 2025-12-30)

| 항목 | 결과 |
|------|------|
| SDK 호출 | ✅ Hook에서 가능 |
| Latency | ~30초 (CLI 세션 초기화) |
| Background | ✅ 비차단 실행 가능 (0.01초 반환) |
| 비용 | 구독 사용량으로 처리 (추가 API 비용 없음) |

## 아키텍처

```
Hook (bash) → Background (&) → SDK (Python) → CLI → 구독 사용량
     │                                                    │
     └─── 즉시 반환 (0.01초) ─────────────────────────────┘
```

## 패턴 선택

| 상황 | 패턴 | 이유 |
|------|------|------|
| 빠른 평가 필요 | `type: "prompt"` | 세션 내 실행, 빠름 |
| 격리 필요 | CLI 직접 호출 | 별도 MCP 설정 가능 |
| 복잡한 로직 | SDK + Background | 타입 안전, 비차단 |
| 비용 절감 | 로컬 LLM (ollama) | 무료, 프라이버시 |

## SDK 설정 (Python)

```python
from u_llm_sdk import LLM, LLMConfig
from llm_types import Provider, ModelTier, AutoApproval

config = LLMConfig(
    provider=Provider.CLAUDE,
    tier=ModelTier.LOW,
    auto_approval=AutoApproval.FULL,
    timeout=60.0,
)

async with LLM(config) as llm:
    result = await llm.run("Your prompt")
```

## 비용 구조

| 방식 | 비용 |
|------|------|
| `type: "prompt"` | 구독 포함 |
| Claude CLI | 구독 포함 |
| SDK → CLI | 구독 포함 |
| 직접 API | 토큰 과금 |

## References

- **[LLM SDK 상세 가이드](../llm-sdk-guide/SKILL.md)** ← SDK API 상세
- [SDK 통합 패턴](references/sdk-patterns.md)
- [Background Agent 구현](references/background-agent.md)
- [비용 최적화](references/cost-optimization.md)
- [실제 사례](references/real-world-projects.md)
