"""
CRITICAL #3: Phase 9 초기화 에러 핸들링 테스트

memory_manager.py의 Phase 9 컴포넌트 초기화 실패 시
graceful degradation을 검증합니다.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock
from core.memory_manager import MemoryManager


def test_all_components_success():
    """모든 Phase 9 컴포넌트 정상 초기화"""
    print("\n[TEST 1] 모든 컴포넌트 정상 초기화")

    test_project_id = "test_init_success"
    mm = MemoryManager(project_id=test_project_id)
    mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

    # 모든 컴포넌트가 None이 아님
    assert mm.claim_extractor is not None, "claim_extractor가 None입니다"
    assert mm.claim_verifier is not None, "claim_verifier가 None입니다"
    assert mm.fuzzy_analyzer is not None, "fuzzy_analyzer가 None입니다"
    assert mm.contradiction_detector is not None, "contradiction_detector가 None입니다"
    assert mm.grounding_scorer is not None, "grounding_scorer가 None입니다"

    # Phase 9 활성화 확인
    assert mm.hallucination_detection_available is True, "Phase 9가 활성화되지 않았습니다"

    print("  ✅ PASS: 모든 컴포넌트 정상 초기화됨")
    print(f"  - hallucination_detection_available: {mm.hallucination_detection_available}")


def test_claim_extractor_failure():
    """ClaimExtractor 초기화 실패 시 graceful degradation"""
    print("\n[TEST 2] ClaimExtractor 초기화 실패")

    test_project_id = "test_claim_extractor_fail"

    with patch("core.memory_manager.ClaimExtractor") as MockCE:
        # ClaimExtractor 초기화 시 예외 발생
        MockCE.side_effect = ImportError("ClaimExtractor 모듈을 찾을 수 없습니다")

        mm = MemoryManager(project_id=test_project_id)
        mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

        # ClaimExtractor만 None
        assert mm.claim_extractor is None, "claim_extractor가 None이 아닙니다"

        # 나머지 컴포넌트는 정상
        # (단, ClaimExtractor가 필수이므로 Phase 9 비활성화될 수 있음)

        # 핵심 컴포넌트 중 하나라도 실패하면 Phase 9 비활성화
        assert mm.hallucination_detection_available is False, "Phase 9가 비활성화되지 않았습니다"

        print("  ✅ PASS: ClaimExtractor 실패 시 graceful degradation")
        print(f"  - claim_extractor: {mm.claim_extractor}")
        print(f"  - hallucination_detection_available: {mm.hallucination_detection_available}")


def test_claim_verifier_failure():
    """ClaimVerifier 초기화 실패 시 graceful degradation"""
    print("\n[TEST 3] ClaimVerifier 초기화 실패")

    test_project_id = "test_claim_verifier_fail"

    with patch("core.memory_manager.ClaimVerifier") as MockCV:
        # ClaimVerifier 초기화 시 예외 발생
        MockCV.side_effect = RuntimeError("Git 저장소를 찾을 수 없습니다")

        mm = MemoryManager(project_id=test_project_id)
        mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

        # ClaimVerifier만 None
        assert mm.claim_verifier is None, "claim_verifier가 None이 아닙니다"

        # 핵심 컴포넌트 실패 → Phase 9 비활성화
        assert mm.hallucination_detection_available is False, "Phase 9가 비활성화되지 않았습니다"

        print("  ✅ PASS: ClaimVerifier 실패 시 graceful degradation")
        print(f"  - claim_verifier: {mm.claim_verifier}")
        print(f"  - hallucination_detection_available: {mm.hallucination_detection_available}")


def test_grounding_scorer_failure():
    """GroundingScorer 초기화 실패 시 graceful degradation"""
    print("\n[TEST 4] GroundingScorer 초기화 실패")

    test_project_id = "test_grounding_scorer_fail"

    with patch("core.memory_manager.GroundingScorer") as MockGS:
        # GroundingScorer 초기화 시 예외 발생
        MockGS.side_effect = ValueError("프로젝트 경로가 잘못되었습니다")

        mm = MemoryManager(project_id=test_project_id)
        mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

        # GroundingScorer만 None
        assert mm.grounding_scorer is None, "grounding_scorer가 None이 아닙니다"

        # 핵심 컴포넌트 실패 → Phase 9 비활성화
        assert mm.hallucination_detection_available is False, "Phase 9가 비활성화되지 않았습니다"

        print("  ✅ PASS: GroundingScorer 실패 시 graceful degradation")
        print(f"  - grounding_scorer: {mm.grounding_scorer}")
        print(f"  - hallucination_detection_available: {mm.hallucination_detection_available}")


def test_optional_component_failure():
    """선택적 컴포넌트(CodeStructureAnalyzer) 실패 시 Phase 9 계속 작동"""
    print("\n[TEST 5] 선택적 컴포넌트 실패 시 Phase 9 계속 작동")

    test_project_id = "test_optional_fail"

    with patch("core.memory_manager.CodeStructureAnalyzer") as MockCSA:
        # CodeStructureAnalyzer 초기화 시 예외 발생
        MockCSA.side_effect = OSError("프로젝트 구조 분석 실패")

        mm = MemoryManager(project_id=test_project_id)
        mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

        # CodeStructureAnalyzer만 None
        assert mm.code_structure_analyzer is None, "code_structure_analyzer가 None이 아닙니다"

        # 핵심 컴포넌트는 정상이므로 Phase 9 활성화
        assert mm.hallucination_detection_available is True, "Phase 9가 비활성화되었습니다"

        print("  ✅ PASS: 선택적 컴포넌트 실패 시 Phase 9 계속 작동")
        print(f"  - code_structure_analyzer: {mm.code_structure_analyzer}")
        print(f"  - hallucination_detection_available: {mm.hallucination_detection_available}")


def test_update_memory_with_none_components():
    """Phase 9 컴포넌트가 None일 때 update_memory 동작 확인"""
    print("\n[TEST 6] Phase 9 비활성화 시 update_memory 동작")

    test_project_id = "test_update_with_none"

    with patch("core.memory_manager.ClaimExtractor") as MockCE:
        MockCE.side_effect = ImportError("모듈 없음")

        mm = MemoryManager(project_id=test_project_id)
        mm.initialize_context(test_project_id, str(Path.cwd()), scan_mode="NONE")

        # Phase 9 비활성화 확인
        assert mm.hallucination_detection_available is False

        # 브랜치 생성
        branch_result = mm.create_branch(test_project_id, "test_branch")
        branch_id = branch_result["branch_id"]

        # update_memory 호출 (Phase 9 비활성화 상태)
        # 에러 없이 정상 동작해야 함
        result = mm.update_memory(
            project_id=test_project_id,
            branch_id=branch_id,
            content="Phase 9가 비활성화된 상태에서 메모리 업데이트 테스트",
            role="assistant"
        )

        assert result.get("success") is not False, "update_memory 실패"

        print("  ✅ PASS: Phase 9 비활성화 시에도 update_memory 정상 작동")
        print(f"  - update_memory 성공: {result.get('success', 'N/A')}")


if __name__ == "__main__":
    print("=" * 60)
    print("CRITICAL #3: Phase 9 초기화 에러 핸들링 테스트")
    print("=" * 60)

    test_all_components_success()
    test_claim_extractor_failure()
    test_claim_verifier_failure()
    test_grounding_scorer_failure()
    test_optional_component_failure()
    test_update_memory_with_none_components()

    print("\n" + "=" * 60)
    print("전체 테스트 통과!")
    print("=" * 60)
