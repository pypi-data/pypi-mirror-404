# Cortex Benchmark 구현 문제 수정 계획

**작성일**: 2025-12-29
**전문가 패널**: SW QA, MCP 개발, Python, AI, 데이터 분석, 알고리즘, 운영 전문가 합동 분석

---

## 1. 전문가 패널 종합 분석 (Ultra-Think Mode)

### 문제의 본질

**결론: 기능 구현 자체는 완료되었으나, 테스트 환경에서 정상 작동하지 않음**

벤치마크 테스트가 무의미한 이유는 크게 2가지:

1. **구현 문제 (50%)**: 핵심 기능이 테스트 환경에서 작동하지 않음
2. **테스트 설계 문제 (50%)**: 통계적으로 무의미한 샘플, 더미 데이터

---

## 2. 기능별 문제점 및 해결책

### 2.1. Evidence Graph 시스템 (test_06 실패 원인)

#### 현재 상태
```
- Evidence Graph가 초기화는 되지만 **노드가 추가되지 않음**
- 모든 grounding_score = 0.0
- ROC-AUC = 0.5 (random level)
```

#### 근본 원인 (코드 분석)

**문제 위치**: `memory_manager.py:330-350`, `evidence_graph.py:90-100`

```python
# memory_manager.py:330-350
self.claim_verifier = ClaimVerifier(
    project_id=self.project_id,
    project_path=actual_project_path  # Evidence Graph 초기화됨
)
```

하지만 Evidence Graph에 노드를 추가하는 코드가 **실행되지 않음**:

**원인 1**: `update_memory()`가 `context` 파라미터 없이 호출됨
```python
# 테스트 코드 (test_06_hallucination_detection.py:58-65)
result = memory_manager.update_memory(
    project_id=test_project_id,
    branch_id=branch_id,
    content=response["text"],
    role="assistant"
    # context 파라미터 없음!!! ← 핵심 문제
)
```

**원인 2**: `context` 파라미터가 없으면 Evidence Graph에 노드 추가가 실행되지 않음

Evidence Graph에 노드를 추가하는 함수들:
- `add_context_node()` (evidence_graph.py:90)
- `add_file_node()` (evidence_graph.py:140)
- `add_diff_node()` (evidence_graph.py:190)

이 함수들이 **호출되지 않아서** 그래프가 비어있음.

#### 해결책

**Option A: update_memory()에 자동 Evidence Graph 구축 추가 (권장)**

```python
# memory_manager.py의 update_memory() 함수 수정

def update_memory(..., context: Optional[Dict] = None):
    # ...

    # [신규] Phase 9: Evidence Graph 자동 구축
    if self.claim_verifier and self.evidence_graph:
        # 1. Context 노드 추가
        self.evidence_graph.add_context_node(
            context_id=f"context_{branch_id}_{timestamp}",
            branch_id=branch_id,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            metadata={"timestamp": timestamp, "role": role}
        )

        # 2. 파일 참조 추출 및 File 노드 추가
        file_refs = self._extract_file_references(content)
        for file_path in file_refs:
            if Path(file_path).exists():
                self.evidence_graph.add_file_node(
                    file_path=file_path,
                    content_hash=self._get_file_hash(file_path)
                )
                # Context → File 엣지 추가
                self.evidence_graph.add_edge(
                    source=f"context_{branch_id}_{timestamp}",
                    target=file_path,
                    edge_type="REFERENCED"
                )

        # 3. Git diff 노드 추가 (있으면)
        try:
            diff_output = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True, text=True, timeout=5
            )
            if diff_output.stdout.strip():
                self.evidence_graph.add_diff_node(
                    commit_hash="staging",
                    diff_content=diff_output.stdout,
                    modified_files=file_refs
                )
        except Exception:
            pass  # Git 없으면 무시

    # ...
```

**장점**:
- 테스트 코드 수정 불필요
- 실제 사용 시에도 자동으로 Evidence Graph 구축
- Zero-Effort 원칙 준수

**단점**:
- memory_manager.py가 무거워짐
- 파일 I/O 추가 (성능 영향)

