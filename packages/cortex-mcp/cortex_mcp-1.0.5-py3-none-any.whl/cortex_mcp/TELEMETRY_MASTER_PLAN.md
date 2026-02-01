# Cortex 텔레메트리 마스터 플랜

**작성일**: 2025-12-14
**버전**: v1.0
**스코프**: MCP 서비스 + Extension 서비스 (Web 제외)

---

## 목차

1. [개요](#1-개요)
2. [전문가 팀 분석](#2-전문가-팀-분석)
3. [아키텍처 설계](#3-아키텍처-설계)
4. [데이터 모델](#4-데이터-모델)
5. [MCP 서비스 텔레메트리](#5-mcp-서비스-텔레메트리)
6. [Extension 서비스 텔레메트리](#6-extension-서비스-텔레메트리)
7. [Admin 대시보드](#7-admin-대시보드)
8. [구현 로드맵](#8-구현-로드맵)
9. [QA 및 검증](#9-qa-및-검증)

---

## 1. 개요

### 1.1 목표

Cortex의 MCP 서비스와 Extension 서비스에서 유료/무료 사용자의 사용 데이터를 체계적으로 수집하고, Admin 대시보드에서 실시간으로 분석할 수 있는 텔레메트리 시스템 구축.

### 1.2 핵심 요구사항

| 항목 | 요구사항 |
|------|----------|
| **대상 서비스** | MCP 서비스, Extension 서비스 (Web 제외) |
| **사용자 구분** | 유료/무료 사용자 데이터 분리 |
| **데이터 보안** | Zero-Trust 원칙 준수 (로컬 데이터 수집) |
| **Admin 뷰** | 실시간 대시보드, 통계 분석, 이벤트 로그 조회 |
| **확장성** | 향후 Web 서비스 추가 가능하도록 설계 |

### 1.3 제약사항

- **Zero-Trust 원칙**: 모든 데이터는 로컬에서 수집, 중앙 서버 전송은 opt-in
- **익명화**: 개인 정보는 해시화, PII는 수집하지 않음
- **성능**: 텔레메트리가 핵심 기능에 영향을 주지 않아야 함 (비동기 처리)
- **스토리지**: 로컬 SQLite DB 사용 (확장 시 PostgreSQL 고려)

---

## 2. 전문가 팀 분석

### 2.1 SaaS 운영자 관점

**[운영자: Sarah Kim]**

**핵심 질문**:
- 사용자는 어떤 기능을 가장 많이 사용하는가?
- 유료 전환율은 얼마인가?
- Churn Rate는 어떻게 되는가?
- 어떤 기능에서 오류가 자주 발생하는가?

**필요한 메트릭**:
1. **사용자 세그먼트**: 유료/무료/트라이얼
2. **활성 사용자**: DAU/MAU
3. **기능 사용률**: 도구별 호출 빈도
4. **오류율**: 실패한 작업 비율
5. **성능 지표**: 평균 응답 시간, P95/P99
6. **전환 깔때기**: 무료 → 유료 전환 경로

**권장사항**:
- 실시간 알림: 오류율 급증 시 Slack 알림
- 주간 리포트: 자동 생성 PDF 리포트
- A/B 테스트: Feature Flag와 연동하여 실험 추적

### 2.2 소프트웨어 개발자 관점

**[개발자: Alex Park]**

**핵심 질문**:
- 텔레메트리가 성능에 영향을 주지 않는가?
- 데이터 수집이 실패해도 핵심 기능은 정상 작동하는가?
- 로그가 너무 많이 쌓여서 디스크를 가득 채우지 않는가?

**필요한 기능**:
1. **비동기 처리**: 텔레메트리는 별도 스레드에서 실행
2. **Fail-Safe**: 텔레메트리 실패 시에도 핵심 기능 정상 작동
3. **로그 로테이션**: 일정 크기 초과 시 자동 압축/삭제
4. **샘플링**: 고빈도 이벤트는 샘플링 (1% ~ 10%)
5. **Circuit Breaker**: 텔레메트리 서버 다운 시 자동 비활성화

**권장 기술 스택**:
- **수집**: Python `asyncio` 기반 비동기 큐
- **저장**: SQLite (로컬), PostgreSQL (중앙)
- **전송**: HTTP POST (opt-in, 배치 전송)
- **모니터링**: Prometheus 메트릭 export

### 2.3 MCP 개발자 관점

**[MCP 전문가: Chris Lee]**

**핵심 질문**:
- MCP 도구별 사용 빈도는?
- 어떤 도구에서 오류가 자주 발생하는가?
- 사용자는 어떤 패턴으로 도구를 조합하는가?

**수집할 데이터**:
1. **도구 호출 로그**: Tool Name, Parameters, Result, Error
2. **브랜치 생성 이벤트**: 자동/수동 생성 비율
3. **RAG 검색 성능**: 검색 쿼리, 결과 개수, 응답 시간
4. **맥락 압축 이벤트**: 압축 전/후 토큰 수
5. **Reference History**: 추천 정확도, 수락/거부율

**MCP 특화 메트릭**:
- **Smart Context 효율**: 토큰 절감율 (목표: 70%)
- **Reference History 정확도**: 추천 수락율 (목표: 80%+)
- **RAG 회상률**: Needle-in-a-Haystack 테스트 정확도

### 2.4 Extension 개발자 관점

**[Extension 전문가: Emily Wang]**

**핵심 질문**:
- Extension 설치 후 활성 사용자 비율은?
- 어떤 IDE에서 가장 많이 사용되는가? (VS Code, Cursor, etc.)
- Extension UI 인터랙션은 얼마나 자주 발생하는가?

**수집할 데이터**:
1. **설치/활성화 이벤트**: IDE 종류, Extension 버전
2. **UI 인터랙션**: 버튼 클릭, 패널 열기/닫기
3. **맥락 전환 이벤트**: 브랜치 전환, 파일 열기
4. **코드 작성 이벤트**: 자동 완성 사용, 코드 삽입
5. **오류 이벤트**: Extension 충돌, 타임아웃

**Extension 특화 메트릭**:
- **활성 사용자**: Extension이 설치되었지만 사용하지 않는 비율
- **IDE 분포**: VS Code vs Cursor vs JetBrains
- **평균 세션 길이**: 하루 평균 사용 시간

### 2.5 기획자 관점

**[기획자: David Choi]**

**핵심 질문**:
- 어떤 기능을 추가하면 전환율이 올라갈까?
- 사용자는 어떤 흐름으로 제품을 사용하는가?
- 어떤 기능이 사용자 만족도가 높은가?

**필요한 분석**:
1. **Funnel Analysis**: 무료 → 유료 전환 경로
2. **Retention Cohort**: 주차별 사용자 유지율
3. **Feature Usage Matrix**: 기능별 사용 빈도 히트맵
4. **User Journey Map**: 사용자 행동 흐름 시각화

**권장 대시보드**:
- **전환율 대시보드**: 무료 → 유료 전환 깔때기
- **리텐션 대시보드**: 주차별 Cohort 분석
- **기능 인기도**: 도구별 사용 빈도 순위

### 2.6 로그 개발자 관점

**[로그 전문가: Grace Yoon]**

**핵심 질문**:
- 로그 포맷이 일관성 있는가?
- 로그 레벨 (DEBUG/INFO/ERROR)이 적절한가?
- 로그 검색/필터링이 쉬운가?

**권장 로그 구조**:
```json
{
  "timestamp": "2025-12-14T08:30:00Z",
  "level": "INFO",
  "service": "mcp",
  "event_type": "tool_call",
  "user_tier": "paid",
  "user_id_hash": "abc123...",
  "tool_name": "search_context",
  "parameters": {"query": "...", "top_k": 5},
  "result": "success",
  "duration_ms": 125,
  "error": null,
  "metadata": {
    "project_id": "proj_xyz",
    "branch_id": "branch_123"
  }
}
```

**로그 레벨 정책**:
- **DEBUG**: 개발 환경에서만 활성화
- **INFO**: 정상 작동 이벤트 (도구 호출 성공)
- **WARNING**: 경미한 오류 (재시도 성공)
- **ERROR**: 중대한 오류 (작업 실패)
- **CRITICAL**: 서비스 다운 수준

### 2.7 Admin 개발자 관점

**[Admin 전문가: Frank Kim]**

**핵심 질문**:
- 대시보드 로딩 속도가 빠른가?
- 데이터 필터링/정렬이 쉬운가?
- CSV Export가 가능한가?

**필요한 Admin 기능**:
1. **실시간 대시보드**: WebSocket 기반 자동 업데이트
2. **필터링**: 날짜, 사용자 티어, 서비스 종류
3. **검색**: 사용자 ID, 이벤트 타입
4. **Export**: CSV/JSON 다운로드
5. **알림 설정**: 오류율 임계값 설정

**Admin 페이지 구성**:
- `/admin/telemetry/overview`: 전체 개요
- `/admin/telemetry/mcp`: MCP 서비스 상세
- `/admin/telemetry/extension`: Extension 서비스 상세
- `/admin/telemetry/users`: 사용자별 분석
- `/admin/telemetry/errors`: 오류 로그

---

## 3. 아키텍처 설계

### 3.1 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Cortex Telemetry System                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ MCP Service  │    │  Extension   │    │ Web Service  │
│              │    │  Service     │    │  (Future)    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
            ┌──────────────────────────┐
            │  Telemetry Collector     │
            │  (Async Queue)           │
            └────────┬─────────────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Local DB │  │ Central  │  │ Log File │
│ (SQLite) │  │ Server   │  │ (JSONL)  │
│          │  │ (opt-in) │  │          │
└────┬─────┘  └──────────┘  └────┬─────┘
     │                           │
     └───────────┬───────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Admin Dashboard│
        │ (localhost:8080│
        │  or Web)       │
        └────────────────┘
```

### 3.2 데이터 수집 플로우

```
[Service Event]
    → TelemetryClient.track_event()
    → AsyncQueue.put()
    → BackgroundWorker.process()
    → [Local DB] + [Log File]
    → (opt-in) [Central Server]
```

### 3.3 기술 스택

| 계층 | 기술 |
|------|------|
| **수집 클라이언트** | Python `asyncio`, `queue.Queue` |
| **로컬 저장** | SQLite (로컬), PostgreSQL (중앙) |
| **로그 파일** | JSONL 포맷, 일별 로테이션 |
| **전송** | HTTP POST (배치 전송, 최대 100개/배치) |
| **Admin 서버** | FastAPI, WebSocket (실시간 업데이트) |
| **Admin UI** | Jinja2 템플릿, Chart.js (시각화) |

---

## 4. 데이터 모델

### 4.1 데이터베이스 스키마

#### 4.1.1 `telemetry_events` 테이블

```sql
CREATE TABLE telemetry_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    service TEXT NOT NULL,  -- 'mcp', 'extension', 'web'
    event_type TEXT NOT NULL,  -- 'tool_call', 'branch_create', 'search', etc.
    user_tier TEXT NOT NULL,  -- 'free', 'paid', 'enterprise'
    user_id_hash TEXT NOT NULL,  -- SHA256 hash of user ID
    session_id TEXT NOT NULL,

    -- Event details (JSON)
    event_data TEXT NOT NULL,  -- JSON string

    -- Result
    result TEXT NOT NULL,  -- 'success', 'error', 'timeout'
    duration_ms INTEGER,
    error_message TEXT,

    -- Metadata
    project_id TEXT,
    branch_id TEXT,
    tool_name TEXT,  -- for MCP tools

    -- Indexing
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_service (service),
    INDEX idx_user_tier (user_tier),
    INDEX idx_event_type (event_type),
    INDEX idx_user_id_hash (user_id_hash)
);
```

#### 4.1.2 `telemetry_metrics` 테이블

```sql
CREATE TABLE telemetry_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    service TEXT NOT NULL,
    metric_name TEXT NOT NULL,  -- 'dau', 'error_rate', 'avg_response_time'
    metric_value REAL NOT NULL,
    user_tier TEXT,  -- NULL for aggregated metrics

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_metric_name (metric_name)
);
```

#### 4.1.3 `telemetry_user_sessions` 테이블

```sql
CREATE TABLE telemetry_user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id_hash TEXT NOT NULL,
    user_tier TEXT NOT NULL,
    service TEXT NOT NULL,

    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_sec INTEGER,

    event_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- Device info
    os TEXT,
    ide TEXT,  -- for extension
    extension_version TEXT,  -- for extension
    mcp_version TEXT,  -- for mcp

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id_hash (user_id_hash),
    INDEX idx_start_time (start_time)
);
```

### 4.2 이벤트 타입 정의

#### 4.2.1 MCP 서비스 이벤트

| Event Type | 설명 | Parameters |
|------------|------|------------|
| `mcp.tool_call` | MCP 도구 호출 | `tool_name`, `parameters`, `result` |
| `mcp.branch_create` | 브랜치 생성 | `branch_topic`, `auto_or_manual` |
| `mcp.search_context` | RAG 검색 | `query`, `top_k`, `results_count` |
| `mcp.update_memory` | 메모리 업데이트 | `file_size_bytes`, `token_count` |
| `mcp.compress_context` | 맥락 압축 | `before_tokens`, `after_tokens` |
| `mcp.reference_suggest` | Reference History 추천 | `suggestion_count`, `accepted` |
| `mcp.ontology_classify` | 온톨로지 분류 | `category`, `confidence` |

#### 4.2.2 Extension 서비스 이벤트

| Event Type | 설명 | Parameters |
|------------|------|------------|
| `ext.install` | Extension 설치 | `ide`, `version` |
| `ext.activate` | Extension 활성화 | `ide`, `project_path` |
| `ext.ui_interaction` | UI 인터랙션 | `action`, `element` |
| `ext.code_insert` | 코드 삽입 | `language`, `lines_inserted` |
| `ext.context_switch` | 맥락 전환 | `from_branch`, `to_branch` |
| `ext.error` | Extension 오류 | `error_type`, `stack_trace` |

### 4.3 메트릭 정의

| Metric Name | 계산 방식 | 업데이트 주기 |
|-------------|----------|--------------|
| `dau` | 일일 활성 사용자 수 (유니크) | 1일 |
| `mau` | 월간 활성 사용자 수 (유니크) | 1일 |
| `error_rate` | 오류 이벤트 / 전체 이벤트 | 1시간 |
| `avg_response_time` | 평균 응답 시간 (ms) | 1시간 |
| `p95_response_time` | P95 응답 시간 (ms) | 1시간 |
| `token_savings_rate` | Smart Context 토큰 절감율 | 1일 |
| `reference_accuracy` | Reference History 추천 수락율 | 1일 |
| `conversion_rate` | 무료 → 유료 전환율 | 1주 |

---

## 5. MCP 서비스 텔레메트리

### 5.1 수집 포인트

MCP 서비스에서 텔레메트리를 수집하는 위치:

1. **`tools/cortex_tools.py`**: 모든 MCP 도구 호출
2. **`core/memory_manager.py`**: 메모리 업데이트, 요약 생성
3. **`core/context_manager.py`**: Smart Context 압축/해제
4. **`core/reference_history.py`**: Reference History 추천
5. **`core/rag_engine.py`**: RAG 검색
6. **`core/ontology_engine.py`**: 온톨로지 분류

### 5.2 구현 예시

#### 5.2.1 `core/telemetry_mcp.py` (신규 파일)

```python
"""
MCP 서비스 텔레메트리 클라이언트
"""

import asyncio
import time
from typing import Dict, Any, Optional
from core.telemetry_base import TelemetryClient, TelemetryEvent


class MCPTelemetryClient(TelemetryClient):
    """MCP 서비스용 텔레메트리 클라이언트"""

    def __init__(self):
        super().__init__(service="mcp")

    def track_tool_call(
        self,
        tool_name: str,
        user_tier: str,
        user_id_hash: str,
        parameters: Dict[str, Any],
        result: str,
        duration_ms: int,
        error_message: Optional[str] = None,
        project_id: Optional[str] = None,
        branch_id: Optional[str] = None
    ):
        """MCP 도구 호출 추적"""
        event = TelemetryEvent(
            service="mcp",
            event_type="tool_call",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "tool_name": tool_name,
                "parameters": parameters
            },
            result=result,
            duration_ms=duration_ms,
            error_message=error_message,
            project_id=project_id,
            branch_id=branch_id,
            tool_name=tool_name
        )
        self.track_event(event)

    def track_branch_create(
        self,
        user_tier: str,
        user_id_hash: str,
        branch_topic: str,
        auto_or_manual: str,
        project_id: str
    ):
        """브랜치 생성 추적"""
        event = TelemetryEvent(
            service="mcp",
            event_type="branch_create",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "branch_topic": branch_topic,
                "auto_or_manual": auto_or_manual
            },
            result="success",
            project_id=project_id
        )
        self.track_event(event)

    def track_search_context(
        self,
        user_tier: str,
        user_id_hash: str,
        query: str,
        top_k: int,
        results_count: int,
        duration_ms: int,
        project_id: Optional[str] = None
    ):
        """RAG 검색 추적"""
        event = TelemetryEvent(
            service="mcp",
            event_type="search_context",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "query": query,
                "top_k": top_k,
                "results_count": results_count
            },
            result="success",
            duration_ms=duration_ms,
            project_id=project_id
        )
        self.track_event(event)

    def track_compress_context(
        self,
        user_tier: str,
        user_id_hash: str,
        before_tokens: int,
        after_tokens: int,
        savings_rate: float,
        project_id: str,
        branch_id: str
    ):
        """맥락 압축 추적"""
        event = TelemetryEvent(
            service="mcp",
            event_type="compress_context",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "before_tokens": before_tokens,
                "after_tokens": after_tokens,
                "savings_rate": savings_rate
            },
            result="success",
            project_id=project_id,
            branch_id=branch_id
        )
        self.track_event(event)

    def track_reference_suggest(
        self,
        user_tier: str,
        user_id_hash: str,
        suggestion_count: int,
        accepted: bool,
        project_id: str
    ):
        """Reference History 추천 추적"""
        event = TelemetryEvent(
            service="mcp",
            event_type="reference_suggest",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "suggestion_count": suggestion_count,
                "accepted": accepted
            },
            result="success",
            project_id=project_id
        )
        self.track_event(event)


# Singleton 인스턴스
_mcp_telemetry_client = None


def get_mcp_telemetry_client() -> MCPTelemetryClient:
    """MCP 텔레메트리 클라이언트 싱글톤 반환"""
    global _mcp_telemetry_client
    if _mcp_telemetry_client is None:
        _mcp_telemetry_client = MCPTelemetryClient()
    return _mcp_telemetry_client
```

#### 5.2.2 `tools/cortex_tools.py` 수정 예시

```python
# 기존 코드에 텔레메트리 추가

from core.telemetry_mcp import get_mcp_telemetry_client
import time
import hashlib

def _handle_search_context(query: str, project_id: str, top_k: int = 5):
    """search_context 도구 핸들러 (예시)"""

    # 사용자 정보 가져오기
    user_tier = get_user_tier()  # 'free', 'paid', 'enterprise'
    user_id = get_user_id()
    user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

    # 시작 시간 기록
    start_time = time.time()

    try:
        # 실제 검색 수행
        results = rag_engine.search(query, top_k=top_k)

        # 성공 시 텔레메트리 전송
        duration_ms = int((time.time() - start_time) * 1000)
        telemetry = get_mcp_telemetry_client()
        telemetry.track_search_context(
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            query=query,
            top_k=top_k,
            results_count=len(results),
            duration_ms=duration_ms,
            project_id=project_id
        )

        return {"success": True, "results": results}

    except Exception as e:
        # 오류 시에도 텔레메트리 전송
        duration_ms = int((time.time() - start_time) * 1000)
        telemetry = get_mcp_telemetry_client()
        telemetry.track_tool_call(
            tool_name="search_context",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            parameters={"query": query, "top_k": top_k},
            result="error",
            duration_ms=duration_ms,
            error_message=str(e),
            project_id=project_id
        )
        raise
```

### 5.3 유료/무료 사용자 구분

사용자 티어는 `license_manager.py`에서 가져옵니다:

```python
from core.license_manager import get_license_manager

def get_user_tier() -> str:
    """사용자 티어 반환"""
    license_mgr = get_license_manager()
    license_info = license_mgr.get_license_info()

    if license_info["is_valid"]:
        tier = license_info["tier"]  # 1, 2, 3
        if tier == 1:
            return "free"
        elif tier == 2:
            return "paid"
        elif tier == 3:
            return "enterprise"

    return "free"  # 기본값
```

---

## 6. Extension 서비스 텔레메트리

### 6.1 수집 포인트

Extension 서비스에서 텔레메트리를 수집하는 위치:

1. **Extension 설치/활성화 이벤트**
2. **UI 인터랙션** (버튼 클릭, 패널 열기)
3. **코드 삽입 이벤트**
4. **맥락 전환 이벤트**
5. **Extension 오류 이벤트**

### 6.2 구현 예시

#### 6.2.1 `core/telemetry_extension.py` (신규 파일)

```python
"""
Extension 서비스 텔레메트리 클라이언트
"""

from typing import Optional
from core.telemetry_base import TelemetryClient, TelemetryEvent


class ExtensionTelemetryClient(TelemetryClient):
    """Extension 서비스용 텔레메트리 클라이언트"""

    def __init__(self):
        super().__init__(service="extension")

    def track_install(
        self,
        user_tier: str,
        user_id_hash: str,
        ide: str,
        version: str
    ):
        """Extension 설치 추적"""
        event = TelemetryEvent(
            service="extension",
            event_type="install",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "ide": ide,
                "version": version
            },
            result="success"
        )
        self.track_event(event)

    def track_activate(
        self,
        user_tier: str,
        user_id_hash: str,
        ide: str,
        project_path: str
    ):
        """Extension 활성화 추적"""
        event = TelemetryEvent(
            service="extension",
            event_type="activate",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "ide": ide,
                "project_path": project_path
            },
            result="success"
        )
        self.track_event(event)

    def track_ui_interaction(
        self,
        user_tier: str,
        user_id_hash: str,
        action: str,
        element: str,
        project_id: Optional[str] = None
    ):
        """UI 인터랙션 추적"""
        event = TelemetryEvent(
            service="extension",
            event_type="ui_interaction",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "action": action,
                "element": element
            },
            result="success",
            project_id=project_id
        )
        self.track_event(event)

    def track_code_insert(
        self,
        user_tier: str,
        user_id_hash: str,
        language: str,
        lines_inserted: int,
        project_id: Optional[str] = None
    ):
        """코드 삽입 추적"""
        event = TelemetryEvent(
            service="extension",
            event_type="code_insert",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "language": language,
                "lines_inserted": lines_inserted
            },
            result="success",
            project_id=project_id
        )
        self.track_event(event)

    def track_error(
        self,
        user_tier: str,
        user_id_hash: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ):
        """Extension 오류 추적"""
        event = TelemetryEvent(
            service="extension",
            event_type="error",
            user_tier=user_tier,
            user_id_hash=user_id_hash,
            event_data={
                "error_type": error_type,
                "stack_trace": stack_trace
            },
            result="error",
            error_message=error_message
        )
        self.track_event(event)


