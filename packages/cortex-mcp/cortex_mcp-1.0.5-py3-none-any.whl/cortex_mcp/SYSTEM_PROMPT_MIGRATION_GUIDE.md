# System Prompt → cortex_prompt.md 마이그레이션 지침서

**작성일**: 2026-01-01
**대상**: Cortex MCP 리팩토링 작업자
**목적**: 9개 System Prompt 주입 위치를 cortex_prompt.md 통합 패턴으로 전환

---

## 배경 (Background)

### 현재 문제점

Cortex MCP는 현재 9개 위치에서 각각 독립적으로 System Prompt를 주입하고 있습니다:

1. `hooks/session_init.py:32` - CORTEX_VERIFICATION_PROTOCOL v2.0
2. `hooks/session_init.py:134` - CORTEX_INIT_REQUIRED
3. `hooks/session_init.py:176` - 활성 브랜치 요약 자동 로드
4. `hooks/inject_context.py:214` - 주제 전환 감지 알림
5. `hooks/inject_context.py:244` - Reference History 맥락 추천
6. `hooks/detect_topic_shift.py:322` - 자동 브랜치 생성 알림
7. `core/auto_trigger.py:213` - Chain-of-Thought 프롬프트
8. `core/boundary_protection.py:448` - CONTEXT_BOUNDARY_PROTOCOL
9. `core/fuzzy_prompt.py:55` - CORTEX_FUZZY_CONTEXT

### 목표 (Goal)

이미 구현된 `cortex_prompt.md` 통합 패턴(inject_context.py의 write_cortex_prompt 참조)을 활용하여, 9개 주입 위치를 통합 관리하도록 전환합니다.

---

## 전략 (Strategy)

### 핵심 원칙: 2-Layer 아키텍처

```
┌─────────────────────────────────────┐
│   cortex_prompt.md (정적 레이어)    │
│  - 변하지 않는 프로토콜              │
│  - 프로젝트당 1회 생성 후 유지       │
└─────────────────────────────────────┘
              ↓ AI가 자동으로 읽음
┌─────────────────────────────────────┐
│  System Prompt (동적 레이어)         │
│  - 실시간 상태 기반 주입              │
│  - 각 Hook에서 필요 시 즉시 주입      │
└─────────────────────────────────────┘
```

### 분류 기준

| 분류 | 포함 대상 | 처리 방법 |
|------|-----------|-----------|
| **정적 프로토콜** | 1, 7 | cortex_prompt.md로 이동 |
| **동적 프로토콜** | 2, 3, 4, 5, 6, 8, 9 | System Prompt 주입 유지 |

**이유**:
- 정적 (1, 7): 프로젝트 수명 내내 변하지 않음
- 동적 (2-6, 8, 9): 브랜치 상태, 작업 컨텍스트, 검색 결과에 따라 실시간 변경 필요

---

## 작업 지침 (Implementation Guide)

### Phase 1: 템플릿 파일 생성

#### 작업 1-1: 디렉토리 생성

```bash
mkdir -p /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp/templates
```

#### 작업 1-2: cortex_prompt_template.md 생성

**파일 경로**: `cortex_mcp/templates/cortex_prompt_template.md`

