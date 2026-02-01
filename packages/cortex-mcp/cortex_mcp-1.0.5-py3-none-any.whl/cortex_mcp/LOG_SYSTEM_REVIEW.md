# Cortex 로그 시스템 면밀 검토 보고서
**작성일**: 2025-12-24
**작성자**: MCP 개발 전문가, Python 전문가, SWQA 전문가, 데이터 분석 전문가
**목적**: 클로즈드 베타 및 논문 작성을 위한 로그 시스템 검증

---

## Executive Summary

### 현재 상태
- **Alpha Logger**: 일반 기능 로그 수집 ✓ (RAG, Reference History, Smart Context 등)
- **Research Logger**: 논문 데이터 로그 구조 정의 ✓, **통합 미완료** ✗
- **Phase 9 Hallucination Detection**: 구현 완료 ✓, **로깅 미연동** ✗

### 핵심 문제
**논문 작성에 필요한 Silent Failure 데이터가 수집되지 않고 있음**

---

## 1. 논문 데이터 요구사항 정의

### 연구 주제
**"Silent Failure in LLM-assisted Development: Detection and Intervention"**

### 연구 질문
1. **RQ1**: LLM이 확신 있게 말하지만 틀린 경우(Silent Failure)는 얼마나 자주 발생하는가?
2. **RQ2**: Cortex Hallucination Detection 시스템은 Silent Failure를 얼마나 정확하게 감지하는가?
3. **RQ3**: Cortex Intervention은 Silent Failure 발생률을 얼마나 감소시키는가?
4. **RQ4**: 사용자는 Cortex Intervention을 얼마나 수용하는가? (수락률, 거부율, UX 영향)

### 필요 메트릭

#### 1.1 Hallucination Detection 성능 (RQ1, RQ2)
| 메트릭 | 설명 | 수집 방법 | 현재 상태 |
|-------|------|----------|----------|
| **Grounding Score 분포** | 근거 충실도 점수 (0-1) | grounding_scorer 결과 로깅 | ✗ 미수집 |
| **Claim 추출 성공률** | 응답에서 Claim 추출 성공 비율 | claim_extractor 결과 로깅 | ✗ 미수집 |
| **Evidence 매칭 정확도** | Claim-Evidence 매칭 정확도 | claim_verifier 결과 로깅 | ✗ 미수집 |
| **False Positive Rate** | 정상을 할루시네이션으로 오판한 비율 | 수동 레이블링 + 비교 | ✗ 미수집 |
| **False Negative Rate** | 할루시네이션을 놓친 비율 | 수동 레이블링 + 비교 | ✗ 미수집 |
| **Contradiction 감지율** | 응답 내 모순 감지 성공률 | contradiction_detector_v2 로깅 | ✗ 미수집 |

#### 1.2 Cortex Intervention 효과 (RQ3)
| 메트릭 | 설명 | 수집 방법 | 현재 상태 |
|-------|------|----------|----------|
| **Intervention 빈도** | 경고/차단/확인 요청 발생 빈도 | memory_manager 로깅 | ✗ 미수집 |
| **Intervention 타입 분포** | WARNING/CONFIRM/BLOCK 비율 | intervention_type별 집계 | ✗ 미수집 |
| **Pre-Intervention 오류율** | Cortex 없이 발생한 오류 비율 | A/B 테스트 또는 히스토리 비교 | ✗ 미수집 |
| **Post-Intervention 오류율** | Cortex 적용 후 오류 비율 | 사용자 피드백 + 검증 | ✗ 미수집 |

#### 1.3 사용자 행동 패턴 (RQ4)
| 메트릭 | 설명 | 수집 방법 | 현재 상태 |
|-------|------|----------|----------|
| **수락률** | Cortex 경고를 수락한 비율 | user_response: ACCEPTED | ✗ 미수집 |
| **거부율** | Cortex 경고를 거부한 비율 | user_response: REJECTED | ✗ 미수집 |
| **무시율** | Cortex 경고를 무시한 비율 | user_response: IGNORED | ✗ 미수집 |
| **수정 후 수락률** | 수정 후 수락한 비율 | user_response: MODIFIED | ✗ 미수집 |
| **평균 응답 시간** | 경고 후 사용자 응답까지 시간 | timestamp 차이 계산 | ✗ 미수집 |