# Singleton 인스턴스
_ext_telemetry_client = None


def get_extension_telemetry_client() -> ExtensionTelemetryClient:
    """Extension 텔레메트리 클라이언트 싱글톤 반환"""
    global _ext_telemetry_client
    if _ext_telemetry_client is None:
        _ext_telemetry_client = ExtensionTelemetryClient()
    return _ext_telemetry_client
```

### 6.3 Extension에서 호출 예시 (VS Code Extension)

```typescript
// VS Code Extension (TypeScript)

import * as vscode from 'vscode';
import { trackUIInteraction, trackCodeInsert } from './telemetry';

export function activate(context: vscode.ExtensionContext) {
    // Extension 활성화 시 텔레메트리 전송
    trackActivate();

    // 버튼 클릭 이벤트
    const disposable = vscode.commands.registerCommand('cortex.openPanel', () => {
        trackUIInteraction('click', 'open_panel_button');
        // 패널 열기 로직
    });

    context.subscriptions.push(disposable);
}

// telemetry.ts
export function trackUIInteraction(action: string, element: string) {
    // HTTP POST로 텔레메트리 서버에 전송
    fetch('http://localhost:8080/api/telemetry/extension/ui-interaction', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            action,
            element,
            user_tier: getUserTier(),
            user_id_hash: getUserIdHash()
        })
    }).catch(err => {
        // 텔레메트리 실패는 무시 (Fail-Safe)
        console.debug('Telemetry failed:', err);
    });
}
```

---

## 7. Admin 대시보드

### 7.1 대시보드 페이지 구성

| 페이지 | URL | 설명 |
|--------|-----|------|
| **개요** | `/admin/telemetry/overview` | 전체 서비스 개요 |
| **MCP** | `/admin/telemetry/mcp` | MCP 서비스 상세 |
| **Extension** | `/admin/telemetry/extension` | Extension 서비스 상세 |
| **사용자** | `/admin/telemetry/users` | 사용자별 분석 |
| **오류** | `/admin/telemetry/errors` | 오류 로그 |

### 7.2 개요 페이지 (/admin/telemetry/overview)

**표시 내용**:
1. **전체 지표 카드**:
   - DAU (일일 활성 사용자)
   - MAU (월간 활성 사용자)
   - 오류율 (%)
   - 평균 응답 시간 (ms)

2. **사용자 티어 분포** (파이 차트):
   - Free: 70%
   - Paid: 25%
   - Enterprise: 5%

3. **서비스별 이벤트 수** (막대 차트):
   - MCP: 10,000 events
   - Extension: 5,000 events
   - Web: 0 events (미구현)

4. **최근 24시간 이벤트 추이** (라인 차트):
   - 시간별 이벤트 수 추이

### 7.3 MCP 서비스 페이지 (/admin/telemetry/mcp)

**표시 내용**:
1. **MCP 도구별 사용 빈도** (막대 차트):
   - search_context: 3,000 calls
   - create_branch: 1,500 calls
   - update_memory: 2,000 calls
   - ...

2. **도구별 오류율** (테이블):
   | Tool Name | Total Calls | Errors | Error Rate |
   |-----------|-------------|--------|------------|
   | search_context | 3,000 | 15 | 0.5% |
   | create_branch | 1,500 | 5 | 0.3% |

3. **Smart Context 토큰 절감율** (라인 차트):
   - 일별 절감율 추이 (목표: 70%)

4. **Reference History 추천 정확도** (라인 차트):
   - 일별 추천 수락율 (목표: 80%)

### 7.4 Extension 서비스 페이지 (/admin/telemetry/extension)

**표시 내용**:
1. **IDE 분포** (파이 차트):
   - VS Code: 60%
   - Cursor: 30%
   - JetBrains: 10%

2. **UI 인터랙션 Top 10** (테이블):
   | Element | Action | Count |
   |---------|--------|-------|
   | open_panel_button | click | 1,200 |
   | context_switch | click | 800 |

3. **Extension 오류 로그** (테이블):
   | Timestamp | Error Type | Message |
   |-----------|------------|---------|
   | 2025-12-14 08:30 | timeout | API timeout |

### 7.5 사용자별 분석 페이지 (/admin/telemetry/users)

**표시 내용**:
1. **사용자 검색**:
   - User ID Hash 검색
   - 날짜 범위 필터

2. **사용자 세부 정보**:
   - 총 이벤트 수
   - 오류 수
   - 평균 세션 길이
   - 사용한 도구 목록

3. **사용자 행동 타임라인** (시간순 이벤트 로그)

### 7.6 오류 로그 페이지 (/admin/telemetry/errors)

**표시 내용**:
1. **오류 필터**:
   - 서비스 (MCP/Extension)
   - 오류 타입
   - 날짜 범위

2. **오류 로그 테이블**:
   | Timestamp | Service | Event Type | User Tier | Error Message |
   |-----------|---------|------------|-----------|---------------|
   | 2025-12-14 08:30 | mcp | search_context | paid | Query timeout |

3. **오류 통계**:
   - 시간별 오류 발생 빈도
   - 오류 타입별 분포

### 7.7 Admin API 엔드포인트

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/api/telemetry/overview` | GET | 개요 데이터 |
| `/api/telemetry/mcp/summary` | GET | MCP 요약 데이터 |
| `/api/telemetry/mcp/tools` | GET | 도구별 사용 통계 |
| `/api/telemetry/extension/summary` | GET | Extension 요약 |
| `/api/telemetry/users/{user_id_hash}` | GET | 사용자 상세 |
| `/api/telemetry/errors` | GET | 오류 로그 (페이징) |
| `/api/telemetry/export/csv` | GET | CSV Export |

