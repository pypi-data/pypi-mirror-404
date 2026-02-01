"""
Cortex MCP - Accountability Handler

4가지 책임성 기능을 통합 관리하는 핸들러

기능:
- Intent Cache, Promise Tracker, Key Claims Manager 통합
- verify_response와 연동하여 책임성 검증 수행
- AI 판단 결과 처리 및 상태 업데이트
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .intent_cache import IntentCache, get_intent_cache
from .key_claims_manager import KeyClaimsManager, get_key_claims_manager
from .promise_tracker import PromiseTracker, get_promise_tracker

logger = logging.getLogger(__name__)


class AccountabilityHandler:
    """
    책임성 기능 통합 핸들러

    verify_response 호출 시 함께 사용되어
    의도 일치, 약속 이행, 모순 감지를 수행
    """

    def __init__(self, project_id: str, memory_dir: Optional[Path] = None):
        """
        Args:
            project_id: 프로젝트 ID
            memory_dir: 메모리 저장 디렉토리
        """
        self.project_id = project_id
        self.memory_dir = memory_dir

        # 싱글톤 인스턴스 가져오기
        self.intent_cache = get_intent_cache(project_id, memory_dir)
        self.promise_tracker = get_promise_tracker(project_id, memory_dir)
        self.key_claims_manager = get_key_claims_manager(project_id, memory_dir)

    def get_accountability_context(self) -> Dict:
        """
        AI에게 제공할 책임성 컨텍스트 생성

        Returns:
            {
                "pending_intents": "...",
                "pending_promises": "...",
                "previous_claims": "...",
                "has_pending_items": bool
            }
        """
        pending_intents = self.intent_cache.get_context_for_ai()
        pending_promises = self.promise_tracker.get_context_for_ai()
        previous_claims = self.key_claims_manager.get_context_for_ai()

        has_pending = (
            len(self.intent_cache.get_pending_intents()) > 0
            or len(self.promise_tracker.get_pending_promises()) > 0
        )

        return {
            "pending_intents": pending_intents,
            "pending_promises": pending_promises,
            "previous_claims": previous_claims,
            "has_pending_items": has_pending,
        }

    def generate_protocol_prompt(self, current_action: str, current_response: str) -> str:
        """
        AI에게 제공할 프로토콜 프롬프트 생성

        Args:
            current_action: 현재 수행한 작업 요약
            current_response: 현재 응답 전문

        Returns:
            변수가 치환된 프로토콜 프롬프트
        """
        context = self.get_accountability_context()

        prompt = f"""[CORTEX_ACCOUNTABILITY_PROTOCOL v1.0]

verify_response와 함께 다음 4가지를 판단해주세요:

## 1. 의도 일치 검증 (Intent Alignment)

{context['pending_intents']}

현재 수행한 작업:
{current_action}

질문: 현재 작업이 위 의도들 중 하나를 이행하고 있습니까?

## 2. 약속 이행 검증 (Promise Fulfillment)

{context['pending_promises']}

현재 작업 내용:
{current_action}

질문: 현재 작업이 위 약속들 중 하나를 이행합니까?

## 3. 수치 주장 검증 (Numeric Claim Check)

현재 응답에 수치적 주장이 포함되어 있습니까?
(예: "5개 수정", "30% 향상", "3개 파일 생성")

## 4. 이전 주장과 모순 검증 (Cross-session Consistency)

{context['previous_claims']}

현재 응답 요약:
{current_response[:500]}...

질문: 현재 응답이 이전 주장과 모순됩니까?

---

다음 JSON 형식으로 응답해주세요:

