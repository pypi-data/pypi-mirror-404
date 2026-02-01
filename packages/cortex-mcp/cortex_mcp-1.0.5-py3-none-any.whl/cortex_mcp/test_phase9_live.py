"""
Phase 9 할루시네이션 검증 라이브 테스트

실제 프로젝트 환경에서 할루시네이션 검증이 작동하는지 확인
"""

import tempfile
from pathlib import Path
from core.memory_manager import MemoryManager


def test_scenario_1_real_file():
    """
    시나리오 1: 실제 파일을 언급 (True Positive)

    "memory_manager.py를 수정했습니다" → 실제 파일 존재
    기대: verified_claims > 0, grounding_score >= 0.5, risk_level = low
    """
    print("\n" + "="*80)
    print("시나리오 1: 실제 파일 언급 (True Positive)")
    print("="*80)

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_id = "live_test_tp"
        memory_dir = Path(tmp_dir) / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # 프로젝트 경로는 현재 cortex_mcp 디렉토리
        project_path = Path(__file__).parent

        mm = MemoryManager(project_id=project_id, memory_dir=memory_dir)

        # 초기화
        init_result = mm.initialize_context(
            project_id=project_id,
            project_path=str(project_path),
            scan_mode="NONE"
        )
        branch_id = init_result.get("branch_id")

        # 실제 존재하는 파일을 언급하는 응답
        result = mm.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content="memory_manager.py 파일을 수정하여 Evidence Graph 업데이트 기능을 추가했습니다. "
                    "claim_verifier.py도 함께 수정했습니다. 테스트 결과 모두 통과했습니다.",
            role="assistant",
            verified=False  # 자동 검증 트리거
        )

        # 결과 출력
        print(f"\n[결과 요약]")
        print(f"성공: {result['success']}")

        if "hallucination_check" in result:
            h = result["hallucination_check"]
            print(f"\n[Phase 9 검증 결과]")
            print(f"  - Total Claims: {h['total_claims']}")
            print(f"  - Verified Claims: {h['verified_claims']}")
            print(f"  - Grounding Score: {h['grounding_score']}")
            print(f"  - Risk Level: {h['risk_level']}")
            print(f"  - Contradictions: {h['contradictions']}")

            # 검증
            if h['verified_claims'] > 0:
                print(f"\n✓ PASS: {h['verified_claims']}개의 Claim이 검증되었습니다.")
            else:
                print(f"\n✗ FAIL: Claim이 검증되지 않았습니다.")

            if h['grounding_score'] >= 0.5:
                print(f"✓ PASS: Grounding Score {h['grounding_score']} >= 0.5")
            else:
                print(f"✗ FAIL: Grounding Score {h['grounding_score']} < 0.5")

            if h['risk_level'] == 'low':
                print(f"✓ PASS: Risk Level = {h['risk_level']}")
            else:
                print(f"✗ FAIL: Risk Level = {h['risk_level']} (expected: low)")

        return result


