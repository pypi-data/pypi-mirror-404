"""
Cortex MCP - Branch Decision Engine
AI 자동 맥락 생성 핵심 엔진 (Zero-Effort 구현)

기능:
- 주제 전환 자동 감지
- 대화량/작업량 기반 브랜치 분리 판단
- 모듈/기능 단위 자동 분류
- Node 자동 그룹핑 제안
"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BranchDecisionEngine:
    """
    브랜치 생성 자동 결정 엔진

    Zero-Effort 원칙에 따라:
    - 유저 개입 없이 자동으로 브랜치 생성 필요성 판단
    - 주제 전환, 대화량, 작업량 등 다각도 분석
    - 확신도(confidence) 기반 결정
    """

    # 주제 전환 키워드 (가중치 포함)
    TOPIC_TRANSITION_KEYWORDS = {
        # 명시적 전환 (가중치 1.0)
        "새로운": 1.0,
        "다른": 1.0,
        "시작하자": 1.0,
        "새 프로젝트": 1.0,
        "별도": 1.0,
        "분리": 1.0,
        # 암시적 전환 (가중치 0.7)
        "이제": 0.7,
        "다음으로": 0.7,
        "넘어가서": 0.7,
        "전환": 0.7,
        "바꿔서": 0.7,
        # 약한 전환 (가중치 0.4)
        "추가로": 0.4,
        "그리고": 0.4,
        "또한": 0.4,
    }

    # 모듈/기능 키워드
    MODULE_KEYWORDS = [
        "모듈",
        "기능",
        "컴포넌트",
        "서비스",
        "API",
        "데이터베이스",
        "UI",
        "UX",
        "프론트엔드",
        "백엔드",
        "인증",
        "결제",
        "로그인",
        "회원가입",
        "대시보드",
    ]

    def __init__(self):
        self.decision_history: List[Dict[str, Any]] = []

    def should_create_branch(
        self,
        new_content: str,
        current_topic: Optional[str] = None,
        current_branch_id: Optional[str] = None,
        current_branch_topic: Optional[str] = None,
        current_branch_content: Optional[str] = None,
        context_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, float, str]:
        """
        브랜치 생성 필요 여부 판단

        Args:
            new_content: 새로 추가될 내용
            current_topic: 현재 브랜치 주제 (current_branch_topic의 alias)
            current_branch_id: 현재 브랜치 ID (선택)
            current_branch_topic: 현재 브랜치 주제 (선택)
            current_branch_content: 현재 브랜치 전체 내용 (선택)
            context_metadata: 컨텍스트 메타데이터 (시간, 크기 등)

        Returns:
            (should_create, confidence, reason)
            - should_create: 생성 필요 여부
            - confidence: 확신도 (0.0 ~ 1.0)
            - reason: 판단 근거
        """
        # current_topic이 제공되면 current_branch_topic으로 사용
        if current_topic is not None and current_branch_topic is None:
            current_branch_topic = current_topic

        # 기본값 설정
        if current_branch_topic is None:
            current_branch_topic = ""
        if current_branch_content is None:
            current_branch_content = ""

        scores = []
        reasons = []

        # 1. 주제 전환 감지
        topic_score, topic_reason = self._detect_topic_transition(current_branch_topic, new_content)
        scores.append(topic_score)
        reasons.append(topic_reason)

        # 2. 대화량 기반 판단
        volume_score, volume_reason = self._check_conversation_volume(
            current_branch_content, new_content
        )
        scores.append(volume_score)
        reasons.append(volume_reason)

        # 3. 시간 간격 판단
        if context_metadata:
            time_score, time_reason = self._check_time_gap(context_metadata)
            scores.append(time_score)
            reasons.append(time_reason)

        # 4. 모듈/기능 차이 판단
        module_score, module_reason = self._detect_module_change(current_branch_topic, new_content)
        scores.append(module_score)
        reasons.append(module_reason)

        # 종합 점수 계산 (가중 평균)
        weights = [0.4, 0.3, 0.2, 0.1][: len(scores)]
        total_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)

        # 확신도 기반 결정 (threshold: 0.45)
        should_create = total_score >= 0.45

        # 판단 근거 조합
        combined_reason = " | ".join([r for r in reasons if r])

        # 의사결정 이력 기록
        self.decision_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_branch": current_branch_id,
                "should_create": should_create,
                "confidence": total_score,
                "reason": combined_reason,
                "scores": {"topic": topic_score, "volume": volume_score, "module": module_score},
            }
        )

        return should_create, total_score, combined_reason

    def _detect_topic_transition(self, current_topic: str, new_content: str) -> Tuple[float, str]:
        """
        주제 전환 감지

        Returns:
            (score, reason)
            score: 0.0 (전환 없음) ~ 1.0 (명확한 전환)
        """
        score = 0.0
        matched_keywords = []

        # 키워드 매칭
        for keyword, weight in self.TOPIC_TRANSITION_KEYWORDS.items():
            if keyword in new_content:
                score = max(score, weight)
                matched_keywords.append(keyword)

        # 현재 주제와 새 내용의 주제 비교
        if current_topic and len(new_content) > 50:
            # 간단한 유사도 체크 (공통 명사 비율)
            current_nouns = self._extract_keywords(current_topic)
            new_nouns = self._extract_keywords(new_content)

            if current_nouns and new_nouns:
                overlap = len(current_nouns & new_nouns)
                similarity = overlap / max(len(current_nouns), len(new_nouns))

                # 유사도가 낮으면 주제 전환으로 판단
                if similarity < 0.3:
                    score = max(score, 0.7)
                    matched_keywords.append(f"주제 유사도 {similarity:.2f}")

        reason = f"주제 전환 감지: {', '.join(matched_keywords)}" if matched_keywords else ""
        return score, reason

    def _check_conversation_volume(
        self, current_content: str, new_content: str
    ) -> Tuple[float, str]:
        """
        대화량 기반 판단

        기준:
        - 50KB 이상: 높은 분리 필요성 (score 0.8)
        - 30KB ~ 50KB: 중간 (score 0.5)
        - 30KB 미만: 낮음 (score 0.2)
        """
        current_size_kb = len(current_content.encode("utf-8")) / 1024

        if current_size_kb >= 50:
            return 0.8, f"대화량 {current_size_kb:.1f}KB (임계치 50KB 초과)"
        elif current_size_kb >= 30:
            return 0.5, f"대화량 {current_size_kb:.1f}KB (중간 수준)"
        else:
            return 0.2, ""

    def _check_time_gap(self, metadata: Dict[str, Any]) -> Tuple[float, str]:
        """
        시간 간격 판단

        기준:
        - 24시간 이상: 높은 분리 필요성 (score 0.7)
        - 12시간 ~ 24시간: 중간 (score 0.4)
        - 12시간 미만: 낮음 (score 0.1)
        """
        last_updated = metadata.get("last_updated")
        if not last_updated:
            return 0.0, ""

        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))

        time_diff = datetime.now(timezone.utc) - last_updated
        hours = time_diff.total_seconds() / 3600

        if hours >= 24:
            return 0.7, f"시간 간격 {hours:.1f}시간 (1일 이상)"
        elif hours >= 12:
            return 0.4, f"시간 간격 {hours:.1f}시간"
        else:
            return 0.1, ""

    def _detect_module_change(self, current_topic: str, new_content: str) -> Tuple[float, str]:
        """
        모듈/기능 전환 감지
        """
        current_modules = self._extract_module_keywords(current_topic)
        new_modules = self._extract_module_keywords(new_content)

        if not current_modules or not new_modules:
            return 0.0, ""

        # 공통 모듈이 없으면 전환으로 판단
        overlap = current_modules & new_modules
        if not overlap:
            return 0.6, f"모듈 전환: {current_modules} → {new_modules}"

        return 0.0, ""

    def _extract_keywords(self, text: str) -> set:
        """간단한 키워드 추출 (명사 위주)"""
        # 한글/영문 단어 추출
        words = re.findall(r"[가-힣a-zA-Z]{2,}", text)
        # 불용어 제거
        stopwords = {"있습니다", "합니다", "입니다", "것", "수", "등", "the", "is", "are", "and"}
        return {w for w in words if w not in stopwords and len(w) >= 2}

    def _extract_module_keywords(self, text: str) -> set:
        """모듈 키워드 추출"""
        found = set()
        for keyword in self.MODULE_KEYWORDS:
            if keyword in text:
                found.add(keyword)
        return found

    def suggest_branch_name(
        self, new_content: str, context_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        새 브랜치 이름 제안

        전략:
        - 새 내용에서 핵심 키워드 추출
        - 모듈/기능 키워드 우선
        - 시간 기반 폴백
        """
        # 모듈 키워드 우선
        modules = self._extract_module_keywords(new_content)
        if modules:
            return "_".join(sorted(modules)[:2])

        # 일반 키워드 추출
        keywords = self._extract_keywords(new_content[:500])  # 앞부분 500자만
        if keywords:
            # 빈도순 정렬 (간단히 첫 등장 순서)
            top_keywords = sorted(keywords)[:2]
            return "_".join(top_keywords)

        # 폴백: 시간 기반
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"branch_{timestamp}"


