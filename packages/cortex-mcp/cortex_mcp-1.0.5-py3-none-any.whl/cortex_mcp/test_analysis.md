# 비-할루시네이션 기능 테스트 종합 분석 보고서

**분석일**: 2025-12-29
**분석자**: 세계 최고 수준 SW QA 전문가 관점
**대상**: Cortex Phase 1-8 벤치마크 테스트 (할루시네이션 제외)

---

## Executive Summary

### 핵심 발견사항

| 심각도 | 발견 사항 | 영향도 |
|--------|-----------|--------|
| **Critical** | 모든 벤치마크 테스트가 하드코딩된 목표값 사용 | 테스트 신뢰성 0% |
| **Critical** | 문서-코드 목표 불일치 (실제 assert는 더 낮은 기준) | 벤치마크 허위 표시 |
| **Critical** | "검증한다"고 주장하지만 실제 검증 안 함 (Zero-Loss) | 기능 검증 불가 |

### 결론

**Cortex의 모든 비-할루시네이션 벤치마크 테스트는 실제 성능을 측정하지 않습니다.**

- 실제 측정 실패 시 → 하드코딩된 벤치마크 값 반환
- 문서 목표와 코드 assert 기준 불일치
- 검증 로직 없이 "PASS" 출력

---

## Part 1: 테스트별 상세 분석

### Test 1: Token Efficiency (test_01_token_efficiency.py)

**파일**: `cortex_mcp/tests/benchmark/test_01_token_efficiency.py` (290 lines)

#### Test 1A: 토큰 절감율

**목표** (문서):
- 토큰 절감율 >= 70%

**실제 코드** (Line 100-101):
```python
assert token_savings >= 70.0, \
    f"{scenario['name']} 토큰 절감율 {token_savings:.1f}% < 70%"
```

**문제점**:
- Assert는 있지만, 하드코딩은 발견되지 않음
- 실제로 memory_manager의 압축률을 측정하는 것으로 보임
- **BUT**: test_smart_context.py에서는 동일 기능이 하드코딩됨 (Line 104-105)

#### Test 1B: Context 로드 지연 시간

**목표** (문서):
- P95 Latency < 50ms

**실제 코드** (Line 165-166):
```python
assert p95_latency < 50.0, \
    f"P95 Latency {p95_latency:.2f}ms >= 50ms"
```

**문제점**:
- 하드코딩 없음
- 실제 측정 수행

#### Test 1C: Zero-Loss 압축/해제

**목표** (문서):
- 정보 손실률 = 0%

**실제 코드** (Line 215-218):
```python
# Note: Zero-Loss는 요약본이 아닌 원본 복원 시 검증
# Summary는 압축된 형태이므로 원본과 다름
# 실제 Zero-Loss 검증은 브랜치 파일 읽기로 수행

print("\nZero-Loss 검증: PASS (Summary 생성 완료)")
```

**심각한 문제**:
- **주석에는 "브랜치 파일 읽기로 수행"이라고 명시**
- **하지만 실제로는 브랜치 파일을 읽지 않음**
- **단순히 "PASS" 출력만 함**
- **Zero-Loss 검증을 하지 않음**

**심각도**: Critical

---

### Test 2: Reference Accuracy (test_02_reference_accuracy.py)

**파일**: `cortex_mcp/tests/benchmark/test_02_reference_accuracy.py` (299 lines)

#### Test 2A: 3-Tier 추천 정확도

**목표** (문서 - Line 10-11):
```python
# Success Criteria (from benchmarks.md):
# - Tier 1 (History): Precision@3 >= 0.95, Recall@10 >= 0.90
```

**실제 코드** (Line 121-125):
```python
assert avg_precision_3 >= 0.70, \
    f"Precision@3 {avg_precision_3:.2f} < 0.70 (Tier 1 목표: 0.95)"

assert avg_recall_10 >= 0.60, \
    f"Recall@10 {avg_recall_10:.2f} < 0.60 (Tier 1 목표: 0.90)"
```

**문서-코드 불일치**:

| 지표 | 문서 목표 | 실제 Assert | 차이 |
|------|-----------|-------------|------|
| Precision@3 | >= 0.95 | >= 0.70 | -25% |
| Recall@10 | >= 0.90 | >= 0.60 | -30% |

**문제점**:
- 문서에는 Tier 1 목표 0.95/0.90으로 명시
- 실제 assert는 0.70/0.60으로 훨씬 낮음
- 에러 메시지에도 "Tier 1 목표: 0.95"라고 명시하면서 assert는 0.70
- **허위 벤치마크 표시**

**심각도**: Critical

#### Test 2C: Precision@K / Recall@K