**Option B: 테스트 코드에서 context 파라미터 명시 (빠른 수정)**

```python
# test_06_hallucination_detection.py:58-65 수정

result = memory_manager.update_memory(
    project_id=test_project_id,
    branch_id=branch_id,
    content=response["text"],
    role="assistant",
    context={  # ← 추가
        "files": ["test_file.py", "config.yaml"],
        "git_diff": True
    }
)
```

**장점**:
- 즉시 수정 가능
- memory_manager.py 수정 불필요

**단점**:
- 테스트마다 context 파라미터 작성해야 함
- 실제 사용 시 사용자가 수동으로 제공해야 함 (Zero-Effort 위반)

**권장: Option A (자동 구축)**

---

### 2.2. Reference History 시스템 (test_02, test_99 실패 원인)

#### 현재 상태
```
- suggest_contexts() 호출 시 0개 추천
- 테스트 통과했지만 실제로는 키워드 매칭 실패
```

#### 근본 원인 (코드 분석)

**문제 위치**: `reference_history.py:100-150` (suggest_contexts 로직)

**원인 1**: 키워드 매칭이 너무 엄격함
```python
# 테스트 쿼리: "Implement user authentication feature"
# 기록된 keywords: ["authentication", "login", "security"]

# 매칭 실패 케이스:
# "Implement" → keywords에 없음
# "user" → keywords에 없음
# "feature" → keywords에 없음
```

**원인 2**: Co-occurrence 계산이 부족함
```python
# reference_history.py:record() 호출은 되지만
# _co_occurrence 딕셔너리에 제대로 업데이트되지 않음
```

#### 해결책

**Option A: 퍼지 키워드 매칭 추가 (권장)**

```python
# reference_history.py의 suggest_contexts() 수정

from difflib import SequenceMatcher

def _fuzzy_match_keywords(self, query: str, entry_keywords: List[str]) -> float:
    """
    퍼지 키워드 매칭

    Returns:
        매칭 점수 (0.0 ~ 1.0)
    """
    query_words = set(query.lower().split())
    entry_words = set(word.lower() for word in entry_keywords)

    # 1. 완전 일치
    exact_matches = query_words & entry_words
    if exact_matches:
        return len(exact_matches) / max(len(query_words), len(entry_words))

    # 2. 부분 일치 (substring)
    partial_score = 0.0
    for q_word in query_words:
        for e_word in entry_words:
            if q_word in e_word or e_word in q_word:
                partial_score += 0.8
            elif SequenceMatcher(None, q_word, e_word).ratio() >= 0.7:
                partial_score += 0.5

    return min(1.0, partial_score / len(query_words))

def suggest_contexts(self, query: str, ...):
    # ...
    for entry in self._history:
        match_score = self._fuzzy_match_keywords(query, entry["task_keywords"])
        if match_score >= 0.3:  # 30% 이상 매칭 시 후보
            candidates.append((match_score, entry))
    # ...
```

**Option B: 테스트 데이터 수정 (빠른 수정)**

```python
# test_02_reference_accuracy.py:59-72 수정

test_queries = [
    {
        "query": "authentication login",  # ← 단순화
        "expected": ["auth_handler.py", "user_model.py", "security_utils.py"]
    },
    {
        "query": "database connection",  # ← 단순화
        "expected": ["db_connector.py", "config.py", "error_handler.py"]
    },
    # ...
]
```

**권장: Option A (퍼지 매칭)**

---

### 2.3. Grounding Score 계산 (test_06 실패 원인)

#### 현재 상태
```
- 모든 grounding_score = 0.0
- Evidence Graph 비어있어서 계산 불가
```

#### 근본 원인

**Grounding Score는 Evidence Graph에 의존함**:
```python
# grounding_scorer.py:90-100
def calculate_score(self, ..., referenced_contexts: List[str], ...):
    if not referenced_contexts:
        return {"score": 0.0, ...}  # ← Evidence Graph 비어있으면 0.0
```

Evidence Graph가 비어있으면 `referenced_contexts = []` → score = 0.0

#### 해결책

**2.1의 해결책과 동일**

Evidence Graph를 자동으로 구축하면 grounding_score도 자동으로 계산됨.

