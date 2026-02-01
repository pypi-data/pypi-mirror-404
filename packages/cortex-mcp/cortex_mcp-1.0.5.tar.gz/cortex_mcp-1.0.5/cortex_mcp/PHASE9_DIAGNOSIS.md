# Phase 9 할루시네이션 검증 시스템 진단 보고서

**작성일:** 2025-12-21
**작성자:** Claude Code
**목적:** Phase 9 할루시네이션 검증 시스템의 실제 작동 여부 정밀 진단

---

## 1. 진단 개요

Phase 9 할루시네이션 검증 시스템이 "실행된다"고 보고되었으나, 실제로는 **제대로 검증하지 못하고 있음**을 발견했습니다.

### 테스트 결과
- 4개 시나리오 모두 통과 (100%)
- **하지만**: 모든 경우에 `verified_claims: 0`, `grounding_score: 0.0`

### 근본 원인
Evidence Graph가 비어있어서 모든 검증이 실패함

---

## 2. 발견한 핵심 문제

### 문제 1: Evidence Graph 비어있음 (CRITICAL)

**현상:**
```python
# ClaimVerifier 초기화
self.evidence_graph = EvidenceGraph(project_id)  # 빈 그래프 생성
```

**원인:**
- ClaimVerifier 생성 시 빈 Evidence Graph만 생성
- 이후 Evidence Graph를 채우는 코드가 **전혀 없음**
- memory_manager.py에 "evidence_graph" 관련 코드 0개

**영향:**
- `claim_verifier._has_file_diff(file_path)` → 항상 False
- `grounding_scorer.calculate_score()` → 항상 0.0
- 모든 Claim 검증 실패

**증거:**
```bash
$ grep -r "evidence_graph" cortex_mcp/core/memory_manager.py
# 결과: 0개
```

---

### 문제 2: 잘못된 키 참조 (BUG)

**위치:** `memory_manager.py:508`

**현재 코드:**
```python
"verified_claims": len([
    vc for vc in verified_claims
    if vc["verification"].get("grounded", False)  # 잘못된 키!
])
```

**실제 ClaimVerifier 반환값:**
```python
result = {
    "verified": False,  # "grounded"가 아니라 "verified"
    "evidence": [],
    "confidence": 0.0,
}
```

**영향:**
- `vc["verification"].get("grounded")` → 항상 None
- `verified_claims` 계산이 항상 0

---

### 문제 3: referenced_contexts 빈 리스트 (INCOMPLETE)

**위치:** `memory_manager.py:497`

**현재 코드:**
```python
grounding_score = self.grounding_scorer.calculate_score(
    response_text=content,
    claims=claims,
    referenced_contexts=[]  # 항상 빈 리스트!
)
```

**영향:**
- Grounding Score 계산에 참조된 맥락 정보 없음
- 실제 Evidence와의 연결 불가능

---

## 3. 컴포넌트별 실제 작동 여부

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| **claim_extractor** | ✅ 정상 | 패턴 기반 Claim 추출 작동 |
| **fuzzy_analyzer** | ✅ 정상 | 확신도 분석 작동 |
| **contradiction_detector** | ⚠️ 부분 | Claim 추출에 의존, 일반 모순 감지 안됨 |
| **claim_verifier** | ❌ 실패 | Evidence Graph 비어있어 검증 불가 |
| **grounding_scorer** | ❌ 실패 | Evidence 없어 항상 0.0 |
| **code_structure_analyzer** | ❓ 미확인 | 테스트 안됨 |

---

## 4. 실제 검증 흐름 분석

### 현재 흐름 (실패)
```
1. update_memory(content="test_module.py에 함수 구현")
2. ClaimExtractor.extract_claims() → ["test_module.py 구현 완료"]
3. ClaimVerifier.verify_claim()
   ├─ _extract_file_references() → ["test_module.py"]
   ├─ _has_file_diff("test_module.py")
   │  └─ Evidence Graph 확인 → 빈 그래프
   │  └─ return False
   └─ verified: False, evidence: []
4. verified_claims 계산
   └─ vc["verification"].get("grounded") → None (잘못된 키)
   └─ count = 0
5. grounding_score.calculate_score()
   └─ referenced_contexts=[] → score = 0.0
```

### 기대하는 흐름 (수정 필요)
```
1. update_memory(content="test_module.py에 함수 구현")
2. **Evidence Graph 업데이트**
   ├─ 파일 참조 추출: ["test_module.py"]
   ├─ Git diff 확인 또는 파일 존재 확인
   └─ Evidence Graph 노드/엣지 추가
3. ClaimExtractor.extract_claims() → ["test_module.py 구현 완료"]
4. ClaimVerifier.verify_claim()
   ├─ _extract_file_references() → ["test_module.py"]
   ├─ _has_file_diff("test_module.py")
   │  └─ Evidence Graph 확인 → Diff 노드 발견!
   │  └─ return True
   └─ verified: True, evidence: [...]
5. verified_claims 계산
   └─ vc["verification"].get("verified") → True (올바른 키)
   └─ count = 1
6. grounding_score.calculate_score()
   └─ referenced_contexts=[실제 맥락] → score > 0.0
```

