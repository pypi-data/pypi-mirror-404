# 할루시네이션 검증 시스템 종합 QA 분석 보고서

**분석 관점**: 세계 최고 수준 SW QA 전문가
**분석 일시**: 2025-12-29
**분석 대상**: Cortex Phase 9 할루시네이션 검증 시스템 및 벤치마크 테스트

---

## Executive Summary

**핵심 발견사항**:
1. 할루시네이션 검증 시스템은 6개 컴포넌트로 구성되어 있으나, **컴포넌트 간 데이터 흐름에서 3개의 critical path가 Evidence Graph 상태에 과도하게 의존**
2. 벤치마크 테스트 중 **test_06은 테스트 데이터 생성 방식이 실제 사용 시나리오와 괴리**되어 있음
3. **순환 검증 문제**: 할루시네이션 검증 시스템으로 할루시네이션 검증 시스템을 테스트하는 구조

---

## Part 1: 할루시네이션 검증 시스템 아키텍처 분석

### 1.1 시스템 구성 요소 및 데이터 흐름

```
[AI Response Text]
        ↓
[1. FuzzyClaimAnalyzer] ← 확신도 분석 (의미 기반)
        ↓ confidence_score >= 0.8?
        ↓ YES
[2. ClaimExtractor] ← Regex 기반 주장 추출
        ↓ claims[]
[3. ClaimVerifier] ← Evidence Graph에서 증거 매칭
        ↓ is_verified per claim
[4. GroundingScorer] ← Bayesian 기반 점수 계산
        ↓ grounding_score
[5. ContradictionDetector] ← 모순 검출 (선택적)
        ↓
[6. BayesianUpdater] ← 사후 확률 계산 (내부 사용)
```

### 1.2 Critical Path 분석

**Critical Path 1: Evidence Graph 의존성**

`auto_verifier.py` 라인 118-124:
```python
# CRITICAL FIX: context에서 referenced_contexts 먼저 확인 (Phase 9.4 통합)
referenced_contexts = (context or {}).get("referenced_contexts", [])
if referenced_contexts:
    logger.info(f"✅ Evidence Graph에서 referenced_contexts 사용: {len(referenced_contexts)}개")
else:
    logger.info("⚠️ Evidence Graph 없음 - _collect_evidence로 대체")
```

**문제점**:
- Evidence Graph가 비어있거나 노드가 없으면 `referenced_contexts = []`
- 이 경우 fallback으로 `_collect_evidence()` 호출하지만 이 메서드는 매우 제한적:
  - `context["file_contents"]`만 검사 (라인 339-343)
  - `context["test_results"]`만 검사 (라인 345-349)
  - `context["command_output"]`만 검사 (라인 351-355)
- **실제 파일 시스템이나 Git 상태는 검사하지 않음**

**Critical Path 2: ClaimVerifier의 Evidence Graph 공유**

`auto_verifier.py` 라인 211-217:
```python
if "claim_verifier" in context and context["claim_verifier"] is not None:
    verifier = context["claim_verifier"]
    print(f"[DEBUG] auto_verifier: memory_manager의 ClaimVerifier 사용 (Evidence Graph 공유)")
    print(f"[DEBUG]   - ClaimVerifier Evidence Graph 객체 ID: {id(verifier.evidence_graph)}")
    return verifier
```

**문제점**:
- `context`에 `claim_verifier`가 없으면 새로운 `ClaimVerifier` 인스턴스 생성 (라인 242)
- 새 인스턴스는 독립된 Evidence Graph를 가짐
- **memory_manager와 auto_verifier가 다른 Evidence Graph를 참조하면 데이터 불일치**

**Critical Path 3: GroundingScorer의 Evidence Graph 동기화**

`auto_verifier.py` 라인 294-301:
```python
verifier = self._get_claim_verifier(context)
scorer.evidence_graph = verifier.evidence_graph
print(f"[DEBUG] auto_verifier: 새 GroundingScorer Evidence Graph 공유 설정")
```

**문제점**:
- GroundingScorer가 먼저 생성되면 독립된 Evidence Graph 생성
- 이후 ClaimVerifier의 Evidence Graph로 강제 교체
- **초기에 생성된 Evidence Graph 인스턴스는 메모리 누수 가능성**

