# Cortex MCP Tools → Telemetry Events Mapping

**Date**: 2025-12-15
**Purpose**: MCP 도구 호출 시 발생시켜야 할 텔레메트리 이벤트 매핑 가이드

---

## Overview

각 MCP 도구는 호출 시 적절한 텔레메트리 이벤트를 발생시켜야 합니다.
이를 통해 CDR, Resurrection, DAU/WAU, Paid Conversion 등의 KPI를 계산할 수 있습니다.

---

## 17개 핵심 이벤트 (CortexEventName)

### Context Lifecycle (7개)
- `CONTEXT_CREATED` - 새로운 맥락 생성
- `CONTEXT_AUTO_CREATED` - AI가 자동으로 맥락 생성
- `CONTEXT_LOADED` - 맥락 로드 (CDR 계산용)
- `CONTEXT_RESUMED` - 기존 맥락 재개 (CDR 계산용)
- `CONTEXT_MODIFIED` - 맥락 수정
- `CONTEXT_MERGED` - 맥락 병합
- `CONTEXT_DELETED` - 맥락 삭제

### Dependency / Protection (3개)
- `CONTEXT_PROTECTION_TRIGGERED` - 보호 장치 트리거
- `CONTEXT_PROTECTION_BLOCKED` - 보호 장치가 작업 차단
- `CONTEXT_OVERRIDE_MANUAL` - 사용자가 보호 무시

### Session Continuity (3개)
- `SESSION_STARTED` - 세션 시작 (DAU 계산용)
- `SESSION_ENDED` - 세션 종료
- `SESSION_RESUMED_FROM_CONTEXT` - 맥락에서 세션 재개 (Resurrection 계산용)

### Channel Usage (3개)
- `EXTENSION_ACTIVATED` - IDE Extension 활성화 (DAU 계산용)
- `SERVER_OPERATION_CALLED` - MCP Server 작업 호출 (DAU 계산용)
- `WEB_VIEW_OPENED` - 웹 뷰 열림 (DAU 계산용)

### Monetization (2개)
- `PAID_SUBSCRIPTION_STARTED` - 유료 구독 시작 (Paid Conversion 계산용)
- `PAID_SUBSCRIPTION_CANCELED` - 유료 구독 취소

---

## MCP 도구별 이벤트 매핑

### 1. `initialize_context`

**목적**: 프로젝트 초기 맥락 스캔 (FULL/LIGHT/NONE)

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `CONTEXT_CREATED` - 초기 프로젝트 루트 브랜치 생성
- ✅ `SESSION_STARTED` - 새 프로젝트 시작 = 새 세션

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `initialize_context` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 브랜치 생성 성공: `CONTEXT_CREATED`
- 초기화 완료: `SESSION_STARTED`

---

### 2. `create_branch`

**목적**: Context Tree(브랜치) 생성 (주제 전환 시)

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `CONTEXT_CREATED` (수동 생성) 또는 `CONTEXT_AUTO_CREATED` (AI 감지)

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `create_branch` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 브랜치 생성 성공: `CONTEXT_CREATED` or `CONTEXT_AUTO_CREATED`

**판단 로직**:
```python
# AI 감지 vs 수동 요청 판단 (메타데이터 기반)
if auto_created:
    event_name = CortexEventName.CONTEXT_AUTO_CREATED
else:
    event_name = CortexEventName.CONTEXT_CREATED
```

---

### 3. `search_context`

**목적**: 로컬 Vector RAG 검색

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `CONTEXT_LOADED` - 검색 결과로 맥락 로드 (CDR 계산용)

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `search_context` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 검색 성공 (결과 > 0): `CONTEXT_LOADED`

---

### 4. `update_memory`

**목적**: 대화 내용 메모리에 기록 및 자동 요약

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `CONTEXT_MODIFIED` - 맥락 수정

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `update_memory` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 메모리 업데이트 성공: `CONTEXT_MODIFIED`

---

### 5. `get_active_summary`

**목적**: 현재 브랜치의 최신 요약 정보 반환

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `SESSION_RESUMED_FROM_CONTEXT` - 맥락에서 세션 재개 (Resurrection 계산용)
- ✅ `CONTEXT_RESUMED` - 기존 맥락 재개 (CDR 계산용)

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `get_active_summary` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 요약 로드 성공: `CONTEXT_RESUMED` + `SESSION_RESUMED_FROM_CONTEXT`

