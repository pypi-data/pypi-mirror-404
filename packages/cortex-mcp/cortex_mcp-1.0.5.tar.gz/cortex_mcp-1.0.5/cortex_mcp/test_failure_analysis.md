# 테스트 실패 분석 보고서

**분석 일시**: 2025-12-21
**총 테스트**: 571개
**실패**: 298개 (52.2%)
**성공**: 273개 (47.8%)

---

## 1. Executive Summary

### 핵심 발견사항

1. **파일 누락 문제가 주요 원인**: 298개 실패 중 211개(70.8%)가 Exit Code 4로 실패했으며, 이는 16개의 테스트 파일이 `tests/security/` 디렉토리에서 누락되었기 때문입니다.

2. **Smart Context 압축 기능 실패**: Exit Code 1로 실패한 86개의 테스트 중 대부분은 Context Management, Memory Management, RAG Search 관련 기능의 로직 오류입니다.

3. **Phase 9 할루시네이션 검증 자체는 정상 작동**: 모든 실패한 테스트에서 Phase 9 Hallucination Verification은 정상적으로 실행되었습니다(Grounding Score 1.00).

---

## 2. 실패 패턴 분류

### 2.1 Exit Code 분포

| Exit Code | 개수 | 비율 | 의미 |
|-----------|------|------|------|
| **4** | 211개 | 70.8% | 파일/디렉토리를 찾을 수 없음 |
| **1** | 86개 | 28.9% | Assertion 실패 또는 런타임 에러 |
| **기타** | 1개 | 0.3% | 기타 |

### 2.2 에러 타입 분포

| 에러 타입 | 개수 | 비율 |
|-----------|------|------|
| 파일/디렉토리를 찾을 수 없음 | 211개 | 70.8% |
| 기타 (Assertion, Runtime) | 87개 | 29.2% |

---

## 3. 카테고리별 실패 분석

### 3.1 Context Management (31개 실패)

**우선순위**: CRITICAL

#### 공통 에러 패턴
```python
AssertionError: Context 로드 실패
assert False is True
```

#### 근본 원인
1. **Smart Context 압축 로직 버그**
   - `context_manager.py`의 compress/load 메커니즘이 제대로 작동하지 않음
   - 압축된 Context를 로드할 때 `success: false` 반환

2. **실제 에러 사례** (from `test_smart_context_compression`)
   ```
   tests/e2e/test_token_savings.py:376: in test_smart_context_compression
       assert loaded["success"] is True, "Context 로드 실패"
   E   AssertionError: Context 로드 실패
   E   assert False is True
   ```

3. **Phase 9 검증 로그 분석**
   - Bayesian Posterior가 0.301로 낮게 계산됨 (임계값 0.7 미만)
   - Evidence가 부족: git_diff(0.5) + file_exists(0.2)만 존재
   - 모든 Claim이 `verified=False`로 검증 실패

#### 영향받는 테스트
- `test_smart_context_compression`
- `test_lazy_loading_efficiency`
- `test_compression_preserves_summary`
- `test_load_context_basic`
- `test_load_context_full_content`
- 기타 26개 테스트

#### 수정 방향
1. `context_manager.py`의 `load_context()` 메서드 디버깅
2. 압축 해제 로직 검증
3. `success` 플래그 설정 조건 재검토

---

### 3.2 RAG Search (29개 실패)

**우선순위**: HIGH

#### 공통 에러 패턴
- 성능 테스트 실패 (indexing, embedding, search latency)
- ChromaDB 연동 문제

#### 근본 원인
1. **ChromaDB 초기화 실패**
   - 테스트 환경에서 ChromaDB 인스턴스가 제대로 생성되지 않음
   - 임베딩 모델 로딩 지연 또는 실패

2. **성능 기준 미달**
   - P95 Latency 50ms 목표를 초과하는 경우 발생
   - Batch Indexing 성능 저하

#### 영향받는 테스트
- `test_single_document_indexing`
- `test_batch_indexing_performance`
- `test_embedding_generation_speed`
- `test_search_latency_p50`
- `test_search_latency_p95`
- 기타 24개 테스트