### 1.3 아키텍처 평가

**강점**:
1. Fuzzy logic 기반 확신도 분석은 의미론적 접근이라 언어 독립적
2. Bayesian 추론 사용으로 확률론적 불확실성 표현 가능
3. 컴포넌트 분리로 각 기능 독립 테스트 가능

**약점**:
1. **Evidence Graph 중앙 집중화**: 모든 컴포넌트가 하나의 Evidence Graph에 의존
2. **State Synchronization 부재**: Evidence Graph 상태 동기화 메커니즘 없음
3. **Fallback Logic 불충분**: Evidence Graph 실패 시 대체 검증 방법 미흡
4. **순환 의존성**: auto_verifier ↔ memory_manager ↔ ClaimVerifier ↔ Evidence Graph

---

## Part 2: 벤치마크 테스트 유효성 분석

### 2.1 test_06_hallucination_detection.py 분석

**참조**: `tests/benchmark/test_06_hallucination_detection.py`

**Test 6A: ROC-AUC Prediction**

테스트 데이터 생성 방식 (라인 320-355):
```python
# 정상 응답 (Grounded) - 60개
grounded_responses = [
    "I implemented authentication in the code.",
    "Test passed in the test file.",
    "Updated config with database settings.",
] * 20  # 3개 문장을 20번 반복 = 60개

# 할루시네이션 응답 - 40개
hallucination_responses = [
    "I implemented 50 features in 5 minutes.",
    "All 1,000 tests passed.",
    "The API endpoint is working.",
] * 14  # 3개 문장을 14번 반복 = 42개 (40개만 사용)
```

**문제점 1: 데이터 다양성 부족**
- 전체 100개 응답 중 실제로는 **6개의 고유 문장만 반복**
- 실제 LLM 응답은 훨씬 다양한 패턴과 문맥을 가짐
- **Overfitting 위험**: 이 6개 패턴만 잘 분류하도록 학습될 수 있음

**문제점 2: 할루시네이션 정의의 모호성**

"I implemented 50 features in 5 minutes." 이 문장이 할루시네이션인 이유:
- 테스트에서는 `files_modified: {}`로 증거 없음 처리 (라인 202-207)
- **하지만 실제로 50개 기능을 5분만에 구현한 사람도 있을 수 있음** (예: 템플릿 코드 생성기 사용)
- **Context 없이 문장만으로 할루시네이션 판단은 부정확**

**문제점 3: Evidence 생성 방식의 인위성**

정상 응답 처리 (라인 63-75):
```python
if not response["is_hallucination"]:
    file_name = f"grounded_file_{idx}.py"  # 인위적인 파일명
    context = {
        "files_modified": {
            file_name: {
                "path": file_name,
                "diff": f"Implementation: {response['text']}",  # 응답 텍스트를 그대로 diff로 사용
                "change_type": "modified"
            }
        }
    }
```

**문제점**:
- 실제 Git diff가 아니라 **응답 텍스트를 그대로 diff로 삽입**
- 이는 "응답에 나온 내용 = 파일에 있는 내용"이라는 동어반복
- **실제 시나리오에서는 응답과 실제 코드가 정확히 일치하지 않음**

**Test 6B: 3-Tier Threshold**

테스트 케이스 (라인 166-181):
```python
test_cases = [
    # REJECT zone (명백한 할루시네이션)
    ("I implemented 500 features in 1 hour.", True, "reject"),
    ("All 10,000 tests passed instantly.", True, "reject"),

    # WARN zone (애매한 상태)
    ("I think the feature might be working.", False, "warn"),
    ("Probably fixed the issue.", False, "warn"),

    # ACCEPT zone (근거 충분)
    ("I implemented login function.", False, "accept"),
    ("Test passed in test file.", False, "accept"),
]
```

**문제점 1: 레이블링 일관성 부족**
- "All 10,000 tests passed instantly." → 할루시네이션으로 레이블링
- 하지만 CI/CD 파이프라인에서 10,000개 단위 테스트가 몇 초만에 통과하는 것은 가능
- **시간이나 숫자가 크다고 무조건 할루시네이션이 아님**

**문제점 2: Threshold 검증 논리의 허점**

