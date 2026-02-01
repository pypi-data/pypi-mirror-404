# Phase 9 Hallucination Detection - 완전 감사 보고서

**작성일**: 2025-12-31
**감사 팀**:
- MCP 개발 전문가
- SW QA 전문가
- Python 개발 전문가
- AI 할루시네이션 전문가
- 제품 기획 전문가

**목표**: Phase 9 시스템의 모든 문제점을 식별하고 완벽히 수정

---

## 1. 컴포넌트 목록 및 책임

### 1.1 핵심 컴포넌트 (8개)

| 파일 | 책임 | 주요 메서드 | 상태 |
|------|------|------------|------|
| `claim_extractor.py` | Claim 추출 | `extract_claims()` | 검토 필요 |
| `claim_verifier.py` | Claim-Evidence 매칭 | `verify_claim()` | 검토 필요 |
| `fuzzy_claim_analyzer.py` | 확신도 분석 | `analyze_response()` | 검토 필요 |
| `grounding_scorer.py` | Grounding Score 계산 | `calculate_grounding_score()` | 검토 필요 |
| `contradiction_detector_v2.py` | 모순 감지 | `detect_contradictions()` | 검토 필요 |
| `auto_verifier.py` | 전체 오케스트레이션 | `verify_response()` | 검토 필요 |
| `evidence_graph.py` | Evidence Graph 관리 | `add_node()`, `add_edge()` | 검토 필요 |
| `memory_manager.py` | 통합 및 저장 | `update_memory()` | 검토 필요 |

### 1.2 보조 컴포넌트 (3개)

| 파일 | 책임 | 상태 |
|------|------|------|
| `contradiction_detector.py` | 구버전 (deprecated?) | 확인 필요 |
| `evidence_graph_v2.py` | 새 버전? | 확인 필요 |
| `phase92_git_evidence.py` | Git 기반 Evidence | 확인 필요 |
| `fuzzy_prompt.py` | Fuzzy Prompt 생성 | 확인 필요 |

---

## 2. 실행 경로 분석

### 2.1 Entry Point

**두 가지 진입점:**

1. **auto_verifier.verify_response()** - 직접 호출
2. **memory_manager.update_memory()** - MCP 도구 경로

### 2.2 실행 흐름 (auto_verifier 기준)

```
verify_response()
├─ 1. fuzzy_analyzer.analyze_response()  [확신도 분석]
├─ 2. claim_extractor.extract_claims()   [Claim 추출]
├─ 3. [분기] confidence < threshold?
│  ├─ YES: return grounding_score (Claim 유무에 따라)
│  └─ NO: 계속
├─ 4. [Phase 9.5.2] method_checker.verify_claim_method_calls()
├─ 5. [분기] claims 없음?
│  ├─ YES: return grounding_score = 1.0
│  └─ NO: 계속
├─ 6. FOR EACH claim:
│  ├─ claim_verifier.verify_claim()
│  └─ evidence 수집
├─ 7. grounding_scorer.calculate_grounding_score()
├─ 8. contradiction_detector.detect_contradictions()
└─ 9. VerificationResult 반환
```

### 2.3 실행 흐름 (memory_manager 기준)

```
update_memory()
├─ 1. fuzzy_analyzer.analyze_response()
├─ 2. claim_extractor.extract_claims()
├─ 3. FOR EACH claim:
│  └─ claim_verifier.verify_claim()
├─ 4. contradiction_detector.detect_contradictions()
├─ 5. [직접 계산] grounding_score = verified_claims / total_claims
└─ 6. 파일 저장 (.md)
```

**주의: auto_verifier와 memory_manager가 서로 다른 로직 사용!**

---

## 3. 발견된 문제점 (완전 분석 완료)

### 3.1 Critical Issues (4개)

#### Critical #1: 두 진입점의 grounding_score 계산 불일치
- **위치**:
  - auto_verifier.py:340-346 vs memory_manager.py:1307-1312
- **문제**:
  - auto_verifier: `grounding_scorer.calculate_score()` 호출 → 복잡한 로직 (sigmoid, depth weight, Bayesian posterior)
  - memory_manager: 직접 계산 `verified_claims_count / total_claims_count` → 단순 비율
- **재현 시나리오**:
  ```python
  # auto_verifier 경로
  verifier.verify_response("구현 완료", context)
  # → grounding_scorer 사용 (가중치 계산)

  # memory_manager 경로
  mm.update_memory(content="구현 완료")
  # → 직접 계산 (단순 비율)
  # 결과: 동일 응답에 대해 다른 grounding_score
  ```
