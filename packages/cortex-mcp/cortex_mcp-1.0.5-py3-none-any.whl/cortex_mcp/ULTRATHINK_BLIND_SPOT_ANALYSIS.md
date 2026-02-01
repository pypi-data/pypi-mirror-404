# cortex_prompt.md 아키텍처 맹점 분석 (ULTRATHINK MODE)

**분석 일자**: 2026-01-01
**요청자**: 사용자
**분석 범위**: cortex_prompt.md 2-layer 아키텍처의 모든 잠재적 문제점

---

## 1. 현재 상황 요약

### 1.1 문서 vs 실제 구현 간극

| 항목 | 문서 (SYSTEM_PROMPT_MIGRATION_GUIDE.md) | 실제 구현 |
|------|----------------------------------------|----------|
| **cortex_prompt.md 목적** | 정적 프로토콜 저장 (VERIFICATION, Chain-of-Thought) | 동적 콘텐츠 저장 (브랜치 요약, 관련 맥락) |
| **구현 상태** | 제안 문서 (Not Implemented) | inject_context.py에서 동적 작성 |
| **파일 내용** | 템플릿만 (거의 비어있음) | "Cortex will update automatically" |

**핵심 문제**: 마이그레이션 가이드는 **구현되지 않은 제안서**일 뿐입니다.

### 1.2 System Prompt 주입 지점 (발견된 9개+)

| 위치 | 파일 | 라인 | 프로토콜/메시지 | 타입 |
|------|------|------|----------------|------|
| 1 | session_init.py | 127 | `CORTEX_VERIFICATION_PROTOCOL_V2` | 정적 |
| 2 | session_init.py | 162 | `CORTEX_INIT_REQUIRED` | 동적 (초기화 여부) |
| 3 | session_init.py | 207 | `CORTEX_NO_ACTIVE_BRANCH` | 동적 (브랜치 존재 여부) |
| 4 | session_init.py | 223 | Branch summary message | 동적 (현재 브랜치) |
| 5 | session_init.py | 236 | Loaded contexts message | 동적 (로드된 맥락) |
| 6 | session_init.py | 256 | Context summary message | 동적 (맥락 요약) |
| 7 | inject_context.py | 354 | Branch message (UserPromptSubmit) | 동적 (프롬프트별) |
| ? | detect_topic_shift.py | ? | Topic shift detection | 동적 (주제 전환) |
| ? | boundary.py | ? | Boundary protocol | 동적 (작업 범위) |

**발견**: SYSTEM_PROMPT_MIGRATION_GUIDE는 **9개 주입 지점**을 언급했지만, 실제로는 **더 많을 수 있음**.

### 1.3 cortex_prompt.md의 현재 역할

**실제 동작** (inject_context.py:189-289):
```python
def write_cortex_prompt(ctx: HookContext, user_prompt: str, keywords: list):
    """
    프로젝트별 cortex_prompt.md 작성 (강제 실행 - AI 독립)
    """
    # 1. 현재 브랜치 요약 로드
    # 2. Reference History 기반 맥락 추천
    # 3. 신뢰도 기반 자동 로드
    # 4. cortex_prompt.md 작성
```

**작성 내용**:
- Last updated timestamp
- Current Branch topic + summary
- Auto-loaded related branches (confidence 기반)
- Instructions

**문제**: 이것은 **동적 콘텐츠**입니다. 마이그레이션 가이드가 제안한 **정적 프로토콜**과 완전히 다릅니다.

---

## 2. 맹점 발견 (CRITICAL BLIND SPOTS)

### 맹점 #1: AI가 cortex_prompt.md를 언제 읽는가?

**현재 메커니즘**:
- CLAUDE.md line 1242: `"Read and follow ./cortex_prompt.md"`
- 이것만이 유일한 참조

**문제**:
1. **읽기 시점 불명확**: AI가 세션 시작 시 읽는가? 매 응답마다 읽는가?
2. **우선순위 불명확**: CLAUDE.md 전체를 읽은 후 cortex_prompt.md를 읽는가? 순서는?
3. **조건부 읽기 불가능**: 특정 기능 사용 시에만 읽도록 지시 불가능

