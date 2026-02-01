"""
Fractal Dimension + Self-Similarity Analyzer

Enhancement #1: Evidence Graph의 프랙탈 차원 분석
- Box-counting dimension으로 그래프 복잡도 측정
- Self-similarity score로 반복 패턴 감지

이론적 배경:
- Mandelbrot의 프랙탈 기하학
- 건강한 그래프는 적절한 복잡도 (dimension 1.5~2.0)
- 과도하게 복잡한 그래프 (dimension > 2.5)는 hallucination 의심
"""

import math
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FractalAnalysisResult:
    """프랙탈 분석 결과"""
    dimension: float  # Box-counting dimension
    health_status: str  # "healthy", "complex", "sparse"
    self_similarity_score: float  # 자기유사성 점수 (0.0 ~ 1.0)
    is_fractal_loop_detected: bool  # 프랙탈 할루시네이션 루프 감지 여부
    details: Dict  # 상세 분석 정보


class FractalAnalyzer:
    """
    Evidence Graph의 프랙탈 분석기

    주요 기능:
    1. Box-counting dimension 계산
    2. 그래프 건강도 판정
    3. Self-similarity 기반 반복 패턴 감지
    """

    # 기본 설정
    DEFAULT_CONFIG = {
        "healthy_dimension_range": (1.5, 2.0),
        "hallucination_threshold": 2.5,
        "sparse_threshold": 1.2,
        "self_similarity_threshold": 0.7,
        "min_nodes_for_analysis": 5,
        "box_sizes": [1, 2, 4, 8, 16, 32],  # Box-counting용 크기
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Fractal Analyzer 초기화

        Args:
            config: 설정 딕셔너리 (None이면 기본값 사용)
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._pattern_history: List[Dict] = []
        self._embeddings_cache: Dict[str, np.ndarray] = {}

    def analyze_graph(
        self,
        adjacency_matrix: np.ndarray,
        node_positions: Optional[np.ndarray] = None
    ) -> FractalAnalysisResult:
        """
        Evidence Graph의 프랙탈 차원 분석

        Args:
            adjacency_matrix: 그래프 인접 행렬 (N x N)
            node_positions: 노드 위치 (N x 2), None이면 자동 생성

        Returns:
            FractalAnalysisResult: 분석 결과
        """
        n_nodes = adjacency_matrix.shape[0]

        # 노드 수가 부족하면 분석 불가
        if n_nodes < self.config["min_nodes_for_analysis"]:
            return FractalAnalysisResult(
                dimension=0.0,
                health_status="insufficient_data",
                self_similarity_score=0.0,
                is_fractal_loop_detected=False,
                details={"reason": f"노드 수 부족: {n_nodes} < {self.config['min_nodes_for_analysis']}"}
            )

        # 노드 위치가 없으면 spring layout으로 생성
        if node_positions is None:
            node_positions = self._generate_positions(adjacency_matrix)

        # Box-counting dimension 계산
        dimension = self._calculate_box_counting_dimension(
            adjacency_matrix, node_positions
        )

        # 건강도 판정
        health_status = self._determine_health_status(dimension)

        # Self-similarity score 계산
        self_sim_score = self._calculate_self_similarity(adjacency_matrix)

        # 프랙탈 루프 감지
        is_loop = (
            self_sim_score >= self.config["self_similarity_threshold"] and
            dimension > self.config["hallucination_threshold"]
        )

        logger.info(
            f"[FRACTAL] dimension={dimension:.3f}, "
            f"health={health_status}, self_sim={self_sim_score:.3f}"
        )

        return FractalAnalysisResult(
            dimension=dimension,
            health_status=health_status,
            self_similarity_score=self_sim_score,
            is_fractal_loop_detected=is_loop,
            details={
                "n_nodes": n_nodes,
                "n_edges": int(np.sum(adjacency_matrix) / 2),
                "healthy_range": self.config["healthy_dimension_range"],
                "thresholds": {
                    "hallucination": self.config["hallucination_threshold"],
                    "sparse": self.config["sparse_threshold"],
                }
            }
        )

    def _generate_positions(self, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Spring layout 알고리즘으로 노드 위치 생성

        Fruchterman-Reingold 알고리즘 간소화 버전
        """
        n = adj_matrix.shape[0]
        if n == 0:
            return np.array([])

        # 초기 위치: 원형 배치
        positions = np.zeros((n, 2))
        for i in range(n):
            angle = 2 * math.pi * i / n
            positions[i] = [math.cos(angle), math.sin(angle)]

        # Spring iteration (간소화)
        k = 1.0 / math.sqrt(n)  # 최적 거리
        iterations = 50

        for _ in range(iterations):
            # 척력 계산
            displacement = np.zeros((n, 2))
            for i in range(n):
                for j in range(n):
                    if i != j:
                        delta = positions[i] - positions[j]
                        dist = max(np.linalg.norm(delta), 0.01)
                        displacement[i] += (delta / dist) * (k * k / dist)

            # 인력 계산 (연결된 노드들)
            for i in range(n):
                for j in range(i + 1, n):
                    if adj_matrix[i, j] > 0:
                        delta = positions[j] - positions[i]
                        dist = max(np.linalg.norm(delta), 0.01)
                        force = (delta / dist) * (dist * dist / k)
                        displacement[i] += force
                        displacement[j] -= force

            # 위치 업데이트 (temperature 감소)
            temp = 0.1 * (1 - _ / iterations)
            positions += displacement * temp

        # 정규화 (0~1 범위)
        min_pos = positions.min(axis=0)
        max_pos = positions.max(axis=0)
        range_pos = max_pos - min_pos
        range_pos[range_pos == 0] = 1  # division by zero 방지
        positions = (positions - min_pos) / range_pos

        return positions

    def _calculate_box_counting_dimension(
        self,
        adj_matrix: np.ndarray,
        positions: np.ndarray
    ) -> float:
        """
        Box-counting 방법으로 프랙탈 차원 계산

        D = lim(ε→0) [log(N(ε)) / log(1/ε)]
        """
        if len(positions) == 0:
            return 0.0

        box_sizes = self.config["box_sizes"]
        box_counts = []

        for box_size in box_sizes:
            # 그리드 크기 계산
            grid_size = 1.0 / box_size

            # 각 노드가 속하는 박스 계산
            boxes = set()
            for pos in positions:
                box_x = int(pos[0] / grid_size) if grid_size > 0 else 0
                box_y = int(pos[1] / grid_size) if grid_size > 0 else 0
                boxes.add((box_x, box_y))

            # 엣지가 지나는 박스도 포함
            n = adj_matrix.shape[0]
            for i in range(n):
                for j in range(i + 1, n):
                    if adj_matrix[i, j] > 0:
                        # 두 노드 사이의 선분이 지나는 박스들
                        edge_boxes = self._get_edge_boxes(
                            positions[i], positions[j], grid_size
                        )
                        boxes.update(edge_boxes)

            box_counts.append(len(boxes))

        # 선형 회귀로 기울기(차원) 계산
        if len(box_counts) < 2:
            return 0.0

        log_sizes = [math.log(1.0 / s) for s in box_sizes if s > 0]
        log_counts = [math.log(max(c, 1)) for c in box_counts]

        if len(log_sizes) != len(log_counts):
            return 0.0

        # 최소자승법
        x = np.array(log_sizes)
        y = np.array(log_counts)
        n = len(x)

        if n < 2:
            return 0.0

        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_x2 = np.sum(x * x)

        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0

        dimension = (n * sum_xy - sum_x * sum_y) / denominator

        return max(0.0, min(3.0, dimension))  # 0~3 범위로 클리핑

    def _get_edge_boxes(
        self,
        pos1: np.ndarray,
        pos2: np.ndarray,
        grid_size: float
    ) -> set:
        """두 노드를 연결하는 엣지가 지나는 박스들 계산"""
        if grid_size <= 0:
            return set()

        boxes = set()

        # 선분을 여러 점으로 샘플링
        n_samples = max(2, int(np.linalg.norm(pos2 - pos1) / grid_size) + 1)
        for t in np.linspace(0, 1, n_samples):
            point = pos1 + t * (pos2 - pos1)
            box_x = int(point[0] / grid_size)
            box_y = int(point[1] / grid_size)
            boxes.add((box_x, box_y))

        return boxes

    def _determine_health_status(self, dimension: float) -> str:
        """
        프랙탈 차원으로 그래프 건강도 판정

        Returns:
            "healthy": 건강한 그래프 (dimension 1.5~2.0)
            "complex": 과도하게 복잡 (hallucination 의심)
            "sparse": 너무 단순 (증거 부족)
        """
        low, high = self.config["healthy_dimension_range"]

        if low <= dimension <= high:
            return "healthy"
        elif dimension > self.config["hallucination_threshold"]:
            return "complex"
        elif dimension < self.config["sparse_threshold"]:
            return "sparse"
        else:
            # 경계 영역
            if dimension < low:
                return "sparse"
            else:
                return "complex"

    def _calculate_self_similarity(self, adj_matrix: np.ndarray) -> float:
        """
        그래프의 자기유사성 점수 계산

        서브그래프들 간의 구조적 유사성 측정
        """
        n = adj_matrix.shape[0]
        if n < 6:  # 최소 2개의 서브그래프 필요
            return 0.0

        # 그래프를 절반으로 나눠 비교
        mid = n // 2
        subgraph1 = adj_matrix[:mid, :mid]
        subgraph2 = adj_matrix[mid:, mid:]

        # 구조적 특성 비교
        features1 = self._extract_graph_features(subgraph1)
        features2 = self._extract_graph_features(subgraph2)

        if features1 is None or features2 is None:
            return 0.0

        # 코사인 유사도
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)

        if norm1 * norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(max(0.0, min(1.0, similarity)))

    def _extract_graph_features(self, adj_matrix: np.ndarray) -> Optional[np.ndarray]:
        """그래프 구조적 특성 추출"""
        if adj_matrix.shape[0] == 0:
            return None

        n = adj_matrix.shape[0]

        # 특성 벡터
        features = []

        # 1. 평균 차수
        degrees = np.sum(adj_matrix, axis=1)
        features.append(np.mean(degrees) / max(n, 1))

        # 2. 차수 분산
        features.append(np.var(degrees) / max(n, 1))

        # 3. 밀도
        max_edges = n * (n - 1) / 2
        n_edges = np.sum(adj_matrix) / 2
        features.append(n_edges / max(max_edges, 1))

        # 4. 삼각형 수 (clustering 지표)
        triangles = 0
        for i in range(n):
            for j in range(i + 1, n):
                if adj_matrix[i, j]:
                    for k in range(j + 1, n):
                        if adj_matrix[i, k] and adj_matrix[j, k]:
                            triangles += 1
        max_triangles = n * (n - 1) * (n - 2) / 6
        features.append(triangles / max(max_triangles, 1))

        return np.array(features)

    def track_pattern(self, pattern_embedding: np.ndarray, pattern_id: str):
        """
        패턴 이력 추적 (STEP 9 연동)

        Args:
            pattern_embedding: 패턴 임베딩 벡터
            pattern_id: 패턴 식별자
        """
        self._pattern_history.append({
            "id": pattern_id,
            "embedding": pattern_embedding,
        })

        # 최대 100개 유지
        if len(self._pattern_history) > 100:
            self._pattern_history = self._pattern_history[-100:]

    def detect_fractal_loop(self) -> Tuple[bool, float]:
        """
        패턴 이력에서 프랙탈 루프 감지

        Returns:
            (is_loop_detected, similarity_score)
        """
        if len(self._pattern_history) < 3:
            return False, 0.0

        # 최근 패턴들 간의 유사도 계산
        recent = self._pattern_history[-10:]  # 최근 10개
        similarities = []

        for i in range(len(recent) - 1):
            for j in range(i + 1, len(recent)):
                emb1 = recent[i]["embedding"]
                emb2 = recent[j]["embedding"]

                # 코사인 유사도
                dot = np.dot(emb1, emb2)
                norm = np.linalg.norm(emb1) * np.linalg.norm(emb2)
                if norm > 0:
                    similarities.append(dot / norm)

        if not similarities:
            return False, 0.0

        avg_similarity = float(np.mean(similarities))
        is_loop = avg_similarity >= self.config["self_similarity_threshold"]

        if is_loop:
            logger.warning(
                f"[FRACTAL] 프랙탈 루프 감지! "
                f"self_similarity={avg_similarity:.3f}"
            )

        return is_loop, avg_similarity

    def get_hallucination_risk_score(
        self,
        analysis_result: FractalAnalysisResult
    ) -> float:
        """
        프랙탈 분석 결과를 할루시네이션 위험 점수로 변환

        Returns:
            0.0 ~ 1.0 (높을수록 위험)
        """
        if analysis_result.health_status == "insufficient_data":
            return 0.5  # 데이터 부족 시 중립

        risk = 0.0

        # 1. 차원 기반 위험도
        dim = analysis_result.dimension
        low, high = self.config["healthy_dimension_range"]

        if dim > high:
            # 복잡할수록 위험
            risk += min(1.0, (dim - high) / (self.config["hallucination_threshold"] - high))
        elif dim < low:
            # 단순할수록 위험 (증거 부족)
            risk += min(1.0, (low - dim) / (low - self.config["sparse_threshold"]))

        # 2. Self-similarity 기반 위험도
        if analysis_result.self_similarity_score > 0.5:
            risk += 0.3 * analysis_result.self_similarity_score

        # 3. 프랙탈 루프 감지 시 추가 위험
        if analysis_result.is_fractal_loop_detected:
            risk += 0.3

        return min(1.0, risk)


# 싱글톤 인스턴스
_fractal_analyzer: Optional[FractalAnalyzer] = None


def get_fractal_analyzer(config: Optional[Dict] = None) -> FractalAnalyzer:
    """Fractal Analyzer 싱글톤 반환"""
    global _fractal_analyzer
    if _fractal_analyzer is None:
        _fractal_analyzer = FractalAnalyzer(config)
    return _fractal_analyzer