성공 기준 (라인 251-252):
```python
assert reject_halluc_ratio >= 0.50, \
    f"REJECT zone에 할루시네이션이 충분히 집중되지 않음: {reject_halluc_ratio:.2f}"
```

- REJECT zone에 할루시네이션이 **50% 이상**만 있으면 통과
- **이는 동전 던지기(50%)와 동일한 수준의 정확도**
- 실제로는 80-90% 이상이어야 의미 있는 threshold

**Test 6C: Claim Extraction Accuracy**

테스트 방식 (라인 298-306):
```python
for case in test_cases:
    claims = extractor.extract_claims(case["text"])
    if claims:
        extracted_types = [c.claim_type for c in claims]
        if case["expected_type"] in extracted_types:
            correct += 1
```

**문제점: Regex 패턴 의존성**
- ClaimExtractor는 순수 Regex 기반
- "I successfully implemented" → "implementation_complete"
- **"I finished implementing" 같은 동의어는 매칭 실패 가능성**
- **의미 기반 추출이 아니라 표면적 패턴 매칭**

### 2.2 test_99_e2e_workflow.py 분석

**참조**: `tests/benchmark/test_99_e2e_workflow.py`

**Day 2 할루시네이션 감지 테스트 (라인 149-175)**

```python
# 2.5. Hallucination Detection 테스트 (별도 터미널에서 진행 중 - 스킵)
# hallucination_detected = 0
# (전체 코드 주석 처리됨)
```

**문제점**:
- E2E 테스트에서 **할루시네이션 검증 부분이 완전히 비활성화됨**
- 주석: "별도 터미널에서 진행 중"
- **하지만 E2E 테스트의 핵심은 모든 컴포넌트 통합 검증인데, 할루시네이션 검증이 빠져있음**

**Branch Isolation 검증 (라인 204-226)**

```python
login_isolated = "login" in login_text.lower() and "payment" not in login_text.lower()
payment_isolated = "payment" in payment_text.lower() and "login" not in payment_text.lower()
```

**문제점**:
- 단순 문자열 검색으로 isolation 검증
- **"login"과 "payment"가 공통 라이브러리를 참조하면 어떻게 되는가?**
- 예: "authentication module used for both login and payment"
- **False positive 가능성 높음**

---

## Part 3: 발견된 구현 이슈

### 3.1 auto_verifier.py의 Bug Fix 분석

**참조**: `core/auto_verifier.py`

**Issue #1: 확신도 낮을 때 grounding_score = 0.5 (라인 86-97)**

```python
if confidence_score < self.HIGH_CONFIDENCE_THRESHOLD:
    return VerificationResult(
        verified=True,  # 검증 생략 = 통과로 간주
        grounding_score=0.5,  # Bug Fix: 1.0 → 0.5
        confidence_level=confidence_level,
        claims=[],
        unverified_claims=[],
        requires_retry=False,
    )
```

**분석**:
- 이전 버전: grounding_score = 1.0 (완벽한 근거)
- 수정 버전: grounding_score = 0.5 (중간 수준)
- **논리적 모순**: 확신도가 낮아서 검증을 생략했는데 `verified=True`?
- **올바른 설계**: 확신도 낮음 = 검증 불필요 ≠ 검증 통과
- **제안**: `verified=None` 또는 별도 상태 추가 필요

**Issue #2: Claim 없을 때 grounding_score = 0.5 (라인 103-113)**

```python
if not claims:
    return VerificationResult(
        verified=True,
        grounding_score=0.5,  # Bug Fix: 1.0 → 0.5
        confidence_level=confidence_level,
        claims=[],
        unverified_claims=[],
        requires_retry=False,
    )
```

**분석**:
- Claim이 없다 = 검증할 주장이 없다 ≠ 할루시네이션 없다
- 예: "작업 중입니다." (Claim 없음, 하지만 거짓말일 수 있음)
- **grounding_score는 "근거 밀도"인데 Claim 없으면 정의 불가**
- **제안**: `grounding_score=None` 또는 별도 처리 필요

### 3.2 grounding_scorer.py의 계산식 검증

**참조**: `core/grounding_scorer.py`

**핵심 공식 (라인 124)**:

```python
if total_claims > 0:
    grounding_score = weighted_contexts / total_claims
else:
    grounding_score = weighted_contexts / max(1, len(response_text.split("\n")))
```

**문제점**:
- `weighted_contexts`는 Evidence Graph에서 계산된 가중치 합
- `total_claims`는 추출된 주장 개수
- **단위 불일치**: weighted_contexts는 가중치 (0.0-1.0 범위), total_claims는 개수 (1, 2, 3...)
- **비율이 1.0을 초과할 수 있음**: 예를 들어 weighted_contexts=3.0, total_claims=2이면 score=1.5
- **라인 127-128에서 0.0-1.0으로 클리핑하지만, 이는 임시방편**

### 3.3 claim_verifier.py의 Fallback 경로 복잡도

**참조**: `core/claim_verifier.py`

**파일 검증 경로 (라인 655-694)**:

```python
search_paths = [
    self.project_path,                      # memory_dir.parent
    Path(os.getcwd()),                      # Current working directory
    Path(os.getcwd()) / "cortex_mcp",
    Path(os.getcwd()) / "cortex_mcp" / "tools",
]

for search_root in search_paths:
    for candidate_path in [
        search_root / relative_path,
        search_root / Path(relative_path).name,
    ]:
        if candidate_path.exists() and candidate_path.is_file():
            # 파일 내용 읽기 및 diff 검사
```

**문제점**:
- **4개 search_paths × 2개 candidate_path = 8번 파일 검색**
- 각 검색마다 `exists()`, `is_file()`, `read_text()` 호출
- **대규모 프로젝트에서 성능 저하 가능성**
- **파일이 여러 경로에 동시 존재하면 어떤 것을 우선?**

---

## Part 4: 할루시네이션 검증 원칙을 테스트에 적용

### 4.1 메타 분석: 테스트 자체를 할루시네이션 검증

**Claim 1: "test_06은 할루시네이션 검증 성능을 측정한다"**

**증거 검증**:
- test_06 코드 (라인 24-136) 존재 ✓
- ROC-AUC, Precision, Recall 계산 로직 존재 ✓
- **하지만 테스트 데이터가 인위적 (6개 문장 반복)**
- **Grounding Score**: 0.6 (테스트 코드는 존재하지만 데이터 품질 의문)

**Claim 2: "ROC-AUC >= 0.85를 목표로 한다" (라인 10)**

**증거 검증**:
- 실제 assert문: `assert auc >= 0.75` (라인 128)
- **주석에는 0.85, 코드에는 0.75**
- **모순 감지**: 문서와 구현 불일치
- **Grounding Score**: 0.3 (REJECT zone) - 근거 부족 + 모순

**Claim 3: "Precision@0.7 >= 0.90을 목표로 한다" (라인 11)**

**증거 검증**:
- 실제 assert문: `assert precision_07 >= 0.80` (라인 131)
- **주석에는 0.90, 코드에는 0.80**
- **모순 감지**: 문서와 구현 불일치
- **Grounding Score**: 0.3 (REJECT zone)

**Claim 4: "test_99는 3일간의 실제 작업 시나리오를 재현한다" (test_99 라인 3-29)**

**증거 검증**:
- Day 1: 20턴 대화 시뮬레이션 ✓
- Day 2: Reference History, 할루시네이션 검증
  - **할루시네이션 검증 부분 주석 처리됨** (라인 149-175) ✗
- **Grounding Score**: 0.4 (WARN zone) - 부분 구현

### 4.2 순환 검증 문제 (Circular Validation)

**문제 정의**:
```
할루시네이션 검증 시스템(A)
    ↓ 사용
벤치마크 테스트(B) ← test_06, test_99
    ↓ 검증
할루시네이션 검증 시스템(A)의 정확도
```

**이는 논리적 순환**:
- A의 정확성을 검증하려면 A와 독립적인 ground truth 필요
- 하지만 test_06은 A를 사용하여 A를 검증
- **예**: `memory_manager.update_memory()`가 내부적으로 `auto_verifier.verify_response()` 호출