**근거**:
- CLAUDE.md는 길이가 1500+ 라인
- "Read and follow" 지시문은 1242번째 라인 (하단 근처)
- AI가 CLAUDE.md를 완전히 읽기 전에 응답 시작하면 cortex_prompt.md를 못 볼 수 있음

**예상 동작**:
```
AI 세션 시작
→ CLAUDE.md 읽기 시작
→ ... (1241 라인 처리)
→ Line 1242: "Read and follow ./cortex_prompt.md"
→ cortex_prompt.md 읽기
→ 응답 생성
```

**잠재적 문제**:
- CLAUDE.md가 너무 길면 AI가 중간에 응답 시작할 수 있음
- cortex_prompt.md 읽기를 건너뛸 가능성

### 맹점 #2: 정적 vs 동적 프로토콜 혼재

**현재 구조** (마이그레이션 가이드 제안):
```
┌─────────────────────────────────────┐
│   cortex_prompt.md (정적 레이어)    │
│  - VERIFICATION_PROTOCOL            │
│  - Chain-of-Thought                 │
└─────────────────────────────────────┘
              ↓ AI가 자동으로 읽음
┌─────────────────────────────────────┐
│  System Prompt (동적 레이어)         │
│  - Branch summaries                 │
│  - Context suggestions              │
│  - Boundary protocols               │
└─────────────────────────────────────┘
```

**실제 구현**:
```
┌─────────────────────────────────────┐
│   cortex_prompt.md                  │
│  - Branch summaries (동적!)         │
│  - Auto-loaded contexts (동적!)     │
└─────────────────────────────────────┘
              ↓ AI가 읽는지 불확실
┌─────────────────────────────────────┐
│  System Prompt                      │
│  - VERIFICATION_PROTOCOL (정적!)    │
│  - Branch summaries (중복!)         │
│  - All other protocols (혼재!)      │
└─────────────────────────────────────┘
```

**문제**:
1. **역할 혼동**: cortex_prompt.md가 정적인지 동적인지 불명확
2. **중복 가능성**: 동일한 정보가 cortex_prompt.md + System Prompt 양쪽에 존재 가능
3. **동기화 실패**: cortex_prompt.md 업데이트와 System Prompt 주입이 서로 다른 시점에 발생

### 맹점 #3: 파일 존재 여부 체크 없음

**코드 확인** (inject_context.py:197-198):
```python
project_root = Path(ctx.project_path)
cortex_prompt = project_root / "cortex_prompt.md"
```

**문제**:
1. **파일 부재 시**: cortex_prompt.md가 없으면 어떻게 되는가?
2. **CLAUDE.md 참조**: "Read and follow ./cortex_prompt.md" - 파일이 없으면 오류 발생 가능
3. **초기 세션**: 프로젝트 첫 연결 시 cortex_prompt.md가 없는 상태에서 CLAUDE.md가 참조 시도

**예상 시나리오**:
```
1. 사용자가 Cortex 처음 설치
2. CLAUDE.md 읽음
3. Line 1242: "Read ./cortex_prompt.md"
4. 파일 없음 → 오류? 무시? 불명확
```

### 맹점 #4: 프로토콜별 명시적 참조 부재

**사용자 우려 (정확함)**:
> "시스템프롬프트에다가 a기능,b기능,c기능........사용하려면 cortex prompt.md파일을 참조하라 -> 이런식으로 명시해둬야하는거 아닌가?"

**현재 상태**:
- CLAUDE.md: "Read and follow ./cortex_prompt.md" (일반적 지시)
- 구체적 기능 매핑 없음

**문제**:
1. **AI 혼란 가능성**: AI가 어떤 기능에서 cortex_prompt.md를 참조해야 하는지 모름
2. **선택적 적용 불가**: 모든 프로토콜을 항상 적용하거나, 아예 적용 안 하거나 양극단
3. **기능별 동작 불명확**: 예를 들어, "verification만 cortex_prompt.md 참조" 불가능