---

## 5. 수정 필요 사항

### 5.1 즉시 수정 (CRITICAL)

#### A. Evidence Graph 자동 업데이트 구현
**위치:** `memory_manager.update_memory()`

**추가 필요:**
```python
# Phase 9 검증 전에 Evidence Graph 업데이트
if self.hallucination_detection_available and role == "assistant":
    # 1. 파일 참조 추출
    file_refs = self._extract_file_references_from_content(content)

    # 2. Evidence Graph에 노드 추가
    for file_path in file_refs:
        self._update_evidence_graph_for_file(file_path)

    # 3. Git diff 파싱하여 Diff 노드 추가
    self._update_evidence_graph_from_git_diff()
```

#### B. 키 참조 수정
**파일:** `memory_manager.py:508`

**수정:**
```python
# 변경 전
if vc["verification"].get("grounded", False)

# 변경 후
if vc["verification"].get("verified", False)
```

#### C. referenced_contexts 실제 값 전달
**파일:** `memory_manager.py:497`

**수정:**
```python
# 변경 전
referenced_contexts=[]

# 변경 후
referenced_contexts=self._get_current_branch_contexts(branch_id)
```

---

### 5.2 중기 개선 (IMPORTANT)

1. **Claim 추출 패턴 확장**
   - 현재: "구현 완료", "수정 완료" 등 특정 패턴만
   - 개선: 일반적인 주장도 추출

2. **Evidence 매칭 알고리즘 개선**
   - 현재: 파일명 exact match
   - 개선: 유사도 기반 매칭

3. **Grounding Score 계산 개선**
   - 현재: Evidence 개수만 계산
   - 개선: Evidence 품질, 관련성 고려

---

## 6. 테스트 전략

### 6.1 Unit Test (각 컴포넌트 독립)
```python
def test_claim_extractor_patterns():
    """Claim 추출 패턴 테스트"""

def test_evidence_graph_update():
    """Evidence Graph 업데이트 테스트"""

def test_claim_verifier_with_evidence():
    """Evidence가 있을 때 검증 테스트"""
```

### 6.2 Integration Test
```python
def test_memory_manager_evidence_integration():
    """memory_manager + Evidence Graph 통합 테스트"""
    # 1. update_memory 호출
    # 2. Evidence Graph 업데이트 확인
    # 3. 검증 결과 확인
```

### 6.3 E2E Test
```python
def test_hallucination_detection_e2e():
    """실제 사용 시나리오 E2E 테스트"""
    # Scenario 1: True Positive (실제 구현)
    # Scenario 2: True Negative (거짓 주장)
    # Scenario 3: False Positive/Negative 비율 측정
```

---

## 7. 품질 목표

| 지표 | 현재 | 목표 |
|------|------|------|
| verified_claims (실제 구현) | 0% | 95%+ |
| grounding_score (실제 구현) | 0.0 | 0.7+ |
| False Positive 비율 | 미측정 | <5% |
| False Negative 비율 | 미측정 | <10% |

---

## 8. 다음 단계

### Step 1: Evidence Graph 자동 업데이트 구현
- [ ] `_extract_file_references_from_content()` 메서드 추가
- [ ] `_update_evidence_graph_for_file()` 메서드 추가
- [ ] `_update_evidence_graph_from_git_diff()` 메서드 추가

### Step 2: 버그 수정
- [ ] "grounded" → "verified" 키 수정
- [ ] referenced_contexts 실제 값 전달

### Step 3: 테스트 작성
- [ ] Unit Test 작성
- [ ] Integration Test 작성
- [ ] E2E Test 작성

### Step 4: 검증 및 배포
- [ ] 모든 테스트 통과 확인
- [ ] 품질 목표 달성 확인
- [ ] 문서 업데이트

---

## 9. 결론

**현재 상태:** Phase 9가 "실행되지만" "검증하지 못함"

**핵심 문제:** Evidence Graph가 비어있음

**해결 방법:** memory_manager에 Evidence Graph 자동 업데이트 로직 추가

**예상 작업:** 3-5일 (구현 + 테스트 + 검증)

**우선순위:** CRITICAL - 할루시네이션 검증은 Cortex의 핵심 차별화 기능

---

*이 보고서는 Phase 9 전면 재검토의 첫 단계로, 정확한 현황 파악을 목표로 작성되었습니다.*