---

## 8. 구현 로드맵

### 8.1 Phase 1: 기반 인프라 (1주)

**작업 항목**:
1. `core/telemetry_base.py` 작성 (TelemetryClient, TelemetryEvent)
2. `core/telemetry_storage.py` 작성 (SQLite 저장)
3. 데이터베이스 스키마 생성 (SQLite)
4. 비동기 큐 및 백그라운드 워커 구현
5. 로그 파일 로테이션 (JSONL)

**검증 기준**:
- 초당 1,000개 이벤트 수집 가능
- 메모리 사용량 < 50MB
- CPU 사용률 < 5%

### 8.2 Phase 2: MCP 텔레메트리 (1주)

**작업 항목**:
1. `core/telemetry_mcp.py` 작성
2. `tools/cortex_tools.py` 수정 (모든 도구에 텔레메트리 추가)
3. `core/memory_manager.py` 수정
4. `core/context_manager.py` 수정
5. `core/reference_history.py` 수정
6. 유료/무료 사용자 구분 로직 추가

**검증 기준**:
- 모든 MCP 도구 호출 추적 (100%)
- 오류 이벤트 누락 없음
- 성능 저하 없음 (기존 대비 <3% 오버헤드)

### 8.3 Phase 3: Extension 텔레메트리 (1주)