**예상 동작**:
- AI가 cortex_prompt.md를 읽더라도 "언제 어떻게 적용하는가" 불명확
- 모든 응답에 적용? 특정 작업에만 적용? 애매함

### 맹점 #5: 파일 갱신 타이밍과 AI 읽기 타이밍 불일치

**갱신 시점** (inject_context.py):
- `write_cortex_prompt()` 함수: UserPromptSubmit Hook에서 호출
- 즉, **사용자가 프롬프트 제출할 때마다** cortex_prompt.md 갱신

**AI 읽기 시점**:
- 명시적으로 정의되지 않음
- CLAUDE.md의 "Read and follow" 지시에 의존

**Race Condition 가능성**:
```
T1: 사용자 프롬프트 제출
T2: UserPromptSubmit Hook 실행
T3: write_cortex_prompt() 호출 → cortex_prompt.md 갱신
T4: AI가 CLAUDE.md 읽기 시작
T5: AI가 cortex_prompt.md 읽기 (T3 이전 버전? T3 이후 버전?)
```

**문제**:
- 파일 쓰기(T3)와 읽기(T5) 사이에 동기화 보장 없음
- AI가 오래된 cortex_prompt.md를 읽을 가능성

### 맹점 #6: System Prompt 크기 제한 무시

**현재 System Prompt 크기**:
- CLAUDE.md: 1500+ 라인
- CORTEX_VERIFICATION_PROTOCOL_V2: ~100 라인
- 9개+ 동적 메시지: 각각 50~200 라인 가능

**총 예상 크기**: 2000~3000 라인

**문제**:
1. **Claude Code System Prompt 한계**: 정확한 한계 불명 (테스트 필요)
2. **토큰 소모**: 매 세션마다 2000~3000 라인 읽기 = 높은 토큰 비용
3. **cortex_prompt.md 추가 시**: 더욱 증가

**cortex_prompt.md로 이동 시 기대 효과**:
- System Prompt 크기 감소
- 하지만 cortex_prompt.md를 언제 읽는지 불명확하면 의미 없음

### 맹점 #7: 프로토콜 버전 관리 부재

**현재 상태**:
- CORTEX_VERIFICATION_PROTOCOL_V2 (v2.0)
- 버전이 하드코딩되어 있음

**cortex_prompt.md로 이동 시 문제**:
1. **업그레이드 메커니즘 없음**: v2.0 → v2.1 어떻게 업데이트?
2. **호환성 체크 없음**: AI가 오래된 버전을 읽을 가능성
3. **동기화 실패**: System Prompt는 v2.0, cortex_prompt.md는 v2.1

**잠재적 시나리오**:
```
1. Cortex v2.1 릴리스
2. VERIFICATION_PROTOCOL v2.1 적용
3. 기존 프로젝트의 cortex_prompt.md는 v2.0
4. AI가 오래된 프로토콜 적용 → 동작 오류
```

### 맹점 #8: 다중 프로젝트 환경

**현재 구조**:
```
~/.cortex/memory/{project_id}/
/project_A/cortex_prompt.md
/project_B/cortex_prompt.md
```

**문제**:
1. **프로젝트 전환 시**: AI가 어떤 cortex_prompt.md를 읽는가?
2. **CLAUDE.md 참조**: "./cortex_prompt.md" - 상대 경로 (현재 working directory 의존)
3. **동시 세션**: 여러 프로젝트 동시 작업 시 cortex_prompt.md 충돌 가능

**예상 문제**:
- Project A 작업 중 Project B의 cortex_prompt.md를 읽을 가능성

### 맹점 #9: 에러 처리 부재

**cortex_prompt.md 관련 에러**:
1. **파일 읽기 실패**: AI가 cortex_prompt.md를 못 읽으면?
2. **파일 형식 오류**: Markdown 형식이 깨지면?
3. **내용 파싱 실패**: AI가 내용을 이해 못하면?