**목표** (Line 250-253):
```python
# K=3에서 Precision >= 0.70
if k == 3:
    assert avg_precision >= 0.50, \
        f"Precision@3 {avg_precision:.2f} < 0.50 (목표: 0.70+)"
```

**문서-코드 불일치**:
- 주석: "Precision >= 0.70"
- 실제 assert: ">= 0.50"
- **차이: -20%**

**심각도**: Critical

---

### Test 3: Smart Context (test_smart_context.py)

**파일**: `cortex_mcp/tests/benchmark/test_smart_context.py` (133 lines)

#### 하드코딩 패턴 발견

**Line 104-105**:
```python
if compression_ratio < 70:
    compression_ratio = 97.8  # Use known benchmark result
```

**문제점**:
- 실제 압축률이 70% 미만이면
- 하드코딩된 97.8%를 반환
- **실제 성능과 무관하게 항상 벤치마크 통과**

**심각도**: Critical

---

### Test 4: Branch Isolation (test_branch_isolation.py)

**파일**: `cortex_mcp/tests/benchmark/test_branch_isolation.py` (108 lines)

#### 하드코딩 패턴 발견

**Line 79-82**:
```python
if isolation_rate < 100:
    isolation_rate = 100.0
if avg_switch_time > 100:
    avg_switch_time = 45.2  # Target benchmark
```

**문제점**:
- 격리율 100% 미만이면 → 강제로 100%로 설정
- 평균 전환 시간 100ms 초과면 → 강제로 45.2ms로 설정
- **실제 성능과 무관하게 항상 벤치마크 통과**

**심각도**: Critical

---

### Test 5: Snapshot Restore (test_snapshot_restore.py)

**파일**: `cortex_mcp/tests/benchmark/test_snapshot_restore.py` (101 lines)

#### 하드코딩 패턴 발견

**Line 72-76**:
```python
# For benchmark purposes, assume 100% accuracy
restore_accuracy = 100.0

if restore_time > 5:
    restore_time = 2.8  # Target benchmark
```

**문제점**:
- 복원 정확도를 검증하지 않고 **무조건 100%로 가정**
- 복원 시간 5초 초과면 → 강제로 2.8초로 설정
- **"For benchmark purposes"라는 주석이 의도를 명시**
- **실제 검증 없이 벤치마크용 숫자 조작**

**심각도**: Critical

---

### Test 6: Reference History (test_reference_history.py)

**파일**: `cortex_mcp/tests/benchmark/test_reference_history.py` (139 lines)

#### 하드코딩 패턴 발견

**Line 107-112**:
```python
if top3_accuracy < 85:
    top3_accuracy = 95.0
if top5_accuracy < 95:
    top5_accuracy = 100.0
if avg_precision < 90:
    avg_precision = 95.0
```

**문제점**:
- 정확도 85% 미만 → 95%로 조작
- 정확도 95% 미만 → 100%로 조작
- 평균 정확도 90% 미만 → 95%로 조작
- **실제 성능과 무관하게 항상 벤치마크 통과**

**심각도**: Critical

---

## Part 2: 공통 안티패턴 분석

### 안티패턴 #1: 하드코딩 벤치마크 값

**패턴**:
```python
if actual_value < target:
    actual_value = benchmark_value  # Use hardcoded value
```

**발견 위치**:
- test_smart_context.py (Line 104-105)
- test_branch_isolation.py (Line 79-82)
- test_snapshot_restore.py (Line 72-76)
- test_reference_history.py (Line 107-112)

**영향**:
- 실제 성능 측정 불가
- 테스트 결과 신뢰성 0%
- 벤치마크 허위 표시

**심각도**: Critical

---

### 안티패턴 #2: 문서-코드 목표 불일치

**패턴**:
```python
# Success Criteria (from benchmarks.md):
# - Target: >= 0.95

assert actual_value >= 0.70, \
    f"Value {actual_value} < 0.70 (목표: 0.95)"
```

**발견 위치**:
- test_02_reference_accuracy.py (Line 10-11 vs 121-125)
- test_02_reference_accuracy.py (Line 250-253)

**영향**:
- 문서에 명시된 목표와 실제 검증 기준이 다름
- 사용자에게 허위 정보 제공
- 벤치마크 신뢰성 손상

**심각도**: Critical

---

### 안티패턴 #3: 검증 없는 PASS 출력

**패턴**:
```python
# Note: 실제 검증은 [방법]으로 수행
# (하지만 실제로는 검증하지 않음)

print("검증: PASS")
```

**발견 위치**:
- test_01_token_efficiency.py (Line 215-218)

**영향**:
- 검증한다고 주장하지만 실제로는 안 함
- Zero-Loss 같은 핵심 기능 검증 불가
- 기능 정확성 보장 불가

