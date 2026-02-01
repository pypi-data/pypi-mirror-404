# Cortex MCP - 자동화 불가능 도구 39개 상세

**작성일**: 2026-01-01
**총 도구**: 53개
**자동화 가능**: 14개 (AI 자동 호출)
**자동화 불가능**: 39개 (수동 호출 필요)

---

## 1. 기본 설정 도구 (6개)

### 1.1 initialize_context
**기능**: 프로젝트 초기 맥락 스캔
**왜 불가능한가**: 사용자가 스캔 모드(FULL/LIGHT/NONE) 선택해야 함
- FULL: 전체 코드베이스 심층 분석 (토큰 소모 높음)
- LIGHT: 핵심 파일만 (README, 진입점, 설정)
- NONE: 스캔 건너뛰기
**비용/위험**: FULL 모드는 $0.5-2.0 비용 발생 가능 → 사용자 확인 필수

### 1.2 create_branch
**기능**: 새 브랜치 생성 (주제별 맥락 분리)
**왜 불가능한가**: 사용자가 브랜치명 결정해야 함
**참고**: MANDATORY 표시되어 있지만, 자동 생성은 주제 전환 감지 Hook에서 처리
- Hook이 자동 감지 → 사용자에게 확인 → create_branch 호출
- AI가 직접 호출하는 것은 브랜치명을 AI가 마음대로 정하는 것이므로 위험

### 1.3 sync_to_cloud
**기능**: 로컬 메모리를 Google Drive에 암호화 업로드
**왜 불가능한가**: 라이센스키 입력 필요
**보안**: E2E 암호화 → 라이센스키 없으면 복호화 불가

### 1.4 sync_from_cloud
**기능**: Google Drive에서 암호화된 메모리 복원
**왜 불가능한가**: 라이센스키 입력 필요
**보안**: 동일 라이센스키 필요

### 1.5 scan_project_deep
**기능**: Context Graph 기반 프로젝트 심층 스캔
**왜 불가능한가**: initialize_context와 동일 (스캔 모드 선택 필요)
**Phase**: Phase 9.4 (Initial Scan)

### 1.6 rescan_project
**기능**: 프로젝트 증분 재스캔
**왜 불가능한가**: 사용자 명시적 요청 필요 (자동 재스캔은 위험)
**용도**: 대규모 파일 변경 후 수동 재동기화

---

## 2. 조회/통계 도구 (9개)

### 2.1 get_scan_estimate
**기능**: 스캔 예상 비용 조회
**왜 불가능한가**: 사용자가 직접 확인 후 결정
**출력**: 예상 파일 수, 토큰 수, 비용

### 2.2 get_context_graph_info
**기능**: Context Graph 통계 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 총 노드 수, 엣지 수, 언어별 분포

### 2.3 get_hierarchy
**기능**: 프로젝트 계층 구조 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: Project → Branch → Node → Context 트리

### 2.4 list_nodes
**기능**: 브랜치의 Node 목록 조회
**왜 불가능한가**: 단순 조회 기능

### 2.5 list_git_links
**기능**: Git-Cortex 브랜치 연동 목록 조회
**왜 불가능한가**: 단순 조회 기능

### 2.6 list_snapshots
**기능**: 스냅샷 백업 목록 조회
**왜 불가능한가**: 단순 조회 기능

### 2.7 get_backup_history
**기능**: 백업 이력 타임라인 조회
**왜 불가능한가**: 단순 조회 기능

### 2.8 get_automation_status
**기능**: Plan A/B 모드 상태 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 현재 모드, 거부율, 성공률

### 2.9 get_reference_statistics
**기능**: Reference History 통계 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 추천 수락률, 가장 많이 사용된 맥락

---

## 3. Node 관리 도구 (2개)

### 3.1 create_node
**기능**: Context를 그룹핑하는 Node 생성
**왜 불가능한가**: 사용자가 그룹명 결정해야 함
**사용 시점**: Context 30개+ 누적 시
**계층**: Project → Branch → **Node** → Context