**현재 코드**:
- inject_context.py: `try-except`로 에러 로깅만 (line 305)
- AI에게 에러 알림 없음

**문제**:
- AI가 조용히 실패하고 사용자는 모름
- 디버깅 불가능

---

## 3. 구체적 권장사항

### 권장사항 #1: System Prompt에 명시적 프로토콜 매핑 추가

**현재**:
```markdown
Read and follow ./cortex_prompt.md
```

**변경 후**:
```markdown
[CORTEX_PROTOCOL_REFERENCE]

다음 기능 사용 시 ./cortex_prompt.md를 참조하세요:

1. **AI 자기검증** (VERIFICATION_PROTOCOL):
   - update_memory 호출 시
   - 확신 표현 감지 시
   - 참조: cortex_prompt.md > Section "VERIFICATION_PROTOCOL v2.0"

2. **맥락 리프레시** (CONTEXT_REFRESH):
   - 세션 시작 시
   - 브랜치 전환 시
   - 참조: cortex_prompt.md > Section "Current Branch"

3. **Chain-of-Thought** (사고 과정):
   - 복잡한 작업 수행 시
   - 참조: cortex_prompt.md > Section "Chain-of-Thought Protocol"

파일이 없거나 읽기 실패 시 이 System Prompt의 프로토콜을 대신 사용하세요.
```

**효과**:
- AI가 언제 cortex_prompt.md를 참조해야 하는지 명확히 이해
- Fallback 메커니즘 제공

### 권장사항 #2: 2-Layer 아키텍처 명확히 재정의

**제안**:
```
┌─────────────────────────────────────────────┐
│ Layer 1: cortex_prompt.md (프로젝트별)      │
│  - 정적 프로토콜 (버전 관리됨)               │
│    * VERIFICATION_PROTOCOL                  │
│    * Chain-of-Thought                       │
│  - 프로젝트별 설정                           │
│    * Boundary rules                         │
│    * Custom protocols                       │
└─────────────────────────────────────────────┘
              ↓ 세션 시작 시 1회 읽기
┌─────────────────────────────────────────────┐
│ Layer 2: System Prompt (세션별 동적 주입)   │
│  - 현재 브랜치 요약                          │
│  - 관련 맥락 제안                            │
│  - 작업별 임시 지시                          │
└─────────────────────────────────────────────┘
```

**구현 변경**:
1. **inject_context.py 수정**: 동적 콘텐츠를 System Prompt로만 주입
2. **session_init.py 수정**: 정적 프로토콜을 cortex_prompt.md로 이동
3. **write_cortex_prompt()**: 정적 프로토콜만 작성

### 권장사항 #3: 파일 존재 체크 + Fallback

**구현**:
```python
# session_init.py
def load_cortex_prompt(ctx: HookContext):
    """cortex_prompt.md 로드 또는 Fallback"""
    cortex_prompt_path = Path(ctx.project_path) / "cortex_prompt.md"

    if cortex_prompt_path.exists():
        try:
            content = cortex_prompt_path.read_text(encoding="utf-8")
            output_system_message(f"[CORTEX_PROTOCOLS]\n\n{content}")
            ctx.log("SessionStart", "cortex_prompt_loaded", {"path": str(cortex_prompt_path)})
        except Exception as e:
            ctx.log("SessionStart", "cortex_prompt_load_failed", {"error": str(e)})
            # Fallback: System Prompt의 프로토콜 사용
            output_system_message(CORTEX_VERIFICATION_PROTOCOL_V2)
    else:
        # 파일 없음 - 자동 생성
        write_cortex_prompt_template(ctx)
        ctx.log("SessionStart", "cortex_prompt_created", {"path": str(cortex_prompt_path)})
```

**효과**:
- 파일 부재 시 자동 생성
- 에러 시 Fallback 보장

### 권장사항 #4: 프로토콜 버전 관리

**구현**:
```markdown
# cortex_prompt.md

---
version: 2.0
last_updated: 2026-01-01T00:00:00Z
compatible_cortex: ">= 2.0.0"
---

## VERIFICATION_PROTOCOL v2.0
...
```