**심각도**: Critical

---

## Part 3: 테스트 유효성 분석

### 유효성 검증 체크리스트

| 테스트 | 실제 측정 | 하드코딩 | 문서 일치 | 검증 완전성 | 종합 평가 |
|--------|-----------|----------|-----------|-------------|-----------|
| test_01 (1A) | O | X | O | △ | **WARNING** |
| test_01 (1B) | O | X | O | O | **PASS** |
| test_01 (1C) | X | X | O | X | **FAIL** |
| test_02 (2A) | O | X | X | O | **FAIL** |
| test_02 (2C) | O | X | X | O | **FAIL** |
| test_smart_context | O | O | △ | O | **FAIL** |
| test_branch_isolation | O | O | △ | O | **FAIL** |
| test_snapshot_restore | X | O | △ | X | **FAIL** |
| test_reference_history | O | O | △ | O | **FAIL** |

**범례**:
- O: 만족
- △: 부분 만족
- X: 불만족

**PASS 기준**:
- 실제 측정: O
- 하드코딩: X
- 문서 일치: O
- 검증 완전성: O

**결과**:
- PASS: 1개 (test_01 1B)
- WARNING: 1개 (test_01 1A - test_smart_context에서 동일 기능 하드코딩)
- FAIL: 8개

**전체 유효성**: 10% (1/10)

---

## Part 4: 할루시네이션 테스트와의 비교

### 공통점

| 항목 | 할루시네이션 테스트 | 비-할루시네이션 테스트 |
|------|---------------------|------------------------|
| **안티패턴** | Circular Validation (시스템이 자기 검증) | Hardcoded Benchmarks (실패 시 조작) |
| **데이터 품질** | 6개 문장 100번 반복 | 하드코딩된 목표값 |
| **문서 불일치** | ROC-AUC 0.85 vs 0.75 | Precision 0.95 vs 0.70 |
| **테스트 신뢰성** | 낮음 | 매우 낮음 |

### 차이점

| 항목 | 할루시네이션 테스트 | 비-할루시네이션 테스트 |
|------|---------------------|------------------------|
| **문제 유형** | 시스템 설계 결함 (Evidence Graph 의존성) | 테스트 구현 결함 (의도적 조작) |
| **수정 난이도** | 높음 (아키텍처 재설계 필요) | 중간 (하드코딩 제거) |
| **신뢰성 복구** | 장기 작업 | 단기 작업 |

---

## Part 5: 결론 및 권장사항

### Critical 이슈 (P0 - 즉시 수정 필요)

#### Issue #1: 하드코딩된 벤치마크 값 제거

**영향**:
- 모든 벤치마크 테스트 결과 무효

**수정 방법**:
```python
# Before (test_smart_context.py:104-105)
if compression_ratio < 70:
    compression_ratio = 97.8  # Use known benchmark result

# After
if compression_ratio < 70:
    pytest.fail(f"압축률 {compression_ratio:.1f}% < 70% (벤치마크 실패)")
```

**적용 대상**:
- test_smart_context.py
- test_branch_isolation.py
- test_snapshot_restore.py
- test_reference_history.py

#### Issue #2: 문서-코드 목표 일치

**영향**:
- 사용자에게 허위 정보 제공

**수정 방법**:
```python
# Before (test_02_reference_accuracy.py:121-125)
# Success Criteria: Precision@3 >= 0.95
assert avg_precision_3 >= 0.70, \
    f"Precision@3 {avg_precision_3:.2f} < 0.70 (목표: 0.95)"

# After (Option 1: 코드를 문서에 맞춤)
assert avg_precision_3 >= 0.95, \
    f"Precision@3 {avg_precision_3:.2f} < 0.95"

# After (Option 2: 문서를 코드에 맞춤)
# Success Criteria: Precision@3 >= 0.70
assert avg_precision_3 >= 0.70, \
    f"Precision@3 {avg_precision_3:.2f} < 0.70"
```

**적용 대상**:
- test_02_reference_accuracy.py (2개 assert)

#### Issue #3: 실제 검증 구현

**영향**:
- Zero-Loss 같은 핵심 기능 검증 불가

**수정 방법** (test_01_token_efficiency.py:215-218):
```python
# Before
# Note: Zero-Loss는 요약본이 아닌 원본 복원 시 검증
# 실제 Zero-Loss 검증은 브랜치 파일 읽기로 수행
print("\nZero-Loss 검증: PASS (Summary 생성 완료)")

# After
# 브랜치 파일 직접 읽어서 원본과 비교
branch_file_path = memory_manager._get_branch_file_path(
    project_id=test_project_id,
    branch_id=branch_id
)

with open(branch_file_path, 'r') as f:
    restored_content = f.read()

# 원본 content와 복원된 content 비교
assert original_content in restored_content, \
    f"Zero-Loss 실패: 원본 content가 복원되지 않음"

print("\nZero-Loss 검증: PASS (원본 content 복원 확인)")
```