---

## 3. 우선순위별 수정 계획

### Phase 1: 핵심 기능 수정 (P0 - 즉시)

| 작업 | 파일 | 예상 시간 | 중요도 |
|------|------|-----------|--------|
| 1. Evidence Graph 자동 구축 | `memory_manager.py:330-400` | 2시간 | **P0** |
| 2. Reference History 퍼지 매칭 | `reference_history.py:100-150` | 1.5시간 | **P0** |
| 3. 테스트 context 파라미터 추가 | `test_06_hallucination_detection.py` | 30분 | P1 |

### Phase 2: 테스트 재설계 (P1 - 1일 내)

| 작업 | 파일 | 예상 시간 | 중요도 |
|------|------|-----------|--------|
| 4. test_01 토큰 계산 개선 | `test_01_token_efficiency.py` | 2시간 | P1 |
| 5. test_02 샘플 증가 (10→50) | `test_02_reference_accuracy.py` | 1시간 | P1 |
| 6. test_99 실제 코드 생성 | `test_99_e2e_workflow.py` | 3시간 | P1 |

### Phase 3: 검증 및 문서화 (P2 - 2일 내)

| 작업 | 파일 | 예상 시간 | 중요도 |
|------|------|-----------|--------|
| 7. 전체 테스트 재실행 | `pytest cortex_mcp/tests/` | 1시간 | P2 |
| 8. 벤치마크 리포트 생성 | `docs/benchmarks/` | 2시간 | P2 |
| 9. README 업데이트 | `README.md` | 1시간 | P2 |

**총 예상 시간**: 14시간 (2일)

---

## 4. 수정 상세 명세

### 4.1. Evidence Graph 자동 구축

**파일**: `cortex_mcp/core/memory_manager.py`

**수정 위치**: `update_memory()` 함수 내부

**추가할 코드**:
```python
# Line ~500-600 (update_memory 함수 내부)

# [신규] Phase 9: Evidence Graph 자동 구축
if self.claim_verifier and hasattr(self.claim_verifier, 'evidence_graph'):
    evidence_graph = self.claim_verifier.evidence_graph

    # 1. Context 노드 추가
    import hashlib
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    context_node_id = f"context_{branch_id}_{timestamp}"

    evidence_graph.add_context_node(
        context_id=context_node_id,
        branch_id=branch_id,
        content_hash=content_hash,
        metadata={"timestamp": timestamp, "role": role}
    )

    # 2. 파일 참조 추출 및 File 노드 추가
    import re
    file_pattern = r"(?:[\w./]+/)?[\w.]+\.(?:py|js|ts|tsx|jsx|java|cpp|c|h|go|rs|md|yaml|yml|json|xml|toml|ini|cfg|conf|txt)"
    file_refs = re.findall(file_pattern, content, re.IGNORECASE)
    file_refs = list(set(file_refs))  # 중복 제거

    for file_path in file_refs:
        # 파일 존재 확인 (여러 경로 시도)
        from pathlib import Path
        search_paths = [
            Path.cwd(),
            Path.cwd() / "cortex_mcp",
            Path(self.claim_verifier.project_path),
        ]

        file_found = False
        for base_path in search_paths:
            full_path = base_path / file_path
            if full_path.exists():
                # File 노드 추가
                try:
                    file_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
                except Exception:
                    file_hash = "unknown"

                evidence_graph.add_file_node(
                    file_path=str(full_path),
                    content_hash=file_hash
                )

                # Context → File 엣지 추가
                evidence_graph.add_edge(
                    source=context_node_id,
                    target=str(full_path),
                    edge_type="REFERENCED"
                )

                file_found = True
                break

    # 3. Git diff 노드 추가 (staging area 확인)
    try:
        import subprocess
        diff_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.claim_verifier.project_path,
            capture_output=True,
            text=True,
            timeout=5
        )

        if diff_result.returncode == 0 and diff_result.stdout.strip():
            modified_files = diff_result.stdout.strip().split("\n")

            # Diff 내용 가져오기
            diff_content_result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=self.claim_verifier.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if diff_content_result.returncode == 0:
                evidence_graph.add_diff_node(
                    commit_hash="staging",
                    diff_content=diff_content_result.stdout,
                    modified_files=modified_files
                )

                # Diff → File 엣지 추가
                for file_path in modified_files:
                    evidence_graph.add_edge(
                        source="diff_staging",
                        target=file_path,
                        edge_type="MODIFIED"
                    )
    except Exception as git_err:
        # Git 명령 실패는 무시 (Git 저장소가 아닐 수 있음)
        pass

    # Evidence Graph 저장
    evidence_graph._save_graph()
```

