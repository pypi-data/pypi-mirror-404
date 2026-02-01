"""
Cortex MCP - Misc Branch Analyzer

misc 브랜치에 쌓인 맥락들을 분석하여 적절한 브랜치로 재분류하는 기능

기능:
- misc 브랜치 맥락 분석
- 온톨로지 카테고리 기반 분류
- 임베딩 유사도 기반 기존 브랜치 매칭
- 재분류 제안 및 실행 (사용자 승인 후)

작성일: 2026-01-21
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .file_io import FileIO

logger = logging.getLogger(__name__)

# 유사도 임계값
SIMILARITY_THRESHOLD_AUTO = 0.75  # 자동 이동 임계값
SIMILARITY_THRESHOLD_SUGGEST = 0.50  # 제안 임계값
NEW_BRANCH_THRESHOLD = 0.40  # 이 이하면 새 브랜치 생성 제안

# misc 브랜치 상수
MISC_BRANCH_ID = "misc"
MISC_BRANCH_TOPIC = "기타 (분류되지 않은 대화)"


@dataclass
class ReclassificationSuggestion:
    """재분류 제안 데이터"""

    context_file: str  # 맥락 파일 경로
    context_summary: str  # 맥락 요약
    current_branch: str  # 현재 브랜치 (misc)

    # 제안된 대상
    suggested_branch_id: Optional[str] = None  # 기존 브랜치 ID
    suggested_branch_topic: Optional[str] = None  # 브랜치 주제
    similarity_score: float = 0.0  # 유사도 점수

    # 온톨로지 분류 결과
    ontology_category: Optional[str] = None
    ontology_confidence: float = 0.0

    # 추천 행동
    action: str = "keep"  # "move", "new_branch", "keep"
    new_branch_suggestion: Optional[str] = None  # 새 브랜치 제안 이름

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_file": self.context_file,
            "context_summary": self.context_summary[:200] if self.context_summary else "",
            "current_branch": self.current_branch,
            "suggested_branch_id": self.suggested_branch_id,
            "suggested_branch_topic": self.suggested_branch_topic,
            "similarity_score": round(self.similarity_score, 4),
            "ontology_category": self.ontology_category,
            "ontology_confidence": round(self.ontology_confidence, 4),
            "action": self.action,
            "new_branch_suggestion": self.new_branch_suggestion,
        }


@dataclass
class AnalysisResult:
    """분석 결과"""

    total_misc_contexts: int = 0
    analyzed_contexts: int = 0
    suggestions: List[ReclassificationSuggestion] = field(default_factory=list)

    # 통계
    move_suggestions: int = 0
    new_branch_suggestions: int = 0
    keep_suggestions: int = 0

    # 온톨로지 카테고리별 분포
    category_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_misc_contexts": self.total_misc_contexts,
            "analyzed_contexts": self.analyzed_contexts,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "statistics": {
                "move_suggestions": self.move_suggestions,
                "new_branch_suggestions": self.new_branch_suggestions,
                "keep_suggestions": self.keep_suggestions,
            },
            "category_distribution": self.category_distribution,
        }


class MiscBranchAnalyzer:
    """
    misc 브랜치 분석 및 재분류 엔진

    misc 브랜치에 쌓인 맥락들을 분석하여:
    1. 온톨로지 카테고리 기반 분류
    2. 기존 브랜치와의 유사도 매칭
    3. 재분류 제안 (이동 / 새 브랜치 생성 / 유지)
    """

    def __init__(
        self,
        memory_dir: Path,
        file_io: FileIO,
        similarity_threshold_auto: float = SIMILARITY_THRESHOLD_AUTO,
        similarity_threshold_suggest: float = SIMILARITY_THRESHOLD_SUGGEST,
    ):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            file_io: 파일 I/O 유틸리티
            similarity_threshold_auto: 자동 이동 임계값 (기본: 0.75)
            similarity_threshold_suggest: 제안 임계값 (기본: 0.50)
        """
        self.memory_dir = Path(memory_dir)
        self.file_io = file_io
        self.similarity_threshold_auto = similarity_threshold_auto
        self.similarity_threshold_suggest = similarity_threshold_suggest

        # 온톨로지 엔진 (lazy loading)
        self._ontology_engine = None

        # 유사도 판단 엔진 (lazy loading)
        self._similarity_judge = None

        logger.info("[MiscBranchAnalyzer] 초기화 완료")

    @property
    def ontology_engine(self):
        """온톨로지 엔진 (lazy loading)"""
        if self._ontology_engine is None:
            try:
                from cortex_mcp.core.ontology_engine import get_ontology_engine
                self._ontology_engine = get_ontology_engine()
                logger.debug("[MiscBranchAnalyzer] 온톨로지 엔진 로드 완료")
            except Exception as e:
                logger.warning(f"[MiscBranchAnalyzer] 온톨로지 엔진 로드 실패: {e}")
                self._ontology_engine = None
        return self._ontology_engine

    @property
    def similarity_judge(self):
        """유사도 판단 엔진 (lazy loading)"""
        if self._similarity_judge is None:
            try:
                from cortex_mcp.core.similarity_judge import get_similarity_judge
                self._similarity_judge = get_similarity_judge()
                logger.debug("[MiscBranchAnalyzer] 유사도 엔진 로드 완료")
            except Exception as e:
                logger.warning(f"[MiscBranchAnalyzer] 유사도 엔진 로드 실패: {e}")
                self._similarity_judge = None
        return self._similarity_judge

    def analyze_misc_contexts(
        self,
        project_id: str,
        max_contexts: int = 100,
    ) -> AnalysisResult:
        """
        misc 브랜치의 맥락들을 분석하여 재분류 제안 생성

        Args:
            project_id: 프로젝트 ID
            max_contexts: 분석할 최대 맥락 수 (기본: 100)

        Returns:
            AnalysisResult: 분석 결과
        """
        result = AnalysisResult()

        # 1. misc 브랜치의 맥락 파일들 수집
        misc_contexts = self._get_misc_contexts(project_id)
        result.total_misc_contexts = len(misc_contexts)

        if not misc_contexts:
            logger.info(f"[MiscBranchAnalyzer] {project_id}: misc 브랜치에 맥락이 없습니다")
            return result

        # 2. 기존 브랜치 목록 가져오기 (misc 제외)
        active_branches = self._get_active_branches(project_id, exclude_misc=True)

        # 3. 각 맥락 분석
        for i, context_file in enumerate(misc_contexts[:max_contexts]):
            try:
                suggestion = self._analyze_single_context(
                    project_id=project_id,
                    context_file=context_file,
                    active_branches=active_branches,
                )
                result.suggestions.append(suggestion)
                result.analyzed_contexts += 1

                # 통계 업데이트
                if suggestion.action == "move":
                    result.move_suggestions += 1
                elif suggestion.action == "new_branch":
                    result.new_branch_suggestions += 1
                else:
                    result.keep_suggestions += 1

                # 카테고리 분포 업데이트
                if suggestion.ontology_category:
                    cat = suggestion.ontology_category
                    result.category_distribution[cat] = result.category_distribution.get(cat, 0) + 1

            except Exception as e:
                logger.warning(f"[MiscBranchAnalyzer] 맥락 분석 실패 ({context_file}): {e}")

        logger.info(
            f"[MiscBranchAnalyzer] {project_id}: "
            f"{result.analyzed_contexts}/{result.total_misc_contexts}개 분석 완료, "
            f"이동 제안: {result.move_suggestions}, "
            f"새 브랜치 제안: {result.new_branch_suggestions}"
        )

        return result

    def suggest_reclassification(
        self,
        project_id: str,
        max_contexts: int = 50,
    ) -> Dict[str, Any]:
        """
        재분류 제안 반환 (사용자 확인용)

        Args:
            project_id: 프로젝트 ID
            max_contexts: 분석할 최대 맥락 수

        Returns:
            재분류 제안 딕셔너리
        """
        # 분석 수행
        analysis = self.analyze_misc_contexts(project_id, max_contexts)

        # 액션별로 그룹화
        move_items = []
        new_branch_items = []
        keep_items = []

        for suggestion in analysis.suggestions:
            item = {
                "context_file": suggestion.context_file,
                "summary": suggestion.context_summary[:100] + "..." if len(suggestion.context_summary) > 100 else suggestion.context_summary,
                "ontology_category": suggestion.ontology_category,
            }

            if suggestion.action == "move":
                item["target_branch"] = suggestion.suggested_branch_id
                item["target_topic"] = suggestion.suggested_branch_topic
                item["similarity"] = round(suggestion.similarity_score, 2)
                move_items.append(item)

            elif suggestion.action == "new_branch":
                item["suggested_name"] = suggestion.new_branch_suggestion
                item["category"] = suggestion.ontology_category
                new_branch_items.append(item)

            else:
                item["reason"] = "유사한 브랜치 없음, 카테고리 불명확"
                keep_items.append(item)

        return {
            "success": True,
            "project_id": project_id,
            "total_analyzed": analysis.analyzed_contexts,
            "summary": {
                "move_to_existing": len(move_items),
                "create_new_branch": len(new_branch_items),
                "keep_in_misc": len(keep_items),
            },
            "recommendations": {
                "move_to_existing_branch": move_items,
                "create_new_branch": new_branch_items,
                "keep_in_misc": keep_items,
            },
            "category_distribution": analysis.category_distribution,
        }

    def execute_reclassification(
        self,
        project_id: str,
        suggestions: List[Dict[str, Any]],
        create_branches: bool = False,
    ) -> Dict[str, Any]:
        """
        재분류 실행 (사용자 승인 후)

        Args:
            project_id: 프로젝트 ID
            suggestions: 실행할 제안 목록
                [{"context_file": "...", "action": "move", "target_branch": "..."}, ...]
            create_branches: 새 브랜치 생성 허용 여부

        Returns:
            실행 결과
        """
        results = {
            "success": True,
            "project_id": project_id,
            "executed": [],
            "failed": [],
            "skipped": [],
        }

        for suggestion in suggestions:
            context_file = suggestion.get("context_file")
            action = suggestion.get("action")

            if not context_file or not action:
                results["skipped"].append({
                    "context_file": context_file,
                    "reason": "필수 필드 누락 (context_file, action)",
                })
                continue

            try:
                if action == "move":
                    target_branch = suggestion.get("target_branch")
                    if not target_branch:
                        results["skipped"].append({
                            "context_file": context_file,
                            "reason": "target_branch 누락",
                        })
                        continue

                    success = self._move_context_to_branch(
                        project_id=project_id,
                        context_file=context_file,
                        target_branch=target_branch,
                    )

                    if success:
                        results["executed"].append({
                            "context_file": context_file,
                            "action": "moved",
                            "target_branch": target_branch,
                        })
                    else:
                        results["failed"].append({
                            "context_file": context_file,
                            "reason": "이동 실패",
                        })

                elif action == "new_branch" and create_branches:
                    new_branch_name = suggestion.get("new_branch_name")
                    if not new_branch_name:
                        results["skipped"].append({
                            "context_file": context_file,
                            "reason": "new_branch_name 누락",
                        })
                        continue

                    success, branch_id = self._create_branch_and_move(
                        project_id=project_id,
                        context_file=context_file,
                        branch_topic=new_branch_name,
                    )

                    if success:
                        results["executed"].append({
                            "context_file": context_file,
                            "action": "created_and_moved",
                            "new_branch_id": branch_id,
                        })
                    else:
                        results["failed"].append({
                            "context_file": context_file,
                            "reason": "브랜치 생성/이동 실패",
                        })

                elif action == "keep":
                    results["skipped"].append({
                        "context_file": context_file,
                        "reason": "유지 요청 (keep)",
                    })

                else:
                    results["skipped"].append({
                        "context_file": context_file,
                        "reason": f"지원하지 않는 action: {action}",
                    })

            except Exception as e:
                results["failed"].append({
                    "context_file": context_file,
                    "reason": str(e),
                })

        # 성공 여부 판단
        results["success"] = len(results["failed"]) == 0
        results["summary"] = {
            "executed": len(results["executed"]),
            "failed": len(results["failed"]),
            "skipped": len(results["skipped"]),
        }

        logger.info(
            f"[MiscBranchAnalyzer] 재분류 실행 완료: "
            f"성공 {len(results['executed'])}, "
            f"실패 {len(results['failed'])}, "
            f"건너뜀 {len(results['skipped'])}"
        )

        return results

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _get_misc_contexts(self, project_id: str) -> List[Path]:
        """misc 브랜치의 맥락 파일 목록 반환"""
        # V2 구조: memory_dir/contexts/misc/
        v2_misc_dir = self.memory_dir / "contexts" / MISC_BRANCH_ID
        if v2_misc_dir.exists():
            return sorted(v2_misc_dir.glob("context_*.md"))

        # V1 구조: memory_dir/{project_id}/contexts/misc/
        v1_misc_dir = self.memory_dir / project_id / "contexts" / MISC_BRANCH_ID
        if v1_misc_dir.exists():
            return sorted(v1_misc_dir.glob("context_*.md"))

        return []

    def _get_active_branches(
        self,
        project_id: str,
        exclude_misc: bool = True,
    ) -> List[Dict[str, Any]]:
        """활성 브랜치 목록 반환"""
        index = self.file_io.load_project_index(project_id)
        branches = []

        for branch_id, info in index.get("branches", {}).items():
            if exclude_misc and branch_id == MISC_BRANCH_ID:
                continue

            if info.get("status") == "active":
                branches.append({
                    "branch_id": branch_id,
                    "branch_topic": info.get("branch_topic", ""),
                    "context_count": info.get("context_count", 0),
                })

        return branches

    def _analyze_single_context(
        self,
        project_id: str,
        context_file: Path,
        active_branches: List[Dict[str, Any]],
    ) -> ReclassificationSuggestion:
        """단일 맥락 분석"""
        suggestion = ReclassificationSuggestion(
            context_file=str(context_file.name),
            context_summary="",
            current_branch=MISC_BRANCH_ID,
        )

        # 1. 맥락 파일 읽기
        try:
            frontmatter, body = self.file_io.parse_md_file(context_file)
            suggestion.context_summary = frontmatter.get("summary", body[:500])
        except Exception as e:
            logger.warning(f"[MiscBranchAnalyzer] 파일 읽기 실패: {e}")
            suggestion.action = "keep"
            return suggestion

        content_for_analysis = suggestion.context_summary or body[:1000]

        # 2. 온톨로지 분류
        if self.ontology_engine:
            try:
                classification = self.ontology_engine.classify(content_for_analysis)
                suggestion.ontology_category = classification.node_name
                suggestion.ontology_confidence = classification.confidence
            except Exception as e:
                logger.debug(f"[MiscBranchAnalyzer] 온톨로지 분류 실패: {e}")

        # 3. 기존 브랜치와 유사도 계산
        if active_branches and self.similarity_judge:
            best_match = self._find_best_matching_branch(
                content=content_for_analysis,
                branches=active_branches,
            )

            if best_match:
                suggestion.suggested_branch_id = best_match["branch_id"]
                suggestion.suggested_branch_topic = best_match["branch_topic"]
                suggestion.similarity_score = best_match["similarity"]

        # 4. 액션 결정
        suggestion.action = self._decide_action(suggestion)

        # 5. 새 브랜치 이름 제안 (필요시)
        if suggestion.action == "new_branch":
            suggestion.new_branch_suggestion = self._suggest_branch_name(
                content=content_for_analysis,
                ontology_category=suggestion.ontology_category,
            )

        return suggestion

    def _find_best_matching_branch(
        self,
        content: str,
        branches: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """콘텐츠와 가장 유사한 브랜치 찾기"""
        if not branches or not self.similarity_judge:
            return None

        best_match = None
        best_score = 0.0

        # 브랜치 토픽들과 유사도 계산
        branch_topics = [b["branch_topic"] for b in branches if b.get("branch_topic")]

        if not branch_topics:
            return None

        try:
            # 배치 유사도 계산
            results = self.similarity_judge.calculate_similarity_batch(
                text=content,
                candidates=branch_topics,
            )

            # 최고 점수 찾기
            for i, result in enumerate(results):
                similarity = result.get("similarity", 0.0)
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        "branch_id": branches[i]["branch_id"],
                        "branch_topic": branches[i]["branch_topic"],
                        "similarity": similarity,
                    }

        except Exception as e:
            logger.warning(f"[MiscBranchAnalyzer] 유사도 계산 실패: {e}")
            return None

        # 최소 임계값 확인
        if best_match and best_match["similarity"] >= self.similarity_threshold_suggest:
            return best_match

        return None

    def _decide_action(self, suggestion: ReclassificationSuggestion) -> str:
        """재분류 액션 결정"""
        # 1. 높은 유사도 → 기존 브랜치로 이동
        if suggestion.similarity_score >= self.similarity_threshold_auto:
            return "move"

        # 2. 중간 유사도 → 이동 제안
        if suggestion.similarity_score >= self.similarity_threshold_suggest:
            return "move"

        # 3. 온톨로지 분류 신뢰도 높음 → 새 브랜치 생성 제안
        if suggestion.ontology_confidence >= 0.7 and suggestion.ontology_category:
            return "new_branch"

        # 4. 낮은 유사도, 낮은 분류 신뢰도 → 유지
        return "keep"

    def _suggest_branch_name(
        self,
        content: str,
        ontology_category: Optional[str],
    ) -> str:
        """새 브랜치 이름 제안"""
        # 온톨로지 카테고리 기반
        if ontology_category and ontology_category != "general":
            return f"{ontology_category}_work"

        # 콘텐츠에서 키워드 추출
        keywords = self._extract_keywords(content)
        if keywords:
            return f"{keywords[0]}_context"

        return "new_topic"

    def _extract_keywords(self, content: str, max_keywords: int = 3) -> List[str]:
        """콘텐츠에서 주요 키워드 추출"""
        import re

        # 간단한 키워드 추출 (영문/한글 단어)
        words = re.findall(r"[a-zA-Z가-힣]+", content.lower())

        # 불용어 제거
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall",
            "이", "가", "을", "를", "은", "는", "에", "에서", "의", "로", "으로",
            "와", "과", "하다", "되다", "있다", "없다", "것", "수", "등",
        }

        # 빈도수 계산
        word_freq: Dict[str, int] = {}
        for word in words:
            if len(word) >= 2 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 상위 키워드 반환
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]

    def _move_context_to_branch(
        self,
        project_id: str,
        context_file: str,
        target_branch: str,
    ) -> bool:
        """맥락 파일을 다른 브랜치로 이동"""
        try:
            # 소스 파일 경로
            source_path = self._get_context_path(project_id, MISC_BRANCH_ID, context_file)
            if not source_path or not source_path.exists():
                logger.warning(f"[MiscBranchAnalyzer] 소스 파일 없음: {context_file}")
                return False

            # 대상 디렉토리 경로
            target_dir = self._get_branch_dir(project_id, target_branch)
            target_dir.mkdir(parents=True, exist_ok=True)

            # 대상 파일 경로 (같은 파일명 유지)
            target_path = target_dir / context_file

            # 파일 이동
            shutil.move(str(source_path), str(target_path))

            # 인덱스 업데이트
            self._update_indexes_after_move(
                project_id=project_id,
                context_file=context_file,
                from_branch=MISC_BRANCH_ID,
                to_branch=target_branch,
            )

            logger.info(f"[MiscBranchAnalyzer] 이동 완료: {context_file} → {target_branch}")
            return True

        except Exception as e:
            logger.error(f"[MiscBranchAnalyzer] 이동 실패: {e}")
            return False

    def _create_branch_and_move(
        self,
        project_id: str,
        context_file: str,
        branch_topic: str,
    ) -> Tuple[bool, Optional[str]]:
        """새 브랜치 생성 후 맥락 이동"""
        try:
            # 브랜치 ID 생성
            from cortex_mcp.core.memory.branch_manager import _sanitize_to_ascii

            sanitized_topic = _sanitize_to_ascii(branch_topic)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_id = f"{sanitized_topic}_{timestamp}"

            # 브랜치 디렉토리 생성
            branch_dir = self._get_branch_dir(project_id, branch_id)
            branch_dir.mkdir(parents=True, exist_ok=True)

            # 프로젝트 인덱스에 브랜치 추가
            index = self.file_io.load_project_index(project_id)
            index["branches"][branch_id] = {
                "branch_id": branch_id,
                "branch_topic": branch_topic,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active",
                "context_count": 0,
                "auto_created": True,
                "created_from": "misc_reclassification",
            }
            self.file_io.save_project_index(project_id, index)

            # 맥락 이동
            success = self._move_context_to_branch(
                project_id=project_id,
                context_file=context_file,
                target_branch=branch_id,
            )

            if success:
                return True, branch_id
            else:
                return False, None

        except Exception as e:
            logger.error(f"[MiscBranchAnalyzer] 브랜치 생성/이동 실패: {e}")
            return False, None

    def _get_context_path(
        self,
        project_id: str,
        branch_id: str,
        context_file: str,
    ) -> Optional[Path]:
        """맥락 파일 경로 반환"""
        # V2 구조
        v2_path = self.memory_dir / "contexts" / branch_id / context_file
        if v2_path.exists():
            return v2_path

        # V1 구조
        v1_path = self.memory_dir / project_id / "contexts" / branch_id / context_file
        if v1_path.exists():
            return v1_path

        return None

    def _get_branch_dir(self, project_id: str, branch_id: str) -> Path:
        """브랜치 디렉토리 경로 반환"""
        # V2 구조 확인
        v2_contexts_dir = self.memory_dir / "contexts"
        if v2_contexts_dir.exists():
            return v2_contexts_dir / branch_id

        # V1 구조
        return self.memory_dir / project_id / "contexts" / branch_id

    def _update_indexes_after_move(
        self,
        project_id: str,
        context_file: str,
        from_branch: str,
        to_branch: str,
    ):
        """이동 후 인덱스 업데이트"""
        # 프로젝트 인덱스 업데이트
        index = self.file_io.load_project_index(project_id)

        # from_branch context_count 감소
        if from_branch in index.get("branches", {}):
            count = index["branches"][from_branch].get("context_count", 0)
            index["branches"][from_branch]["context_count"] = max(0, count - 1)

        # to_branch context_count 증가
        if to_branch in index.get("branches", {}):
            count = index["branches"][to_branch].get("context_count", 0)
            index["branches"][to_branch]["context_count"] = count + 1

        self.file_io.save_project_index(project_id, index)

        # 브랜치 인덱스도 업데이트 (선택적)
        try:
            # from_branch 인덱스에서 제거
            from_index = self.file_io.load_branch_index(project_id, from_branch)
            if "contexts" in from_index:
                from_index["contexts"] = [
                    c for c in from_index["contexts"]
                    if c.get("filename") != context_file
                ]
                self.file_io.save_branch_index(project_id, from_branch, from_index)

            # to_branch 인덱스에 추가
            to_index = self.file_io.load_branch_index(project_id, to_branch)
            if "contexts" not in to_index:
                to_index["contexts"] = []
            to_index["contexts"].append({
                "filename": context_file,
                "moved_from": from_branch,
                "moved_at": datetime.now(timezone.utc).isoformat(),
            })
            self.file_io.save_branch_index(project_id, to_branch, to_index)

        except Exception as e:
            logger.warning(f"[MiscBranchAnalyzer] 브랜치 인덱스 업데이트 실패: {e}")


# =============================================================================
# Factory Function
# =============================================================================

def create_misc_branch_analyzer(
    memory_dir: Path,
    file_io: Optional[FileIO] = None,
) -> MiscBranchAnalyzer:
    """
    MiscBranchAnalyzer 인스턴스 생성 헬퍼

    Args:
        memory_dir: 메모리 저장 디렉토리
        file_io: FileIO 인스턴스 (없으면 새로 생성)

    Returns:
        MiscBranchAnalyzer 인스턴스
    """
    memory_dir = Path(memory_dir)

    if file_io is None:
        logs_dir = memory_dir.parent / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_io = FileIO(memory_dir=memory_dir, logs_dir=logs_dir)

    return MiscBranchAnalyzer(memory_dir=memory_dir, file_io=file_io)