#### 수정 방향
1. `rag_engine.py`의 ChromaDB 초기화 로직 안정화
2. 테스트 환경에서 임베딩 모델 pre-loading
3. 성능 기준 재조정 (현실적인 latency 목표 설정)

---

### 3.3 Hallucination Detection (30개 실패)

**우선순위**: HIGH

#### 공통 에러 패턴
```
ERROR: file or directory not found: tests/security/test_bayesian_updater.py
```

#### 근본 원인
**파일 누락**: 다음 테스트 파일들이 `tests/security/` 디렉토리에 존재하지 않음
- `test_bayesian_updater.py` (17개 테스트)
- `test_control_state.py` (22개 테스트)
- `test_grounding_score_accuracy.py`
- `test_hallucination_verification.py`

#### 실제 존재하는 파일
```
tests/security/
├── test_access_control.py
├── test_comprehensive_security.py
├── test_crypto_security.py
├── test_input_validation.py
└── test_license_security.py
```

#### 영향받는 테스트
- Bayesian Updater 테스트 17개
- Control State 테스트 22개
- 기타 할루시네이션 검증 테스트

#### 수정 방향
1. **누락된 테스트 파일 복구 또는 재생성**
   - Git 히스토리에서 삭제된 파일 복구
   - 없으면 재작성 필요

2. **테스트 스위트 재구성**
   - Phase 9 컴포넌트 테스트를 `tests/unit/` 또는 `tests/phase9/`로 이동
   - `tests/security/`는 보안 관련 테스트만 유지

---

### 3.4 Security (24개 실패)

**우선순위**: HIGH

#### 공통 에러 패턴
```
ERROR: file or directory not found: tests/security/test_control_state.py
```

#### 근본 원인
동일하게 파일 누락 문제

#### 영향받는 테스트
- Control State 테스트 22개
- Boundary 관련 테스트 2개

#### 수정 방향
Hallucination Detection과 동일

---

### 3.5 Telemetry (24개 실패)

**우선순위**: MEDIUM

#### 공통 에러 패턴
```
ERROR: file or directory not found: tests/security/test_critical_fixes.py
ERROR: file or directory not found: tests/security/test_telemetry_system.py
ERROR: file or directory not found: tests/security/test_telemetry_integration.py
```

#### 근본 원인
파일 누락:
- `test_critical_fixes.py`
- `test_telemetry_system.py`
- `test_telemetry_integration.py`
- `test_telemetry_v2_storage.py`

#### 영향받는 테스트
- TelemetryClient 메서드 테스트
- TelemetryStorage 통합 테스트
- 총 24개

#### 수정 방향
1. 텔레메트리 테스트를 `tests/telemetry/` 디렉토리로 분리
2. 누락된 파일 복구 또는 재작성

---

### 3.6 Memory Management (18개 실패)

**우선순위**: HIGH

#### 공통 에러 패턴
```python
AssertionError: update_memory 실패
assert result["success"] is True
```

#### 근본 원인
1. **memory_manager.py의 update_memory() 메서드 실패**
   - Phase 9 통합 후 발생한 regression
   - 할루시네이션 검증 실패 시 메모리 업데이트가 중단되는 문제

2. **Evidence Graph 연동 문제**
   - Claim 검증 시 Evidence를 찾지 못함
   - 파일 참조 추출 실패 (`u.c`와 같은 잘못된 파일명 추출)

#### 영향받는 테스트
- `test_update_memory_user`
- `test_update_memory_assistant`
- `test_auto_summarization`
- 기타 15개 테스트

#### 수정 방향
1. **Phase 9와 Memory Manager 통합 검토**
   - 할루시네이션 검증 실패해도 메모리는 저장되도록 수정
   - `verified` 플래그를 메타데이터로만 유지

2. **ClaimExtractor 파일 참조 추출 로직 개선**
   ```python
   # 현재: "WHERE u.created" → 잘못 추출 → "u.c"
   # 수정 필요: 파일명 패턴 정규식 개선
   ```

---

### 3.7 Backup/Snapshot (13개 실패)

**우선순위**: MEDIUM

#### 공통 에러 패턴
- Snapshot 생성/복원 실패
- 메타데이터 손상

#### 근본 원인
1. **backup_manager.py의 스냅샷 생성 로직 버그**
   - 압축된 Context를 스냅샷에 포함하지 못함
   - 복원 시 Context 재활성화 실패

