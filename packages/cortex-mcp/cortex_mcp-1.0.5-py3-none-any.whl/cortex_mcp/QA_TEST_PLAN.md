# Cortex MCP - QA 및 테스트 계획서

## 개요

본 문서는 Cortex MCP 서비스의 프로덕션 배포 전 필수 테스트 항목을 정의합니다.

---

## 1. 테스트 단계 (Test Phases)

### Phase 1: 단위 테스트 (Unit Tests)
### Phase 2: 통합 테스트 (Integration Tests)
### Phase 3: 기능 테스트 (Functional Tests)
### Phase 4: MCP 프로토콜 준수 테스트
### Phase 5: Plan A/B 시스템 테스트
### Phase 6: 성능/부하 테스트 (Load Testing)
### Phase 7: 보안/침투 테스트 (Security Testing)
### Phase 8: 복구 및 안정성 테스트
### Phase 9: E2E 시나리오 테스트
### Phase 10: 배포 전 최종 검증

---

## Phase 1: 단위 테스트 (Unit Tests)

### 1.1 Core 모듈 단위 테스트

| 모듈 | 테스트 항목 | 우선순위 |
|------|-------------|----------|
| `memory_manager.py` | 브랜치 CRUD, 메모리 업데이트, 요약 생성 | P0 |
| `context_manager.py` | 압축/해제, Lazy Loading, 자동 압축 | P0 |
| `reference_history.py` | 참조 기록, 추천, 피드백 업데이트 | P0 |
| `rag_engine.py` | 인덱싱, 검색, Hybrid RAG | P0 |
| `git_sync.py` | 브랜치 연동, 변경 감지, 매핑 관리 | P1 |
| `backup_manager.py` | 스냅샷 생성/복원/삭제/비교 | P1 |
| `automation_manager.py` | Plan A/B 전환, 피드백 기록, 통계 | P1 |
| `crypto_utils.py` | 암호화/복호화, 키 유효성 | P1 |
| `cloud_sync.py` | 업로드/다운로드, 암호화 연동 | P2 |

### 1.2 예상 테스트 케이스 수
- memory_manager: 25개
- context_manager: 20개
- reference_history: 15개
- rag_engine: 20개
- git_sync: 15개
- backup_manager: 20개
- automation_manager: 15개
- crypto_utils: 10개
- cloud_sync: 10개
- **총계: ~150개**

---

## Phase 2: 통합 테스트 (Integration Tests)

### 2.1 모듈 간 통합 테스트

| 통합 시나리오 | 관련 모듈 | 검증 항목 |
|--------------|----------|----------|
| 브랜치 생성 → RAG 인덱싱 | memory_manager + rag_engine | 자동 인덱싱 동작 |
| 메모리 업데이트 → 자동 압축 | memory_manager + context_manager | 임계치 도달 시 압축 |
| 맥락 로드 → Reference History 기록 | context_manager + reference_history | 참조 이력 저장 |
| Git 체크아웃 → Cortex 브랜치 전환 | git_sync + memory_manager | 자동 전환 |
| 스냅샷 생성 → 복원 | backup_manager + memory_manager | 데이터 무결성 |
| 피드백 누적 → Plan 전환 | automation_manager | 자동 모드 전환 |

### 2.2 데이터 흐름 테스트

```
[사용자 입력] → [MCP Tool 호출] → [Core 처리] → [RAG 인덱싱] → [응답 반환]
```

각 단계에서 데이터 손실/변형 없이 전달되는지 검증

---

## Phase 3: 기능 테스트 (Functional Tests)

### 3.1 MCP 도구별 기능 테스트

#### 기본 도구 (7개)
| 도구 | 정상 케이스 | 에러 케이스 | 경계 케이스 |
|------|------------|------------|------------|
| initialize_context | FULL/LIGHT/NONE 모드 | 잘못된 경로 | 빈 프로젝트 |
| create_branch | 단일/중첩 브랜치 | 중복 이름 | 특수문자 이름 |
| search_context | 일치/부분 일치 | 결과 없음 | 대용량 쿼리 |
| update_memory | 짧은/긴 텍스트 | 빈 내용 | 특수문자 |
| get_active_summary | 활성 브랜치 | 브랜치 없음 | 요약 없음 |
| sync_to_cloud | 정상 동기화 | 인증 실패 | 네트워크 에러 |
| sync_from_cloud | 정상 복원 | 데이터 없음 | 키 불일치 |