class NodeGroupingEngine:
    """
    Node 자동 그룹핑 제안 엔진

    30개 이상의 Context 누적 시 자동으로 Node 그룹핑 제안
    """

    GROUPING_THRESHOLD = 30  # 30개 이상 시 그룹핑 제안

    def __init__(self):
        pass

    def should_suggest_grouping(self, branch_id: str, context_count: int) -> Tuple[bool, str]:
        """
        Node 그룹핑 제안 필요 여부

        Returns:
            (should_suggest, reason)
        """
        if context_count >= self.GROUPING_THRESHOLD:
            return True, f"Context {context_count}개 누적 (임계치 {self.GROUPING_THRESHOLD}개 초과)"
        return False, ""

    def suggest_node_groups(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        자동 Node 그룹 제안

        전략:
        - 온톨로지 카테고리 기반 그룹핑
        - 시간 기반 그룹핑
        - 유사도 기반 그룹핑
        """
        groups = []

        # 온톨로지 기반 그룹핑
        ontology_groups = {}
        for ctx in contexts:
            category = ctx.get("ontology_category", "uncategorized")
            if category not in ontology_groups:
                ontology_groups[category] = []
            ontology_groups[category].append(ctx)

        # 각 그룹이 5개 이상이면 Node로 제안
        for category, group_contexts in ontology_groups.items():
            if len(group_contexts) >= 5:
                groups.append(
                    {
                        "node_name": category,
                        "strategy": "ontology",
                        "contexts": group_contexts,
                        "count": len(group_contexts),
                    }
                )

        return groups
