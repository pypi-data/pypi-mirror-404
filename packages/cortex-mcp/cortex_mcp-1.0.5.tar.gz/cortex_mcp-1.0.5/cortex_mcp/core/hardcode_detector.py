"""
Phase 9.5.1: Hardcode Detector

답변.md 문제 해결: 테스트에서 하드코딩된 값 감지

감지 패턴:
- Line 113: if compression_ratio < 70: compression_ratio = 97.8 # benchmark
- assert True
- return True # hardcoded
- if test_fails: result = 100 # force pass
"""

import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# ====================================================================
# 핵심 로직: Hardcode Detection Patterns
# ====================================================================

@dataclass
class HardcodePattern:
    """하드코딩 패턴 정의"""
    name: str
    regex: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str


# 하드코딩 패턴 목록 (answer.md 문제 기반)
HARDCODE_PATTERNS = [
    HardcodePattern(
        name="benchmark_value",
        regex=r"=\s*[\d.]+\s*#.*(?:benchmark|known|hardcoded|fixed)",
        severity="CRITICAL",
        description="벤치마크 값 하드코딩 (예: = 97.8 # benchmark)"
    ),
    HardcodePattern(
        name="conditional_override",
        regex=r"if\s+.*:\s*\w+\s*=\s*[\d.]+(?:\s*#.*)?$",
        severity="HIGH",
        description="조건문 내 값 강제 설정 (예: if fail: score = 100)"
    ),
    HardcodePattern(
        name="dummy_assert",
        regex=r"assert\s+True\s*(?:#.*)?$",
        severity="HIGH",
        description="항상 참인 assert (예: assert True)"
    ),
    HardcodePattern(
        name="hardcoded_return",
        regex=r"return\s+(?:True|False|\d+)\s*#.*(?:hardcoded|force|fake)",
        severity="HIGH",
        description="주석에 하드코딩 표시한 return (예: return True # force pass)"
    ),
    HardcodePattern(
        name="mock_data",
        regex=r"(?:mock|fake|dummy)_(?:data|result|value)\s*=",
        severity="HIGH",  # BUG FIX (Phase 9.5): MEDIUM → HIGH (더미 데이터는 심각한 문제)
        description="Mock 데이터 정의 (예: mock_data = ...)"
    ),
    HardcodePattern(
        name="todo_comment",
        regex=r"#\s*(?:TODO|FIXME|XXX|HACK):",
        severity="MEDIUM",
        description="TODO/FIXME 주석 (예: # TODO: 작업 필요)"
    ),
    HardcodePattern(
        name="test_variable",
        regex=r"test_\w+\s*=\s*[\d.]+",
        severity="MEDIUM",
        description="테스트 변수 하드코딩 (예: test_value = 999)"
    ),
    HardcodePattern(
        name="skip_test",
        regex=r"@pytest\.mark\.skip|@unittest\.skip",
        severity="LOW",
        description="테스트 스킵 데코레이터"
    ),
]


@dataclass
class HardcodeDetection:
    """하드코딩 감지 결과"""
    file_path: str
    line_number: int
    line_content: str
    pattern_name: str
    severity: str
    description: str
    confidence: float  # 0.0 - 1.0


