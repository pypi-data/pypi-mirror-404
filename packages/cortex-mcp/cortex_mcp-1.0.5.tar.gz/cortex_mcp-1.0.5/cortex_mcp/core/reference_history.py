"""
Cortex MCP - Reference History System v2.1
맥락 참조 이력 기록 및 추천 + Alpha Logger 연동

기능:
- 함께 참조된 맥락 이력 저장
- 3-Tier 추천 시스템 (History -> AI -> User)
- 사용자 피드백 학습
- Co-occurrence 기반 연관 분석
- Alpha Logger 연동 (v2.1)
"""

import json
import re
import sys
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from config import Tier, config

from .alpha_logger import LogModule, get_alpha_logger


@dataclass
class ReferenceEntry:
    """개별 참조 이력 엔트리"""

    timestamp: str
    task_keywords: List[str]
    contexts_used: List[str]
    branch_id: str
    project_id: str
    user_feedback: str = "pending"  # pending, accepted, rejected, modified
    query: str = ""


@dataclass
class RecommendationResult:
    """맥락 추천 결과"""

    tier: int  # 1: History, 2: AI, 3: User
    contexts: List[str]
    confidence: float
    reason: str
    source_entry: Optional[Dict] = None


class ReferenceHistory:
    """
    Reference History System
    - 맥락 추천 정확도 95% 목표
    - 함께 사용된 맥락 기반 추천
    """

    def __init__(self, project_id: str = None):
        self.project_id = project_id
        self.memory_dir = config.memory_dir

        # Feature Flags 체크 (Pro 이상에서만 활성화)
        self.reference_history_enabled = config.is_feature_enabled("reference_history_enabled")

        # Alpha Logger
        self.logger = get_alpha_logger()

        # 프로젝트별 히스토리 파일
        if project_id:
            self.history_file = self.memory_dir / project_id / "_reference_history.json"
        else:
            # 전역 히스토리
            self.history_file = config.base_dir / "global_reference_history.json"

        # 메모리 캐시
        self._history: List[Dict] = []
        self._context_frequency: Dict[str, int] = defaultdict(int)
        self._co_occurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._pending_suggestions: Dict[str, Dict] = {}  # session_id -> suggestion_info

        # P0-2: Threading Lock 추가 (동시성 보호)
        self._lock = threading.Lock()

        # 로드
        self._load()

    # ==================== Public API ====================

    def is_enabled(self) -> bool:
        """Reference History 기능이 활성화되어 있는지 확인"""
        return self.reference_history_enabled

    def record(
        self,
        task_keywords: List[str],
        contexts_used: List[str],
        branch_id: str,
        query: str = "",
        project_id: str = None,
    ) -> Dict[str, Any]:
        """
        맥락 참조 이력 기록

        Args:
            task_keywords: 작업 키워드 목록
            contexts_used: 사용된 맥락 ID 목록
            branch_id: 브랜치 ID
            query: 원본 쿼리 (선택)
            project_id: 프로젝트 ID (선택)

        Returns:
            기록 결과
        """
        # Feature Flags 체크
        if not self.reference_history_enabled:
            return {
                "success": False,
                "error": "Reference History 기능이 비활성화되어 있습니다. Pro 이상 티어가 필요합니다.",
                "tier_required": "pro",
            }

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_keywords": task_keywords,
            "contexts_used": contexts_used,
            "branch_id": branch_id,
            "project_id": project_id or self.project_id,
            "query": query,
            "user_feedback": "pending",
        }

        self._history.append(entry)

        # 빈도 업데이트
        for ctx_id in contexts_used:
            self._context_frequency[ctx_id] += 1

        # Co-occurrence 업데이트
        for i, ctx1 in enumerate(contexts_used):
            for ctx2 in contexts_used[i + 1 :]:
                self._co_occurrence[ctx1][ctx2] += 1
                self._co_occurrence[ctx2][ctx1] += 1

        self._save()

        return {
            "success": True,
            "message": "참조 이력 기록 완료",
            "entry_count": len(self._history),
        }

    def record_reference(
        self,
        task_keywords: List[str],
        contexts_used: List[str],
        branch_id: str,
        query: str = "",
        project_id: str = None,
    ) -> Dict[str, Any]:
        """
        맥락 참조 이력 기록 (record 메서드의 alias)

        Args:
            task_keywords: 작업 키워드 목록
            contexts_used: 사용된 맥락 ID 목록
            branch_id: 브랜치 ID
            query: 원본 쿼리 (선택)
            project_id: 프로젝트 ID (선택)

        Returns:
            기록 결과
        """
        return self.record(
            task_keywords=task_keywords,
            contexts_used=contexts_used,
            branch_id=branch_id,
            query=query,
            project_id=project_id,
        )

    def suggest_contexts(self, query: str, branch_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        3-Tier 맥락 추천

        Args:
            query: 검색 쿼리
            branch_id: 브랜치 ID (선택)
            top_k: 반환할 최대 개수

        Returns:
            추천 결과 (tier, contexts, confidence, reason)
        """
        # P0-1: 30분 지난 pending_suggestions 자동 정리 (High-5: 5분 → 30분 개선)
        expired = self._cleanup_expired_suggestions(timeout_minutes=30)
        if expired:
            self.logger.log_reference_history(
                action="cleanup",
                query=f"Expired {len(expired)} suggestions",
                recommended_contexts=[],
            )

        # ============================================================
        # P3 수정: Free 티어에서 Tier 3 (사용자 수동 선택) 제공
        # ============================================================
        if not self.reference_history_enabled:
            # Free 티어: Tier 1, 2를 건너뛰고 바로 Tier 3 제공
            session_id = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"
            latency_ms = (time.time() - start_time) * 1000

            return {
                "success": True,
                "session_id": session_id,
                "tier": 3,
                "tier_name": "User Selection Required (Free Tier)",
                "confidence": 1.0,
                "contexts": [],
                "reason": "Free 티어에서는 자동 추천을 사용할 수 없습니다. 맥락을 직접 선택해주세요.",
                "available_contexts": self._get_all_contexts(),
                "message": "추천할 맥락이 없습니다. RAG 검색 또는 직접 선택해주세요.",
                "latency_ms": round(latency_ms, 2),
            }

        start_time = time.time()
        keywords = self._extract_keywords(query)

        # Session ID 생성 (타임스탬프 + UUID)
        session_id = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"

        # Tier 1: Reference History 기반 (정확도 95%)
        tier1_result = self._suggest_from_history(keywords, branch_id, top_k)
        if tier1_result["contexts"]:
            latency_ms = (time.time() - start_time) * 1000
            result = {
                "success": True,
                "session_id": session_id,
                "tier": 1,
                "tier_name": "Reference History",
                "confidence": 0.95,
                "contexts": tier1_result["contexts"],
                "reason": tier1_result["reason"],
                "source_keywords": tier1_result.get("matched_keywords", []),
                "message": f"이전에 유사한 작업에서 함께 사용한 맥락 {len(tier1_result['contexts'])}개를 찾았습니다.",
                "latency_ms": round(latency_ms, 2),
            }

            # P0-2: Lock으로 동시성 보호
            with self._lock:
                # Pending suggestions에 기록 (30분 timeout) (High-5: 5분 → 30분 개선)
                self._pending_suggestions[session_id] = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "query": query,
                    "tier": 1,
                    "contexts": tier1_result["contexts"],
                    "decision": "pending",
                    "timeout_minutes": 30,
                }

            self.logger.log_reference_history(
                action="recommend",
                query=query,
                recommended_contexts=tier1_result["contexts"],
                latency_ms=latency_ms,
            )
            return result

        # Tier 2: Co-occurrence 기반 (정확도 70%)
        tier2_result = self._suggest_from_cooccurrence(keywords, top_k)
        if tier2_result["contexts"]:
            latency_ms = (time.time() - start_time) * 1000
            result = {
                "success": True,
                "session_id": session_id,
                "tier": 2,
                "tier_name": "Co-occurrence Analysis",
                "confidence": 0.70,
                "contexts": tier2_result["contexts"],
                "reason": tier2_result["reason"],
                "message": f"함께 자주 사용되는 맥락 {len(tier2_result['contexts'])}개를 찾았습니다.",
                "latency_ms": round(latency_ms, 2),
            }

            # P0-2: Lock으로 동시성 보호
            with self._lock:
                # Pending suggestions에 기록 (High-5: 5분 → 30분 개선)
                self._pending_suggestions[session_id] = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "query": query,
                    "tier": 2,
                    "contexts": tier2_result["contexts"],
                    "decision": "pending",
                    "timeout_minutes": 30,
                }

            self.logger.log_reference_history(
                action="recommend",
                query=query,
                recommended_contexts=tier2_result["contexts"],
                latency_ms=latency_ms,
            )
            return result

        # Tier 3: 사용자 선택 필요 (정확도 100% - 사용자 결정)
        latency_ms = (time.time() - start_time) * 1000
        self.logger.log_reference_history(
            action="recommend", query=query, recommended_contexts=[], latency_ms=latency_ms
        )

        # Tier 3은 추천이 없으므로 pending_suggestions에 기록하지 않음 (session_id는 반환)
        return {
            "success": True,
            "session_id": session_id,
            "tier": 3,
            "tier_name": "User Selection Required",
            "confidence": 1.0,
            "contexts": [],
            "reason": "관련 이력을 찾을 수 없습니다. 맥락을 직접 선택해주세요.",
            "available_contexts": self._get_all_contexts(),
            "message": "추천할 맥락이 없습니다. 직접 선택해주세요.",
            "latency_ms": round(latency_ms, 2),
        }

    def update_feedback(
        self,
        entry_timestamp: str = None,
        feedback: str = "accepted",
        contexts_actually_used: List[str] = None,
    ) -> Dict[str, Any]:
        """
        사용자 피드백 업데이트

        Args:
            entry_timestamp: 특정 엔트리 타임스탬프 (없으면 최신)
            feedback: accepted, rejected, modified
            contexts_actually_used: 실제 사용된 맥락 (modified인 경우)

        Returns:
            업데이트 결과
        """
        if not self._history:
            return {"success": False, "error": "이력이 없습니다."}

        # 대상 엔트리 찾기
        target_entry = None
        if entry_timestamp:
            for entry in self._history:
                if entry["timestamp"] == entry_timestamp:
                    target_entry = entry
                    break
        else:
            # 최신 pending 엔트리
            for entry in reversed(self._history):
                if entry.get("user_feedback") == "pending":
                    target_entry = entry
                    break

        if not target_entry:
            return {"success": False, "error": "대상 엔트리를 찾을 수 없습니다."}

        target_entry["user_feedback"] = feedback

        # modified인 경우 실제 사용된 맥락으로 업데이트
        if feedback == "modified" and contexts_actually_used:
            # 기존 빈도/co-occurrence 감소
            old_contexts = target_entry["contexts_used"]
            for ctx_id in old_contexts:
                self._context_frequency[ctx_id] = max(0, self._context_frequency[ctx_id] - 1)
            for i, ctx1 in enumerate(old_contexts):
                for ctx2 in old_contexts[i + 1 :]:
                    self._co_occurrence[ctx1][ctx2] = max(0, self._co_occurrence[ctx1][ctx2] - 1)
                    self._co_occurrence[ctx2][ctx1] = max(0, self._co_occurrence[ctx2][ctx1] - 1)

            # 새 맥락으로 업데이트
            target_entry["contexts_used"] = contexts_actually_used
            for ctx_id in contexts_actually_used:
                self._context_frequency[ctx_id] += 1
            for i, ctx1 in enumerate(contexts_actually_used):
                for ctx2 in contexts_actually_used[i + 1 :]:
                    self._co_occurrence[ctx1][ctx2] += 1
                    self._co_occurrence[ctx2][ctx1] += 1

        self._save()

        # 피드백 로깅
        accepted_flag = None
        if feedback == "accepted":
            accepted_flag = True
        elif feedback == "rejected":
            accepted_flag = False
        # modified는 None으로 유지

        self.logger.log_reference_history(
            action="update",
            query=target_entry.get("query", ""),
            recommended_contexts=target_entry.get("contexts_used", []),
            accepted=accepted_flag,
        )

        return {
            "success": True,
            "message": f"피드백 '{feedback}' 업데이트 완료",
            "entry_timestamp": target_entry["timestamp"],
        }

    def record_suggestion_decision(
        self,
        session_id: str,
        decision: str,  # "accepted", "rejected", "ignored"
        contexts_used: List[str],
        reason: str = "",
    ) -> Dict[str, Any]:
        """
        추천 결정 기록 (출처에 대한 책임 강제)

        Args:
            session_id: suggest_contexts에서 반환한 session_id
            decision: "accepted", "rejected", "ignored"
            contexts_used: 실제 사용된 맥락 ID 목록
            reason: 거부 이유 (rejected인 경우 필수)

        Returns:
            기록 결과
        """
        # P0-2: Lock으로 동시성 보호
        with self._lock:
            # Session 확인
            if session_id not in self._pending_suggestions:
                return {"success": False, "error": f"유효하지 않은 session_id: {session_id}"}

            suggestion = self._pending_suggestions[session_id]

            # 거부 시 이유 필수
            if decision == "rejected" and not reason:
                return {"success": False, "error": "거부 시 이유(reason) 입력이 필수입니다."}

            # 결정 기록
            suggestion["decision"] = decision
            suggestion["decision_timestamp"] = datetime.now(timezone.utc).isoformat()
            suggestion["contexts_used"] = contexts_used
            suggestion["reason"] = reason

            # Alpha Logger 기록
            self.logger.log_reference_history(
                action="decision",
                query=suggestion["query"],
                recommended_contexts=suggestion["contexts"],
                accepted=(decision == "accepted"),
            )

            # Pending에서 제거
            del self._pending_suggestions[session_id]

            # 영구 저장 (decision history)
            self._save()

        return {
            "success": True,
            "message": f"추천 결정 '{decision}' 기록 완료",
            "session_id": session_id,
        }

    def accept_suggestions(
        self,
        session_id: str,
        contexts_used: List[str] = None,
    ) -> Dict[str, Any]:
        """
        P0-3: 추천 자동 수락 (출처에 대한 책임)

        Args:
            session_id: suggest_contexts에서 반환한 session_id
            contexts_used: 실제 사용된 맥락 ID 목록 (None이면 추천된 전체)

        Returns:
            수락 결과
        """
        # Session 확인
        if session_id not in self._pending_suggestions:
            return {"success": False, "error": f"유효하지 않은 session_id: {session_id}"}

        # contexts_used가 None이면 추천된 전체 사용
        if contexts_used is None:
            contexts_used = self._pending_suggestions[session_id].get("contexts", [])

        return self.record_suggestion_decision(
            session_id=session_id,
            decision="accepted",
            contexts_used=contexts_used,
            reason="",
        )

    def reject_suggestions(
        self,
        session_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        P0-4: 추천 자동 거부 (출처에 대한 책임)

        Args:
            session_id: suggest_contexts에서 반환한 session_id
            reason: 거부 이유 (필수)

        Returns:
            거부 결과
        """
        # 이유 필수 체크
        if not reason or not reason.strip():
            return {"success": False, "error": "거부 이유(reason) 입력이 필수입니다."}

        return self.record_suggestion_decision(
            session_id=session_id,
            decision="rejected",
            contexts_used=[],
            reason=reason,
        )

    def get_pending_suggestions(self, timeout_minutes: int = 30) -> List[Dict]:  # High-5: 5분 → 30분 개선
        """
        Timeout 경과한 미결정 추천 목록 반환

        Args:
            timeout_minutes: timeout 기준 (분)

        Returns:
            미결정 추천 목록
        """
        now = datetime.now(timezone.utc)
        expired = []

        for session_id, suggestion in list(self._pending_suggestions.items()):
            timestamp = datetime.fromisoformat(suggestion["timestamp"])
            elapsed_minutes = (now - timestamp).total_seconds() / 60

            if elapsed_minutes > timeout_minutes:
                # 자동으로 "ignored"로 처리
                suggestion["decision"] = "ignored"
                suggestion["decision_timestamp"] = now.isoformat()
                expired.append(
                    {"session_id": session_id, "elapsed_minutes": round(elapsed_minutes, 2), **suggestion}
                )

                # Alpha Logger 기록
                self.logger.log_reference_history(
                    action="timeout",
                    query=suggestion["query"],
                    recommended_contexts=suggestion["contexts"],
                    accepted=False,
                )

                # Pending에서 제거
                del self._pending_suggestions[session_id]

        if expired:
            self._save()

        return expired

    def get_statistics(self) -> Dict[str, Any]:
        """
        Reference History 통계 반환
        """
        total_entries = len(self._history)
        accepted = sum(1 for e in self._history if e.get("user_feedback") == "accepted")
        rejected = sum(1 for e in self._history if e.get("user_feedback") == "rejected")
        modified = sum(1 for e in self._history if e.get("user_feedback") == "modified")

        acceptance_rate = accepted / total_entries if total_entries > 0 else 0

        # 가장 많이 사용된 맥락
        top_contexts = sorted(self._context_frequency.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return {
            "total_entries": total_entries,
            "feedback_stats": {
                "accepted": accepted,
                "rejected": rejected,
                "modified": modified,
                "pending": total_entries - accepted - rejected - modified,
            },
            "acceptance_rate": round(acceptance_rate, 2),
            "top_contexts": [{"context_id": k, "count": v} for k, v in top_contexts],
            "unique_contexts": len(self._context_frequency),
        }

    def get_co_occurring_contexts(
        self, context_id: str, min_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        특정 맥락과 함께 자주 사용되는 맥락 목록
        """
        if context_id not in self._co_occurrence:
            return []

        co_contexts = []
        for other_id, count in self._co_occurrence[context_id].items():
            if count >= min_count:
                co_contexts.append({"context_id": other_id, "co_occurrence_count": count})

        return sorted(co_contexts, key=lambda x: x["co_occurrence_count"], reverse=True)

    # ==================== Private Methods ====================

    def _cleanup_expired_suggestions(self, timeout_minutes: int = 30) -> List[Dict]:  # High-5: 5분 → 30분 개선
        """
        P0-1: Timeout 경과한 pending_suggestions 자동 정리 (내부용)

        Args:
            timeout_minutes: timeout 기준 (분)

        Returns:
            만료된 추천 목록
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            expired = []

            for session_id, suggestion in list(self._pending_suggestions.items()):
                timestamp = datetime.fromisoformat(suggestion["timestamp"])
                elapsed_minutes = (now - timestamp).total_seconds() / 60

                if elapsed_minutes > timeout_minutes:
                    # 자동으로 "ignored"로 처리
                    suggestion["decision"] = "ignored"
                    suggestion["decision_timestamp"] = now.isoformat()
                    expired.append(
                        {"session_id": session_id, "elapsed_minutes": round(elapsed_minutes, 2), **suggestion}
                    )

                    # Alpha Logger 기록
                    self.logger.log_reference_history(
                        action="timeout",
                        query=suggestion["query"],
                        recommended_contexts=suggestion["contexts"],
                        accepted=False,
                    )

                    # Pending에서 제거
                    del self._pending_suggestions[session_id]

            if expired:
                self._save()

            return expired

    def _extract_keywords(self, query: str) -> List[str]:
        """쿼리에서 키워드 추출"""
        # 간단한 키워드 추출 (공백 분리 + 불용어 제거)
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "이",
            "가",
            "은",
            "는",
            "을",
            "를",
            "에",
            "의",
            "와",
            "과",
            "하다",
            "되다",
            "있다",
            "없다",
            "해",
            "해줘",
            "해주세요",
            "좀",
            "그",
            "저",
            "이것",
            "저것",
        }

        # 소문자 변환 및 특수문자 제거
        words = re.findall(r"\b[\w가-힣]+\b", query.lower())

        # 불용어 제거 및 2글자 이상만
        keywords = [w for w in words if w not in stopwords and len(w) >= 2]

        return keywords

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

    def _suggest_from_history(
        self, keywords: List[str], branch_id: str = None, top_k: int = 5
    ) -> Dict[str, Any]:
        """Reference History에서 추천 (퍼지 매칭 포함)"""
        if not keywords or not self._history:
            return {"contexts": [], "reason": "키워드 또는 이력 없음"}

        # 퍼지 매칭 점수 계산 (개선: 완전 일치 -> 퍼지 매칭)
        matches = []
        query_str = " ".join(keywords)

        for entry in self._history:
            # accepted 또는 pending인 것만 (rejected 제외)
            if entry.get("user_feedback") == "rejected":
                continue

            entry_keywords = entry.get("task_keywords", [])

            # 퍼지 매칭 점수 계산
            fuzzy_score = self._fuzzy_match_keywords(query_str, entry_keywords)

            if fuzzy_score >= 0.3:  # 30% 이상 매칭 시 후보
                # 매칭된 키워드 추출 (디버깅용)
                entry_keywords_set = set(word.lower() for word in entry_keywords)
                query_keywords_set = set(keywords)
                matched_keywords = list(entry_keywords_set & query_keywords_set)

                matches.append({
                    "entry": entry,
                    "score": fuzzy_score,
                    "matched_keywords": matched_keywords if matched_keywords else ["(fuzzy)"]
                })

        if not matches:
            return {"contexts": [], "reason": "매칭되는 이력 없음"}

        # 최고 점수 엔트리
        best_match = max(matches, key=lambda x: x["score"])

        if best_match["score"] < 0.3:  # 최소 30% 매칭
            return {"contexts": [], "reason": "매칭 점수 부족"}

        return {
            "contexts": best_match["entry"]["contexts_used"][:top_k],
            "reason": f"키워드 '{', '.join(best_match['matched_keywords'])}'와 매칭되는 이전 작업 발견",
            "matched_keywords": best_match["matched_keywords"],
            "match_score": best_match["score"],
        }

    def _suggest_from_cooccurrence(self, keywords: List[str], top_k: int = 5) -> Dict[str, Any]:
        """Co-occurrence 기반 추천"""
        # 키워드를 포함하는 맥락 찾기
        candidate_contexts = set()

        for ctx_id in self._context_frequency.keys():
            ctx_lower = ctx_id.lower()
            for keyword in keywords:
                if keyword.lower() in ctx_lower:
                    candidate_contexts.add(ctx_id)
                    break

        if not candidate_contexts:
            return {"contexts": [], "reason": "후보 맥락 없음"}

        # 후보와 함께 자주 사용되는 맥락 수집
        related_contexts = defaultdict(int)
        for ctx_id in candidate_contexts:
            if ctx_id in self._co_occurrence:
                for other_id, count in self._co_occurrence[ctx_id].items():
                    if other_id not in candidate_contexts:
                        related_contexts[other_id] += count

        # 후보 + 관련 맥락 정렬
        all_contexts = list(candidate_contexts) + sorted(
            related_contexts.keys(), key=lambda x: related_contexts[x], reverse=True
        )

        return {
            "contexts": all_contexts[:top_k],
            "reason": f"키워드 기반 후보와 Co-occurrence 분석 결과",
        }

    def _get_all_contexts(self) -> List[str]:
        """모든 알려진 맥락 목록"""
        return list(self._context_frequency.keys())

    # ==================== Semantic Relationship 지원 메서드 ====================

    def get_cooccurrence(
        self,
        context_id: str,
        project_id: Optional[str] = None,
        min_count: int = 3
    ) -> List[Tuple[str, int, float]]:
        """
        함께 사용된 Context 반환 (FREQUENTLY_USED_WITH 관계)

        Args:
            context_id: 기준 Context ID
            project_id: 프로젝트 ID (필터링)
            min_count: 최소 빈도

        Returns:
            [
                ("file://session.py", 12, 0.92),  # (context_id, count, score)
                ...
            ]
        """
        with self._lock:
            if context_id not in self._co_occurrence:
                return []

            cooccurred = []
            total_count = sum(self._co_occurrence[context_id].values())

            for other_ctx, count in self._co_occurrence[context_id].items():
                if count >= min_count:
                    # Jaccard Similarity 기반 스코어
                    score = count / (self._context_frequency[context_id] +
                                   self._context_frequency[other_ctx] - count)
                    cooccurred.append((other_ctx, count, score))

            # 스코어 내림차순 정렬
            cooccurred.sort(key=lambda x: (-x[2], -x[1]))

            return cooccurred

    def get_sequence_patterns(
        self,
        context_id: str,
        project_id: Optional[str] = None,
        min_probability: float = 0.7
    ) -> List[Tuple[str, float, int]]:
        """
        작업 시퀀스 패턴 반환 (PRECEDES 관계)

        조건부 확률: P(B|A) = Count(A→B) / Count(A)

        Args:
            context_id: 기준 Context ID (A)
            project_id: 프로젝트 ID (필터링)
            min_probability: 최소 확률 (기본 0.7)

        Returns:
            [
                ("file://payment.py", 0.78, 10),  # (next_context, probability, count)
                ...
            ]
        """
        with self._lock:
            sequences = []

            # A가 포함된 모든 이력 엔트리 수집
            context_a_entries = [
                entry for entry in self._history
                if context_id in entry.get("contexts_used", [])
            ]

            if not context_a_entries:
                return []

            # 시퀀스 패턴 분석
            # A 다음에 B가 사용된 빈도 계산
            next_contexts = defaultdict(int)

            for i, entry in enumerate(context_a_entries):
                contexts_used = entry.get("contexts_used", [])
                try:
                    # A의 위치 찾기
                    a_index = contexts_used.index(context_id)

                    # A 다음에 나온 Context들
                    for next_ctx in contexts_used[a_index + 1:]:
                        next_contexts[next_ctx] += 1

                    # 다음 이력 엔트리도 확인 (시간 순서)
                    if i + 1 < len(self._history):
                        next_entry = self._history[i + 1]
                        next_entry_contexts = next_entry.get("contexts_used", [])
                        for next_ctx in next_entry_contexts:
                            next_contexts[next_ctx] += 0.5  # 약한 가중치

                except ValueError:
                    continue

            # 조건부 확률 계산
            total_a_count = len(context_a_entries)

            for next_ctx, count in next_contexts.items():
                probability = count / total_a_count

                if probability >= min_probability:
                    sequences.append((next_ctx, probability, int(count)))

            # 확률 내림차순 정렬
            sequences.sort(key=lambda x: (-x[1], -x[2]))

            return sequences

    def _load(self):
        """파일에서 히스토리 로드"""
        if not self.history_file.exists():
            return

        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            self._history = data.get("history", [])
            self._context_frequency = defaultdict(int, data.get("context_frequency", {}))

            # co_occurrence 로드 (중첩 defaultdict)
            co_data = data.get("co_occurrence", {})
            for ctx1, others in co_data.items():
                for ctx2, count in others.items():
                    self._co_occurrence[ctx1][ctx2] = count

            # pending_suggestions 로드
            self._pending_suggestions = data.get("pending_suggestions", {})

        except (json.JSONDecodeError, Exception):
            pass

    def _save(self):
        """히스토리를 파일에 저장"""
        # 디렉토리 생성
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "2.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "history": self._history,
            "context_frequency": dict(self._context_frequency),
            "co_occurrence": {k: dict(v) for k, v in self._co_occurrence.items()},
            "pending_suggestions": self._pending_suggestions,
        }

        self.history_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# 전역 인스턴스 (프로젝트별로 생성해야 함)
def get_reference_history(project_id: str = None) -> ReferenceHistory:
    """프로젝트별 Reference History 인스턴스 반환"""
    return ReferenceHistory(project_id=project_id)
