# Cortex Telemetry System v2.0 Migration

**Date**: 2025-12-14
**Status**: In Progress (continuous execution mode)

---

## Overview

additional_job.md 기반 텔레메트리 시스템 재구성:

- **17개 핵심 이벤트** 정의
- **Event/Error/Trace 3-pipeline** 분리
- **Closed/Open Beta Dashboard** 분리
- **KPI 계산 로직** (CDR, Resurrection, DAU/WAU)

---

## Completed Work

### 1. Event Schema Definition ✅
- ✅ `core/telemetry_events.py` 생성
- ✅ `CortexEventName` enum (17개 이벤트)
- ✅ `ChannelType` enum
- ✅ `EventSeverity` enum
- ✅ `EVENT_TO_KPI_MAPPING` dictionary

### 2. Base Classes Update ✅
- ✅ `core/telemetry_base.py` 업데이트
  - ✅ `TelemetryEvent` - 표준 스키마 적용
  - ✅ `TelemetryError` - 에러 전용 클래스
  - ✅ `TelemetryTrace` - 성능 추적 전용
  - ✅ 하위 호환성 유지 (`__post_init__`)

### 3. Storage Layer Update ✅
- ✅ `core/telemetry_storage.py` 업데이트
  - ✅ `telemetry_events` 테이블 (표준 스키마)
  - ✅ `telemetry_errors` 테이블
  - ✅ `telemetry_traces` 테이블
  - ✅ 인덱스 생성 (performance)

---

## Completed (Phase 2)

### 4. Integration Layer Update ✅
- ✅ `core/telemetry_integration.py` - v2.0 스키마 적용 완료
  - track_tool_call(), track_error(), track_performance(), track_feature_usage() 업데이트
  - 하위 호환성 유지 (deprecated 필드 사용)
  - 테스트 통과

- ✅ `core/telemetry_mcp.py` - MCP 서비스 전용 텔레메트리 업데이트
  - 8개 메서드 v2.0 주석 추가
  - telemetry_integration.py를 통한 자동 v2.0 스키마 적용
  - 테스트 통과

## Completed (Phase 3 - KPI Implementation)

### 6. KPI Calculation Layer ✅
- ✅ `website/services/kpi_calculator.py` - KPI 계산 로직 구현 완료
  - `calculate_cdr()` - CDR (Context Dependency Rate) 계산
  - `calculate_resurrection()` - 7일 이상 미사용 후 복귀 유저 비율
  - `calculate_dau_wau()` - 일일/주간 활성 사용자 계산
  - `calculate_paid_conversion()` - 유료 전환율 계산
  - `calculate_all_kpis()` - 모든 KPI 일괄 계산

- ✅ `website/routers/telemetry.py` - KPI API 엔드포인트 추가 완료
  - `GET /admin/kpi/cdr?days=7` - CDR 조회
  - `GET /admin/kpi/resurrection?days=30` - Resurrection 조회
  - `GET /admin/kpi/dau-wau?days=7` - DAU/WAU 조회
  - `GET /admin/kpi/paid-conversion?days=30` - 유료 전환율 조회
  - `GET /admin/kpi/all?days=7` - 모든 KPI 한번에 조회

## Completed (Phase 7 - Dashboard Reconstruction)

### 7. Dashboard Reconstruction ✅
- ✅ Closed Beta Dashboard 페이지 생성 (`website/templates/admin/dashboard_closed_beta.html`)
  - KPI 카드 4개 (CDR, Resurrection, DAU, Paid Conversion)
  - KPI 차트 4개 (Chart.js 사용)
  - JavaScript 데이터 로딩 및 렌더링
- ✅ Open Beta Dashboard 페이지 생성 (`website/templates/admin/dashboard_open_beta.html`)
  - 동일한 KPI 섹션 추가 완료
  - Closed Beta와 동일한 시각화 제공

## Completed (Phase 5 - MCP Tools Integration)

