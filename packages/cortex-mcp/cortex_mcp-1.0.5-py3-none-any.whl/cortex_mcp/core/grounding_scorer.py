"""
Grounding Score 계산 시스템

Cortex Phase 9: Hallucination Detection System
LLM 응답의 근거 밀도(Grounding Density)를 계산합니다.

핵심 공식:
Grounding Score = (참조된 contexts × 깊이 가중치) / 응답 내 주장 개수

점수 해석:
- 높음: 말 적고 근거 많음 (신뢰도 높음)
- 낮음: 말 많고 근거 없음 (할루시네이션 의심)
"""

from datetime import datetime
from typing import Dict, List, Optional

from .bayesian_updater import BayesianUpdater
from .claim_extractor import Claim
from .evidence_graph import EvidenceGraph, get_evidence_graph
from .reference_history import ReferenceHistory


class GroundingScorer:
    """
    Grounding Score 계산 클래스

    응답의 근거 밀도를 계산하여
    할루시네이션 가능성을 정량화합니다.

    Phase 1 통합: Bayesian Claim Confidence
    - 각 Claim의 posterior를 고려하여 스코어 조정
    - False Positive 감소
    """

    # 깊이별 가중치 설정 (Phase 9.3 개선: Exponential Decay)
    # Option A: 0.85^depth (수학적으로 자연스럽고, 프로젝트별 설정 가능)
    DEPTH_DECAY_FACTOR = 0.85  # 깊이마다 85%로 감소
    DEPTH_WEIGHT_MIN = 0.15  # 최소 가중치 (너무 낮은 값 방지)

    def __init__(
        self,
        project_id: str,
        project_path: str,
        reference_history: Optional[ReferenceHistory] = None,
        depth_decay_factor: float = 0.85,
        evidence_graph: Optional[EvidenceGraph] = None,  # MEDIUM #1: Evidence Graph 주입
    ):
        """
        Grounding Scorer 초기화

        Args:
            project_id: 프로젝트 식별자
            project_path: 프로젝트 경로 (필수)
            reference_history: Reference History 시스템 (선택적)
            depth_decay_factor: 깊이별 감소 계수 (기본: 0.85)
            evidence_graph: Evidence Graph 인스턴스 (선택적, 없으면 새로 생성)

        Raises:
            ValueError: project_path가 제공되지 않았을 때
        """
        if not project_path:
            raise ValueError(
                "project_path is required for GroundingScorer.\n"
                "GroundingScorer needs to know where Evidence Graph data is stored.\n"
                "Please provide the project root directory path."
            )

        self.project_id = project_id
        self.project_path = project_path

        # MEDIUM #1: Evidence Graph 캐시 동기화 개선
        # - 제공된 Evidence Graph 사용 (memory_manager와 동일 인스턴스 공유)
        # - 없으면 싱글톤 패턴 사용 (backward compatibility + performance)
        if evidence_graph is not None:
            self.evidence_graph = evidence_graph
        else:
            # PERFORMANCE: 싱글톤 패턴 사용 (~80ms 절감)
            self.evidence_graph = get_evidence_graph(project_id, project_path=project_path)

        self.depth_decay_factor = depth_decay_factor

        # Phase 1: Bayesian Updater 통합
        self.bayesian_updater = BayesianUpdater(
            project_id=project_id, reference_history=reference_history
        )

    def _calculate_depth_weight(self, depth: int) -> float:
        """
        깊이별 가중치 계산 (Exponential Decay)

        Args:
            depth: Context 깊이 (0=직접 참조, 1=1단계, 2=2단계, ...)

        Returns:
            가중치 (depth_decay_factor^depth, 최소 DEPTH_WEIGHT_MIN)
        """
        if depth == 0:
            return 1.0  # 직접 참조는 항상 1.0

        # Exponential decay: factor^depth
        weight = self.depth_decay_factor ** depth

        # 최소 가중치 적용
        return max(self.DEPTH_WEIGHT_MIN, weight)

    def calculate_score(
        self,
        response_text: str,
        claims: List[Claim],
        referenced_contexts: List[str],
        context_history: Optional[Dict] = None,
        claim_evidence_map: Optional[Dict[str, List[str]]] = None,  # 신규: Claim별 Evidence 매핑
    ) -> Dict:
        """
        Grounding Score 계산 (Phase 1: Bayesian Confidence 적용)

        Args:
            response_text: LLM 응답 텍스트
            claims: 추출된 Claim 목록
            referenced_contexts: 참조된 Context ID 목록 (전체 파일 리스트, 하위 호환)
            context_history: Context 이력 정보 (선택적)
            claim_evidence_map: Claim별 Evidence 매핑 (선택적, 신규)

        Returns:
            점수 및 상세 정보
        """
        # 성능 주장 분리 (정보 제공용 - 검증 점수에서 제외)
        impl_claims = [c for c in claims if c.claim_type != "performance_claim"]
        perf_claims = [c for c in claims if c.claim_type == "performance_claim"]

        # 기본 계산 (구현 주장만 사용)
        total_claims = len(impl_claims)
        total_perf_claims = len(perf_claims)
        total_contexts = len(referenced_contexts)

        import math

        # 신규: Claim별 Evidence 매핑 기반 검증 모드
        if claim_evidence_map is not None:
            # Claim별 검증 모드 (구현 주장만 검증)
            verified_claims = 0
            unverified_claim_ids = []

            for claim in impl_claims:
                claim_id = f"{claim.claim_type}:{claim.start}:{claim.end}"
                claim_evidences = claim_evidence_map.get(claim_id, [])

                # 이 Claim이 최소 1개 이상의 evidence를 가지고 있으면 검증 성공
                if claim_evidences:
                    verified_claims += 1
                else:
                    unverified_claim_ids.append(claim_id)

            # Claim별 검증률 계산
            if total_claims > 0:
                grounding_score = verified_claims / total_claims
            else:
                # BUG FIX: Claim이 없는 경우 (조사 보고서, 설명 등)
                # 검증 대상이 없으므로 1.0 반환 (검증 통과)
                grounding_score = 1.0

            # Sigmoid 정규화 (선택적)
            # grounding_score = 1.0 / (1.0 + math.exp(-5 * (grounding_score - 0.5)))

            return {
                "grounding_score": round(grounding_score, 3),
                "verified_claims": verified_claims,
                "total_claims": total_claims,
                "unverified_claim_ids": unverified_claim_ids,
                "performance_claims": {
                    "total": total_perf_claims,
                    "claims": [{"type": c.claim_type, "text": c.text} for c in perf_claims],
                },
                "mode": "claim_evidence_map",
                "timestamp": datetime.now().isoformat(),
            }

        # 기존: 전체 컨텍스트 기반 검증 (하위 호환)
        else:
            # 깊이별 Context 분석
            context_analysis = self._analyze_context_depth(referenced_contexts)

            # 가중치 적용 Context 수 (Exponential Decay 사용)
            weighted_contexts = sum(
                count * self._calculate_depth_weight(depth)
                for depth, count in context_analysis["by_depth"].items()
            )

            # Grounding Score 계산 (0.0-1.0 범위로 정규화)
            # CRITICAL FIX: weighted_contexts가 누적되면서 점수가 비정상적으로 높아지는 문제 해결
            # Sigmoid 정규화를 사용하여 항상 0.0-1.0 범위로 제한
            if total_claims > 0:
                # Context per Claim 비율
                context_per_claim = weighted_contexts / total_claims
                # Sigmoid 정규화: 1 / (1 + e^(-x))
                # x = 2 일 때 ~0.88, x = 1 일 때 ~0.73, x = 0 일 때 0.5
                grounding_score = 1.0 / (1.0 + math.exp(-context_per_claim))
            else:
                # BUG FIX: Claim이 없는 경우 (조사 보고서, 설명 등)
                # 검증 대상이 없으므로 1.0 반환 (검증 통과)
                grounding_score = 1.0

            # Phase 1: Bayesian Posterior 조정
            # 각 Claim의 posterior를 계산하여 평균을 구하고 grounding score에 반영
            if total_claims > 0 and impl_claims:
                bayesian_adjustment = self._calculate_bayesian_adjustment(
                    impl_claims, referenced_contexts, context_history
                )
                # Posterior 평균을 grounding score에 가중치로 적용
                adjusted_grounding_score = grounding_score * bayesian_adjustment["avg_posterior"]
            else:
                adjusted_grounding_score = grounding_score
                bayesian_adjustment = {"avg_posterior": 1.0, "claim_posteriors": [], "applied": False}

            # 정규화 (0-100 스케일) - adjusted_grounding_score는 이미 0.0-1.0 범위
            normalized_score = min(100, adjusted_grounding_score * 100)

            # 등급 계산
            grade = self._calculate_grade(normalized_score)

            # 상세 분석 (구현 주장만 사용)
            density_analysis = self._analyze_density(response_text, impl_claims, referenced_contexts)

            return {
                "grounding_score": round(grounding_score, 3),
                "adjusted_grounding_score": round(adjusted_grounding_score, 3),
                "normalized_score": round(normalized_score, 1),
                "grade": grade,
                "total_claims": total_claims,
                "total_contexts": total_contexts,
                "weighted_contexts": round(weighted_contexts, 2),
                "context_analysis": context_analysis,
                "density_analysis": density_analysis,
                "bayesian_adjustment": bayesian_adjustment,
                "interpretation": self._interpret_score(normalized_score, grade),
                "performance_claims": {
                    "total": total_perf_claims,
                    "claims": [{"type": c.claim_type, "text": c.text} for c in perf_claims],
                },
                "mode": "legacy",
                "timestamp": datetime.now().isoformat(),
            }

    def _calculate_bayesian_adjustment(
        self, claims: List[Claim], referenced_contexts: List[str], context_history: Optional[Dict]
    ) -> Dict:
        """
        Bayesian Posterior 기반 조정 계산

        Args:
            claims: Claim 목록
            referenced_contexts: 참조된 Context 목록
            context_history: Context 이력

        Returns:
            조정 정보
        """
        if not claims:
            return {"avg_posterior": 1.0, "claim_posteriors": [], "applied": False}

        posteriors = []

        for claim in claims:
            # 간단한 evidence 생성 (context 기반)
            evidence_list = [
                {"type": "context_match", "quality_score": 0.7}  # Context가 있으면 기본 0.7
                for _ in referenced_contexts
            ]

            # Bayesian posterior 계산
            bayesian_result = self.bayesian_updater.update_posterior(
                claim=claim, evidence_list=evidence_list, context_history=context_history
            )

            posteriors.append(
                {
                    "claim_text": claim.text,
                    "claim_type": claim.claim_type,
                    "posterior": bayesian_result.posterior,
                    "confidence_level": bayesian_result.confidence_level,
                }
            )

        avg_posterior = sum(p["posterior"] for p in posteriors) / len(posteriors)

        return {"avg_posterior": avg_posterior, "claim_posteriors": posteriors, "applied": True}

    def calculate_batch_scores(self, responses: List[Dict]) -> List[Dict]:
        """
        여러 응답에 대한 일괄 점수 계산

        Args:
            responses: 응답 정보 목록
                [{"text": str, "claims": List[Claim], "contexts": List[str]}]

        Returns:
            점수 목록
        """
        return [self.calculate_score(r["text"], r["claims"], r["contexts"]) for r in responses]

    def _analyze_context_depth(self, context_ids: List[str]) -> Dict:
        """
        Context 깊이 분석

        Args:
            context_ids: Context ID 목록

        Returns:
            깊이별 분석 결과
        """
        by_depth = {}
        context_details = []

        # [DEBUG] Evidence Graph의 모든 노드 ID 출력
        all_graph_nodes = list(self.evidence_graph.graph.nodes())
        print(f"[DEBUG] Evidence Graph 노드 수: {len(all_graph_nodes)}")
        if all_graph_nodes:
            print(f"[DEBUG] Evidence Graph 노드 샘플 (최대 5개): {all_graph_nodes[:5]}")

        # [DEBUG] Evidence Graph 상태 출력
        print(f"[DEBUG] grounding_scorer: Evidence Graph 상태")
        print(f"[DEBUG]   - 객체 ID: {id(self.evidence_graph)}")
        print(f"[DEBUG]   - 파일 경로: {self.evidence_graph._get_graph_path()}")
        print(f"[DEBUG]   - 노드 수: {len(self.evidence_graph.graph.nodes())}")

        # [DEBUG] 전달받은 context_ids 출력
        print(f"[DEBUG] referenced_contexts 개수: {len(context_ids)}")
        if context_ids:
            print(f"[DEBUG] referenced_contexts 샘플 (최대 5개): {context_ids[:5]}")

        matched_count = 0
        skipped_count = 0

        for context_id in context_ids:
            # Evidence Graph에서 Context 노드 확인
            if context_id not in self.evidence_graph.graph:
                # CRITICAL #4: Evidence Graph 기반 semantic depth 계산 (fallback 개선)
                # Evidence Graph에 노드가 없으면 파일 경로 깊이를 fallback으로 사용
                skipped_count += 1

                # Fallback: 파일 경로 깊이 사용
                try:
                    # context_id가 파일 경로 형식인지 확인
                    path_depth = len(Path(context_id).parts)
                    # 최대 depth=3으로 제한 (너무 깊으면 가중치가 과도하게 낮아짐)
                    depth = min(3, max(0, path_depth - 1))
                except Exception:
                    # 파일 경로가 아니면 depth=0 (기본값)
                    depth = 0

                if skipped_count <= 3:
                    print(f"[DEBUG] Evidence Graph 노드 없음 - fallback depth={depth} (경로 깊이): {context_id}")

                by_depth[depth] = by_depth.get(depth, 0) + 1

                context_details.append(
                    {
                        "context_id": context_id,
                        "depth": depth,
                        "chain_length": 1,  # 자기 자신만 (노드 없으므로)
                        "weight": self._calculate_depth_weight(depth),
                        "method": "path_fallback",  # fallback 사용 표시
                    }
                )
                continue

            matched_count += 1

            # CRITICAL #4: Evidence Graph 기반 semantic depth 계산
            # 연결된 증거 체인 깊이 계산 (get_evidence_chain 사용)
            chain = self.evidence_graph.get_evidence_chain(context_id, max_depth=3)
            depth = min(3, chain.get("chain_length", 0) - 1)  # 자기 자신 제외

            by_depth[depth] = by_depth.get(depth, 0) + 1

            context_details.append(
                {
                    "context_id": context_id,
                    "depth": depth,
                    "chain_length": chain.get("chain_length", 0),
                    "weight": self._calculate_depth_weight(depth),
                    "method": "evidence_graph",  # Evidence Graph 기반 계산
                }
            )

        # [DEBUG] 최종 결과 요약
        print(f"[DEBUG] 매칭 결과: {matched_count}개 매칭, {skipped_count}개 스킵")
        print(f"[DEBUG] by_depth: {by_depth}")

        return {"by_depth": by_depth, "details": context_details}

    def _analyze_density(self, text: str, claims: List[Claim], contexts: List[str]) -> Dict:
        """
        근거 밀도 상세 분석

        Args:
            text: 응답 텍스트
            claims: Claim 목록
            contexts: Context 목록

        Returns:
            밀도 분석 결과
        """
        # 텍스트 길이 분석
        text_length = len(text)
        word_count = len(text.split())
        line_count = len(text.split("\n"))

        # Claim 타입별 분포
        claim_distribution = {}
        for claim in claims:
            claim_type = claim.claim_type
            claim_distribution[claim_type] = claim_distribution.get(claim_type, 0) + 1

        # Context per Claim 비율
        if len(claims) > 0:
            context_per_claim = len(contexts) / len(claims)
        else:
            context_per_claim = len(contexts)

        # 밀도 지표
        if word_count > 0:
            claims_per_100_words = (len(claims) / word_count) * 100
            contexts_per_100_words = (len(contexts) / word_count) * 100
        else:
            claims_per_100_words = 0
            contexts_per_100_words = 0

        return {
            "text_length": text_length,
            "word_count": word_count,
            "line_count": line_count,
            "claim_distribution": claim_distribution,
            "context_per_claim": round(context_per_claim, 2),
            "claims_per_100_words": round(claims_per_100_words, 2),
            "contexts_per_100_words": round(contexts_per_100_words, 2),
        }

    def _calculate_grade(self, normalized_score: float) -> str:
        """
        점수를 등급으로 변환

        Args:
            normalized_score: 정규화된 점수 (0-100)

        Returns:
            등급 (A+, A, B, C, D, F)
        """
        if normalized_score >= 90:
            return "A+"
        elif normalized_score >= 80:
            return "A"
        elif normalized_score >= 70:
            return "B"
        elif normalized_score >= 60:
            return "C"
        elif normalized_score >= 50:
            return "D"
        else:
            return "F"

    def _interpret_score(self, normalized_score: float, grade: str) -> str:
        """
        점수 해석

        Args:
            normalized_score: 정규화된 점수
            grade: 등급

        Returns:
            해석 문구
        """
        interpretations = {
            "A+": "매우 우수한 근거 밀도. 모든 주장이 충분한 증거로 뒷받침됨.",
            "A": "우수한 근거 밀도. 대부분의 주장이 증거로 뒷받침됨.",
            "B": "양호한 근거 밀도. 주요 주장은 증거가 있으나 일부 보완 필요.",
            "C": "보통 수준의 근거 밀도. 근거 없는 주장이 일부 포함됨.",
            "D": "낮은 근거 밀도. 많은 주장이 근거 없이 작성됨.",
            "F": "매우 낮은 근거 밀도. 대부분의 주장이 근거 없음. 할루시네이션 의심.",
        }

        return interpretations.get(grade, "평가 불가")

    def compare_scores(self, scores: List[Dict]) -> Dict:
        """
        여러 응답의 점수 비교

        Args:
            scores: 점수 목록

        Returns:
            비교 분석 결과
        """
        if not scores:
            return {"error": "no_scores_provided"}

        normalized_scores = [s["normalized_score"] for s in scores]
        grounding_scores = [s["grounding_score"] for s in scores]

        return {
            "count": len(scores),
            "average_normalized": round(sum(normalized_scores) / len(normalized_scores), 1),
            "average_grounding": round(sum(grounding_scores) / len(grounding_scores), 3),
            "min_score": min(normalized_scores),
            "max_score": max(normalized_scores),
            "grade_distribution": self._get_grade_distribution(scores),
            "best_response_index": normalized_scores.index(max(normalized_scores)),
            "worst_response_index": normalized_scores.index(min(normalized_scores)),
        }

    def _get_grade_distribution(self, scores: List[Dict]) -> Dict:
        """
        등급 분포 계산

        Args:
            scores: 점수 목록

        Returns:
            등급별 개수
        """
        distribution = {}
        for score in scores:
            grade = score["grade"]
            distribution[grade] = distribution.get(grade, 0) + 1

        return distribution

    def get_score_trend(self, scores: List[Dict]) -> Dict:
        """
        점수 추이 분석

        Args:
            scores: 시간순 점수 목록

        Returns:
            추이 분석 결과
        """
        if len(scores) < 2:
            return {"error": "insufficient_data"}

        normalized_scores = [s["normalized_score"] for s in scores]

        # 추세 계산 (간단한 선형 회귀)
        n = len(normalized_scores)
        x = list(range(n))
        y = normalized_scores

        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        # 추세 판단
        if slope > 5:
            trend = "improving_significantly"
        elif slope > 1:
            trend = "improving"
        elif slope > -1:
            trend = "stable"
        elif slope > -5:
            trend = "declining"
        else:
            trend = "declining_significantly"

        return {
            "count": n,
            "slope": round(slope, 3),
            "trend": trend,
            "first_score": normalized_scores[0],
            "last_score": normalized_scores[-1],
            "change": round(normalized_scores[-1] - normalized_scores[0], 1),
            "average": round(sum(normalized_scores) / n, 1),
        }