**작업 항목**:
1. `core/telemetry_extension.py` 작성
2. Extension에서 텔레메트리 API 호출 (TypeScript)
3. HTTP 엔드포인트 추가 (`/api/telemetry/extension/*`)
4. Extension 오류 로깅

**검증 기준**:
- Extension 설치/활성화 이벤트 추적
- UI 인터랙션 추적
- Extension 충돌 시에도 텔레메트리 전송

### 8.4 Phase 4: Admin 대시보드 (1주)

**작업 항목**:
1. Admin 페이지 템플릿 작성 (Jinja2)
2. Admin API 엔드포인트 작성 (FastAPI)
3. Chart.js 시각화 추가
4. 실시간 업데이트 (WebSocket)
5. CSV Export 기능

**검증 기준**:
- 대시보드 로딩 시간 < 2초
- 실시간 업데이트 지연 < 1초
- CSV Export 파일 크기 < 10MB

### 8.5 Phase 5: 중앙 서버 (opt-in) (2주)

**작업 항목**:
1. 중앙 텔레메트리 서버 구축 (PostgreSQL)
2. 배치 전송 로직 (최대 100개/배치)
3. 서버 API 인증 (라이센스키)
4. Retry 로직 (실패 시 재전송)
5. Circuit Breaker (서버 다운 시 자동 비활성화)