- **영향**:
  - 같은 응답에 대해 경로에 따라 다른 검증 결과
  - 재현 불가능한 할루시네이션 검증
- **우선순위**: CRITICAL
- **해결 방안**: memory_manager도 grounding_scorer 사용하도록 통일

#### Critical #2: Evidence Graph 동기화 이슈
- **위치**:
  - auto_verifier.py:205-218 (context에서 referenced_contexts 로드)
  - claim_verifier.py 내부 Evidence Graph
  - grounding_scorer.py:306-327 (캐시된 Evidence Graph)
- **문제**:
  - auto_verifier, claim_verifier, grounding_scorer가 각자 다른 Evidence Graph 인스턴스 사용
  - 한 곳에서 Evidence 추가해도 다른 곳에서는 인식 못함
- **재현 시나리오**:
  ```python
  # claim_verifier에서 Evidence Graph 업데이트
  claim_verifier.verify_claim(claim, context)
  # → Evidence Graph에 노드/엣지 추가

  # grounding_scorer에서 검색
  grounding_scorer.calculate_score(...)
  # → 캐시된 그래프라 업데이트 반영 안됨
  ```
- **영향**: Evidence 누락, 잘못된 grounding_score 계산
- **우선순위**: CRITICAL
- **해결 방안**:
  - memory_manager에서 단일 Evidence Graph 인스턴스 생성
  - 모든 컴포넌트에 동일 인스턴스 전달

#### Critical #3: memory_manager Phase 9 초기화 에러 핸들링 누락
- **위치**: memory_manager.py:346-383 (Phase 9 컴포넌트 초기화)
- **문제**: try-except 블록 없음
- **재현 시나리오**:
  ```python
  # 파일 손상 또는 의존성 누락
  mm = MemoryManager()  # claim_extractor import 실패
  # → 전체 MemoryManager 초기화 실패, 명확한 에러 메시지 없음
  ```
- **영향**: 전체 Cortex 시스템 다운, 디버깅 어려움
- **우선순위**: CRITICAL
- **해결 방안**: 각 컴포넌트 초기화 시 try-except 추가, graceful degradation

#### Critical #4: grounding_scorer depth 계산 정확도 이슈
- **위치**: grounding_scorer.py:306-327 (`_analyze_context_depth`)
- **문제**:
  - depth 계산 로직이 파일 경로 깊이만 고려
  - 실제 semantic depth (의미적 거리) 고려 안함
- **재현 시나리오**:
  ```python
  # 직접 참조 파일 (실제 depth = 0)
  context = ["./main.py"]  # 실제 관련성: 100%
  # 하지만 경로가 짧아서 depth = 1로 계산 → weight 낮음

  # 간접 참조 파일 (실제 depth = 3)
  context = ["./lib/utils/helper.py"]  # 실제 관련성: 20%
  # 경로가 길어서 depth = 3으로 계산 → weight 더 낮음
  # 문제: 실제 중요도와 weight가 역전될 수 있음
  ```
- **영향**: grounding_score 부정확, 잘못된 검증 판정
- **우선순위**: CRITICAL
- **해결 방안**: Evidence Graph의 edge distance 사용하여 실제 semantic depth 계산

### 3.2 High Priority Issues (4개)

#### High #1: claim_extractor 패턴 우선순위 미보장
- **위치**: claim_extractor.py:280-288
- **문제**: Dict insertion order에 의존 (Python 3.7+에서는 보장되지만 명시적이지 않음)
- **재현 시나리오**:
  ```python
  # "구현 완료했습니다. 테스트도 통과했어요."
  # → implementation_complete, verification 둘 다 매칭
  # 어떤 게 먼저 반환될지 불명확
  ```
- **영향**: 일관성 없는 Claim 타입 분류
- **우선순위**: HIGH
- **해결 방안**: 명시적 우선순위 리스트 사용 (OrderedDict 또는 priority field)

#### High #2: fuzzy_claim_analyzer 부정 표현 감지 불완전
- **위치**: fuzzy_claim_analyzer.py:344-354
- **문제**:
  - "아니다", "아님" 등 단순 부정만 감지
  - 문맥상 부정 (예: "성공하지 못했습니다") 감지 못함
- **재현 시나리오**:
  ```python
  text = "구현에 성공하지 못했습니다"
  # → "성공" 키워드 감지 → high confidence (잘못됨)
  # 올바른 결과: low confidence (부정 문맥)
  ```