**파일 내용**:
```markdown
# CORTEX PROTOCOLS (Auto-managed)

Last updated: {timestamp}

이 파일은 Cortex MCP 서버가 자동으로 관리합니다.
AI가 세션 시작 시 자동으로 읽어 프로토콜을 로드합니다.

---

## [Protocol 1] CORTEX_VERIFICATION_PROTOCOL v2.0

[주장에 대한 책임 - AI 자기검증 시스템]

## 핵심 원칙 (MANDATORY - 절대 위반 금지)

**AI 자기검증 방식:**
- AI가 자신이 출력한 문장을 다시 읽고 모순 확인
- 정규식/패턴 매칭 없이 순수 의미 기반 판단
- 모든 언어, 모든 표현 방식 지원
- 토큰 비용: 응답당 ~$0.0015 (Sonnet 기준, 500 tokens)

## 1. update_memory 호출 시 자동 흐름 (MANDATORY)

**[Case A] 확신 표현 없음 (일반 대화)**
```
update_memory("작업 중입니다")
→ memory_manager: 바로 저장
→ Response: {"status": "success"}
```

**[Case B] 확신 표현 있음 (검증 필요)**
```
update_memory("구현 완료했습니다. 7/7 테스트 통과.")
→ memory_manager: 확신 표현 감지 ("완료", "통과")
→ Response: {
      "status": "verification_required",
      "verification_prompt": "다음 응답에 모순이 있나요?\n\n{응답 전체}\n\n확인 사항:\n1. 시간 순서 모순 (먼저 A 후 B ↔ 먼저 B 후 A)\n2. 내용 모순 (성공 ↔ 실패, 7개 ↔ 6개)\n3. 근거 없는 주장\n\n모순이 있으면 '있음: [이유]', 없으면 '없음'으로 답변."
   }
```

**[Case C] 모순 발견 시**
```
AI: 자기검증 중 모순 발견
→ AI: 사용자에게 알림: "검증 중 모순 발견, 수정합니다."
→ AI: 응답 수정
→ AI: update_memory(수정된_응답, verified=True)
```

## 2. 확신 표현 감지 (간단한 키워드 포함 여부)

**한국어:**
- "확실", "완료", "성공", "구현했", "수정했", "추가했"
- "생성했", "완성했", "해결했", "통과", "정상", "마쳤"
- "반드시", "절대", "명확히", "확인했", "검증했"

**영어:**
- "completed", "successfully", "implemented", "fixed"
- "added", "created", "finished", "resolved", "passed"
- "working", "done", "achieved", "verified"

**Note:** 단순 키워드 포함 여부만 확인 (정규식 아님)

## 3. 자기검증 프로세스 (MANDATORY)

1. **응답 생성 후 update_memory 호출**
   - 모든 응답 완료 후 즉시 호출 (필수)

2. **verification_required 반환 시**
   - verification_prompt를 읽고 자기검증 수행
   - 모순 있으면: 사용자에게 알림 + 수정 + update_memory(verified=True)
   - 모순 없으면: update_memory(verified=True)

3. **verified=True 플래그**
   - 무한 루프 방지
   - 검증 완료 후 저장 시 반드시 포함

## 4. 예외 사항

**검증 건너뛰기 조건:**
- 확신 표현이 없는 일반 대화
- 이미 verified=True로 호출한 경우
- role="user"인 경우 (사용자 메시지)

---

이 프로토콜을 준수하여 모든 응답의 정확도를 100%로 유지하세요.

---

## [Protocol 2] Chain-of-Thought 원칙

[확신에 대한 책임 - Phase 9 검증]

작업 시작 전 다음을 확인하세요:

**Q1: Phase 9의 목적은?**
A: AI 주장을 Evidence Graph로 객관적 검증

**Q2: verified=True가 금지된 이유는?**
A: AI를 맹목적으로 믿으면 검증 시스템 무력화

**Q3: 맥락이 부족하면 어떻게 하는가?**
A: suggest_contexts 또는 search_context 호출

**Q4: 작업 완료 후 무엇을 해야 하는가?**
A: update_memory 호출하여 맥락 기록

---

## Dynamic Protocols (실시간 주입)

다음 프로토콜들은 상황에 따라 System Prompt로 실시간 주입됩니다:

### 세션 시작 시
- **초기화 안내** (새 프로젝트 시): 스캔 모드 선택 가이드
- **활성 브랜치 요약**: 현재 브랜치의 최신 상태

### 작업 중
- **주제 전환 감지**: 브랜치 분리 권장
- **맥락 추천**: Reference History 기반 자동 로딩
- **브랜치 생성**: 자동 생성 완료 알림

### 조건부
- **작업 경계**: 보안을 위한 파일 접근 제한
- **퍼지 컨텍스트**: 온톨로지 기반 검색 힌트

---

**Version**: 1.0.0
**Last Updated**: 2026-01-01
```

