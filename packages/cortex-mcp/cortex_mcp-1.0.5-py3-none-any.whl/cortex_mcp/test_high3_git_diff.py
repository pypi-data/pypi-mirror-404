"""
HIGH #3: claim_verifier 파일 수정 여부 확인 테스트
"""

import os
import subprocess
import tempfile
from pathlib import Path
from core.claim_verifier import ClaimVerifier
from core.claim_extractor import Claim
from core.evidence_graph import EvidenceGraph


def test_modification_claim_with_git_diff():
    """modification 타입 Claim + Git diff 있음 → 검증 성공"""
    print("\n=== Test 1: modification Claim with Git diff ===")

    # 임시 Git 저장소 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Git 초기화
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)

        # 파일 생성 및 커밋
        test_file = tmpdir_path / "test.py"
        test_file.write_text("def old_function():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        # 파일 수정 (unstaged)
        test_file.write_text("def new_function():\n    return 42\n")

        # ClaimVerifier 생성
        verifier = ClaimVerifier(
            project_id="test_project",
            project_path=str(tmpdir_path)
        )

        # modification Claim 생성
        claim = Claim(
            claim_type="modification",
            text="test.py 파일을 수정했습니다",
            start=0,
            end=100,
            confidence=1.0,
            metadata={"file_references": ["test.py"]}
        )

        # 검증
        result = verifier._has_file_diff("test.py", claim=claim)
        assert result is True, f"Expected True, got {result}"
        print("✅ Test 1 PASSED: Git diff 감지하여 검증 성공")


def test_modification_claim_without_git_diff():
    """modification 타입 Claim + Git diff 없음 → 검증 실패"""
    print("\n=== Test 2: modification Claim without Git diff ===")

    # 임시 Git 저장소 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Git 초기화
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)

        # 파일 생성 및 커밋
        test_file = tmpdir_path / "unchanged.py"
        test_file.write_text("def unchanged_function():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, capture_output=True)

        # 파일 수정 없음 (Git diff 없음)

        # ClaimVerifier 생성
        verifier = ClaimVerifier(
            project_id="test_project",
            project_path=str(tmpdir_path)
        )

        # modification Claim 생성
        claim = Claim(
            claim_type="modification",
            text="unchanged.py 파일을 수정했습니다",
            start=0,
            end=100,
            confidence=1.0,
            metadata={"file_references": ["unchanged.py"]}
        )

        # 검증
        result = verifier._has_file_diff("unchanged.py", claim=claim)
        assert result is False, f"Expected False, got {result}"
        print("✅ Test 2 PASSED: Git diff 없어서 검증 실패")


def test_non_modification_claim():
    """modification이 아닌 타입 Claim → 기존 로직 유지"""
    print("\n=== Test 3: non-modification Claim (기존 로직) ===")

    # 임시 Git 저장소 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Git 초기화
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)

        # 파일 생성 (커밋 없음)
        test_file = tmpdir_path / "new_file.py"
        test_file.write_text("def new_function():\n    pass\n")

        # ClaimVerifier 생성
        verifier = ClaimVerifier(
            project_id="test_project",
            project_path=str(tmpdir_path)
        )

        # implementation_complete Claim 생성 (modification 아님)
        claim = Claim(
            claim_type="implementation_complete",
            text="new_file.py 파일을 생성했습니다",
            start=0,
            end=100,
            confidence=1.0,
            metadata={"file_references": ["new_file.py"]}
        )

        # 검증
        result = verifier._has_file_diff("new_file.py", claim=claim)
        assert result is False, f"Expected False (기존 로직), got {result}"
        print("✅ Test 3 PASSED: modification 아니므로 기존 로직 유지 (False)")


if __name__ == "__main__":
    try:
        test_modification_claim_with_git_diff()
        test_modification_claim_without_git_diff()
        test_non_modification_claim()
        print("\n" + "=" * 60)
        print("✅ HIGH #3 테스트 전체 통과 (3/3)")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        raise