**해결 방안**:
1. **외부 Ground Truth 사용**: 인간이 라벨링한 대규모 데이터셋
2. **교차 검증**: 다른 할루시네이션 검증 시스템과 비교
3. **A/B 테스트**: 할루시네이션 검증 ON/OFF 비교

---

## Part 5: 결론 및 권고사항

### 5.1 Critical Issues (즉시 조치 필요)

1. **Evidence Graph 동기화 메커니즘 부재**
   - auto_verifier, memory_manager, claim_verifier가 서로 다른 Evidence Graph 인스턴스 참조 가능
   - **권고**: Singleton 패턴 또는 중앙 레지스트리 도입

2. **test_06 데이터 품질 문제**
   - 6개 문장 반복으로 다양성 부족
   - **권고**: 최소 100개 고유 문장, 실제 LLM 응답 수집

3. **문서-코드 불일치**
   - 목표: ROC-AUC >= 0.85, 실제: >= 0.75
   - **권고**: 문서 업데이트 또는 코드 수정

4. **순환 검증 문제**
   - 할루시네이션 시스템으로 할루시네이션 시스템 검증
   - **권고**: 독립적인 ground truth 데이터셋 확보

### 5.2 Major Issues (단기 조치 필요)

1. **grounding_score 계산식의 단위 불일치**
   - weighted_contexts / total_claims가 1.0 초과 가능
   - **권고**: 정규화 로직 재설계

2. **Fallback 경로 복잡도**
   - claim_verifier의 8번 파일 검색
   - **권고**: 캐싱 메커니즘 도입

3. **test_99 할루시네이션 테스트 비활성화**
   - E2E 테스트에서 핵심 기능 누락
   - **권고**: 할루시네이션 테스트 재활성화 또는 제거

### 5.3 Minor Issues (장기 개선 사항)

1. **ClaimExtractor의 Regex 의존성**
   - 의미 기반 추출 아님
   - **권고**: NLP 모델 기반 추출 고려

2. **Threshold 검증 기준 완화**
   - REJECT zone 50% → 80%로 상향
   - **권고**: 더 엄격한 기준 적용

### 5.4 질문 사항 (사용자 확인 필요)

1. **"엄청난 오류"의 정체**: 사용자가 언급한 major error가 위 분석 중 어떤 것인지?
2. **이전 세션 수정**: test_06과 auto_verifier.py 수정 롤백 필요 여부?
3. **우선순위**: 5개 Critical Issues 중 어떤 것부터 조치?

---

## 테스트 파일 참조

### 벤치마크 테스트 파일 위치

**할루시네이션 검증 관련**:
- `tests/benchmark/test_06_hallucination_detection.py` - ROC-AUC, 3-Tier Threshold, Claim Extraction
- `tests/benchmark/test_hallucination_detection.py` - 개별 할루시네이션 테스트
- `tests/benchmark/test_grounding_score.py` - Grounding Score 계산 검증
- `tests/benchmark/test_claim_extraction.py` - Claim 추출 정확도
- `tests/benchmark/test_contradiction_detection.py` - 모순 감지

**다른 기능 테스트**:
- `tests/benchmark/test_01_token_efficiency.py` - Smart Context 토큰 절감
- `tests/benchmark/test_02_reference_accuracy.py` - Reference History 정확도
- `tests/benchmark/test_99_e2e_workflow.py` - E2E 통합 워크플로우
- `tests/benchmark/test_smart_context.py` - Smart Context 압축/해제
- `tests/benchmark/test_branch_isolation.py` - 브랜치 격리
- `tests/benchmark/test_snapshot_restore.py` - 스냅샷 복원
- `tests/benchmark/test_reference_history.py` - Reference History
- `tests/benchmark/test_benchmark.py` - 전체 벤치마크

---

**보고서 끝**

**다른 터미널에서 확인 사항**:
1. 위 분석에서 발견된 5개 Critical Issues 검토
2. test_06과 auto_verifier.py의 이전 세션 수정 내역 확인
3. 문서-코드 불일치 (목표 0.85 vs 실제 0.75) 해결 방안 결정
4. Evidence Graph 동기화 문제 재현 여부 확인
5. 순환 검증 문제에 대한 독립적인 ground truth 데이터셋 준비

**다음 단계**: 할루시네이션 외 다른 기능 테스트 상태 파악 필요