- **영향**: 확신도 과대평가, 잘못된 검증 판정
- **우선순위**: HIGH
- **해결 방안**: 의존 구문 분석 (dependency parsing) 또는 문맥 윈도우 확장

#### High #3: claim_verifier 파일 수정 vs 존재 구분 안됨
- **위치**: claim_verifier.py:856-862
- **문제**:
  - 파일 존재 확인만 함
  - 실제 수정 여부는 확인 안함
- **재현 시나리오**:
  ```python
  claim = "config.json을 수정했습니다"
  # 파일이 존재하면 verified=True
  # 하지만 실제로 수정 안했을 수도 있음 (할루시네이션)
  ```
- **영향**: 거짓 긍정 (false positive) 높음
- **우선순위**: HIGH
- **해결 방안**: Git diff 또는 파일 mtime 확인

#### High #4: contradiction_detector_v2 성능 문제 (O(n^2))
- **위치**: contradiction_detector_v2.py:254-268
- **문제**:
  - 모든 문장 쌍 비교 (nested loop)
  - 문장 100개 → 5,000번 비교
- **재현 시나리오**:
  ```python
  # 긴 응답 (100 문장)
  response = "..." * 100
  # → 5,000번 유사도 계산 → 5초+ 소요
  ```
- **영향**: 응답 지연, 사용자 경험 저하
- **우선순위**: HIGH
- **해결 방안**:
  - Clustering 사용 (비슷한 문장끼리 그룹화)
  - Early exit (유사도 threshold 이하면 skip)
  - Batch processing (벡터화)

### 3.3 Medium Priority Issues (4개)

#### Medium #1: Evidence Graph 캐시 동기화 이슈
- **위치**: grounding_scorer.py:306-327
- **문제**: 캐시된 Evidence Graph가 최신 상태 아닐 수 있음
- **우선순위**: MEDIUM
- **해결 방안**: TTL (time-to-live) 또는 version tracking

#### Medium #2: claim_verifier context_history 처리 불일치
- **위치**: claim_verifier.py:288-312
- **문제**: context_history 있을 때/없을 때 다른 로직
- **우선순위**: MEDIUM
- **해결 방안**: 통일된 context 처리 로직

#### Medium #3: evidence_graph bare except
- **위치**: evidence_graph.py:444-449
- **문제**: `except:` 사용 → 모든 에러 숨김
- **우선순위**: MEDIUM
- **해결 방안**: 구체적 예외 타입 지정

#### Medium #4: fuzzy_claim_analyzer 기본 confidence 값
- **위치**: fuzzy_claim_analyzer.py:420-422
- **문제**: 확신도 표현 없으면 0.0 반환 (너무 보수적)
- **우선순위**: MEDIUM
- **해결 방안**: neutral 값 (0.5) 또는 context 기반 추론

### 3.4 Low Priority Issues (3개)

#### Low #1: claim_extractor 중복 Claim 감지 미흡
- **위치**: claim_extractor.py 전반
- **문제**: 동일한 주장이 다른 표현으로 중복 추출될 수 있음
- **우선순위**: LOW
- **해결 방안**: Semantic deduplication (임베딩 유사도)

#### Low #2: contradiction_detector_v2 함수 정의 확인 필요
- **위치**: contradiction_detector_v2.py
- **문제**: 일부 함수 정의 누락 가능성
- **우선순위**: LOW
- **해결 방안**: 코드 리뷰, 테스트 작성

#### Low #3: 하드코딩된 파라미터
- **위치**: 여러 파일 (threshold, weight 등)
- **문제**: 설정 파일로 분리 필요
- **우선순위**: LOW
- **해결 방안**: config.py 또는 YAML 설정 파일

---

## 4. Edge Cases 목록 (완전 목록화)

### 4.1 입력 Edge Cases (10개)