### 3.2 suggest_node_grouping
**기능**: Node 그룹핑 필요 여부 제안
**왜 불가능한가**: 제안만 하고 사용자가 판단
**출력**: "30개 이상 Context 발견. Node 생성을 권장합니다."

---

## 4. Git 연동 도구 (3개)

### 4.1 link_git_branch
**기능**: Git 브랜치와 Cortex 브랜치 연동
**왜 불가능한가**: 사용자가 연동 대상 결정
**동작**: Git checkout 시 Cortex 브랜치 자동 전환
**Phase**: Phase 4 (Git Integration)

### 4.2 get_git_status
**기능**: Git 저장소 상태 및 Cortex 연동 정보 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 현재 브랜치, 커밋 해시, 연동된 Cortex 브랜치

### 4.3 unlink_git_branch
**기능**: Git-Cortex 연동 해제
**왜 불가능한가**: 위험한 작업 (연동 해제 후 복구 불가)

---

## 5. 백업/복구 도구 (2개)

### 5.1 create_snapshot
**기능**: 프로젝트 상태 수동 스냅샷
**왜 불가능한가**: 사용자 명시적 요청 필요
**유형**: manual / auto / git_commit
**Phase**: Phase 7 (Backup/Restore)

### 5.2 restore_snapshot
**기능**: 스냅샷에서 복원
**왜 불가능한가**: 위험한 작업 (현재 상태 덮어씀)
**안전장치**: 복원 전 자동 백업 생성

---

## 6. Dashboard 도구 (1개)

### 6.1 get_dashboard_url
**기능**: Audit Dashboard URL 반환
**왜 불가능한가**: 단순 조회 기능
**출력**: http://localhost:8080 (서버 자동 시작)
**Phase**: Phase 6 (Audit Dashboard)

---

## 7. Automation 설정 도구 (2개)

### 7.1 set_automation_mode
**기능**: Plan A/B 수동 전환
**왜 불가능한가**: 사용자 정책 결정 필요
- Plan A (auto): 자동화 모드
- Plan B (semi_auto): 확인 절차 포함
**Phase**: Phase 8 (Plan B System)

### 7.2 update_reference_feedback
**기능**: Reference History 피드백 수정
**왜 불가능한가**: 사용자 수동 교정 필요
**용도**: 추천 결과에 대한 사후 피드백 업데이트

---

## 8. Boundary 설정 도구 (6개)

### 8.1 set_boundary
**기능**: 작업 경계 수동 설정
**왜 불가능한가**: 사용자가 허용 범위 결정
**Zero-Trust**: AI가 수정 가능한 파일 명시적 제한
**예시**: "auth.py, login.py만 수정 허용, .env 금지"

### 8.2 infer_boundary
**기능**: 작업 경계 자동 추론
**왜 불가능한가**: 추론 결과를 사용자가 확인 후 승인
**동작**: 작업 설명 + 최근 파일 기반 추론

### 8.3 validate_boundary_action
**기능**: 파일 작업 유효성 검증
**왜 불가능한가**: 수동 검증 요청 기능
**출력**: 허용/거부 + 사유

### 8.4 get_boundary_protocol
**기능**: System Prompt용 경계 프로토콜 생성
**왜 불가능한가**: 단순 조회 기능

### 8.5 get_boundary_violations
**기능**: 경계 위반 이력 조회
**왜 불가능한가**: 단순 조회 기능 (보안 감사용)

### 8.6 clear_boundary
**기능**: 작업 경계 초기화
**왜 불가능한가**: 위험한 작업 (보안 해제)

---

## 9. Semantic Web 도구 (Enterprise 전용, 5개)

### 9.1 add_semantic_relation
**기능**: Context 간 관계 수동 추가
**왜 불가능한가**: 사용자가 관계 타입 결정
**관계 타입**: DEPENDS_ON, REFERENCES, PART_OF, CONFLICTS_WITH 등
**Phase**: v2.1 (Semantic Web)

