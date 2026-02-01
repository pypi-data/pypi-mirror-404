# Cortex Accountability Audit Report
## "AI의 책임성" 관점에서 전체 기능 심층 검토

**검토 일시**: 2025-12-23
**검토 목표**: 모든 기능이 "AI work accountable over time" 목표에 부합하는지 검증
**검토 방법**: Python/MCP/QA/UX/PM 전문가 팀 ultrathink 모드

---

## Executive Summary

### 발견된 핵심 문제

| 문제 | 심각도 | 책임 영역 | 상태 |
|------|--------|----------|------|
| **할루시네이션 검증 강제성 부재** | 🔴 CRITICAL | 주장 책임 | 개선 중 |
| **병렬 세션 맥락 충돌** | 🔴 CRITICAL | 기억 책임 | 개선 완료 |
| **Reference History 추천 무시 가능** | 🟡 HIGH | 출처 책임 | 미조치 |
| **브랜치 생성 검증 부재** | 🟡 HIGH | 방향 책임 | 미조치 |
| **Backup 복구 검증 부재** | 🟡 HIGH | 변경 책임 | 미조치 |
| **Plan B 전환 우회 가능** | 🟠 MEDIUM | 확신 책임 | 미조치 |

---

## 1. 기억 책임 (Memory Accountability)

### 관련 모듈
- `memory_manager.py` - 메인 메모리 관리
- `context_manager.py` - Smart Context (압축/해제)
- `smart_retrieval.py` - 지능형 검색
- `multi_session_sync.py` - 병렬 세션 동기화

### 현재 상태

#### ✅ 잘 작동하는 것
1. **압축/해제 메커니즘**
   - metadata + summary만 유지하여 토큰 70% 절감
   - 필요 시 full_content 복원
   - **책임성**: 과거 맥락을 언제든 복원 가능

2. **계층 구조**
   - Project → Branch → Node → Context
   - **책임성**: 맥락 조직화로 추적 가능

#### 🔴 CRITICAL 문제

**병렬 세션 맥락 충돌** (개선 완료)
```python
# 문제: 동시에 여러 터미널에서 작업 시 맥락 파일 충돌
# Terminal 1: update_memory("context A")
# Terminal 2: update_memory("context B")  # 동시 쓰기 → 데이터 손실

# 해결책: 딜레이 기반 동기화 (multi_session_sync.py)
```

**책임성 위반**: AI가 무엇을 했는지 기록이 충돌로 손실됨

#### 🟠 MEDIUM 문제

**압축 타이밍 불명확**
```python
# 현재: 30분 미사용 시 자동 압축
# 문제: 사용자가 압축 여부를 모름
# 개선 필요: 압축 시 명시적 알림 또는 로그
```

**책임성 보완**: AI가 맥락을 압축했다는 사실을 사용자에게 알려야 함

---

## 2. 출처 책임 (Source Accountability)

### 관련 모듈
- `reference_history.py` - 참조 이력 추적
- `rag_engine.py` - 기본 RAG 검색
- `hierarchical_rag.py` - 2-tier RAG

### 현재 상태

#### ✅ 잘 작동하는 것
1. **3-Tier 추천 시스템**
   - History(95%) → AI분석(70%) → 사용자선택(100%)
   - 정확도 95% 달성

2. **Co-occurrence 분석**
   - 함께 사용된 맥락 자동 추천

#### 🟡 HIGH 문제

**추천 무시 가능 (강제성 부재)**
```python
# 현재: suggest_contexts() 호출 → AI가 추천 받음 → 무시 가능
# 문제: AI가 추천을 받고도 사용하지 않을 수 있음
# 결과: 출처 없이 작업 → 책임성 위반

# 해결책 필요:
# 1. 추천 수락/거부를 명시적으로 기록
# 2. 거부 시 사유 기록 강제
# 3. 거부율이 높으면 경고
```

**책임성 위반**: AI가 무엇을 참조했는지 추적 불가

#### 🟠 MEDIUM 문제

**RAG 검색 실패 시 fallback 부재**
```python
# 현재: search_context() 실패 → 빈 결과 반환
# 문제: 왜 검색이 실패했는지 모름
# 개선: 실패 원인 로깅 + 확장 검색 시도
```

---

## 3. 주장 책임 (Claim Accountability) 🔴 CRITICAL

### 관련 모듈
- `claim_extractor.py` - Claim 추출
- `claim_verifier.py` - Claim-Evidence 매칭
- `grounding_scorer.py` - Grounding Score 계산
- `fuzzy_claim_analyzer.py` - 확신도 분석
- `contradiction_detector_v2.py` - 모순 감지
- `auto_verifier.py` - 자동 검증
- `bayesian_updater.py` - 베이지안 업데이트