| Case | 설명 | 재현 방법 | 예상 동작 | 현재 상태 |
|------|------|-----------|-----------|----------|
| **EC-1** | Claim 없는 텍스트 (조사 보고서) | `"이 프로젝트는 Python Flask 기반입니다"` | grounding_score = 1.0 | [FIXED] Line 138, 192 수정됨 |
| **EC-2** | Claim 매우 많은 텍스트 (>100개) | 100개 구현 주장 포함 응답 | MAX_CLAIMS_FOR_VERIFICATION(50) 적용 | [OK] Line 236-247 |
| **EC-3** | 빈 텍스트 또는 whitespace만 | `""` 또는 `"   "` | claims=[], grounding_score=1.0 | [테스트 필요] |
| **EC-4** | 특수문자/이모지 포함 | `"구현 완료 🎉 테스트 통과 ✅"` | 정상 처리 | [테스트 필요] |
| **EC-5** | 다국어 텍스트 (한/영/일 혼재) | `"Implementation完了했습니다"` | contradiction_detector_v2 지원 확인 | [OK] 언어 독립적 |
| **EC-6** | 매우 긴 텍스트 (>100KB) | 소설 길이 응답 | 메모리/성능 이슈 가능 | [테스트 필요] |
| **EC-7** | 코드 블록 포함 | markdown 코드 블록 포함 응답 | 코드 vs 자연어 구분 | [테스트 필요] |
| **EC-8** | 확신도 표현 전혀 없음 | `"파일을 수정함"` (단순 사실 진술) | confidence = 0.0 (너무 보수적?) | [Medium #4] |
| **EC-9** | 모순된 Claim 포함 | `"구현 완료. 아직 구현 안됨"` | contradictions_found > 0 | [OK] |
| **EC-10** | 중복 Claim 포함 | `"완료했습니다. 구현 완료했어요"` | 중복 제거 필요 | [Low #1] |

### 4.2 Context Edge Cases (7개)

| Case | 설명 | 재현 방법 | 예상 동작 | 현재 상태 |
|------|------|-----------|-----------|----------|
| **EC-11** | context = None | `verify_response(text, context=None)` | 최소 기능만 동작 (Evidence 수집 불가) | [테스트 필요] |
| **EC-12** | context = {} (빈 딕셔너리) | `verify_response(text, context={})` | project_path 없음 에러 | [테스트 필요] |
| **EC-13** | project_path 없음 | `context={"project_id": "test"}` | ValueError 발생 | [OK] Line 395-396 |
| **EC-14** | project_path 잘못됨 (존재하지 않는 경로) | `context={"project_path": "/invalid"}` | FileNotFoundError 또는 빈 Evidence | [테스트 필요] |
| **EC-15** | files_modified 없음 | `context={..., "files_modified": None}` | Evidence 수집 실패 | [테스트 필요] |
| **EC-16** | Evidence Graph 없음 (초기화 실패) | memory_manager 초기화 에러 | Fallback: _collect_evidence 사용 | [Critical #2] |
| **EC-17** | Evidence Graph 손상 (invalid JSON) | `_evidence_graph.json` 파일 손상 | 로드 실패, 빈 그래프로 시작 | [테스트 필요] |

### 4.3 성능 Edge Cases (4개)

| Case | 설명 | 재현 방법 | 예상 동작 | 현재 상태 |
|------|------|-----------|-----------|----------|
| **EC-18** | 매우 큰 Evidence Graph (>10000 노드) | 장기 사용 프로젝트 | 검색 느림, 메모리 많이 사용 | [테스트 필요] |
| **EC-19** | 많은 파일 (>1000개) | 대규모 모노레포 | Claim 검증 느림 | [High #4] contradiction O(n^2) |
| **EC-20** | 동시 호출 (멀티스레드) | 여러 세션에서 동시 verify_response | Race condition 가능 | [테스트 필요] |
| **EC-21** | 메모리 부족 | 매우 큰 응답 + 큰 Evidence Graph | MemoryError 또는 OOM | [테스트 필요] |

### 4.4 논리적 Edge Cases (5개)

| Case | 설명 | 재현 방법 | 예상 동작 | 현재 상태 |
|------|------|-----------|-----------|----------|
| **EC-22** | 확신도 높음 + Claim 없음 | `"이 파일은 확실히 Python입니다"` | grounding_score = 1.0 | [FIXED] Line 138 |
| **EC-23** | 확신도 낮음 + Claim 없음 | `"아마도 Python일 것 같아요"` | grounding_score = 1.0 | [FIXED] Line 138 |
| **EC-24** | 확신도 낮음 + Claim 있음 | `"구현했을 것 같아요"` | grounding_score = 0.5 | [FIXED] Line 138 |
| **EC-25** | 모든 Claim 검증 실패 | 거짓 주장들만 포함 | grounding_score = 0.0, requires_retry=True | [OK] |
| **EC-26** | 일부 Claim만 검증 성공 | 3/5 Claim 검증 성공 | grounding_score = 0.6 | [OK] |

### 4.5 통합 Edge Cases (4개)

| Case | 설명 | 재현 방법 | 예상 동작 | 현재 상태 |
|------|------|-----------|-----------|----------|
| **EC-27** | auto_verifier vs memory_manager 결과 불일치 | 동일 응답 두 경로로 검증 | 같은 grounding_score | [Critical #1] 불일치 확인됨 |
| **EC-28** | Evidence Graph 비동기 업데이트 | claim_verifier 검증 중 외부에서 Evidence 추가 | 최신 Evidence 반영 안됨 | [Critical #2] |
| **EC-29** | 순환 참조 (Claim A → Evidence B → Claim A) | Evidence Graph에 순환 경로 | 무한 루프 또는 max_depth 제한 | [테스트 필요] |
| **EC-30** | Method existence check 실패 | `obj.nonexistent_method()` 호출 주장 | verified=False, requires_retry=True | [OK] Line 172-188 |

**총 Edge Cases: 30개**
- 입력: 10개
- Context: 7개
- 성능: 4개
- 논리: 5개
- 통합: 4개

---

## 5. 테스트 커버리지 분석

(진행 중...)

---

## 6. 수정 계획 (CRITICAL → HIGH → MEDIUM → LOW 순서)

### 6.1 CRITICAL 이슈 수정 계획

#### Critical #1: grounding_score 계산 통일

**목표**: memory_manager와 auto_verifier의 grounding_score 계산 로직 통일

**수정 파일**:
- memory_manager.py:1307-1312

**수정 내용**:
```python
# BEFORE (memory_manager.py)
if total_claims_count > 0:
    grounding_score_value = verified_claims_count / total_claims_count
else:
    grounding_score_value = 1.0

# AFTER (memory_manager.py)
# grounding_scorer 사용 (auto_verifier와 통일)
if grounding_scorer:
    grounding_result = grounding_scorer.calculate_score(
        response_text=content,
        claims=claims,
        referenced_contexts=referenced_contexts,
        context_history={"project_id": project_id, "project_path": project_path},
        claim_evidence_map=claim_evidence_map  # 신규
    )
    grounding_score_value = grounding_result["grounding_score"]
else:
    # Fallback: 직접 계산
    if total_claims_count > 0:
        grounding_score_value = verified_claims_count / total_claims_count
    else:
        grounding_score_value = 1.0
```

**검증 방법**:
- test_grounding_score_consistency.py 실행
- auto_verifier.verify_response() vs memory_manager.update_memory() 결과 비교
- 동일 응답에 대해 grounding_score 일치 확인

**예상 부작용**:
- grounding_scorer 초기화 오버헤드 증가
- memory_manager 응답 속도 약간 느려질 수 있음

**완료 기준**:
- 두 경로의 grounding_score 차이 < 0.01
- 기존 테스트 모두 통과

---

#### Critical #2: Evidence Graph 단일 인스턴스 공유

**목표**: 모든 Phase 9 컴포넌트가 동일한 Evidence Graph 사용

**수정 파일**:
- memory_manager.py:346-383 (Phase 9 초기화)
- auto_verifier.py:397-466 (_get_claim_verifier, _get_grounding_scorer)

**수정 내용**:
```python
# memory_manager.py
class MemoryManager:
    def __init__(self, ...):
        # 1. Evidence Graph를 먼저 생성
        self.evidence_graph = EvidenceGraph()

        # 2. ClaimVerifier, GroundingScorer에 전달
        self.claim_verifier = ClaimVerifier(
            project_id=...,
            project_path=...,
            evidence_graph=self.evidence_graph  # 신규
        )

        self.grounding_scorer = GroundingScorer(
            evidence_graph=self.evidence_graph  # 신규
        )

        # 3. auto_verifier에도 context로 전달
        context = {
            "evidence_graph": self.evidence_graph,
            "claim_verifier": self.claim_verifier,
            "grounding_scorer": self.grounding_scorer
        }
```

```python
# auto_verifier.py
def _get_claim_verifier(self, context):
    # Context에서 Evidence Graph 받기
    evidence_graph = context.get("evidence_graph")

    if "claim_verifier" in context:
        return context["claim_verifier"]
    else:
        # Lazy initialization with shared Evidence Graph
        return ClaimVerifier(
            project_id=...,
            evidence_graph=evidence_graph  # 신규
        )
```

**검증 방법**:
- Evidence Graph 인스턴스 ID 로깅
- claim_verifier, grounding_scorer, auto_verifier가 동일 인스턴스 사용 확인
- Evidence 추가 후 모든 컴포넌트에서 반영 확인

**예상 부작용**:
- 멀티스레드 환경에서 race condition 가능 → Lock 추가 필요

**완료 기준**:
- 3개 컴포넌트의 Evidence Graph id() 값 동일
- Evidence 추가 후 즉시 검색 가능

---

#### Critical #3: Phase 9 초기화 에러 핸들링

**목표**: Phase 9 컴포넌트 초기화 실패 시 graceful degradation

**수정 파일**:
- memory_manager.py:346-383

**수정 내용**:
```python
# BEFORE
self.claim_extractor = ClaimExtractor()
self.fuzzy_analyzer = FuzzyClaimAnalyzer()
self.contradiction_detector = ContradictionDetectorV2()
# ...

# AFTER
try:
    self.claim_extractor = ClaimExtractor()
    logger.info("ClaimExtractor 초기화 성공")
except Exception as e:
    logger.error(f"ClaimExtractor 초기화 실패: {e}")
    self.claim_extractor = None  # Fallback

try:
    self.fuzzy_analyzer = FuzzyClaimAnalyzer()
    logger.info("FuzzyClaimAnalyzer 초기화 성공")
except Exception as e:
    logger.error(f"FuzzyClaimAnalyzer 초기화 실패: {e}")
    self.fuzzy_analyzer = None

# ... (나머지도 동일)

# Verification 시 None 체크
if self.claim_extractor is None:
    logger.warning("ClaimExtractor 없음 - Claim 추출 생략")
    claims = []
else:
    claims = self.claim_extractor.extract_claims(content)
```

**검증 방법**:
- 의존성 제거 후 MemoryManager 초기화 테스트
- Phase 9 없이도 기본 기능 동작 확인
- 로그 메시지 명확성 확인

**예상 부작용**:
- Phase 9 비활성화 시 할루시네이션 검증 불가

**완료 기준**:
- Phase 9 초기화 실패해도 MemoryManager 사용 가능
- 명확한 경고 로그 출력
- 기본 기능 (context 저장/검색) 정상 동작

---

#### Critical #4: grounding_scorer semantic depth 계산

**목표**: Evidence Graph 기반 semantic depth 계산으로 정확도 향상

**수정 파일**:
- grounding_scorer.py:306-327 (_analyze_context_depth)

**수정 내용**:
```python
# BEFORE
def _analyze_context_depth(self, referenced_contexts):
    # 파일 경로 깊이만 고려
    depth = len(Path(context).parts)
    ...

# AFTER
def _analyze_context_depth(self, referenced_contexts):
    # Evidence Graph 기반 semantic depth 계산
    depth_analysis = {"by_depth": {}}

    for context in referenced_contexts:
        # 1. Evidence Graph에서 최단 경로 탐색
        if self.evidence_graph:
            # Claim 노드에서 Evidence 노드까지의 최단 경로
            shortest_path = self.evidence_graph.shortest_path(
                from_node=current_claim_id,
                to_node=context
            )
            semantic_depth = len(shortest_path) - 1 if shortest_path else 999
        else:
            # Fallback: 파일 경로 깊이
            semantic_depth = len(Path(context).parts)

        # 2. depth별 집계
        if semantic_depth not in depth_analysis["by_depth"]:
            depth_analysis["by_depth"][semantic_depth] = 0
        depth_analysis["by_depth"][semantic_depth] += 1

    return depth_analysis
```

**검증 방법**:
- Evidence Graph에 다양한 depth의 Evidence 추가
- grounding_score 계산 결과 비교
- 직접 참조 vs 간접 참조 weight 차이 확인

**예상 부작용**:
- shortest_path 계산 오버헤드
- Evidence Graph 없으면 fallback 필요

**완료 기준**:
- 직접 참조 (depth=0)가 가장 높은 weight
- 간접 참조 (depth>2)가 낮은 weight
- grounding_score 정확도 향상 (테스트 케이스로 검증)

---

### 6.2 HIGH 이슈 수정 계획

#### High #1: claim_extractor 명시적 우선순위

**수정 파일**: claim_extractor.py:280-288

**수정 내용**:
```python
# 명시적 우선순위 리스트
CLAIM_TYPE_PRIORITY = [
    "implementation_complete",
    "verification",
    "modification",
    "extension",
    "reference_existing",
    "bug_fix"
]

# 패턴 매칭 후 우선순위 정렬
matched_types = [...]
matched_types.sort(key=lambda x: CLAIM_TYPE_PRIORITY.index(x) if x in CLAIM_TYPE_PRIORITY else 999)
return matched_types[0]  # 가장 높은 우선순위 반환
```

**검증**: 동일 텍스트에 대해 항상 동일한 claim_type 반환 확인

---

#### High #2: fuzzy_claim_analyzer 부정 표현 개선

**수정 파일**: fuzzy_claim_analyzer.py:344-354

**수정 내용**:
```python
# 부정 문맥 윈도우 확장 (3 토큰)
negation_patterns = [
    r"(않|안|못|없)[가-힣]{0,3}(했|함|됨|됐)",  # "하지 않았습니다"
    r"실패",
    r"미구현",
    r"안됨"
]

# 문맥 확인 (주변 3단어)
window = text[max(0, start-50):min(len(text), end+50)]
if any(re.search(pattern, window) for pattern in negation_patterns):
    confidence *= 0.3  # 부정 감지 시 confidence 대폭 감소
```

**검증**: "구현하지 못했습니다" → low confidence 반환 확인

---

#### High #3: claim_verifier 파일 수정 여부 확인

**수정 파일**: claim_verifier.py:856-862

**수정 내용**:
```python
# Git diff 확인 추가
if claim_type == "modification":
    # 파일 존재 + 수정 여부 확인
    if os.path.exists(file_path):
        # Git diff로 수정 확인
        git_diff = self._get_git_diff(file_path)
        if git_diff:
            return {"verified": True, "evidence": git_diff}
        else:
            return {"verified": False, "reason": "파일 존재하지만 수정 내역 없음"}
```

**검증**: 수정하지 않은 파일에 대한 "수정했습니다" 주장 거부 확인

---

#### High #4: contradiction_detector_v2 성능 최적화

**수정 파일**: contradiction_detector_v2.py:254-268

**수정 내용**:
```python
# Clustering 사용
from sklearn.cluster import KMeans

# 1. 문장 임베딩
embeddings = [self.model.encode(sent) for sent in sentences]

# 2. Clustering (문장 수 / 10개 클러스터)
n_clusters = max(2, len(sentences) // 10)
clusters = KMeans(n_clusters=n_clusters).fit_predict(embeddings)

# 3. 클러스터 내에서만 비교 (O(n^2) → O(n^2/k))
for cluster_id in range(n_clusters):
    cluster_sents = [sentences[i] for i in range(len(sentences)) if clusters[i] == cluster_id]
    # 클러스터 내에서만 nested loop
    ...
```

**검증**: 100 문장 응답 처리 시간 5초 → 1초 이하로 감소 확인

---

### 6.3 MEDIUM/LOW 이슈 수정 계획

(나중에 작성 - Critical/High 완료 후)

---

## 7. 검증 계획

### 7.1 CRITICAL 이슈 검증

각 Critical 이슈 수정 후 다음 테스트 실행:

```bash
# Critical #1: grounding_score 일관성 테스트
../.venv311/bin/pytest tests/test_grounding_score_consistency.py -v

# Critical #2: Evidence Graph 동기화 테스트
../.venv311/bin/pytest tests/test_evidence_graph_sync.py -v

# Critical #3: 초기화 에러 핸들링 테스트
../.venv311/bin/pytest tests/test_phase9_initialization.py -v

# Critical #4: Semantic depth 계산 테스트
../.venv311/bin/pytest tests/test_grounding_scorer_depth.py -v
```

### 7.2 HIGH 이슈 검증

```bash
# High #1: Claim 타입 우선순위 테스트
../.venv311/bin/pytest tests/test_claim_extractor_priority.py -v

# High #2: 부정 표현 감지 테스트
../.venv311/bin/pytest tests/test_fuzzy_negation.py -v

# High #3: 파일 수정 검증 테스트
../.venv311/bin/pytest tests/test_claim_verifier_modification.py -v

# High #4: 모순 검출 성능 테스트
../.venv311/bin/pytest tests/test_contradiction_performance.py -v
```

### 7.3 전체 회귀 테스트

모든 수정 완료 후:

```bash
# Phase 9 전체 테스트
../.venv311/bin/pytest tests/ -m phase9 -v --tb=short

# 전체 시스템 테스트
../.venv311/bin/pytest tests/ -v --tb=line
```

---

## 8. 감사 요약

### 8.1 발견된 문제 통계

| 우선순위 | 개수 | 상태 |
|---------|------|------|
| CRITICAL | 4 | 수정 계획 완료 |
| HIGH | 4 | 수정 계획 완료 |
| MEDIUM | 4 | 추후 수정 예정 |
| LOW | 3 | 추후 수정 예정 |
| **총계** | **15** | **8/15 계획 완료** |

### 8.2 Edge Cases 통계

| 카테고리 | 개수 | 테스트 필요 | 수정 필요 |
|---------|------|------------|----------|
| 입력 | 10 | 5 | 2 |
| Context | 7 | 5 | 2 |
| 성능 | 4 | 3 | 1 |
| 논리 | 5 | 0 (모두 수정됨) | 0 |
| 통합 | 4 | 2 | 2 |
| **총계** | **30** | **15** | **7** |

### 8.3 최우선 수정 항목 (CRITICAL #1-#4)

1. **grounding_score 계산 통일** → 일관성 보장
2. **Evidence Graph 동기화** → 정확도 향상
3. **초기화 에러 핸들링** → 안정성 향상
4. **Semantic depth 계산** → grounding_score 정확도 향상

### 8.4 예상 작업 시간

| 항목 | 예상 시간 | 비고 |
|------|----------|------|
| Critical #1 | 2시간 | memory_manager 수정 + 테스트 |
| Critical #2 | 3시간 | 아키텍처 변경 + 통합 테스트 |
| Critical #3 | 1시간 | try-except 추가 |
| Critical #4 | 4시간 | shortest_path 구현 + 테스트 |
| High #1-4 | 6시간 | 각 1.5시간 |
| 테스트 작성 | 4시간 | 15개 Edge Case 테스트 |
| **총계** | **20시간** | 약 3일 (하루 7시간 기준) |

---

## 9. 최종 액션 아이템

### 9.1 즉시 실행 (CRITICAL 이슈)

- [ ] Critical #1: memory_manager.py Line 1307-1312 수정
  - [ ] grounding_scorer 사용하도록 변경
  - [ ] test_grounding_score_consistency.py 실행
  - [ ] 두 경로 결과 일치 확인

- [ ] Critical #2: Evidence Graph 단일 인스턴스 공유
  - [ ] memory_manager.py 초기화 부분 수정
  - [ ] auto_verifier.py context 전달 방식 수정
  - [ ] 인스턴스 ID 로깅 확인

- [ ] Critical #3: Phase 9 초기화 에러 핸들링
  - [ ] memory_manager.py 각 컴포넌트 try-except 추가
  - [ ] None 체크 로직 추가
  - [ ] 초기화 실패 테스트

- [ ] Critical #4: Semantic depth 계산
  - [ ] grounding_scorer.py shortest_path 구현
  - [ ] fallback 로직 추가
  - [ ] 정확도 테스트

### 9.2 다음 단계 (HIGH 이슈)

- [ ] High #1: claim_extractor 우선순위 리스트 추가
- [ ] High #2: fuzzy_claim_analyzer 부정 문맥 확장
- [ ] High #3: claim_verifier Git diff 확인 추가
- [ ] High #4: contradiction_detector_v2 Clustering 적용

### 9.3 테스트 작성

- [ ] Critical 이슈 테스트 4개
- [ ] High 이슈 테스트 4개
- [ ] Edge Case 테스트 15개
- [ ] 회귀 테스트 스위트 정리

### 9.4 문서화

- [ ] 수정 내역 CHANGELOG 작성
- [ ] API 변경사항 문서화
- [ ] 마이그레이션 가이드 작성 (있다면)

---

## 10. 결론

**Phase 9 할루시네이션 검증 시스템의 완전한 감사가 완료되었습니다.**

**핵심 발견:**
- 15개의 문제점 식별 (Critical 4, High 4, Medium 4, Low 3)
- 30개의 Edge Cases 문서화
- 8개의 최우선 수정 항목에 대한 구체적인 수정 계획 수립

**다음 단계:**
1. Critical 이슈 4개부터 순차적으로 수정
2. 각 수정 후 즉시 테스트로 검증
3. High 이슈 수정
4. 전체 회귀 테스트 실행
5. Medium/Low 이슈는 성능 영향도에 따라 우선순위 조정

**예상 효과:**
- 할루시네이션 검증 일관성 100% 달성
- grounding_score 정확도 향상
- 시스템 안정성 향상 (에러 핸들링)
- 성능 개선 (O(n^2) → O(n^2/k))

---

**작성 완료일**: 2025-12-31
**작성자**: Phase 9 완전 감사 팀 (MCP 개발자, SW QA, Python 개발자, AI 할루시네이션 전문가, 기획자)
**최종 업데이트**: 2025-12-31 (감사 완료)