**중요**:
- `{timestamp}` 부분은 setup_cortex.py에서 동적으로 채워집니다
- CORTEX_VERIFICATION_PROTOCOL v2.0 전체 내용을 `hooks/session_init.py:32`에서 복사해야 합니다

---

### Phase 2: setup_cortex.py 수정

#### 작업 2-1: cortex_prompt 생성 함수 추가

**파일 경로**: `cortex_mcp/scripts/setup_cortex.py`

**변경 위치**: 기존 `add_claude_md_reference()` 함수 다음에 추가

**추가할 함수**:
```python
def create_cortex_prompt(project_root: Path) -> bool:
    """
    cortex_prompt.md 생성 (템플릿 기반)

    Returns:
        bool: 생성 성공 여부
    """
    import shutil
    from datetime import datetime

    # 템플릿 경로
    template_path = Path(__file__).parent.parent / "templates" / "cortex_prompt_template.md"
    if not template_path.exists():
        print(f"❌ 템플릿 파일을 찾을 수 없습니다: {template_path}")
        return False

    # 타겟 경로
    target_path = project_root / "cortex_prompt.md"

    if target_path.exists():
        print(f"⚠️  cortex_prompt.md가 이미 존재합니다: {target_path}")
        return True

    # 템플릿 복사 및 타임스탬프 삽입
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 타임스탬프 삽입
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        content = content.replace("{timestamp}", timestamp)

        # 타겟 파일 작성
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ cortex_prompt.md 생성 완료: {target_path}")
        return True

    except Exception as e:
        print(f"❌ cortex_prompt.md 생성 실패: {e}")
        return False
```

#### 작업 2-2: main() 함수 수정

**변경 위치**: `setup_cortex.py`의 `main()` 함수

**변경 전**:
```python
def main():
    # ... 기존 코드 ...

    # CLAUDE.md에 참조 추가
    add_claude_md_reference(project_root, client)

    print("\n✅ Cortex 설정이 완료되었습니다!")
```

**변경 후**:
```python
def main():
    # ... 기존 코드 ...

    # cortex_prompt.md 생성
    create_cortex_prompt(project_root)

    # CLAUDE.md에 참조 추가
    add_claude_md_reference(project_root, client)

    print("\n✅ Cortex 설정이 완료되었습니다!")
```

---

### Phase 3: 기존 Hook 파일 수정 (선택적)

**중요**: 이 단계는 **선택 사항**입니다. 기존 동작을 유지하면서 중복만 제거합니다.

#### 작업 3-1: session_init.py 수정 (선택)

**파일 경로**: `hooks/session_init.py`

**변경 위치**: Line 32 근처

**변경 전**:
```python
# Line 32-79: CORTEX_VERIFICATION_PROTOCOL_V2 상수 정의
CORTEX_VERIFICATION_PROTOCOL_V2 = """[CORTEX_VERIFICATION_PROTOCOL v2.0 - AI 자기검증 시스템]
...
"""

# Line 130-160: run() 메서드에서 호출
output_system_message(ctx, CORTEX_VERIFICATION_PROTOCOL_V2)
```