### 현재 상태

#### 🔴 CRITICAL 문제 (사용자 발견)

**할루시네이션 검증 강제성 부재**
```python
# 현재 구조:
# 1. update_memory() 호출 → memory_manager에 저장
# 2. auto_verifier는 별도 호출 필요
# 3. AI가 auto_verifier를 호출하지 않으면 검증 안 됨

# 문제:
# - AI가 verify_response() 도구를 호출해야만 검증
# - 호출하지 않으면 검증 우회
# - System Prompt에 MANDATORY 있어도 실제 강제 불가

# 책임성 위반: AI가 주장에 대한 책임을 회피 가능
```

#### 개선 방향 (사용자가 작업 중)

**Option 1: memory_manager 내부 자동 검증**
```python
# memory_manager.update_memory() 내부에서 자동 검증
# Trade-off:
# - 장점: 모든 응답 자동 검증, 강제성 완벽
# - 단점: 성능 오버헤드 (모든 응답마다 LLM 호출)
```

**Option 2: Hook 기반 강제 검증**
```python
# Claude Code의 hook 시스템 활용
# update_memory() 호출 후 자동으로 verify_response() 트리거
# Trade-off:
# - 장점: 강제성 확보, 성능 오버헤드 낮음
# - 단점: Claude Code 의존성
```

**Option 3: 검증 스킵 로깅**
```python
# 검증하지 않으면 명시적으로 기록
# "⚠️ This response was not verified. Grounding score: UNKNOWN"
# Trade-off:
# - 장점: 간단, 오버헤드 없음
# - 단점: 강제성 약함
```

**권장**: Option 1 (완전한 책임성 확보)

---

## 4. 방향 책임 (Direction Accountability)

### 관련 모듈
- `branch_decision_engine.py` - 브랜치 생성 결정
- `context_graph.py` - 맥락 그래프 관리
- `pay_attention.py` - 주제 전환 감지

### 현재 상태

#### ✅ 잘 작동하는 것
1. **주제 전환 자동 감지**
   - AI가 새 주제 감지 시 브랜치 생성 제안

2. **보고 스타일 UX**
   - "브랜치를 생성합니다" (허락 구하지 않음)

#### 🟡 HIGH 문제

**브랜치 생성 검증 부재**
```python
# 현재: create_branch() → 성공/실패만 반환
# 문제: 브랜치가 실제로 잘 생성되었는지 검증 안 함

# 검증 필요:
# 1. 브랜치가 독립적으로 생성되었는가?
# 2. 이전 브랜치와 맥락이 완전히 분리되었는가?
# 3. 브랜치 메타데이터가 정확한가?

# 현재 상황:
# - create_branch() 호출 → "성공"
# - 실제로는 이전 브랜치와 맥락 혼재 가능
```

**책임성 위반**: AI가 방향을 전환했다고 주장하지만 실제로는 혼재

#### 개선 방향

```python
def create_branch_verified(project_id, branch_topic, parent_branch=None):
    """검증 포함 브랜치 생성"""
    # 1. 브랜치 생성
    result = create_branch(project_id, branch_topic, parent_branch)

    # 2. 즉시 검증
    verification = {
        "branch_exists": check_branch_exists(result.branch_id),
        "isolated": check_context_isolation(result.branch_id, parent_branch),
        "metadata_valid": check_metadata_integrity(result.branch_id)
    }

    # 3. 검증 실패 시 롤백
    if not all(verification.values()):
        rollback_branch(result.branch_id)
        raise BranchCreationError(f"Verification failed: {verification}")

    return result
```

---

## 5. 변경 책임 (Change Accountability)

### 관련 모듈
- `git_sync.py` - Git 연동
- `backup_manager.py` - 백업/복구
- `extension_sync.py` - 확장 동기화

### 현재 상태

#### ✅ 잘 작동하는 것
1. **Git 브랜치 자동 연동**
   - Git 브랜치 전환 → Cortex 브랜치 전환

2. **스냅샷 자동 생성**
   - 커밋 시 맥락 스냅샷

#### 🟡 HIGH 문제

**Backup 복구 검증 부재**
```python
# 현재: restore_snapshot() → "복구 완료"
# 문제: 실제로 맥락이 완전히 복구되었는지 검증 안 함

# 위험 시나리오:
# 1. 스냅샷 생성 시 일부 파일 누락
# 2. 복구 시 파일 손상
# 3. 복구 완료 메시지만 보고 사용자는 모름
# 4. 나중에 중요한 맥락이 없는 걸 발견

# 책임성 위반: AI가 "복구했다"고 주장하지만 실제로는 불완전
```