#### 확장 도구 (24개)
- Smart Context 도구: 3개
- Reference History 도구: 4개
- Hierarchy 도구: 4개
- Git Integration 도구: 5개
- Dashboard 도구: 1개
- Backup 도구: 4개
- Automation 도구: 4개

### 3.2 CORTEX_MEMORY_PROTOCOL 준수 테스트

| 규칙 | 테스트 시나리오 |
|------|----------------|
| 초기화 책임 | 새 프로젝트 연결 시 스캔 모드 질문 |
| 맥락 로딩 책임 | 답변 전 suggest_contexts 호출 |
| 응답 스타일 | 보고 스타일 ("~합니다") 사용 |
| 정리 의무 | 대화 전환 감지 → 브랜치 생성 |
| Plan A/B 전환 | 거부율 30% 이상 시 Plan B |
| 보안 준수 | 로컬 데이터 유출 없음 |

---

## Phase 4: MCP 프로토콜 준수 테스트

### 4.1 MCP SDK 호환성

| 항목 | 검증 내용 |
|------|----------|
| Server 초기화 | Server("cortex-memory") 정상 생성 |
| Tool 등록 | @server.list_tools(), @server.call_tool() |
| 응답 형식 | TextContent 반환 |
| 에러 처리 | 표준 에러 형식 준수 |
| stdio 통신 | stdin/stdout 정상 동작 |

### 4.2 Claude Code 연동 테스트

```bash
# 등록 테스트
claude mcp add cortex-memory -- python main.py

# 도구 목록 확인
claude mcp list

# 실제 호출 테스트
# Claude Code 내에서 Cortex 도구 호출
```

---

## Phase 5: Plan A/B 시스템 테스트

### 5.1 Plan A (자동 모드) 테스트

| 시나리오 | 예상 동작 | 검증 방법 |
|----------|----------|----------|
| 브랜치 자동 생성 | 확인 없이 즉시 생성 | should_confirm = False |
| 맥락 자동 로드 | 즉시 로드 | 로드 시간 측정 |
| 자동 압축 | 30분 후 압축 | 타이머 검증 |

### 5.2 Plan B (반자동 모드) 테스트

| 시나리오 | 예상 동작 | 검증 방법 |
|----------|----------|----------|
| 브랜치 생성 요청 | 사용자 확인 필요 | should_confirm = True |
| 거부율 30% 도달 | Plan B 전환 | 모드 변경 확인 |
| 거부율 15% 이하 | Plan A 복귀 | 모드 복귀 확인 |

### 5.3 피드백 시스템 테스트

```python
# 테스트 시나리오
1. 피드백 10개 기록 (accepted: 7, rejected: 3)
2. 거부율 = 30% → Plan B 전환 확인
3. 피드백 10개 추가 (accepted: 9, rejected: 1)
4. 거부율 = 20% → Plan A 복귀 확인 안됨 (15% 이하여야 함)
5. 피드백 10개 추가 (accepted: 10, rejected: 0)
6. 거부율 = 13.3% → Plan A 복귀 확인
```

---

## Phase 6: 성능/부하 테스트 (Load Testing)

### 6.1 응답 시간 기준

| 도구 | 목표 응답 시간 | 최대 허용 |
|------|---------------|----------|
| search_context | < 500ms | 2s |
| update_memory | < 200ms | 1s |
| get_active_summary | < 100ms | 500ms |
| create_branch | < 300ms | 1s |
| load_context | < 500ms | 2s |
| create_snapshot | < 5s | 30s |

### 6.2 동시 처리 테스트

| 시나리오 | 동시 요청 수 | 성공률 목표 |
|----------|-------------|-----------|
| 동시 검색 | 10 | 100% |
| 동시 메모리 업데이트 | 5 | 100% |
| 동시 브랜치 생성 | 3 | 100% |

### 6.3 대용량 데이터 테스트

| 시나리오 | 데이터 크기 | 성능 기준 |
|----------|------------|----------|
| 대규모 프로젝트 스캔 | 10,000 파일 | < 5분 |
| 대용량 RAG 검색 | 100,000 문서 | < 2초 |
| 대용량 메모리 파일 | 10MB | 자동 요약 트리거 |
| 다수 브랜치 | 100개 브랜치 | 목록 조회 < 1초 |

### 6.4 부하 테스트 도구

```bash
# pytest-benchmark 사용
pytest tests/performance/ --benchmark-only

# locust 부하 테스트
locust -f tests/load/locustfile.py --host=http://localhost:8080
```