**검증 기준**:
- 네트워크 실패 시에도 로컬 저장
- 서버 다운 시 텔레메트리 비활성화
- 재연결 후 자동 재개

### 8.6 Phase 6: 고급 분석 (2주)

**작업 항목**:
1. Funnel Analysis (무료 → 유료 전환)
2. Retention Cohort (주차별 유지율)
3. Feature Usage Matrix (기능별 사용 빈도 히트맵)
4. User Journey Map (사용자 행동 흐름)
5. 알림 시스템 (Slack 연동)

**검증 기준**:
- 전환율 계산 정확도 100%
- Cohort 분석 쿼리 속도 < 5초
- Slack 알림 지연 < 10초

---

## 9. QA 및 검증

### 9.1 단위 테스트

**테스트 파일**: `tests/test_telemetry_*.py`

```python
# tests/test_telemetry_mcp.py

def test_track_tool_call():
    """도구 호출 추적 테스트"""
    client = MCPTelemetryClient()
    client.track_tool_call(
        tool_name="search_context",
        user_tier="paid",
        user_id_hash="abc123",
        parameters={"query": "test", "top_k": 5},
        result="success",
        duration_ms=100,
        project_id="proj_xyz"
    )

    # DB에 저장되었는지 확인
    db = TelemetryStorage()
    events = db.get_events(event_type="tool_call", limit=1)
    assert len(events) == 1
    assert events[0]["tool_name"] == "search_context"
```