**검증 방법**:
```python
# 테스트 코드
result = memory_manager.update_memory(
    project_id="test",
    branch_id="test_branch",
    content="I implemented login.py and config.yaml",
    role="assistant"
)

# Evidence Graph 확인
graph = memory_manager.claim_verifier.evidence_graph.graph
assert len(graph.nodes) > 0, "Evidence Graph should have nodes"
print(f"Nodes: {list(graph.nodes)}")
```

---

### 4.2. Reference History 퍼지 매칭

**파일**: `cortex_mcp/core/reference_history.py`

**수정 위치**: `suggest_contexts()` 함수

**추가할 메서드**:
```python
# Line ~200 (ReferenceHistory 클래스 내부)

def _fuzzy_match_keywords(self, query: str, entry_keywords: List[str]) -> float:
    """
    퍼지 키워드 매칭

    Args:
        query: 검색 쿼리
        entry_keywords: 히스토리 엔트리의 키워드 목록

    Returns:
        매칭 점수 (0.0 ~ 1.0)
    """
    from difflib import SequenceMatcher

    query_words = set(query.lower().split())
    entry_words = set(word.lower() for word in entry_keywords)

    # 1. 완전 일치
    exact_matches = query_words & entry_words
    if exact_matches:
        exact_score = len(exact_matches) / max(len(query_words), len(entry_words))
        return exact_score

    # 2. 부분 일치 (substring + 유사도)
    partial_score = 0.0
    total_comparisons = 0

    for q_word in query_words:
        best_match = 0.0
        for e_word in entry_words:
            # Substring 매칭
            if q_word in e_word or e_word in q_word:
                best_match = max(best_match, 0.8)
            # 유사도 매칭 (70% 이상)
            elif SequenceMatcher(None, q_word, e_word).ratio() >= 0.7:
                best_match = max(best_match, 0.5)

        partial_score += best_match
        total_comparisons += 1

    if total_comparisons == 0:
        return 0.0

    return min(1.0, partial_score / total_comparisons)
```

**수정할 코드**:
```python
# Line ~250-300 (suggest_contexts 함수 내부)

def suggest_contexts(self, query: str, branch_id: str = None, top_k: int = 5) -> Dict:
    # ...

    # Tier 1: Reference History 기반 추천
    candidates = []

    for entry in self._history:
        # 퍼지 매칭 적용
        match_score = self._fuzzy_match_keywords(query, entry["task_keywords"])

        if match_score >= 0.3:  # 30% 이상 매칭 시 후보
            # Co-occurrence 점수 추가
            cooccurrence_bonus = 0.0
            for ctx_id in entry["contexts_used"]:
                cooccurrence_bonus += self._context_frequency.get(ctx_id, 0) * 0.01

            total_score = match_score + cooccurrence_bonus
            candidates.append((total_score, entry))

    # 정렬 및 Top-K 선택
    candidates.sort(key=lambda x: x[0], reverse=True)
    top_candidates = candidates[:top_k]

    # ...
```

**검증 방법**:
```python
# 테스트 코드
ref_history = ReferenceHistory(project_id="test")

# 히스토리 기록
ref_history.record(
    task_keywords=["authentication", "login"],
    contexts_used=["auth.py", "user.py"],
    branch_id="test_branch",
    project_id="test"
)

# 퍼지 매칭 테스트
result = ref_history.suggest_contexts(
    query="Implement user authentication feature",  # "authentication" 포함
    branch_id="test_branch",
    top_k=5
)

assert result.get("success") == True
assert len(result.get("contexts", [])) > 0
print(f"Suggested: {result.get('contexts')}")
```