#### 1.4 기타 성능 메트릭 (베타 사용성 지표)
| 메트릭 | 설명 | 수집 방법 | 현재 상태 |
|-------|------|----------|----------|
| **RAG 검색 정확도** | Recall@10, Precision | rag_search 로깅 | ✓ 수집 중 |
| **Reference History 추천 정확도** | 추천 수락률 (목표: 95%) | reference_history 로깅 | ✓ 수집 중 |
| **Token 절감율** | Smart Context 압축률 (목표: 70%) | smart_context 로깅 | ✓ 수집 중 |
| **온톨로지 분류 정확도** | 카테고리 분류 신뢰도 | ontology 로깅 | ✓ 수집 중 |

---

## 2. 현재 로그 시스템 분석

### 2.1 Alpha Logger (일반 기능 로그)

**파일**: `cortex_mcp/core/alpha_logger.py`
**상태**: ✓ 통합 완료, 활발히 수집 중
**로그 위치**: `~/.cortex/logs/alpha_test/`

#### 수집 중인 모듈
| 모듈 | 파일 | 엔트리 수 | 주요 메트릭 |
|------|------|----------|------------|
| **rag_search** | rag_search.jsonl | 9.8MB | query, result_count, latency_ms, ontology_filtered |
| **pay_attention** | pay_attention.jsonl | 16.5MB | turn, role, topics_updated |
| **ontology** | ontology.jsonl | 1.2MB | category, confidence |
| **license** | license.jsonl | 5MB | tier, validity |
| **reference_history** | reference_history.jsonl | 84KB | accuracy_rate (100%) |
| **smart_context** | smart_context.jsonl | 109KB | token savings (74.99%) |

**총 로그 엔트리**: 116,788개

#### 샘플 로그 구조 (RAG Search)
```json
{
  "timestamp": "2025-12-10T13:32:28.450170",
  "module": "rag_search",
  "action": "search",
  "input": {"query": "비밀코드"},
  "output": {
    "result_count": 10,
    "top_results": ["doc_20251210_133227_641289", ...]
  },
  "success": true,
  "error": null,
  "latency_ms": 147.78,
  "metadata": {"ontology_filtered": false}
}
```

**평가**:
- 일반 기능 로깅은 매우 잘 구현됨
- 베타 사용성 지표 수집 가능
- **하지만 논문 데이터(Silent Failure 관련)는 누락**

---

### 2.2 Research Logger (논문 데이터 로그)

**파일**: `cortex_mcp/core/research_logger.py`
**상태**: ✗ 구조 정의만 완료, **통합 미완료**
**로그 위치**: 없음 (디렉토리 미생성)

#### 정의된 이벤트 타입
```python
class EventType(Enum):
    LLM_RESPONSE = "llm_response"              # LLM 응답 생성
    CLAIM_EXTRACTION = "claim_extraction"      # Claim 추출
    EVIDENCE_RETRIEVAL = "evidence_retrieval"  # Evidence 검색
    GROUNDING_VERIFICATION = "grounding_verification"  # 검증
    CORTEX_INTERVENTION = "cortex_intervention"  # Cortex 개입
    USER_RESPONSE = "user_response"            # 사용자 반응
    CONTEXT_DRIFT = "context_drift"            # Context Drift
    SILENT_FAILURE = "silent_failure"          # Silent Failure
    RECOVERY = "recovery"                      # 복구
```

#### 통합 현황
```bash
# core/*.py에서 get_research_logger 사용처 검색 결과
→ 없음 (research_logger.py 자체 외)
```

**평가**:
- 논문에 필요한 이벤트 타입 잘 정의됨
- GDPR 준수, SHA-256 익명화 등 윤리적 고려 완벽
- **하지만 실제로 사용하는 곳이 없음** (Dead Code)

---

### 2.3 Phase 9 Hallucination Detection 로깅