### 5. MCP Tools Integration ✅
- ✅ `tools/cortex_tools.py` - 17개 이벤트 발생 로직 추가 완료
  - 텔레메트리 임포트 추가 (하위 호환성 유지)
  - `call_tool()` 함수에 텔레메트리 클라이언트 초기화
  - 모든 도구 호출 시 SERVER_OPERATION_CALLED 이벤트 발생 (DAU 추적)
  - 7개 핵심 도구별 이벤트 발생:
    - `initialize_context` → CONTEXT_CREATED, SESSION_STARTED
    - `create_branch` → CONTEXT_CREATED or CONTEXT_AUTO_CREATED
    - `search_context` → CONTEXT_LOADED
    - `update_memory` → CONTEXT_MODIFIED
    - `get_active_summary` → SESSION_RESUMED_FROM_CONTEXT, CONTEXT_RESUMED
    - `sync_to_cloud` → (SERVER_OPERATION_CALLED만)
    - `sync_from_cloud` → CONTEXT_LOADED
  - 예외 처리기에 에러 추적 추가

## Completed (Phase 8 - Testing)

### 8. Testing ✅
- ✅ 텔레메트리 이벤트 발생 E2E 테스트 (`tests/test_telemetry_e2e.py`)
  - 모듈 import 검증
  - TelemetryClient 초기화 검증
  - 이벤트 발생 검증 (SERVER_OPERATION_CALLED, CONTEXT_CREATED, SESSION_STARTED)
  - 에러 추적 검증
  - 17개 핵심 이벤트 전체 발생 검증
  - MCP 도구 워크플로우 시뮬레이션 (initialize_context)
- ✅ 모든 테스트 PASSED (Status: READY FOR PRODUCTION)

---

## File Changes

| File | Status | Changes |
|------|--------|---------|
| `core/telemetry_events.py` | ✅ NEW | 17개 핵심 이벤트 정의 |
| `core/telemetry_base.py` | ✅ MODIFIED | Event/Error/Trace 3-class 구조 |
| `core/telemetry_storage.py` | ✅ MODIFIED | 3-pipeline 테이블 구조 |
| `core/telemetry_integration.py` | ✅ COMPLETED | 표준 스키마 사용 (하위 호환성 유지) |
| `core/telemetry_mcp.py` | ✅ COMPLETED | v2.0 스키마 자동 적용 (주석 추가) |
| `tools/cortex_tools.py` | ✅ COMPLETED | 17개 이벤트 발생 통합 완료 |
| `website/services/kpi_calculator.py` | ✅ COMPLETED | KPI 계산 로직 구현 |
| `website/routers/telemetry.py` | ✅ COMPLETED | KPI API 엔드포인트 추가 |
| `website/templates/admin/dashboard_*.html` | ✅ COMPLETED | Closed/Open Beta Dashboard 생성 |
| `tests/test_telemetry_e2e.py` | ✅ COMPLETED | E2E 테스트 (17개 이벤트 검증) |

---

## Migration Strategy

### Backward Compatibility

`TelemetryEvent.__post_init__()`를 통한 자동 변환:

```python
# Old code (still works)
event = TelemetryEvent(
    service="mcp",
    event_type="tool_call",
    user_tier="free",
    user_id_hash="abc123"
)

# Automatically converts to new schema:
# - service → channel
# - event_type → event_name
# - user_tier → is_paid_user
```

### Gradual Rollout

1. **Phase 1**: Storage + Base classes (✅ Done)
2. **Phase 2**: Integration layer
3. **Phase 3**: MCP tools
4. **Phase 4**: Dashboard
5. **Phase 5**: Testing

---

## Next Actions

1. ✅ Complete storage layer methods
2. Update integration layer
3. Add event emissions to MCP tools
4. Reconstruct dashboards
5. Run comprehensive tests

---

*This document is being updated in real-time during continuous execution.*