### 9.2 통합 테스트

**테스트 시나리오**:
1. MCP 도구 호출 → 텔레메트리 저장 → Admin API 조회
2. Extension UI 클릭 → 텔레메트리 전송 → Admin 대시보드 업데이트
3. 대량 이벤트 발생 (10,000개) → 성능 저하 없음 확인

### 9.3 부하 테스트

**시나리오**:
- 초당 1,000개 이벤트 전송
- 10분간 지속
- CPU/메모리 사용률 모니터링

**PASS 기준**:
- CPU < 10%
- 메모리 < 100MB
- 이벤트 누락 없음

### 9.4 보안 테스트

**검증 항목**:
1. User ID가 해시화되었는지 확인
2. PII 데이터가 포함되지 않았는지 확인
3. 외부 네트워크로 데이터 유출 없음 (opt-out 시)

---

## 10. 마이그레이션 계획

### 10.1 기존 시스템과의 통합

현재 Cortex에는 다음 로깅 시스템이 존재:
- `core/telemetry.py` (기존 텔레메트리)
- `core/alpha_logger.py` (알파 테스트 로거)

**통합 방안**:
1. `core/telemetry.py` → `core/telemetry_base.py`로 리팩토링
2. `core/alpha_logger.py`는 유지, 텔레메트리와 병행 사용
3. 기존 로그 데이터는 마이그레이션 스크립트로 이관