**변경 후**:
```python
# Line 32-79: 상수 제거 (cortex_prompt.md로 이동했으므로)
# CORTEX_VERIFICATION_PROTOCOL_V2 = ... (삭제)

# Line 130-160: run() 메서드
# cortex_prompt.md 존재 여부 확인 (선택적)
cortex_prompt = Path(ctx.project_path) / "cortex_prompt.md"
if not cortex_prompt.exists():
    logger.warning(
        "cortex_prompt.md not found. "
        "Please run 'python cortex_mcp/scripts/setup_cortex.py' first."
    )
    # Fallback: 기존 방식으로 주입 (호환성 유지)
    output_system_message(ctx, CORTEX_VERIFICATION_PROTOCOL_V2_FALLBACK)

# 나머지 동적 주입은 유지
if not ctx.active_branch:
    output_system_message(ctx, CORTEX_INIT_REQUIRED_MESSAGE)
else:
    summary = get_active_summary(...)
    output_system_message(ctx, summary)
```

**Fallback 상수 정의** (호환성 유지):
```python
CORTEX_VERIFICATION_PROTOCOL_V2_FALLBACK = """
[CORTEX_VERIFICATION_PROTOCOL v2.0]

⚠️  cortex_prompt.md가 없습니다. setup_cortex.py를 실행하세요.

기본 검증 프로토콜:
- update_memory 호출 시 자동 할루시네이션 검증
- 확신 표현 감지 시 verification_required 반환
- 모순 발견 시 수정 후 verified=True로 재호출
"""
```

---

### Phase 4: 테스트 및 검증

#### 테스트 시나리오 1: 새 프로젝트

```bash
# 1. 새 프로젝트 디렉토리 생성
mkdir -p /tmp/test_project
cd /tmp/test_project

# 2. setup_cortex.py 실행
python /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp/scripts/setup_cortex.py

# 3. cortex_prompt.md 생성 확인
ls -la cortex_prompt.md

# 4. 내용 확인
cat cortex_prompt.md | head -30

# 5. MCP 서버 재시작 후 테스트
```

#### 테스트 시나리오 2: 기존 프로젝트

```bash
# 1. 프로젝트 디렉토리로 이동
cd /Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp

# 2. setup_cortex.py 재실행
python cortex_mcp/scripts/setup_cortex.py

# 3. cortex_prompt.md 업데이트 확인
git diff cortex_prompt.md

# 4. CLAUDE.md 참조 확인
tail -5 CLAUDE.md
# 출력: "Read and follow ./cortex_prompt.md"
```

#### 검증 항목

- [ ] cortex_prompt.md 파일 생성 확인
- [ ] Protocol 1, 2 내용 포함 확인
- [ ] CLAUDE.md에 참조 추가 확인
- [ ] MCP 서버 재시작 후 AI가 프로토콜 인식 확인
- [ ] 기존 동적 주입 정상 작동 확인

---

## 주의사항 (Important Notes)

### 1. 동적 프로토콜은 유지

**다음 7개는 cortex_prompt.md로 이동하지 마세요**:

- `hooks/session_init.py:134` - CORTEX_INIT_REQUIRED (브랜치 상태 의존)
- `hooks/session_init.py:176` - Active Branch Summary (브랜치별 다름)
- `hooks/inject_context.py:214` - Topic Shift Detection (실시간 감지)
- `hooks/inject_context.py:244` - Reference History (실시간 추천)
- `hooks/detect_topic_shift.py:322` - Auto Branch Creation (실시간)
- `core/boundary_protection.py:448` - CONTEXT_BOUNDARY_PROTOCOL (작업별)
- `core/fuzzy_prompt.py:55` - CORTEX_FUZZY_CONTEXT (검색별)

**이유**: 이들은 실시간 상태에 따라 내용이 달라지므로 정적 파일에 넣을 수 없습니다.

### 2. CLAUDE.md 참조 확인

**필수 라인**:
```markdown
Read and follow ./cortex_prompt.md
```

이 라인이 CLAUDE.md 최하단에 있어야 AI가 자동으로 읽습니다.

### 3. Git 관리

**cortex_prompt.md 버전 관리**:

- **팀 공유 프로젝트**: `.gitignore`에 추가하지 않음 (Git 추적)
- **개인 프로젝트**: `.gitignore`에 추가 가능