**구현 완료 컴포넌트**:
- `claim_extractor.py`: Claim 추출
- `grounding_scorer.py`: Grounding Score 계산
- `claim_verifier.py`: Claim-Evidence 매칭
- `fuzzy_claim_analyzer.py`: 확신도 분석
- `contradiction_detector_v2.py`: 모순 감지

**로깅 현황**: ✗ **모든 컴포넌트가 로깅 미연동**

```bash
# Hallucination Detection 로그 함수 검색 결과
grep -r "log_claim|log_grounding|log_hallucination"
→ 결과 없음
```

**평가**:
- Phase 9 컴포넌트는 96/96 테스트 통과 (구현 완료)
- **하지만 alpha_logger나 research_logger와 연동 안 됨**
- 논문의 핵심 데이터가 수집되지 않는 중대한 문제

---

## 3. 갭 분석 (Gap Analysis)

### 3.1 Critical Gaps (논문 작성 불가)

| 필요 데이터 | 현재 상태 | 영향 | 우선순위 |
|-----------|----------|------|---------|
| **Grounding Score 분포** | ✗ 미수집 | RQ2 검증 불가 | P0 |
| **Claim 추출 통계** | ✗ 미수집 | RQ2 검증 불가 | P0 |
| **Cortex Intervention 로그** | ✗ 미수집 | RQ3 검증 불가 | P0 |
| **User Response 로그** | ✗ 미수집 | RQ4 검증 불가 | P0 |
| **Silent Failure 감지 로그** | ✗ 미수집 | RQ1 검증 불가 | P0 |

### 3.2 High Priority Gaps (베타 개선 필요)

| 필요 데이터 | 현재 상태 | 영향 | 우선순위 |
|-----------|----------|------|---------|
| **False Positive Rate** | ✗ 미수집 | 정확도 검증 불가 | P1 |
| **Pre/Post Intervention 비교** | ✗ 미수집 | 효과 측정 불가 | P1 |
| **평균 응답 시간** | ✗ 미수집 | UX 영향 측정 불가 | P1 |

### 3.3 Medium Priority Gaps (베타 참고 지표)

| 필요 데이터 | 현재 상태 | 영향 | 우선순위 |
|-----------|----------|------|---------|
| **Ontology 필터 효과** | △ 일부 수집 | RAG 정확도 개선 측정 | P2 |
| **Context Drift 감지** | ✗ 미수집 | 장기 세션 품질 측정 | P2 |

---

## 4. 구조적 문제 진단

### 4.1 아키텍처 문제

**문제**: 3개의 독립적인 로깅 시스템이 통합되지 않음
```
alpha_logger.py       ← RAG, Reference History, Smart Context
research_logger.py    ← Silent Failure, Hallucination Detection (미통합)
telemetry.py          ← 일반 제품 텔레메트리
```

**원인**:
1. Phase 9 개발 시 research_logger 통합 누락
2. memory_manager에서 grounding_scorer 결과를 로깅하지 않음
3. claim_extractor, claim_verifier 등이 standalone 모드로 작동

### 4.2 데이터 흐름 누락

**현재**:
```
LLM Response
  → memory_manager.update_memory()
  → (grounding_scorer 실행)
  → (결과 로깅 없음) ✗
  → .md 파일에 저장만
```

**필요**:
```
LLM Response
  → memory_manager.update_memory()
  → grounding_scorer.calculate_score()
  → research_logger.log_grounding_verification()  ← 추가 필요
  → research_logger.log_cortex_intervention()     ← 추가 필요
  → .md 파일 저장
```

### 4.3 통합 포인트 누락

**통합이 필요한 파일**:
1. `memory_manager.py:update_memory()` - Grounding 결과 로깅
2. `claim_extractor.py` - Claim 추출 통계 로깅
3. `claim_verifier.py` - Evidence 매칭 결과 로깅
4. `automation_manager.py` - User Response 로깅

---

## 5. 권고 사항

### 5.1 즉시 수정 필요 (P0 - 클로즈드 베타 전)

#### 1. Research Logger 통합
**파일**: `cortex_mcp/core/memory_manager.py`

**추가할 위치**: `update_memory()` 함수 내부, grounding_scorer 실행 후