#### 개선 방향

```python
def restore_snapshot_verified(project_id, snapshot_id):
    """검증 포함 스냅샷 복구"""
    # 1. 복구 전 현재 상태 해시
    before_hash = calculate_state_hash(project_id)

    # 2. 스냅샷 정보 확인
    snapshot_info = get_snapshot_info(project_id, snapshot_id)
    expected_hash = snapshot_info["content_hash"]

    # 3. 복구 수행
    restore_snapshot(project_id, snapshot_id)

    # 4. 복구 후 상태 해시
    after_hash = calculate_state_hash(project_id)

    # 5. 검증
    verification = {
        "hash_match": after_hash == expected_hash,
        "file_count_match": check_file_count(project_id, snapshot_info),
        "integrity_check": verify_context_integrity(project_id)
    }

    if not all(verification.values()):
        # 복구 실패 → 이전 상태로 롤백
        restore_from_backup(project_id, before_hash)
        raise RestoreVerificationError(f"Verification failed: {verification}")

    return {
        "status": "verified",
        "verification": verification
    }
```

---

## 6. 확신 책임 (Confidence Accountability)

### 관련 모듈
- `automation_manager.py` - Plan A/B 전환
- `control_state.py` - 상태 관리
- `auto_verifier.py` - 자동 검증

### 현재 상태

#### ✅ 잘 작동하는 것
1. **Plan A/B 자동 전환**
   - 거부율 30%+ → Plan B 자동 전환

2. **Control State 동기화**
   - `_settings`와 `control_state_manager` 동기화

#### 🟠 MEDIUM 문제

**Plan B 전환 우회 가능**
```python
# 현재: 거부율 계산 기준이 느슨함
# - 거부: user가 명시적으로 "거부"
# - 문제: user가 조용히 무시하거나, 나중에 수정하면 카운트 안 됨

# 실제 시나리오:
# AI: "파일 X를 수정했습니다"
# User: (아무 말 안 함, 나중에 직접 수정)
# 시스템: "수락으로 간주" ← 잘못됨

# 책임성 위반: AI가 확신하지만 실제로는 틀림
```

#### 개선 방향

```python
def record_implicit_rejection():
    """암묵적 거부 감지"""
    # 1. AI가 "완료"라고 한 작업
    claimed_actions = get_recent_claims(time_window=300)  # 5분 이내

    # 2. User가 같은 파일을 다시 수정했는가?
    for claim in claimed_actions:
        if claim.type == "file_modification":
            # Git log로 확인
            subsequent_changes = git_log(claim.file, since=claim.timestamp)

            if subsequent_changes:
                # User가 다시 수정 → 암묵적 거부
                record_feedback(
                    action_id=claim.id,
                    feedback="implicit_rejection",
                    reason="User re-modified the same file"
                )
```

---

## 7. 동시성 & 멀티 세션 문제

### 관련 모듈
- `multi_session_sync.py` - 병렬 세션 동기화
- `extension_sync.py` - 확장 동기화
- `team_merge.py` - 팀 병합

### 현재 상태

#### ✅ 개선 완료 (사용자 작업)
- 병렬 대화 중 맥락 충돌 해결 (딜레이 기반)

#### 🟠 MEDIUM 문제

**파일 잠금 메커니즘 부재**
```python
# 현재: 딜레이 기반 충돌 회피
# 문제: 극단적 동시성 시 여전히 충돌 가능

# 개선: 파일 잠금
import fcntl

def update_memory_with_lock(project_id, branch_id, content):
    lock_file = f"/tmp/cortex_{project_id}_{branch_id}.lock"

    with open(lock_file, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 배타적 잠금
        try:
            # 실제 업데이트
            result = update_memory(project_id, branch_id, content)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # 잠금 해제

    return result
```

---

## 8. 보안 & 경계 보호

### 관련 모듈
- `boundary_protection.py` - 작업 경계 보호
- `crypto_utils.py` - 암호화
- `license_manager.py` - 라이센스 관리

### 현재 상태

#### ✅ 잘 작동하는 것
1. **Zero-Trust 원칙**
   - 모든 데이터 로컬 저장

2. **E2E 암호화**
   - 클라우드 동기화 시 암호화

#### 🟠 MEDIUM 문제

**Boundary 검증 타이밍**
```python
# 현재: validate_boundary_action() → 사전 검증
# 문제: 검증 후 실제 작업 사이에 시간 차이

# Race condition:
# 1. validate_boundary_action("write", "file.py") → OK
# 2. [다른 세션에서 boundary 변경]
# 3. write("file.py") → 실제로는 경계 위반

# 개선: Transaction 방식
def atomic_boundary_action(action, file_path, content):
    with boundary_lock():
        if not validate_boundary_action(action, file_path):
            raise BoundaryViolationError()
        perform_action(action, file_path, content)
```