---

### 6. `sync_to_cloud`

**목적**: 로컬 메모리를 Google Drive에 암호화 후 업로드

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `sync_to_cloud` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`

**참고**: 클라우드 동기화는 별도 이벤트 없음 (추후 필요 시 추가 가능)

---

### 7. `sync_from_cloud`

**목적**: Google Drive에서 다운로드 후 복호화하여 맥락 복구

**발생할 이벤트**:
- ✅ `SERVER_OPERATION_CALLED` - 도구 호출 자체 추적 (DAU)
- ✅ `CONTEXT_LOADED` - 클라우드에서 맥락 복구 = 로드 (CDR 계산용)

**구현 위치**: `tools/cortex_tools.py` > `register_tools()` > `sync_from_cloud` 핸들러

**발생 시점**:
- 도구 호출 시작: `SERVER_OPERATION_CALLED`
- 복구 성공: `CONTEXT_LOADED`

---

## 구현 패턴

### 기본 패턴 (모든 도구 공통)

```python
from core.telemetry_integration import CortexTelemetry
from core.telemetry_events import CortexEventName, ChannelType

# 텔레메트리 클라이언트 (전역 또는 함수 내 생성)
telemetry = CortexTelemetry()

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "도구명":
        try:
            # 1. 도구 호출 이벤트 발생 (DAU 추적)
            telemetry.client.emit_event(
                event_name=CortexEventName.SERVER_OPERATION_CALLED,
                channel=ChannelType.SERVER,
                metadata={"tool_name": name, "arguments": arguments}
            )

            # 2. 실제 도구 로직 실행
            result = await _handle_tool(arguments)

            # 3. 성공 시 추가 이벤트 발생
            if result.get("success"):
                telemetry.client.emit_event(
                    event_name=CortexEventName.CONTEXT_CREATED,  # 예시
                    channel=ChannelType.SERVER,
                    metadata={"result": result}
                )

            return result

        except Exception as e:
            # 에러 추적
            telemetry.client.track_error(
                error_type=type(e).__name__,
                error_message=str(e),
                metadata={"tool_name": name}
            )
            raise
```

### 조건부 이벤트 발생 패턴

```python
# 예: create_branch에서 auto_created 판단
if arguments.get("auto_created", False):
    event_name = CortexEventName.CONTEXT_AUTO_CREATED
else:
    event_name = CortexEventName.CONTEXT_CREATED

telemetry.client.emit_event(
    event_name=event_name,
    channel=ChannelType.SERVER,
    metadata={"branch_id": result["branch_id"], "auto": auto_created}
)
```

---

## KPI 계산 연관성

| KPI | 필요 이벤트 | 도구 |
|-----|-------------|------|
| **CDR (Context Dependency Rate)** | `CONTEXT_LOADED`, `CONTEXT_RESUMED` | `search_context`, `get_active_summary`, `sync_from_cloud` |
| **Resurrection** | `SESSION_RESUMED_FROM_CONTEXT` | `get_active_summary` |
| **DAU/WAU** | `SESSION_STARTED`, `SERVER_OPERATION_CALLED` | 모든 도구, `initialize_context` |
| **Paid Conversion** | `PAID_SUBSCRIPTION_STARTED` | (향후 라이센스 시스템과 연동) |

---

## 구현 순서

1. ✅ 텔레메트리 통합 레이어 확인 (`core/telemetry_integration.py`)
2. ✅ 이벤트 스키마 확인 (`core/telemetry_events.py`)
3. 🏃 `tools/cortex_tools.py` 수정
   - 각 도구 핸들러에 텔레메트리 이벤트 발생 코드 추가
   - 에러 핸들링 추가
4. ⏳ E2E 테스트 작성 및 실행
5. ⏳ KPI 대시보드에서 데이터 확인

---

## 참고 파일

- `cortex_mcp/core/telemetry_events.py` - 17개 이벤트 정의
- `cortex_mcp/core/telemetry_base.py` - TelemetryEvent 클래스
- `cortex_mcp/core/telemetry_integration.py` - CortexTelemetry 클래스
- `cortex_mcp/tools/cortex_tools.py` - MCP 도구 구현
- `website/services/kpi_calculator.py` - KPI 계산 로직

---

*이 문서는 텔레메트리 이벤트 발생 통합 작업의 가이드입니다.*