### 10.2 데이터 마이그레이션

**마이그레이션 스크립트**: `scripts/migrate_telemetry.py`

```python
# scripts/migrate_telemetry.py

def migrate_old_logs_to_new_schema():
    """기존 로그를 새 스키마로 마이그레이션"""
    old_logs = load_old_logs("~/.cortex/logs/")

    for log in old_logs:
        # 새 스키마로 변환
        event = convert_to_new_schema(log)

        # 새 DB에 저장
        db = TelemetryStorage()
        db.save_event(event)

    print(f"Migrated {len(old_logs)} events")
```

---

## 11. 운영 가이드

### 11.1 로그 로테이션

**설정**: `config.py`

```python
TELEMETRY_LOG_MAX_SIZE = 100 * 1024 * 1024  # 100MB
TELEMETRY_LOG_RETENTION_DAYS = 30  # 30일
```

**자동 로테이션**: 매일 자정 크론 작업

```bash
# 로그 압축 및 삭제
find ~/.cortex/logs/telemetry -name "*.jsonl" -mtime +30 -exec gzip {} \;
find ~/.cortex/logs/telemetry -name "*.jsonl.gz" -mtime +90 -delete
```

### 11.2 알림 설정

**Slack 알림 조건**:
- 오류율 > 5%
- 평균 응답 시간 > 1초
- 서버 다운