---

## 5. 테스트 검증 계획

### 5.1. Evidence Graph 검증

```python
# tests/test_evidence_graph_fix.py

def test_evidence_graph_auto_population():
    """Evidence Graph 자동 구축 검증"""
    manager = MemoryManager(project_id="test")

    # update_memory 호출
    result = manager.update_memory(
        project_id="test",
        branch_id="test_branch",
        content="I implemented login.py and fixed bug in config.yaml",
        role="assistant"
    )

    # Evidence Graph 확인
    graph = manager.claim_verifier.evidence_graph.graph

    # 1. Context 노드 존재
    context_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "Context"]
    assert len(context_nodes) > 0, "Context node should exist"

    # 2. File 노드 존재 (login.py, config.yaml)
    file_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "File"]
    assert len(file_nodes) >= 2, "File nodes should exist"

    # 3. 엣지 존재
    assert len(graph.edges) > 0, "Edges should exist"

    # 4. Grounding Score 계산 가능
    grounding_score = result.get("grounding_score", 0.0)
    assert grounding_score > 0.0, f"Grounding score should be > 0, got {grounding_score}"
```

### 5.2. Reference History 검증

```python
# tests/test_reference_history_fix.py

def test_fuzzy_keyword_matching():
    """퍼지 키워드 매칭 검증"""
    ref_history = ReferenceHistory(project_id="test")

    # 히스토리 기록
    ref_history.record(
        task_keywords=["authentication", "login", "security"],
        contexts_used=["auth_handler.py", "user_model.py"],
        branch_id="test_branch",
        project_id="test"
    )

    # 퍼지 매칭 테스트 케이스
    test_queries = [
        ("Implement user authentication feature", True),  # "authentication" 포함
        ("Add login functionality", True),  # "login" 포함
        ("Fix database connection", False),  # 관련 없음
    ]

    for query, should_match in test_queries:
        result = ref_history.suggest_contexts(
            query=query,
            branch_id="test_branch",
            top_k=5
        )

        has_suggestions = len(result.get("contexts", [])) > 0

        if should_match:
            assert has_suggestions, f"Should suggest for query: {query}"
        else:
            assert not has_suggestions, f"Should NOT suggest for query: {query}"
```

---

## 6. 성공 기준

### Phase 1 (핵심 기능 수정) 완료 기준:

- [ ] Evidence Graph에 노드 자동 추가 (Context, File, Diff)
- [ ] Grounding Score > 0.0 (테스트 환경)
- [ ] Reference History 퍼지 매칭 작동 (매칭률 >= 70%)

### Phase 2 (테스트 재설계) 완료 기준:

- [ ] test_01: 정확한 토큰 계산 (tiktoken 사용)
- [ ] test_02: 샘플 50개 이상, 통계적 유의성 확보
- [ ] test_06: ROC-AUC >= 0.75
- [ ] test_99: 실제 코드 생성 (더미 제거)

### Phase 3 (전체 검증) 완료 기준:

- [ ] 전체 테스트 통과율 >= 95%
- [ ] 벤치마크 리포트 생성 완료
- [ ] 문서화 완료 (README, docs/)

---

## 7. 리스크 및 대응 방안

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| Evidence Graph 구축 시 성능 저하 | 중간 | 비동기 처리, 캐싱 도입 |
| Git 저장소 없는 환경에서 오류 | 낮음 | try-except로 무시 |
| Reference History 메모리 증가 | 낮음 | 히스토리 크기 제한 (1000개) |
| 테스트 실행 시간 증가 | 중간 | pytest-xdist로 병렬 실행 |

---

## 8. 다음 단계

1. **이 문서 승인 받기** (사용자 확인)
2. **Phase 1 실행**: Evidence Graph + Reference History 수정
3. **검증 테스트 작성 및 실행**
4. **Phase 2 실행**: 테스트 재설계
5. **최종 검증 및 문서화**

**예상 완료일**: 2025-12-31 (2일 소요)

---

*작성: Claude Code Expert Panel*
*최종 수정: 2025-12-29*
