---
name: critical-analysis-patterns
description: 철학적/메타적 프로젝트 분석 - "왜?"를 묻는 비평적 분석 프레임워크
allowed-tools: ["Read", "Glob", "Grep", "Task"]
---

# Critical Analysis Patterns

기술적 검증을 넘어 **의도와 구현의 정합성**을 분석합니다.

## Core Questions (5가지 핵심 질문)

모든 컴포넌트에 대해 다음 질문을 던지세요:

### 1. 존재 정당성 (Existence Justification)
```
- "이것이 왜 여기 있는가?"
- "제거하면 무엇이 깨지는가?"
- "다른 것으로 대체 가능한가?"
```

### 2. 의도-구현 정합성 (Intent-Implementation Alignment)
```
- "이름이 실제 역할을 반영하는가?"
- "선언된 목적과 실제 동작이 일치하는가?"
- "문서와 코드가 동기화되어 있는가?"
```

### 3. 일관성 (Consistency)
```
- "비슷한 것들이 다르게 처리되고 있지 않은가?"
- "패턴 A와 B가 혼재하지 않는가?"
- "예외적인 처리가 정당화되는가?"
```

### 4. 미사용 기능 (Unused Capabilities)
```
- "선언했지만 사용하지 않는 것이 있는가?"
- "구현했지만 호출되지 않는 것이 있는가?"
- "있는데 왜 안 쓰는가?"
```

### 5. 복잡성 정당화 (Complexity Justification)
```
- "이 복잡성이 정말 필요한가?"
- "더 단순한 대안이 있는가?"
- "오버엔지니어링은 아닌가?"
```

---

## Analysis Process

### Step 1: 컴포넌트 인벤토리
```bash
# 모든 컴포넌트 수집
agents/*.md, skills/*/SKILL.md, commands/*.md, hooks/hooks.json
```

### Step 2: 관계 맵핑
| From | To | Relationship |
|------|----|--------------|
| command | agent | invokes via Task |
| agent | skill | loads via Skill() or frontmatter |
| hook | agent/skill | triggers on events |

### Step 3: 핵심 질문 적용
각 컴포넌트에 5가지 질문을 적용하고 불일치 발견

### Step 4: 발견 사항 정리

## Output Format

```markdown
### 철학적 분석 결과

| 발견 | 질문 | 제안 |
|-----|-----|-----|
| {무엇} | {왜?} | {대안} |
```

---

## Red Flags (즉시 질문해야 할 신호)

| 신호 | 질문 | 상세 |
|-----|-----|-----|
| agents/에 있지만 tools: [] | "에이전트인가 문서인가?" | `Read("references/intent-vs-implementation.md")` |
| 선언된 skills 미사용 | "왜 선언만 하고 안 쓰는가?" | `Read("references/unused-capability-detection.md")` |
| 90%+ 유사한 워크플로우 분리 | "통합 안 하는 이유가 있는가?" | `Read("references/architectural-smell-catalog.md")` |
| Hook 20개+ | "오버엔지니어링 아닌가?" | 복잡성 정당화 필요 |
| 책임 중복 컴포넌트 | "경계가 명확한가?" | 역할 재정의 필요 |

---

## Quick Checklist

분석 시 빠르게 확인할 항목:

- [ ] 모든 agents/가 실제로 에이전트 역할을 하는가?
- [ ] skills 선언과 Skill() 사용이 일치하는가?
- [ ] 비슷한 Hook들이 공통 패턴으로 추출 가능하지 않은가?
- [ ] 문서에 남은 구 아키텍처 흔적이 없는가?
- [ ] 각 컴포넌트의 존재 이유를 한 문장으로 설명 가능한가?