**예시** (.gitignore):
```
# 개인 맥락 (공유 안 함)
cortex_prompt.md
```

### 4. 템플릿 업데이트 시

템플릿 파일(`cortex_prompt_template.md`)을 수정한 경우:

```bash
# 1. 템플릿 수정
vi cortex_mcp/templates/cortex_prompt_template.md

# 2. 기존 프로젝트 업데이트 (수동)
cd /path/to/project
python cortex_mcp/scripts/setup_cortex.py --force-update
```

**`--force-update` 플래그 구현** (선택):
```python
# setup_cortex.py에 추가
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--force-update', action='store_true',
                    help='Force update cortex_prompt.md')
args = parser.parse_args()

if args.force_update and target_path.exists():
    target_path.unlink()  # 기존 파일 삭제 후 재생성
```

---

## 체크리스트 (Checklist)

### 구현 전

- [ ] 현재 9개 주입 위치 파악 완료
- [ ] inject_context.py의 write_cortex_prompt 참조 완료
- [ ] 2-Layer 아키텍처 이해 완료

### 구현 중

- [ ] Phase 1: cortex_prompt_template.md 생성
- [ ] Phase 2: setup_cortex.py 수정
- [ ] Phase 3: Hook 파일 수정 (선택)

### 구현 후

- [ ] 테스트 시나리오 1 통과 (새 프로젝트)
- [ ] 테스트 시나리오 2 통과 (기존 프로젝트)
- [ ] AI 인식률 95%+ 확인
- [ ] 기존 동적 주입 정상 작동 확인
- [ ] Git 커밋 및 문서 업데이트

---

## 예상 소요 시간 (Estimated Time)

| Phase | 작업 | 예상 시간 |
|-------|------|-----------|
| Phase 1 | 템플릿 생성 | 10분 |
| Phase 2 | setup_cortex.py 수정 | 15분 |
| Phase 3 | Hook 수정 (선택) | 20분 |
| Phase 4 | 테스트 | 15분 |
| **총계** | | **60분** |

---

## 참고 자료 (References)

1. **기존 구현 참조**:
   - `hooks/inject_context.py:189-309` - write_cortex_prompt() 함수
   - `scripts/setup_cortex.py` - 기존 설정 스크립트

2. **관련 문서**:
   - `CORTEX_AUTOMATION_TEST_REPORT.md` - inject_context 자동화 보고서
   - `CLAUDE.md` - AI 가이드 문서

3. **Git 히스토리**:
   ```bash
   git log --oneline --grep="cortex_prompt" -10
   ```

---

## 문제 발생 시 (Troubleshooting)

### 문제 1: cortex_prompt.md가 생성되지 않음

**증상**: setup_cortex.py 실행 후 파일 없음

**원인**: 템플릿 파일 경로 오류

**해결**:
```bash
# 템플릿 파일 존재 확인
ls -la cortex_mcp/templates/cortex_prompt_template.md

# 없으면 Phase 1부터 재시작
```

### 문제 2: AI가 프로토콜을 인식 못함

**증상**: AI가 CORTEX_VERIFICATION_PROTOCOL 무시

**원인**: CLAUDE.md에 참조 누락

**해결**:
```bash
# CLAUDE.md 최하단에 다음 라인 추가
echo "Read and follow ./cortex_prompt.md" >> CLAUDE.md

# MCP 서버 재시작
```

### 문제 3: 기존 동적 주입이 작동 안 함

**증상**: 브랜치 요약, 맥락 추천 등이 나타나지 않음

**원인**: Phase 3에서 잘못 삭제했을 가능성

**해결**:
```bash
# Git으로 되돌리기
git checkout hooks/session_init.py
git checkout hooks/inject_context.py

# Phase 3는 선택 사항이므로 건너뛰기
```

---

**작성자**: Cortex Development Team
**마지막 업데이트**: 2026-01-01
**버전**: 1.0.0