### 9.2 infer_relations
**기능**: 전이적 관계 추론
**왜 불가능한가**: 추론 요청은 수동 트리거
**예시**: A→B, B→C ⇒ A→C 추론

### 9.3 detect_conflicts
**기능**: 정책/버전 충돌 감지
**왜 불가능한가**: 수동 검사 요청
**출력**: 충돌 목록 + 해결 제안

### 9.4 suggest_related_contexts
**기능**: N-hop 관계 탐색 기반 추천
**왜 불가능한가**: 수동 추천 요청
**차이**: suggest_contexts(자동) vs suggest_related_contexts(수동)

### 9.5 get_semantic_web_stats
**기능**: 시맨틱 웹 통계 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 관계 수, 노드 수, 관계 타입별 분포

---

## 10. Pro+ 기능 (2개)

### 10.1 sync_parallel_sessions
**기능**: 다중 터미널 세션 동기화
**왜 불가능한가**: 사용자 명시적 동기화 요청 필요
**용도**: Terminal 1, 2, 3에서 동시 작업 시 맥락 병합
**Phase**: Pro+ 전용

### 10.2 get_active_sessions
**기능**: 실행 중인 다른 세션 조회
**왜 불가능한가**: 단순 조회 기능
**출력**: 세션 ID, 작업 브랜치, 마지막 활동 시간

---

## 11. Context 수동 작업 (1개)

### 11.1 resolve_context
**기능**: SHALLOW 노드를 DEEP으로 수동 해석
**왜 불가능한가**: 토큰 소모 발생 → 사용자 확인 필요
**Phase**: Phase C (Lazy Resolution)
**동작**:
- SHALLOW: 파일 경로만 (메타데이터)
- DEEP: 파일 내용 의미 분석 + 요약 + RAG 인덱싱

---

## 자동화 불가능한 이유 요약

| 카테고리 | 개수 | 불가능 이유 |
|---------|------|-------------|
| **설정** | 6 | 사용자 선택 필요 (모드, 라이센스, 브랜치명) |
| **조회** | 9 | 단순 정보 조회 (자동 호출 불필요) |
| **Node** | 2 | 그룹명 결정 필요 |
| **Git** | 3 | 연동 설정 또는 위험한 작업 |
| **백업** | 2 | 위험한 작업 (복원은 데이터 덮어씀) |
| **Dashboard** | 1 | 단순 조회 |
| **Automation** | 2 | 정책 결정 필요 |
| **Boundary** | 6 | 보안 범위 설정 또는 조회 |
| **Semantic Web** | 5 | Enterprise 기능, 수동 제어 필요 |
| **Pro+** | 2 | 멀티 세션 동기화 요청 |
| **Context** | 1 | 토큰 소모 발생 (DEEP 전환) |

---

## 자동화 vs 수동 기준

### 자동화 가능 조건
1. **Zero-Effort 원칙**: 사용자 개입 없이 AI가 판단 가능
2. **안전성**: 실수해도 복구 가능
3. **명확성**: 호출 시점이 명확 (세션 시작, 응답 후 등)
4. **비용**: 토큰 소모가 적음

### 자동화 불가능 조건
1. **선택 필요**: 사용자가 모드, 이름, 범위 등 결정
2. **위험성**: 데이터 삭제, 덮어쓰기 등 복구 불가
3. **비용**: 높은 토큰 소모 (사용자 확인 필요)
4. **보안**: 라이센스키, 작업 범위 등 민감한 설정
5. **정책**: Plan A/B, Boundary 등 사용자 정책 결정

---

**총 53개 도구 중:**
- **14개 자동화 가능** (27%)
- **39개 자동화 불가능** (73%)

이 비율은 **Zero-Trust 원칙**을 반영합니다.
AI가 모든 것을 자동으로 하는 것이 아니라, **중요한 결정은 사용자가 통제**합니다.