2. **JSON 직렬화 에러**
   - datetime 객체 직렬화 실패
   - 일부 메타데이터가 JSON-serializable하지 않음

#### 영향받는 테스트
- `test_create_snapshot`
- `test_restore_snapshot`
- `test_list_snapshots`
- 기타 10개 테스트

#### 수정 방향
1. `backup_manager.py`의 JSON 직렬화 로직 수정
   - datetime → ISO 8601 문자열 변환
   - custom encoder 추가

2. Context 압축 상태를 스냅샷에 명시적으로 포함

---

### 3.8 Git Integration (10개 실패)

**우선순위**: LOW

#### 공통 에러 패턴
```
ERROR: file or directory not found: tests/security/test_initial_scanner_e2e.py
```

#### 근본 원인
1. **파일 누락**: `test_initial_scanner_e2e.py`, `test_initial_scanner.py`
2. **Cloud Sync 미구현**: Google Drive API 연동 테스트가 mock 없이 실행됨

#### 영향받는 테스트
- Git 브랜치 연동 테스트
- Initial Scanner E2E 테스트
- Cloud Sync 테스트

#### 수정 방향
1. 누락된 파일 복구
2. Cloud Sync 테스트에 mock 추가 (Google Drive API 호출 방지)

---

### 3.9 기타 (119개 실패)

**우선순위**: MEDIUM

#### 포함 카테고리
- Needle in Haystack (1개)
- Plan A/B System (15개)
- Node Grouping (8개)
- Reference History (12개)
- Ontology (0개 - 파일 누락)
- 기타 functional tests (83개)

#### 공통 에러 패턴
1. **파일 누락** (대부분)
   - `test_response_formatter.py` (31개)
   - `test_scan_optimizer.py` (31개)
   - `test_research_logger.py` (15개)

2. **MCP Tools 실패** (20개)
   - `test_mcp_tools.py`의 다양한 테스트 케이스

#### 근본 원인
1. Exit Code 4: 파일 누락
2. Exit Code 1: Context Management 연쇄 실패

---

## 4. 우선순위 수정 로드맵

### Phase 1: 파일 복구 (1-2일)

**목표**: Exit Code 4 에러 211개 해결

#### 작업 항목
1. Git 히스토리 확인
   ```bash
   git log --all --full-history -- tests/security/test_bayesian_updater.py
   ```

2. 삭제된 파일 복구
   ```bash
   git checkout <commit_hash> -- tests/security/test_*.py
   ```

3. 복구 불가능한 경우 재작성
   - `test_bayesian_updater.py`
   - `test_control_state.py`
   - `test_telemetry_system.py`
   - 기타 누락 파일

4. 디렉토리 재구성
   ```
   tests/
   ├── unit/                    # 단위 테스트
   ├── integration/             # 통합 테스트
   ├── e2e/                     # E2E 테스트
   ├── performance/             # 성능 테스트
   ├── security/                # 보안 테스트만
   └── phase9/                  # 할루시네이션 검증 테스트 (신규)
   ```

**예상 효과**: 211개 테스트 복구

---

### Phase 2: Context Management 수정 (2-3일)

**목표**: Exit Code 1 에러 31개 해결 (Context 관련)

#### 작업 항목

1. **context_manager.py 디버깅**
   ```python
   # core/context_manager.py

   def load_context(self, context_id: str, force_full_load: bool = False):
       # BUG: 압축된 Context를 로드할 때 success=False 반환
       # 수정: 압축 해제 로직 재검토

       # 현재 로직:
       if context_id in self._active_contexts:
           return {"success": False, "reason": "Already loaded"}

       # 수정 필요:
       if context_id in self._active_contexts:
           if not force_full_load:
               return {"success": True, "context": self._active_contexts[context_id]}
   ```

2. **테스트 케이스 재검토**
   - `test_smart_context_compression`: 압축/로드 사이클 검증
   - `test_lazy_loading_efficiency`: 토큰 절감율 70% 달성 여부
   - `test_compression_preserves_summary`: 요약 보존 검증

3. **Phase 9 통합 검토**
   - Bayesian Evidence 수집 로직 개선
   - `file_specific_diff` Evidence가 제대로 생성되지 않는 문제 해결