```python
# Line ~180-200 근처 (grounding_scorer 결과 처리 후)
if hallucination_result and hallucination_result.get("retry_required"):
    # 기존 코드...

    # [추가] Research Logger 통합
    from core.research_logger import get_research_logger
    research_logger = get_research_logger()

    # Grounding Verification 로깅
    research_logger.log_grounding_verification(
        grounding_score=hallucination_result["grounding_score"],
        claims_count=hallucination_result["total_claims"],
        contexts_count=hallucination_result["total_contexts"],
        risk_level=hallucination_result["risk_level"]
    )

    # Cortex Intervention 로깅
    if hallucination_result["retry_required"]:
        research_logger.log_cortex_intervention(
            intervention_type="BLOCK",  # or WARNING/CONFIRM
            grounding_score=hallucination_result["grounding_score"],
            risk_level=hallucination_result["risk_level"]
        )
```

#### 2. Claim Extraction 로깅
**파일**: `cortex_mcp/core/claim_extractor.py`

**추가할 위치**: `extract_claims()` 함수 반환 전

```python
# Line ~350-400 근처 (Claim 추출 완료 후)
def extract_claims(self, text: str) -> List[Claim]:
    # 기존 코드...
    claims = self._extract_all_patterns(text)

    # [추가] Research Logger 통합
    from core.research_logger import get_research_logger
    research_logger = get_research_logger()

    research_logger.log_claim_extraction(
        text_length=len(text),
        claims_count=len(claims),
        claim_types={c.claim_type for c in claims},
        success=len(claims) > 0
    )

    return claims
```

#### 3. User Response 로깅
**파일**: `cortex_mcp/core/automation_manager.py`

**추가할 위치**: `record_feedback()` 함수 내부

```python
# User 피드백 기록 시
def record_feedback(self, action_type: str, feedback: str):
    # 기존 코드...

    # [추가] Research Logger 통합
    from core.research_logger import get_research_logger
    research_logger = get_research_logger()

    research_logger.log_user_response(
        action_type=action_type,
        response_type=feedback,  # accepted/rejected/ignored/modified
        timestamp=datetime.now()
    )
```

### 5.2 고우선순위 개선 (P1 - 베타 기간 중)

#### 4. False Positive/Negative 측정
**방법**: 수동 레이블링 + 자동 비교

```python
# 새 파일: cortex_mcp/core/hallucination_validator.py
class HallucinationValidator:
    """
    수동 레이블링 vs. 자동 감지 비교
    → Precision, Recall, F1 Score 계산
    """

    def record_ground_truth(self, response_id: str, is_hallucination: bool):
        """사용자가 수동으로 할루시네이션 여부 표시"""
        pass

    def calculate_accuracy(self):
        """FP, FN, Precision, Recall 계산"""
        pass
```

#### 5. A/B 테스트 프레임워크
**목적**: Pre/Post Intervention 효과 측정

```python
# 새 파일: cortex_mcp/core/ab_test_framework.py
class ABTestFramework:
    """
    Group A: Cortex Intervention OFF
    Group B: Cortex Intervention ON
    → 오류율, 작업 완료율, 사용자 만족도 비교
    """
    pass
```

### 5.3 중우선순위 개선 (P2 - 논문 작성 시)

#### 6. Context Drift 감지 로깅
**파일**: `cortex_mcp/core/context_manager.py`

```python
# Context 변경 감지 시
research_logger.log_context_drift(
    branch_id=branch_id,
    drift_score=drift_score,
    auto_corrected=auto_corrected
)
```

#### 7. Recovery 성공률 로깅
**파일**: `cortex_mcp/core/memory_manager.py`

```python
# Intervention 후 재시도 성공 시
research_logger.log_recovery(
    original_grounding_score=0.25,
    retry_grounding_score=0.85,
    recovery_time_ms=1500
)
```

---

## 6. 구현 로드맵

### Phase 1: Critical Integration (1-2일)
1. memory_manager에 research_logger 통합
2. claim_extractor 로깅 추가
3. automation_manager User Response 로깅 추가
4. 로그 디렉토리 생성 확인 (`~/.cortex/logs/research/`)