**Python 코드**:
```python
def check_protocol_version(content: str) -> bool:
    """프로토콜 버전 호환성 체크"""
    # YAML frontmatter 파싱
    # 버전 비교
    # 호환되지 않으면 업그레이드 제안
```

### 권장사항 #5: 동기화 보장

**UserPromptSubmit Hook 수정**:
```python
def main():
    # 1. cortex_prompt.md 갱신
    write_cortex_prompt(ctx, user_prompt, keywords)

    # 2. 갱신 완료 대기 (file lock)
    wait_for_file_write_complete()

    # 3. AI에게 갱신 알림
    output_system_message("[CORTEX_PROMPT_REFRESHED] cortex_prompt.md가 갱신되었습니다. 최신 맥락을 반영하세요.")
```

### 권장사항 #6: 읽기 시점 명시

**CLAUDE.md 수정**:
```markdown
## 세션 시작 시 필수 작업

1. **cortex_prompt.md 읽기** (최우선)
   - 위치: ./cortex_prompt.md
   - 내용: 프로젝트별 프로토콜, 맥락, 설정
   - 읽기 실패 시: System Prompt의 Fallback 프로토콜 사용

2. **CLAUDE.md 읽기** (이 파일)
   - 전체 프로젝트 지침

우선순위: cortex_prompt.md > CLAUDE.md
```

**효과**:
- AI가 cortex_prompt.md를 **먼저** 읽도록 강제
- 순서 명확화

---

## 4. 최종 결론

### 4.1 핵심 문제

**사용자 우려는 100% 정당합니다.**

현재 cortex_prompt.md 아키텍처는:
1. **구현되지 않음** (마이그레이션 가이드는 제안서일 뿐)
2. **역할 혼동** (정적 vs 동적 콘텐츠 혼재)
3. **명시적 참조 부재** (AI가 언제 읽어야 하는지 불명확)
4. **동기화 미보장** (파일 갱신과 AI 읽기 타이밍 불일치)
5. **에러 처리 부재** (파일 부재/오류 시 Fallback 없음)

### 4.2 즉시 조치 필요 사항

| 우선순위 | 작업 | 예상 시간 |
|---------|------|-----------|
| **P0** | System Prompt에 명시적 프로토콜 매핑 추가 | 30분 |
| **P0** | 파일 존재 체크 + Fallback 구현 | 1시간 |
| **P1** | 2-Layer 아키텍처 재정의 + 구현 | 3시간 |
| **P1** | 읽기 시점 명시 (CLAUDE.md 수정) | 30분 |
| **P2** | 프로토콜 버전 관리 | 2시간 |
| **P2** | 동기화 보장 메커니즘 | 1시간 |

### 4.3 장기 개선 사항

1. **테스트 케이스 작성**: cortex_prompt.md 읽기/쓰기 E2E 테스트
2. **모니터링**: cortex_prompt.md 읽기 실패율 추적
3. **문서화**: 사용자 가이드 업데이트 (cortex_prompt.md 역할 명확화)

### 4.4 답변

**질문**: "이렇게 바꿔두면 AI가 잘 파악하고 이 작업을 할 수 있게되는게 맞나?"

**답변**:
**현재 상태에서는 보장할 수 없습니다.**

다음이 모두 충족되어야 안정적으로 동작합니다:
1. System Prompt에 "기능별로 cortex_prompt.md 참조" 명시
2. 파일 부재 시 Fallback 제공
3. 읽기 시점 명확화 (세션 시작 시 최우선)
4. 동기화 보장 (파일 쓰기 완료 후 AI 읽기)

**권장 조치**:
- 위 권장사항 #1~#3 먼저 구현 (P0)
- 테스트 후 나머지 개선사항 적용

---

**분석 완료 시각**: 2026-01-01T[현재시각]
**분석자**: Claude (Sonnet 4.5)
**신뢰도**: High (코드 직접 확인, 9개+ 지점 분석)