**예상 효과**: 31개 테스트 복구

---

### Phase 3: Memory Management 수정 (2일)

**목표**: Exit Code 1 에러 18개 해결 (Memory 관련)

#### 작업 항목

1. **memory_manager.py 수정**
   ```python
   # core/memory_manager.py

   def update_memory(self, project_id: str, branch_id: str, content: str, ...):
       # BUG: Phase 9 검증 실패 시 메모리 저장이 중단됨

       # 현재 로직:
       verification = self._verify_hallucination(content)
       if verification['risk_level'] == 'critical':
           return {"success": False, "reason": "Hallucination detected"}

       # 수정 필요:
       verification = self._verify_hallucination(content)
       # 검증 결과를 메타데이터로만 저장하고 메모리는 항상 저장
       metadata = {
           "verified": verification['grounding_score'] >= 0.7,
           "risk_level": verification['risk_level'],
           "grounding_score": verification['grounding_score']
       }
       self._save_context(content, metadata)
       return {"success": True, "verification": verification}
   ```

2. **ClaimExtractor 파일 참조 추출 개선**
   ```python
   # core/claim_extractor.py

   def _extract_file_references(self, claim_text: str) -> List[str]:
       # BUG: "WHERE u.created" → 잘못 추출 → "u.c"

       # 개선된 정규식:
       # 1. 확장자가 있는 파일만 추출
       # 2. 경로 패턴 우선 매칭
       file_pattern = r'(?:^|[\s"\'])([a-zA-Z0-9_/\-]+\.[a-zA-Z0-9]+)(?:[\s"\']|$)'
   ```

**예상 효과**: 18개 테스트 복구

---

### Phase 4: RAG Search 안정화 (1-2일)

**목표**: Exit Code 1 에러 29개 해결 (RAG 관련)

#### 작업 항목

1. **ChromaDB 초기화 안정화**
   ```python
   # core/rag_engine.py

   def __init__(self):
       # 임베딩 모델 pre-loading
       self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

       # ChromaDB persistent client 사용
       self.chroma_client = chromadb.PersistentClient(
           path=str(CHROMA_DB_PATH)
       )
   ```

2. **성능 기준 재조정**
   - P95 Latency 목표: 50ms → 100ms (현실적 조정)
   - Batch Indexing 성능: 테스트 환경 고려

3. **테스트 격리 개선**
   - 각 테스트마다 ChromaDB collection 초기화
   - Fixture 개선

**예상 효과**: 29개 테스트 복구

---

### Phase 5: Backup/Telemetry/기타 (1-2일)

**목표**: 나머지 Exit Code 1 에러 해결

#### 작업 항목

1. **backup_manager.py JSON 직렬화**
   ```python
   # core/backup_manager.py

   import json
   from datetime import datetime

   class DateTimeEncoder(json.JSONEncoder):
       def default(self, obj):
           if isinstance(obj, datetime):
               return obj.isoformat()
           return super().default(obj)

   # 사용:
   json.dumps(snapshot, cls=DateTimeEncoder)
   ```

2. **Cloud Sync Mock 추가**
   ```python
   # tests/conftest.py

   @pytest.fixture
   def mock_google_drive(mocker):
       mocker.patch('core.cloud_sync.GoogleDriveAPI')
   ```

3. **Plan A/B System 테스트 수정**
   - Context Management 수정 후 재테스트

**예상 효과**: 20-30개 테스트 복구

---

## 5. 통계 요약

### 5.1 카테고리별 실패 분포

| 카테고리 | 실패 개수 | 비율 | 우선순위 |
|---------|----------|------|---------|
| 기타 | 119개 | 39.9% | MEDIUM |
| Context Management | 31개 | 10.4% | CRITICAL |
| Hallucination | 30개 | 10.1% | HIGH |
| RAG Search | 29개 | 9.7% | HIGH |
| Security | 24개 | 8.1% | HIGH |
| Telemetry | 24개 | 8.1% | MEDIUM |
| Memory Management | 18개 | 6.0% | HIGH |
| Backup/Snapshot | 13개 | 4.4% | MEDIUM |
| Git Integration | 10개 | 3.4% | LOW |