---

## Phase 7: 보안/침투 테스트 (Security Testing)

### 7.1 Zero-Trust 원칙 검증

| 검증 항목 | 테스트 방법 | 합격 기준 |
|----------|------------|----------|
| 외부 네트워크 차단 | 네트워크 모니터링 | 로컬 외 트래픽 0 |
| 데이터 암호화 | Track B 모드 테스트 | AES-256-GCM 적용 |
| 키 관리 | 키 없이 복호화 시도 | 실패해야 함 |
| 민감 데이터 로깅 | 로그 파일 검사 | PII 노출 없음 |

### 7.2 입력 검증 테스트

| 공격 유형 | 테스트 입력 | 예상 결과 |
|----------|------------|----------|
| SQL Injection | `'; DROP TABLE --` | 무해하게 처리 |
| Path Traversal | `../../etc/passwd` | 경로 제한 |
| Command Injection | `$(rm -rf /)` | 명령 실행 안됨 |
| XSS (Dashboard) | `<script>alert(1)</script>` | 이스케이프 |
| 대용량 입력 | 100MB 텍스트 | 크기 제한 적용 |

### 7.3 인증/인가 테스트

| 시나리오 | 검증 항목 |
|----------|----------|
| 잘못된 라이센스 키 | 클라우드 동기화 거부 |
| 만료된 키 | 복호화 실패 |
| 다른 사용자 데이터 접근 | 프로젝트 격리 확인 |

### 7.4 OWASP Top 10 체크리스트

- [ ] A01: Broken Access Control
- [ ] A02: Cryptographic Failures
- [ ] A03: Injection
- [ ] A04: Insecure Design
- [ ] A05: Security Misconfiguration
- [ ] A06: Vulnerable Components
- [ ] A07: Authentication Failures
- [ ] A08: Data Integrity Failures
- [ ] A09: Security Logging Failures
- [ ] A10: Server-Side Request Forgery

---

## Phase 8: 복구 및 안정성 테스트

### 8.1 장애 복구 테스트

| 장애 시나리오 | 복구 방법 | 검증 항목 |
|--------------|----------|----------|
| 프로세스 강제 종료 | 재시작 | 데이터 손실 없음 |
| 파일 시스템 오류 | 스냅샷 복원 | 복원 성공 |
| 메모리 부족 | Graceful 종료 | 에러 로깅 |
| 디스크 풀 | 경고 및 정지 | 부분 저장 |

### 8.2 데이터 무결성 테스트

| 테스트 항목 | 검증 방법 |
|------------|----------|
| 스냅샷 체크섬 | 생성/복원 후 비교 |
| RAG 인덱스 일관성 | 인덱싱 후 검색 검증 |
| 메모리 파일 손상 | YAML 파싱 테스트 |
| 참조 이력 무결성 | JSON 스키마 검증 |

### 8.3 롤백 테스트

```
1. 현재 상태 스냅샷 생성
2. 의도적 데이터 손상
3. 스냅샷에서 복원
4. 데이터 무결성 확인
```

---

## Phase 9: E2E 시나리오 테스트

### 9.1 사용자 시나리오

#### 시나리오 1: 신규 프로젝트 초기화
```
1. 새 프로젝트에 Cortex 연결
2. FULL 모드 스캔 선택
3. 초기 맥락 생성 확인
4. RAG 검색 동작 확인
```

#### 시나리오 2: 대화 주제 전환
```
1. 기존 브랜치에서 대화
2. 새로운 주제 언급
3. AI가 브랜치 생성 제안
4. 사용자 수락/거부
5. 맥락 분리 확인
```

#### 시나리오 3: 환경 마이그레이션
```
1. 로컬에서 작업
2. sync_to_cloud 실행
3. 새 환경에서 sync_from_cloud
4. 모든 맥락 복원 확인
```

#### 시나리오 4: Git 협업
```
1. Git 브랜치 체크아웃
2. Cortex 브랜치 자동 전환
3. 작업 후 커밋
4. 다른 브랜치로 전환
5. 맥락 전환 확인
```

#### 시나리오 5: 장기 기억 복원
```
1. 100개 이상의 대화 기록
2. 컨텍스트 압축 발생
3. 오래된 맥락 검색
4. 100% 회수율 확인 (Needle in a Haystack)
```

### 9.2 QA 검증 기준 (CLAUDE.md 기준)