def test_scenario_2_hallucination():
    """
    시나리오 2: 존재하지 않는 파일 언급 (할루시네이션)

    "fake_module.py를 구현했습니다" → 파일 존재하지 않음
    기대: verified_claims = 0, grounding_score < 0.3, risk_level = critical/high
    """
    print("\n" + "="*80)
    print("시나리오 2: 존재하지 않는 파일 언급 (할루시네이션)")
    print("="*80)

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_id = "live_test_tn"
        memory_dir = Path(tmp_dir) / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # 프로젝트 경로는 현재 cortex_mcp 디렉토리
        project_path = Path(__file__).parent

        mm = MemoryManager(project_id=project_id, memory_dir=memory_dir)

        # 초기화
        init_result = mm.initialize_context(
            project_id=project_id,
            project_path=str(project_path),
            scan_mode="NONE"
        )
        branch_id = init_result.get("branch_id")

        # 존재하지 않는 파일을 언급하는 응답 (할루시네이션)
        result = mm.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content="fake_hallucination_module.py를 새로 구현했습니다. "
                    "nonexistent_utils.py도 함께 작성했습니다. "
                    "모든 기능이 정상 작동합니다.",
            role="assistant",
            verified=False  # 자동 검증 트리거
        )

        # 결과 출력
        print(f"\n[결과 요약]")
        print(f"성공: {result['success']}")

        if "hallucination_check" in result:
            h = result["hallucination_check"]
            print(f"\n[Phase 9 검증 결과]")
            print(f"  - Total Claims: {h['total_claims']}")
            print(f"  - Verified Claims: {h['verified_claims']}")
            print(f"  - Grounding Score: {h['grounding_score']}")
            print(f"  - Risk Level: {h['risk_level']}")
            print(f"  - Contradictions: {h['contradictions']}")

            # 검증
            if h['verified_claims'] == 0:
                print(f"\n✓ PASS: Claim이 검증되지 않았습니다 (할루시네이션 감지)")
            else:
                print(f"\n✗ FAIL: {h['verified_claims']}개의 Claim이 잘못 검증되었습니다.")

            if h['grounding_score'] < 0.3:
                print(f"✓ PASS: Grounding Score {h['grounding_score']} < 0.3 (할루시네이션)")
            else:
                print(f"✗ FAIL: Grounding Score {h['grounding_score']} >= 0.3")

            if h['risk_level'] in ['high', 'critical']:
                print(f"✓ PASS: Risk Level = {h['risk_level']} (할루시네이션 경고)")
            else:
                print(f"✗ FAIL: Risk Level = {h['risk_level']} (expected: high/critical)")

        return result


def test_scenario_3_mixed():
    """
    시나리오 3: 진짜와 가짜 파일 혼합

    "memory_manager.py 수정 + fake.py 추가" → 혼합
    기대: 부분 검증, grounding_score 중간값, risk_level 조정됨
    """
    print("\n" + "="*80)
    print("시나리오 3: 진짜 + 가짜 파일 혼합")
    print("="*80)

    with tempfile.TemporaryDirectory() as tmp_dir:
        project_id = "live_test_mixed"
        memory_dir = Path(tmp_dir) / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # 프로젝트 경로는 현재 cortex_mcp 디렉토리
        project_path = Path(__file__).parent

        mm = MemoryManager(project_id=project_id, memory_dir=memory_dir)

        # 초기화
        init_result = mm.initialize_context(
            project_id=project_id,
            project_path=str(project_path),
            scan_mode="NONE"
        )
        branch_id = init_result.get("branch_id")

        # 실제 파일 + 가짜 파일 혼합
        result = mm.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content="memory_manager.py 파일을 수정했습니다. "
                    "또한 brand_new_feature.py를 새로 추가했습니다. "
                    "claim_verifier.py도 업데이트했습니다.",
            role="assistant",
            verified=False
        )

        # 결과 출력
        print(f"\n[결과 요약]")
        print(f"성공: {result['success']}")

        if "hallucination_check" in result:
            h = result["hallucination_check"]
            print(f"\n[Phase 9 검증 결과]")
            print(f"  - Total Claims: {h['total_claims']}")
            print(f"  - Verified Claims: {h['verified_claims']}")
            print(f"  - Grounding Score: {h['grounding_score']}")
            print(f"  - Risk Level: {h['risk_level']}")
            print(f"  - Contradictions: {h['contradictions']}")

            print(f"\n[분석]")
            print(f"  혼합 시나리오: 실제 파일(memory_manager.py, claim_verifier.py) + "
                  f"가짜 파일(brand_new_feature.py)")
            print(f"  → Grounding Score는 부분적으로 검증됨을 반영해야 함")

        return result


if __name__ == "__main__":
    print("\n" + "#"*80)
    print("# Phase 9 할루시네이션 검증 시스템 라이브 테스트")
    print("#"*80)

    # 시나리오 1: 실제 파일
    result1 = test_scenario_1_real_file()

    # 시나리오 2: 할루시네이션
    result2 = test_scenario_2_hallucination()

    # 시나리오 3: 혼합
    result3 = test_scenario_3_mixed()

    print("\n" + "#"*80)
    print("# 테스트 완료")
    print("#"*80)