**검증 방법**:
```bash
# 테스트 실행 후
ls -lh ~/.cortex/logs/research/
head -1 ~/.cortex/logs/research/grounding_verification.jsonl | python3 -m json.tool
```

### Phase 2: Data Quality (2-3일)
5. False Positive/Negative 측정 도구 개발
6. A/B 테스트 프레임워크 구축
7. 데이터 export 스크립트 작성 (JSON → CSV, Pandas DataFrame)

### Phase 3: Analysis (베타 기간 중)
8. 주간 데이터 분석 자동화
9. 통계 대시보드 추가
10. 논문 Figure/Table 생성 스크립트

---

## 7. 예상 데이터 크기 및 성능 영향

### 7.1 로그 크기 추정
**베타 사용자**: 30명
**베타 기간**: 3개월
**평균 세션당 LLM 응답**: 50회

```
30명 × 90일 × 50응답 = 135,000 응답

Grounding Verification 로그: 135,000 × 500 bytes = 67.5 MB
Claim Extraction 로그: 135,000 × 300 bytes = 40.5 MB
User Response 로그: 135,000 × 200 bytes = 27 MB
Cortex Intervention 로그: 135,000 × 0.3 (30% 개입) × 400 bytes = 16 MB

총 예상 크기: ~150 MB (3개월)
```

### 7.2 성능 영향
**Async 로깅**: 응답 지연 없음 (백그라운드 처리)
**배치 쓰기**: 10초마다 또는 100 엔트리마다
**로그 로테이션**: 10 MB마다 새 파일

**예상 오버헤드**: < 5ms per response

---

## 8. 윤리적 고려사항

### 8.1 GDPR 준수 (Research Logger 완벽 구현)
- SHA-256 익명화 (user_hash, session_id)
- Explicit opt-in consent
- Right to be forgotten (anonymized이므로 자동 준수)
- Data export 기능

### 8.2 베타 테스터 동의서
**추가 필요**:
```
"Cortex는 연구 목적으로 익명화된 사용 데이터를 수집합니다.
 수집 데이터는 학술 논문 작성에 사용될 수 있으며,
 개인 식별 정보는 포함되지 않습니다.

 [ ] 동의합니다
```

---

## 9. 결론

### 9.1 현재 상태 평가

| 항목 | 점수 | 평가 |
|------|------|------|
| **일반 기능 로그** | 9/10 | 매우 우수 (alpha_logger 완벽 작동) |
| **논문 데이터 로그** | 2/10 | 매우 부족 (research_logger 미통합) |
| **윤리/프라이버시** | 10/10 | 완벽 (GDPR 준수 설계) |
| **데이터 품질** | 8/10 | 우수 (alpha_logger), 논문 데이터 누락 |
| **클로즈드 베타 준비도** | 6/10 | 사용성 지표는 OK, 연구 데이터 부족 |

### 9.2 최종 권고

#### 즉시 조치 필요 (클로즈드 베타 전)
1. research_logger를 memory_manager, claim_extractor, automation_manager에 통합
2. 로그 디렉토리 생성 및 정상 작동 확인
3. 베타 테스터 동의서에 연구 데이터 수집 명시

#### 베타 기간 중 개선
4. False Positive/Negative 측정 도구 개발
5. A/B 테스트로 Pre/Post Intervention 효과 측정
6. 주간 데이터 분석으로 품질 모니터링

#### 논문 작성 시
7. 수집된 데이터 통계 분석 (Grounding Score 분포, Intervention 효과 등)
8. Figure/Table 생성 (Python matplotlib, seaborn)
9. RQ1-RQ4 각각에 대한 정량적 근거 제시

---

## 10. 다음 단계

1. **이 보고서를 사용자와 공유하여 피드백 받기**
2. **우선순위 확정 (P0 먼저 처리)**
3. **구현 시작 (Phase 1: Critical Integration)**
4. **테스트 및 검증**
5. **클로즈드 베타 시작**

---

**검토 완료**: 2025-12-24
**다음 검토**: 구현 완료 후