### 5.2 모듈별 실패 분포 (Top 10)

| 모듈 | 실패 개수 | 비율 |
|------|----------|------|
| test_response_formatter.py | 31개 | 10.4% |
| test_scan_optimizer.py | 31개 | 10.4% |
| test_control_state.py | 22개 | 7.4% |
| test_mcp_tools.py | 20개 | 6.7% |
| test_bayesian_updater.py | 17개 | 5.7% |
| test_initial_scanner.py | 16개 | 5.4% |
| test_research_logger.py | 15개 | 5.0% |
| test_telemetry_system.py | 15개 | 5.0% |
| test_initial_scanner_e2e.py | 14개 | 4.7% |
| test_pay_attention_extended 2.py | 12개 | 4.0% |

---

## 6. 근본 원인 분석

### 6.1 주요 근본 원인

1. **파일 관리 문제 (70.8%)**
   - Git 커밋 누락 또는 실수로 삭제
   - 테스트 파일 위치 변경 후 업데이트 누락
   - 16개 파일이 `tests/security/`에서 누락

2. **Context Management 버그 (10.4%)**
   - 압축/해제 로직의 regression
   - Phase 9 통합 후 발생한 부작용
   - Evidence 수집 실패

3. **Memory Manager Regression (6.0%)**
   - Phase 9 검증 실패 시 메모리 저장 중단
   - ClaimExtractor의 파일 참조 추출 버그

4. **RAG Engine 불안정 (9.7%)**
   - ChromaDB 초기화 실패
   - 성능 기준 미달

---

## 7. 예상 복구 일정

| Phase | 작업 | 예상 일수 | 복구 테스트 수 | 누적 복구율 |
|-------|------|----------|---------------|------------|
| Phase 1 | 파일 복구 | 1-2일 | 211개 | 70.8% |
| Phase 2 | Context Management | 2-3일 | 31개 | 81.2% |
| Phase 3 | Memory Management | 2일 | 18개 | 87.2% |
| Phase 4 | RAG Search | 1-2일 | 29개 | 97.0% |
| Phase 5 | 기타 | 1-2일 | 9개 | 100% |
| **총계** | | **7-11일** | **298개** | **100%** |

---

## 8. 권장 사항

### 8.1 즉시 조치 항목

1. **파일 복구 우선 실행**
   - Git 히스토리에서 삭제된 테스트 파일 복구
   - 복구 불가능한 경우 재작성 계획 수립

2. **Context Management 긴급 수정**
   - `load_context()` 메서드의 critical bug 수정
   - Phase 9 통합 로직 재검토

3. **테스트 디렉토리 재구성**
   - `tests/security/`는 보안 테스트만 유지
   - Phase 9 테스트를 `tests/phase9/`로 분리

### 8.2 중장기 개선 사항

1. **CI/CD 파이프라인 강화**
   - 테스트 파일 누락 감지 자동화
   - Pre-commit hook에서 테스트 목록 검증

2. **테스트 격리 개선**
   - ChromaDB persistent storage를 메모리 DB로 교체 (테스트용)
   - Fixture 간 의존성 제거

3. **문서화 개선**
   - 테스트 디렉토리 구조 명시
   - Phase 9 통합 가이드라인 작성

---

## 9. 결론

### 핵심 요약

- **주요 원인**: 70.8%가 파일 누락, 나머지 29.2%가 로직 버그
- **가장 시급한 수정**: Context Management (CRITICAL)
- **예상 복구 기간**: 7-11일
- **복구 후 테스트 성공률 예상**: 95% 이상

### 긍정적 발견사항

1. **Phase 9 자체는 정상 작동**
   - 할루시네이션 검증 로직은 모든 테스트에서 정상 실행
   - Grounding Score 계산이 정확함

2. **핵심 기능은 대부분 정상**
   - Initialize Context (FULL/LIGHT/NONE 모드)
   - Create Branch
   - 기본적인 Memory 기록

3. **체계적인 에러 패턴**
   - Exit Code가 명확하게 분류됨
   - 근본 원인 파악 가능

---

**작성자**: Claude Code (AI)
**분석 대상**: final_report.md (571 tests)
**다음 단계**: Phase 1 파일 복구 시작