```json
{{
  "accountability_judgment": {{
    "intent_match": {{
      "matched_intent_id": "intent_xxx" | null,
      "is_aligned": true | false,
      "reason": "판단 근거"
    }},
    "promise_check": {{
      "fulfilled_promise_id": "promise_xxx" | null,
      "is_fulfilled": true | false,
      "reason": "판단 근거"
    }},
    "numeric_claims": [
      {{"text": "...", "number": N, "unit": "...", "verifiable": true | false}}
    ],
    "contradiction_check": {{
      "has_contradiction": true | false,
      "conflicting_claims": [
        {{
          "previous_claim_id": "claim_xxx",
          "previous_text": "...",
          "current_text": "...",
          "reason": "..."
        }}
      ]
    }}
  }}
}}
```
"""
        return prompt

    def process_accountability_judgment(
        self,
        judgment: Dict,
        current_action: str,
    ) -> Dict:
        """
        AI의 책임성 판단 결과 처리

        Args:
            judgment: AI의 accountability_judgment 응답
            current_action: 현재 수행한 작업

        Returns:
            {
                "processed": bool,
                "intent_verified": bool,
                "promise_fulfilled": bool,
                "warnings": [...],
                "stats": {...}
            }
        """
        result = {
            "processed": False,
            "intent_verified": False,
            "promise_fulfilled": False,
            "warnings": [],
            "stats": {},
        }

        if not judgment or "accountability_judgment" not in judgment:
            logger.warning("[AccountabilityHandler] 유효하지 않은 판단 결과")
            return result

        aj = judgment["accountability_judgment"]

        # 1. 의도 일치 처리
        intent_match = aj.get("intent_match", {})
        if intent_match.get("is_aligned") and intent_match.get("matched_intent_id"):
            self.intent_cache.verify_intent(
                intent_match["matched_intent_id"],
                evidence=current_action,
                verified_by="ai",
            )
            result["intent_verified"] = True
            logger.info(f"[AccountabilityHandler] 의도 이행 확인: {intent_match['matched_intent_id']}")
        elif not intent_match.get("is_aligned") and self.intent_cache.get_pending_intents():
            result["warnings"].append({
                "type": "intent_mismatch",
                "level": "WARN",
                "message": f"현재 작업이 pending 의도와 불일치: {intent_match.get('reason', '')}",
            })

        # 2. 약속 이행 처리
        promise_check = aj.get("promise_check", {})
        if promise_check.get("is_fulfilled") and promise_check.get("fulfilled_promise_id"):
            self.promise_tracker.fulfill_promise(
                promise_check["fulfilled_promise_id"],
                evidence=current_action,
                verified_by="ai",
            )
            result["promise_fulfilled"] = True
            logger.info(f"[AccountabilityHandler] 약속 이행 확인: {promise_check['fulfilled_promise_id']}")

        # 3. 수치 주장 기록
        numeric_claims = aj.get("numeric_claims", [])
        if numeric_claims:
            result["numeric_claims"] = numeric_claims
            logger.info(f"[AccountabilityHandler] 수치 주장 감지: {len(numeric_claims)}개")

        # 4. 모순 감지 처리
        contradiction_check = aj.get("contradiction_check", {})
        if contradiction_check.get("has_contradiction"):
            conflicts = contradiction_check.get("conflicting_claims", [])
            for conflict in conflicts:
                result["warnings"].append({
                    "type": "cross_session_contradiction",
                    "level": "ERROR",
                    "message": f"이전 주장과 모순 감지: {conflict.get('reason', '')}",
                    "previous_text": conflict.get("previous_text", ""),
                    "current_text": conflict.get("current_text", ""),
                })
            logger.warning(f"[AccountabilityHandler] 모순 감지: {len(conflicts)}개")

        # 통계 수집
        result["stats"] = {
            "intent": self.intent_cache.get_stats(),
            "promise": self.promise_tracker.get_stats(),
            "claims": self.key_claims_manager.get_stats(),
        }

        result["processed"] = True
        return result

    # === 편의 메서드 ===

    def add_intent(self, text: str, **kwargs) -> Dict:
        """사용자 의도 추가"""
        return self.intent_cache.add_intent(text, **kwargs)

    def add_promise(self, text: str, **kwargs) -> Dict:
        """AI 약속 추가"""
        return self.promise_tracker.add_promise(text, **kwargs)

    def add_claim(self, text: str, claim_type: str, **kwargs) -> Optional[Dict]:
        """주요 주장 추가"""
        return self.key_claims_manager.add_claim(text, claim_type, **kwargs)

    def start_session(self, session_id: Optional[str] = None) -> str:
        """세션 시작"""
        return self.key_claims_manager.start_session(session_id)

    def end_session(self) -> bool:
        """세션 종료"""
        return self.key_claims_manager.end_session()

    def get_combined_stats(self) -> Dict:
        """통합 통계 반환"""
        return {
            "intent_cache": self.intent_cache.get_stats(),
            "promise_tracker": self.promise_tracker.get_stats(),
            "key_claims": self.key_claims_manager.get_stats(),
            "promise_fulfillment_rate": self.promise_tracker.get_fulfillment_rate(),
        }

    def clear_all(self) -> None:
        """모든 데이터 초기화 (테스트용)"""
        self.intent_cache.clear_all()
        self.promise_tracker.clear_all()
        self.key_claims_manager.clear_all()
        logger.info("[AccountabilityHandler] 모든 데이터 초기화 완료")


# 싱글톤 인스턴스 관리
_handler_instances: Dict[str, AccountabilityHandler] = {}


def get_accountability_handler(
    project_id: str,
    memory_dir: Optional[Path] = None,
) -> AccountabilityHandler:
    """
    AccountabilityHandler 싱글톤 인스턴스 반환

    Args:
        project_id: 프로젝트 ID
        memory_dir: 메모리 디렉토리 (선택)

    Returns:
        AccountabilityHandler 인스턴스
    """
    if project_id not in _handler_instances:
        _handler_instances[project_id] = AccountabilityHandler(project_id, memory_dir)

    return _handler_instances[project_id]