---

## 9. 온톨로지 & 시맨틱 웹

### 관련 모듈
- `ontology_engine.py` - 온톨로지 분류
- `semantic_web.py` - 시맨틱 관계 추론

### 현재 상태

#### ✅ 잘 작동하는 것
1. **자동 분류**
   - 맥락을 카테고리로 자동 분류 (confidence >= 0.50)

#### 🟢 LOW 문제

**온톨로지 분류 검증 부재**
```python
# 현재: 분류 결과를 그대로 사용
# 개선: 사용자 피드백 수집
# "이 맥락이 'Authentication' 카테고리가 맞나요?"
# → 피드백으로 분류기 재훈련
```

---

## 10. 텔레메트리 & 로깅

### 관련 모듈
- `telemetry.py`, `telemetry_storage.py`, etc.
- `alpha_logger.py` - 알파 테스트 로그
- `research_logger.py` - 연구 로그

### 현재 상태

#### ✅ 잘 작동하는 것
1. **기능별 로그 수집**
   - 알파 테스트용 상세 로깅

#### 🟢 LOW 문제

**로그 개인정보 필터링 부재**
```python
# 현재: 모든 데이터 로깅
# 문제: PII(개인정보) 포함 가능

# 개선:
def sanitize_log_entry(entry):
    # 이메일, API 키, 비밀번호 등 마스킹
    patterns = [
        (r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]'),
        (r'\b[A-Za-z0-9]{32,}\b', '[API_KEY]'),
        (r'password[:=]\s*\S+', 'password=[REDACTED]')
    ]
    for pattern, replacement in patterns:
        entry = re.sub(pattern, replacement, entry)
    return entry
```

---

## 종합 우선순위

### 🔴 CRITICAL (즉시 수정 필요)

1. **할루시네이션 검증 강제성 확보**
   - 현재: 개선 중 (사용자 작업)
   - 조치: memory_manager에 자동 검증 통합
   - 예상 시간: 2-3시간
   - Trade-off: 성능 오버헤드 vs 완벽한 책임성

### 🟡 HIGH (Phase 2에서 수정)

2. **Reference History 추천 강제**
   - 추천 수락/거부 명시적 기록
   - 거부 시 사유 강제
   - 예상 시간: 1-2시간

3. **브랜치 생성 검증**
   - create_branch_verified() 구현
   - 예상 시간: 1시간

4. **Backup 복구 검증**
   - restore_snapshot_verified() 구현
   - 예상 시간: 2시간

### 🟠 MEDIUM (Phase 3+)

5. **Plan B 암묵적 거부 감지**
   - Git log 기반 재작업 감지
   - 예상 시간: 2-3시간

6. **파일 잠금 메커니즘**
   - fcntl 기반 잠금
   - 예상 시간: 1시간

7. **압축 알림**
   - 압축 시 명시적 로깅
   - 예상 시간: 30분

### 🟢 LOW (개선 권장)

8. **온톨로지 피드백 루프**
9. **로그 PII 필터링**
10. **Boundary atomic transaction**

---

## 결론

### 핵심 발견

1. **가장 큰 문제**: 할루시네이션 검증의 강제성 부재
   - AI가 "주장에 대한 책임"을 회피 가능
   - **반드시 수정 필요**

2. **두 번째 문제**: Reference History 추천 무시 가능
   - AI가 "출처에 대한 책임"을 회피 가능
   - Phase 2에서 수정

3. **세 번째 문제**: 검증 메커니즘 부재
   - 브랜치 생성, 백업 복구 등이 "성공"이라고 하지만 실제로는 불완전할 수 있음
   - 검증 레이어 추가 필요

### 권장 조치

**Phase 2 개선 항목 (우선순위순)**

1. 할루시네이션 검증 강제 (CRITICAL) - 사용자 작업 중
2. Reference History 강제 (HIGH)
3. 브랜치 생성 검증 (HIGH)
4. Backup 복구 검증 (HIGH)
5. Plan B 개선 (MEDIUM)

**Trade-off 고려사항**

- 강제성 ↑ = 성능 ↓ (하지만 책임성 확보가 우선)
- 검증 레이어 추가 = 복잡도 ↑ (하지만 신뢰성 확보 필수)
- 파일 잠금 = 동시성 ↓ (하지만 데이터 무결성 필수)

**최종 판단**: 성능보다 책임성이 우선. 모든 CRITICAL/HIGH 항목 수정 권장.

---

*검토 완료: 2025-12-23*