**알림 예시**:
```
[ALERT] MCP Service Error Rate: 7.5%
Time: 2025-12-14 08:30:00
Details: /admin/telemetry/errors
```

### 11.3 백업 정책

**백업 주기**: 매일 자정

**백업 대상**:
- SQLite DB (`cortex.db`)
- 로그 파일 (`*.jsonl`)

**백업 저장소**: S3 (암호화)

---

## 12. FAQ

### Q1: 텔레메트리가 성능에 영향을 주나요?

A: 아니요. 텔레메트리는 비동기로 처리되며, 핵심 기능과 별도의 스레드에서 실행됩니다. 성능 저하는 3% 미만입니다.

### Q2: 개인 정보는 어떻게 보호되나요?

A: 모든 User ID는 SHA256으로 해시화되며, PII 데이터는 수집하지 않습니다. 로컬에서만 저장되며, 중앙 서버 전송은 opt-in입니다.

### Q3: 무료 사용자와 유료 사용자 데이터는 어떻게 구분하나요?

A: `user_tier` 필드를 통해 'free', 'paid', 'enterprise'로 구분됩니다. 라이센스 매니저에서 자동으로 판별합니다.

### Q4: 텔레메트리를 비활성화할 수 있나요?

A: 네. `config.py`에서 `TELEMETRY_ENABLED = False`로 설정하면 완전히 비활성화됩니다.

### Q5: 로그 파일이 너무 커지면 어떻게 되나요?

A: 자동 로테이션이 활성화되어 있습니다. 100MB 초과 시 자동 압축되며, 30일 이상 된 로그는 삭제됩니다.

---

## 13. 참고 문서

- [Cortex Master Plan](./CORTEX_MASTER_PLAN.md)
- [Feature Flags 스펙](./CORTEX_MASTER_PLAN.md#section-24-feature-flags)
- [Alpha Logger 스펙](./CORTEX_MASTER_PLAN.md#section-20-alpha-test-logging)
- [License Manager API](./core/license_manager.py)

---

**문서 종료**
