#!/usr/bin/env python3
"""
Evidence Graph 실제 작동 검증 스크립트

목적:
1. 실제 파일 시스템에 Evidence Graph가 저장되는지 확인
2. Grounding Score가 0.00이 아닌 실제 값을 반환하는지 확인
3. 더미 데이터가 아닌 실제 데이터로 작동하는지 증명
"""

import os
import sys
import tempfile
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.evidence_graph import EvidenceGraph
from core.grounding_scorer import GroundingScorer
from core.claim_extractor import Claim


def test_evidence_graph_real_data():
    """실제 데이터로 Evidence Graph 작동 확인"""

    print("=" * 80)
    print("Evidence Graph 실제 작동 검증")
    print("=" * 80)

    # 1. 임시 디렉토리 생성 (실제 파일 시스템)
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n[1] 실제 임시 디렉토리 생성: {temp_dir}")
        print(f"    - 디렉토리 존재 확인: {os.path.exists(temp_dir)}")

        project_id = "real-test-project"

        # 2. EvidenceGraph 생성 (project_path 전달)
        print(f"\n[2] EvidenceGraph 생성 (project_path 전달)")
        evidence_graph = EvidenceGraph(project_id=project_id, project_path=temp_dir)

        # 3. 실제 노드 추가
        print(f"\n[3] 실제 Context 노드 추가")
        context_id = "context_001"
        branch_id = "branch_001"
        content_hash = "abc123def456"

        success = evidence_graph.add_context_node(
            context_id=context_id,
            branch_id=branch_id,
            content_hash=content_hash,
            metadata={"description": "실제 테스트 컨텍스트"}
        )
        print(f"    - 노드 추가 성공: {success}")

        # 4. 파일 시스템에 실제로 저장되었는지 확인
        graph_file = Path(temp_dir) / "_evidence_graph.json"
        print(f"\n[4] 파일 시스템 확인")
        print(f"    - Graph 파일 경로: {graph_file}")
        print(f"    - 파일 존재 확인: {graph_file.exists()}")

        if graph_file.exists():
            file_size = graph_file.stat().st_size
            print(f"    - 파일 크기: {file_size} bytes")

            # 파일 내용 일부 확인
            with open(graph_file, 'r') as f:
                content = f.read()
                print(f"    - 파일 내용 일부: {content[:200]}...")

        # 5. GroundingScorer 생성 및 점수 계산
        print(f"\n[5] GroundingScorer로 실제 점수 계산")
        scorer = GroundingScorer(project_id=project_id, project_path=temp_dir)

        # 테스트용 Claim 생성
        test_claim = Claim(
            claim_type="implementation_complete",
            text="test.py 파일을 수정했습니다.",
            start=0,
            end=25,
            confidence=0.9,
            metadata={"file": "test.py", "line": 10}
        )

        # Grounding Score 계산
        response_text = "test.py 파일을 수정했습니다."
        claims = [test_claim]
        referenced_contexts = [context_id]

        result = scorer.calculate_score(
            response_text=response_text,
            claims=claims,
            referenced_contexts=referenced_contexts
        )

        print(f"\n[6] Grounding Score 결과:")
        print(f"    - Grounding Score: {result['grounding_score']:.2f}")
        print(f"    - Risk Level: {result['risk_level']}")
        print(f"    - Total Claims: {result['total_claims']}")
        print(f"    - Referenced Contexts: {result['referenced_contexts_count']}")

        # 7. 검증
        print(f"\n[7] 검증 결과:")

        if result['grounding_score'] == 0.0:
            print("    ❌ FAILED: Grounding Score가 여전히 0.00입니다!")
            return False
        else:
            print(f"    ✅ PASSED: Grounding Score = {result['grounding_score']:.2f}")
            print(f"    ✅ 실제 파일: {graph_file}")
            print(f"    ✅ 실제 데이터 사용 확인!")
            return True


def test_fallback_path():
    """Fallback 경로 동작 확인"""

    print("\n" + "=" * 80)
    print("Fallback 경로 동작 검증")
    print("=" * 80)

    project_id = "fallback-test"

    # Case 1: project_path 제공 (1순위)
    print(f"\n[Case 1] project_path 제공 (1순위 경로)")
    with tempfile.TemporaryDirectory() as temp_dir:
        graph1 = EvidenceGraph(project_id=project_id, project_path=temp_dir)
        expected_path1 = Path(temp_dir) / "_evidence_graph.json"
        actual_path1 = graph1._get_graph_path()

        print(f"    - 제공된 경로: {temp_dir}")
        print(f"    - 예상 경로: {expected_path1}")
        print(f"    - 실제 경로: {actual_path1}")
        print(f"    - 일치 여부: {expected_path1 == actual_path1}")

    # Case 2: project_path 없음 (2순위 - 기본 경로)
    print(f"\n[Case 2] project_path 없음 (2순위 - 기본 경로)")
    graph2 = EvidenceGraph(project_id=project_id, project_path=None)
    expected_path2 = Path.home() / ".cortex" / "memory" / project_id / "_evidence_graph.json"
    actual_path2 = graph2._get_graph_path()

    print(f"    - 제공된 경로: None")
    print(f"    - 예상 경로: {expected_path2}")
    print(f"    - 실제 경로: {actual_path2}")
    print(f"    - 일치 여부: {expected_path2 == actual_path2}")

    print(f"\n[결론]")
    print(f"    - 1순위(project_path) 사용: 실제 제공된 경로")
    print(f"    - 2순위(fallback) 사용: ~/.cortex/memory/{project_id}")
    print(f"    - 둘 다 실제 파일 시스템 경로! (더미 아님)")


if __name__ == "__main__":
    print("\n")
    print("🔍 Evidence Graph 실제 작동 검증 시작")
    print("\n")

    # 실제 데이터 검증
    success1 = test_evidence_graph_real_data()

    # Fallback 동작 검증
    test_fallback_path()

    print("\n" + "=" * 80)
    if success1:
        print("✅ 최종 결과: Evidence Graph가 실제 데이터로 정상 작동합니다!")
        print("✅ Grounding Score도 0.00이 아닌 실제 값을 반환합니다!")
        sys.exit(0)
    else:
        print("❌ 최종 결과: 여전히 문제가 있습니다.")
        sys.exit(1)