| 지표 | 목표 | 테스트 방법 |
|------|------|------------|
| 맥락 추천 정확도 | 95% | Reference History 테스트 |
| 토큰 절감율 | 70% | Smart Context 비교 |
| RAG 검색 정확도 | 100% | Needle in a Haystack |
| 자동화 성공률 | 80%+ | Plan A 피드백 분석 |

---

## Phase 10: 배포 전 최종 검증

### 10.1 체크리스트

#### 코드 품질
- [ ] 모든 단위 테스트 통과
- [ ] 코드 커버리지 80% 이상
- [ ] 타입 힌트 완비
- [ ] 독스트링 완비
- [ ] 린트 에러 0개

#### 기능 완성도
- [ ] 모든 MCP 도구 정상 동작
- [ ] Plan A/B 자동 전환 동작
- [ ] Dashboard 정상 표시
- [ ] 스냅샷 생성/복원 동작
- [ ] Git 연동 동작

#### 성능 기준
- [ ] 응답 시간 기준 충족
- [ ] 부하 테스트 통과
- [ ] 메모리 누수 없음

#### 보안 기준
- [ ] Zero-Trust 원칙 준수
- [ ] 암호화 정상 동작
- [ ] 입력 검증 완료
- [ ] OWASP Top 10 점검

#### 문서화
- [ ] README.md 완성
- [ ] API 문서 완성
- [ ] 설치 가이드 완성
- [ ] 사용자 가이드 완성

### 10.2 릴리스 기준

| 항목 | 기준 |
|------|------|
| 단위 테스트 | 100% 통과 |
| 통합 테스트 | 100% 통과 |
| E2E 테스트 | 100% 통과 |
| 성능 테스트 | 목표 달성 |
| 보안 테스트 | Critical 0, High 0 |
| 코드 리뷰 | 승인 완료 |

---

## 테스트 환경

### 개발 환경
- Python 3.11+
- macOS / Linux
- ChromaDB (로컬)
- sentence-transformers

### 테스트 도구
- pytest: 단위/통합 테스트
- pytest-cov: 커버리지
- pytest-benchmark: 성능 측정
- locust: 부하 테스트
- bandit: 보안 스캔
- mypy: 타입 체크
- ruff: 린트

---

## 일정 (예상)

| Phase | 예상 소요 시간 |
|-------|---------------|
| Phase 1: 단위 테스트 | 3-4일 |
| Phase 2: 통합 테스트 | 2일 |
| Phase 3: 기능 테스트 | 2일 |
| Phase 4: MCP 준수 테스트 | 1일 |
| Phase 5: Plan A/B 테스트 | 1일 |
| Phase 6: 성능 테스트 | 2일 |
| Phase 7: 보안 테스트 | 2-3일 |
| Phase 8: 복구 테스트 | 1일 |
| Phase 9: E2E 테스트 | 2일 |
| Phase 10: 최종 검증 | 1일 |
| **총계** | **17-19일** |

---

## 테스트 파일 구조

```
cortex_mcp/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest 설정 및 fixtures
│   ├── unit/                    # 단위 테스트
│   │   ├── test_memory_manager.py
│   │   ├── test_context_manager.py
│   │   ├── test_reference_history.py
│   │   ├── test_rag_engine.py
│   │   ├── test_git_sync.py
│   │   ├── test_backup_manager.py
│   │   ├── test_automation_manager.py
│   │   ├── test_crypto_utils.py
│   │   └── test_cloud_sync.py
│   ├── integration/             # 통합 테스트
│   │   ├── test_memory_rag_integration.py
│   │   ├── test_context_reference_integration.py
│   │   ├── test_git_memory_integration.py
│   │   └── test_backup_restore_integration.py
│   ├── functional/              # 기능 테스트
│   │   ├── test_mcp_tools.py
│   │   ├── test_plan_ab_system.py
│   │   └── test_dashboard.py
│   ├── performance/             # 성능 테스트
│   │   ├── test_search_performance.py
│   │   ├── test_memory_performance.py
│   │   └── benchmark_results/
│   ├── security/                # 보안 테스트
│   │   ├── test_input_validation.py
│   │   ├── test_encryption.py
│   │   └── test_zero_trust.py
│   ├── e2e/                     # E2E 테스트
│   │   ├── test_new_project_scenario.py
│   │   ├── test_branch_switch_scenario.py
│   │   ├── test_migration_scenario.py
│   │   └── test_needle_in_haystack.py
│   └── load/                    # 부하 테스트
│       └── locustfile.py
```