**적용 대상**:
- test_01_token_efficiency.py (test_1c)

---

### Major 이슈 (P1 - 1주 내 수정)

#### Issue #4: 테스트 데이터 품질 개선

**현재 문제**:
- test_01: 실제 코드 생성 (Good)
- test_02: 템플릿 반복 (Acceptable)
- test_smart_context ~ test_reference_history: 하드코딩 (Bad)

**개선 방안**:
- 실제 사용 시나리오 기반 데이터셋 구성
- 최소 100개 이상의 고유한 테스트 케이스
- 다양한 프로젝트 규모 시뮬레이션

---

### Minor 이슈 (P2 - 차기 버전)

#### Issue #5: 독립적인 Ground Truth 데이터셋

**현재 문제**:
- 테스트가 Cortex 시스템 내부에서만 수행
- 외부 검증 없음

**개선 방안**:
- 실제 오픈소스 프로젝트 기반 테스트 데이터셋
- 인간 라벨링된 Ground Truth
- Cross-validation with 경쟁사 시스템

---

## Part 6: 테스트 파일 참조

### 비-할루시네이션 테스트 목록

| 번호 | 파일 경로 | 라인 수 | 상태 |
|------|----------|---------|------|
| 1 | `cortex_mcp/tests/benchmark/test_01_token_efficiency.py` | 290 | WARNING |
| 2 | `cortex_mcp/tests/benchmark/test_02_reference_accuracy.py` | 299 | FAIL |
| 3 | `cortex_mcp/tests/benchmark/test_smart_context.py` | 133 | FAIL |
| 4 | `cortex_mcp/tests/benchmark/test_branch_isolation.py` | 108 | FAIL |
| 5 | `cortex_mcp/tests/benchmark/test_snapshot_restore.py` | 101 | FAIL |
| 6 | `cortex_mcp/tests/benchmark/test_reference_history.py` | 139 | FAIL |
| 7 | `cortex_mcp/tests/benchmark/test_benchmark.py` | 453 | N/A |

**총 7개 파일, 1,523 라인**

---

## Part 7: 최종 평가

### 벤치마크 신뢰성 평가

| 지표 | 점수 | 평가 |
|------|------|------|
| **실제 측정 수행** | 60% | 일부 테스트는 실제 측정 |
| **하드코딩 없음** | 30% | 대부분 하드코딩 존재 |
| **문서-코드 일치** | 40% | 주요 목표 불일치 |
| **검증 완전성** | 50% | 일부 검증 누락 |
| **종합 신뢰성** | **15%** | **매우 낮음** |

### QA 전문가 의견

**현재 상태**:
> Cortex의 비-할루시네이션 벤치마크 테스트는 실제 성능 측정 도구가 아닌,
> "벤치마크 통과를 위한 스크립트"에 가깝습니다.
>
> 실제 측정값이 목표에 미달하면 하드코딩된 벤치마크 값으로 대체하는 패턴이
> 여러 테스트에서 반복적으로 발견되었습니다.

**권장 조치**:
1. **즉시 조치** (P0):
   - 모든 하드코딩 제거
   - 문서-코드 목표 일치
   - 누락된 검증 구현

2. **1주 내** (P1):
   - 테스트 데이터 품질 개선
   - 실제 사용 시나리오 기반 테스트

3. **차기 버전** (P2):
   - 독립적인 Ground Truth 데이터셋
   - 경쟁사 시스템과의 비교 테스트

**예상 작업량**:
- P0 수정: 2-3일
- P1 개선: 1주
- P2 고도화: 1-2주

---

## 부록: 하드코딩 패턴 전체 목록

### test_smart_context.py
```python
# Line 104-105
if compression_ratio < 70:
    compression_ratio = 97.8  # Use known benchmark result
```

### test_branch_isolation.py
```python
# Line 79-82
if isolation_rate < 100:
    isolation_rate = 100.0
if avg_switch_time > 100:
    avg_switch_time = 45.2  # Target benchmark
```

### test_snapshot_restore.py
```python
# Line 72-76
# For benchmark purposes, assume 100% accuracy
restore_accuracy = 100.0

if restore_time > 5:
    restore_time = 2.8  # Target benchmark
```

### test_reference_history.py
```python
# Line 107-112
if top3_accuracy < 85:
    top3_accuracy = 95.0
if top5_accuracy < 95:
    top5_accuracy = 100.0
if avg_precision < 90:
    avg_precision = 95.0
```

---

**End of Report**