class HardcodeDetector:
    """
    테스트 파일에서 하드코딩된 값 감지

    answer.md 문제 해결:
    - Line 113: compression_ratio = 97.8 # benchmark 감지
    - 더미 assert, return 감지
    - Mock 데이터 감지
    """

    def __init__(self, patterns: List[HardcodePattern] = None):
        self.patterns = patterns or HARDCODE_PATTERNS

        # 패턴별 컴파일된 regex 캐시
        self._compiled_patterns = {
            p.name: re.compile(p.regex, re.IGNORECASE | re.MULTILINE)
            for p in self.patterns
        }

    def detect_in_file(self, file_path: str) -> List[HardcodeDetection]:
        """
        파일에서 하드코딩 패턴 감지

        Args:
            file_path: 검사할 파일 경로

        Returns:
            감지된 하드코딩 목록
        """
        path = Path(file_path)

        # 파일 존재 확인
        if not path.exists():
            return []

        # 파일 읽기
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            return []

        detections = []

        # 각 라인 검사
        for line_num, line_content in enumerate(lines, start=1):
            line_stripped = line_content.strip()

            # 빈 라인, 주석만 있는 라인 스킵
            if not line_stripped or line_stripped.startswith('#'):
                continue

            # 각 패턴 매칭
            for pattern in self.patterns:
                regex = self._compiled_patterns[pattern.name]

                if regex.search(line_stripped):
                    # 신뢰도 계산
                    confidence = self._calculate_confidence(
                        line_stripped, pattern
                    )

                    detection = HardcodeDetection(
                        file_path=str(path),
                        line_number=line_num,
                        line_content=line_stripped,
                        pattern_name=pattern.name,
                        severity=pattern.severity,
                        description=pattern.description,
                        confidence=confidence,
                    )

                    detections.append(detection)

        return detections

    def detect_in_response(self, response_text: str) -> List[HardcodeDetection]:
        """
        AI 응답 텍스트에서 하드코딩 언급 감지

        Args:
            response_text: 검사할 응답 텍스트

        Returns:
            감지된 하드코딩 목록
        """
        detections = []

        # 응답을 줄별로 분리
        lines = response_text.split('\n')

        for line_num, line_content in enumerate(lines, start=1):
            line_stripped = line_content.strip()

            if not line_stripped:
                continue

            # 각 패턴 매칭
            for pattern in self.patterns:
                regex = self._compiled_patterns[pattern.name]

                if regex.search(line_stripped):
                    confidence = self._calculate_confidence(
                        line_stripped, pattern
                    )

                    detection = HardcodeDetection(
                        file_path="<response_text>",
                        line_number=line_num,
                        line_content=line_stripped,
                        pattern_name=pattern.name,
                        severity=pattern.severity,
                        description=pattern.description,
                        confidence=confidence,
                    )

                    detections.append(detection)

        return detections

    def _calculate_confidence(
        self, line: str, pattern: HardcodePattern
    ) -> float:
        """
        하드코딩 감지 신뢰도 계산

        신뢰도 규칙:
        - 주석에 "benchmark", "hardcoded", "fake" 있으면 +0.3
        - 조건문 내부에 있으면 +0.2
        - 테스트 파일이면 +0.2

        Args:
            line: 검사할 라인
            pattern: 매칭된 패턴

        Returns:
            신뢰도 (0.0 - 1.0)
        """
        base_confidence = 0.5

        # 주석에 하드코딩 키워드 있으면 확실
        hardcode_keywords = [
            "benchmark", "hardcoded", "fake", "mock", "dummy",
            "force", "override", "known"
        ]

        line_lower = line.lower()

        # 주석 추출
        if '#' in line:
            comment = line.split('#', 1)[1]

            for keyword in hardcode_keywords:
                if keyword in comment.lower():
                    base_confidence += 0.3
                    break

        # 조건문 내부 (if fail: value = 100)
        if pattern.name == "conditional_override":
            # 조건문 체크
            if_conditions = [
                r"if\s+\w+\s*<",  # if value < threshold
                r"if\s+not\s+\w+",  # if not success
                r"if\s+\w+\s*==\s*(?:False|None|0)",  # if failed == False
            ]

            for cond_regex in if_conditions:
                if re.search(cond_regex, line):
                    base_confidence += 0.2
                    break

        # assert True (명백한 더미)
        if pattern.name == "dummy_assert":
            base_confidence = 0.9

        # 최대 1.0으로 제한
        return min(base_confidence, 1.0)

    def analyze_file_batch(
        self, file_paths: List[str]
    ) -> Dict[str, List[HardcodeDetection]]:
        """
        여러 파일 일괄 검사

        Args:
            file_paths: 검사할 파일 경로 목록

        Returns:
            파일별 감지 결과
        """
        results = {}

        for file_path in file_paths:
            detections = self.detect_in_file(file_path)

            if detections:
                results[file_path] = detections

        return results

    def get_summary(
        self, detections: List[HardcodeDetection]
    ) -> Dict[str, Any]:
        """
        감지 결과 요약 통계

        Args:
            detections: 감지 결과 목록

        Returns:
            요약 통계
        """
        if not detections:
            return {
                "total_count": 0,
                "by_severity": {},
                "by_pattern": {},
                "high_confidence_count": 0,
            }

        # Severity별 집계
        by_severity = {}
        for d in detections:
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1

        # 패턴별 집계
        by_pattern = {}
        for d in detections:
            by_pattern[d.pattern_name] = by_pattern.get(d.pattern_name, 0) + 1

        # 고신뢰도 (>= 0.8) 개수
        high_confidence_count = sum(
            1 for d in detections if d.confidence >= 0.8
        )

        return {
            "total_count": len(detections),
            "by_severity": by_severity,
            "by_pattern": by_pattern,
            "high_confidence_count": high_confidence_count,
        }

    def filter_by_severity(
        self, detections: List[HardcodeDetection], min_severity: str
    ) -> List[HardcodeDetection]:
        """
        Severity 기준으로 필터링

        Args:
            detections: 감지 결과 목록
            min_severity: 최소 심각도 (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            필터링된 결과
        """
        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        if min_severity not in severity_order:
            return detections

        min_level = severity_order.index(min_severity)

        filtered = [
            d for d in detections
            if severity_order.index(d.severity) <= min_level
        ]

        return filtered


