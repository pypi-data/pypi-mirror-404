"""
Extension Sync Service - MCP Core to Web API Bridge
MCP 도구 호출 시 Extension API로 데이터를 자동 전송

Purpose:
- Active Context 변경 시 Web API에 상태 업데이트
- Context 참조 시 referenced_context_ids 기록
- Context 전환 시 Transition Log 기록
- Boundary Violation 발생 시 Safety 상태 업데이트
"""

import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger("cortex_mcp.extension_sync")


@dataclass
class ExtensionSyncConfig:
    """Extension Sync 설정"""

    api_base_url: str = field(default_factory=lambda: os.environ.get("CORTEX_API_URL", "https://cortex-mcp.com"))  # Website API URL
    enabled: bool = True
    timeout_seconds: int = 5
    retry_count: int = 2


class ExtensionSyncService:
    """
    MCP Core에서 발생하는 이벤트를 Web API로 전송하는 서비스

    기능:
    1. Active Context 상태 동기화
    2. Referenced Contexts 기록
    3. Context Transition 로깅
    4. Boundary Violation 보고
    """

    def __init__(self, config: Optional[ExtensionSyncConfig] = None):
        self.config = config or ExtensionSyncConfig()
        self._session: Optional[aiohttp.ClientSession] = None

        # 환경변수로 설정 오버라이드
        env_url = os.environ.get("CORTEX_WEB_API_URL")
        if env_url:
            self.config.api_base_url = env_url

        env_enabled = os.environ.get("CORTEX_EXTENSION_SYNC_ENABLED")
        if env_enabled:
            self.config.enabled = env_enabled.lower() in ("true", "1", "yes")

    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP 세션 가져오기 (lazy initialization)"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """HTTP 세션 종료"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _hash_license_key(self, license_key: Optional[str]) -> Optional[str]:
        """라이센스 키 해시화 (프라이버시 보호)"""
        if not license_key:
            return None
        return hashlib.sha256(license_key.encode()).hexdigest()

    async def _post_with_retry(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """재시도 로직이 포함된 POST 요청"""
        if not self.config.enabled:
            return {"success": True, "skipped": True, "reason": "sync disabled"}

        url = f"{self.config.api_base_url}{endpoint}"

        for attempt in range(self.config.retry_count + 1):
            try:
                session = await self._get_session()
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.warning(
                            f"Extension API error (attempt {attempt+1}): "
                            f"{response.status} - {error_text[:200]}"
                        )
            except asyncio.TimeoutError:
                logger.warning(f"Extension API timeout (attempt {attempt+1})")
            except aiohttp.ClientError as e:
                logger.warning(f"Extension API connection error (attempt {attempt+1}): {e}")
            except Exception as e:
                logger.error(f"Extension API unexpected error: {e}")
                break

            # 재시도 전 대기
            if attempt < self.config.retry_count:
                await asyncio.sleep(0.5 * (attempt + 1))

        return {"success": False, "error": "Failed after retries"}

    # ============ Active Context ============

    async def sync_active_context(
        self,
        project_id: str,
        branch_id: str,
        context_id: str,
        context_name: str,
        summary: Optional[str] = None,
        branch_topic: Optional[str] = None,
        license_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Active Context 상태를 Web API에 동기화

        호출 시점:
        - load_context 호출 시
        - create_branch 호출 시 (새 브랜치 활성화)
        - get_active_summary 호출 시 (현재 활성 컨텍스트 확인)
        """
        data = {
            "project_id": project_id,
            "branch_id": branch_id,
            "context_id": context_id,
            "context_name": context_name,
            "summary": summary,
            "branch_topic": branch_topic,
            "license_key": license_key,
        }

        result = await self._post_with_retry("/api/extension/active-context", data)

        if result.get("success"):
            logger.debug(f"Active context synced: {context_id}")
        else:
            logger.warning(f"Failed to sync active context: {result.get('error')}")

        return result

    # ============ Referenced Contexts ============

    async def record_referenced_contexts(
        self,
        project_id: str,
        branch_id: str,
        referenced_context_ids: List[str],
        query: Optional[str] = None,
        task_keywords: Optional[List[str]] = None,
        response_id: Optional[str] = None,
        license_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AI 응답에서 참조된 Context들을 기록

        호출 시점:
        - suggest_contexts 호출 후 (추천 결과 기록)
        - search_context 호출 후 (검색 결과 기록)
        - record_reference 호출 시 (수동 기록)
        """
        if not referenced_context_ids:
            return {"success": True, "skipped": True, "reason": "no contexts to record"}

        data = {
            "project_id": project_id,
            "branch_id": branch_id,
            "referenced_context_ids": referenced_context_ids,
            "query": query,
            "task_keywords": task_keywords or [],
            "response_id": response_id,
            "license_key": license_key,
        }

        result = await self._post_with_retry("/api/extension/referenced-contexts", data)

        if result.get("success"):
            logger.debug(f"Referenced contexts recorded: {len(referenced_context_ids)} contexts")
        else:
            logger.warning(f"Failed to record referenced contexts: {result.get('error')}")

        return result

    # ============ Context Transition ============

    async def record_context_transition(
        self,
        project_id: str,
        branch_id: str,
        to_context_id: str,
        event_type: str,
        from_context_id: Optional[str] = None,
        license_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Context 전환 이벤트를 기록

        event_type:
        - created: 새 컨텍스트 생성
        - activated: 컨텍스트 활성화 (load_context)
        - deactivated: 컨텍스트 비활성화 (compress_context)
        - referenced: 컨텍스트 참조됨
        - compressed: 압축됨
        - decompressed: 압축 해제됨

        호출 시점:
        - create_branch 호출 시 (event_type=created)
        - load_context 호출 시 (event_type=activated)
        - compress_context 호출 시 (event_type=compressed)
        """
        data = {
            "project_id": project_id,
            "branch_id": branch_id,
            "from_context_id": from_context_id,
            "to_context_id": to_context_id,
            "event_type": event_type,
            "license_key": license_key,
        }

        result = await self._post_with_retry("/api/extension/transition-log", data)

        if result.get("success"):
            logger.debug(f"Context transition recorded: {event_type} -> {to_context_id}")
        else:
            logger.warning(f"Failed to record transition: {result.get('error')}")

        return result

    # ============ Boundary Violation ============

    async def report_boundary_violation(
        self,
        project_id: str,
        branch_id: str,
        active_context_id: str,
        file_path: str,
        violation_type: str = "outside_boundary",
        severity: str = "warning",
        license_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Boundary Violation 발생 시 Web API에 보고

        violation_type:
        - outside_boundary: 경계 외 파일 접근
        - cross_branch: 다른 브랜치 컨텍스트 접근
        - forbidden_file: 금지된 파일 접근
        - action_denied: 허용되지 않은 작업

        severity:
        - warning: 경고 (계속 진행 가능)
        - error: 에러 (차단됨)

        호출 시점:
        - validate_boundary_action에서 위반 감지 시
        """
        data = {
            "project_id": project_id,
            "branch_id": branch_id,
            "active_context_id": active_context_id,
            "file_path": file_path,
            "violation_type": violation_type,
            "severity": severity,
            "license_key": license_key,
        }

        result = await self._post_with_retry("/api/extension/safety-status/violation", data)

        if result.get("success"):
            logger.info(f"Boundary violation reported: {violation_type} on {file_path}")
        else:
            logger.warning(f"Failed to report violation: {result.get('error')}")

        return result


# 싱글톤 인스턴스
_extension_sync_instance: Optional[ExtensionSyncService] = None


def get_extension_sync() -> ExtensionSyncService:
    """Extension Sync 서비스 싱글톤 인스턴스 반환"""
    global _extension_sync_instance
    if _extension_sync_instance is None:
        _extension_sync_instance = ExtensionSyncService()
    return _extension_sync_instance


# 동기 래퍼 함수 (기존 코드와의 호환성을 위해)
def sync_active_context_sync(
    project_id: str, branch_id: str, context_id: str, context_name: str, **kwargs
) -> Dict[str, Any]:
    """동기 버전의 Active Context 동기화"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 이미 실행 중인 이벤트 루프가 있으면 태스크로 추가
            future = asyncio.ensure_future(
                get_extension_sync().sync_active_context(
                    project_id, branch_id, context_id, context_name, **kwargs
                )
            )
            return {"success": True, "async": True}
        else:
            return loop.run_until_complete(
                get_extension_sync().sync_active_context(
                    project_id, branch_id, context_id, context_name, **kwargs
                )
            )
    except Exception as e:
        logger.error(f"Sync wrapper error: {e}")
        return {"success": False, "error": str(e)}


def record_referenced_contexts_sync(
    project_id: str, branch_id: str, referenced_context_ids: List[str], **kwargs
) -> Dict[str, Any]:
    """동기 버전의 Referenced Contexts 기록"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.ensure_future(
                get_extension_sync().record_referenced_contexts(
                    project_id, branch_id, referenced_context_ids, **kwargs
                )
            )
            return {"success": True, "async": True}
        else:
            return loop.run_until_complete(
                get_extension_sync().record_referenced_contexts(
                    project_id, branch_id, referenced_context_ids, **kwargs
                )
            )
    except Exception as e:
        logger.error(f"Sync wrapper error: {e}")
        return {"success": False, "error": str(e)}