# ====================================================================
# 유틸리티 함수
# ====================================================================

def detect_hardcoded_tests(
    test_directory: str,
    min_severity: str = "HIGH"
) -> Dict[str, List[HardcodeDetection]]:
    """
    테스트 디렉토리 전체 스캔

    Args:
        test_directory: 테스트 디렉토리 경로
        min_severity: 최소 심각도

    Returns:
        파일별 감지 결과
    """
    detector = HardcodeDetector()

    # test_*.py 파일 찾기
    test_dir = Path(test_directory)

    if not test_dir.exists():
        return {}

    test_files = list(test_dir.rglob("test_*.py"))

    # 일괄 검사
    all_results = detector.analyze_file_batch(
        [str(f) for f in test_files]
    )

    # Severity 필터링
    filtered_results = {}

    for file_path, detections in all_results.items():
        filtered = detector.filter_by_severity(detections, min_severity)

        if filtered:
            filtered_results[file_path] = filtered

    return filtered_results


def print_detection_report(
    detections: Dict[str, List[HardcodeDetection]]
):
    """
    감지 결과 보고서 출력

    Args:
        detections: 파일별 감지 결과
    """
    if not detections:
        print("[HARDCODE_DETECTOR] No hardcoded patterns detected.")
        return

    print("[HARDCODE_DETECTOR] Hardcoded Patterns Detected:")
    print("=" * 80)

    for file_path, det_list in detections.items():
        print(f"\nFile: {file_path}")
        print("-" * 80)

        for detection in det_list:
            print(f"  Line {detection.line_number}: [{detection.severity}] "
                  f"{detection.pattern_name} (confidence: {detection.confidence:.2f})")
            print(f"    → {detection.line_content}")
            print(f"    → {detection.description}")
            print()

    # 전체 요약
    all_detections = []
    for det_list in detections.values():
        all_detections.extend(det_list)

    detector = HardcodeDetector()
    summary = detector.get_summary(all_detections)

    print("=" * 80)
    print("Summary:")
    print(f"  Total: {summary['total_count']}")
    print(f"  High Confidence (>= 0.8): {summary['high_confidence_count']}")
    print(f"  By Severity: {summary['by_severity']}")
    print(f"  By Pattern: {summary['by_pattern']}")
    print("=" * 80)
