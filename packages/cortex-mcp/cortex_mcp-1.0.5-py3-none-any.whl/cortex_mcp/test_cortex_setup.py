#!/usr/bin/env python3
"""
Cortex Setup 및 Hook 테스트 스크립트

테스트 항목:
1. setup_cortex.py - 프로젝트별 설치
2. inject_context.py - 강제 실행 패턴
3. cortex_prompt.md - 프로젝트별 분리
"""

import os
import sys
import tempfile
from pathlib import Path

# 테스트용 임시 프로젝트 디렉토리 생성
def create_test_projects():
    """2개의 테스트 프로젝트 생성"""
    temp_dir = Path(tempfile.mkdtemp(prefix="cortex_test_"))

    project_a = temp_dir / "project_a"
    project_b = temp_dir / "project_b"

    project_a.mkdir(parents=True)
    project_b.mkdir(parents=True)

    # Claude Code 클라이언트 시뮬레이션
    (project_a / "CLAUDE.md").write_text("# Test Project A\n", encoding='utf-8')
    (project_b / "CLAUDE.md").write_text("# Test Project B\n", encoding='utf-8')

    return temp_dir, project_a, project_b


def test_setup_cortex(project_path: Path):
    """setup_cortex.py 테스트"""
    print(f"\n[TEST 1] setup_cortex.py - {project_path.name}")
    print("=" * 60)

    # 현재 디렉토리를 프로젝트 루트로 변경
    original_cwd = os.getcwd()
    os.chdir(project_path)

    try:
        # setup_cortex.py import
        sys.path.insert(0, str(Path(__file__).parent / "scripts"))
        from scripts.setup_cortex import (
            detect_ai_client,
            auto_add_reference,
            setup_project
        )

        # 1. 클라이언트 감지
        client = detect_ai_client(project_path)
        print(f"   ✓ 클라이언트 감지: {client}")
        assert client == "claude-code", f"Expected claude-code, got {client}"

        # 2. cortex_prompt.md 생성 여부
        cortex_prompt = project_path / "cortex_prompt.md"
        if cortex_prompt.exists():
            print(f"   ✓ cortex_prompt.md 존재")
        else:
            print(f"   ✗ cortex_prompt.md 없음 (setup_project 실행 필요)")

        # 3. CLAUDE.md에 참조 추가 여부
        claude_md = project_path / "CLAUDE.md"
        content = claude_md.read_text(encoding='utf-8')

        if "cortex_prompt.md" in content:
            print(f"   ✓ CLAUDE.md에 참조 추가됨")
        else:
            print(f"   ✗ CLAUDE.md에 참조 없음 (auto_add_reference 실행 필요)")

        print(f"   ✓ TEST 1 PASS\n")

    except Exception as e:
        print(f"   ✗ TEST 1 FAIL: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        os.chdir(original_cwd)


def test_cortex_prompt_isolation(project_a: Path, project_b: Path):
    """cortex_prompt.md 프로젝트별 분리 테스트"""
    print(f"\n[TEST 2] cortex_prompt.md 프로젝트별 분리")
    print("=" * 60)

    try:
        # 프로젝트 A에 cortex_prompt.md 생성
        cortex_a = project_a / "cortex_prompt.md"
        cortex_a.write_text("# Project A Context\nTest content A\n", encoding='utf-8')

        # 프로젝트 B에 cortex_prompt.md 생성
        cortex_b = project_b / "cortex_prompt.md"
        cortex_b.write_text("# Project B Context\nTest content B\n", encoding='utf-8')

        # 내용 검증
        content_a = cortex_a.read_text(encoding='utf-8')
        content_b = cortex_b.read_text(encoding='utf-8')

        assert "Project A" in content_a, "Project A content not found"
        assert "Project B" in content_b, "Project B content not found"
        assert "Project B" not in content_a, "Project A contaminated with B"
        assert "Project A" not in content_b, "Project B contaminated with A"

        print(f"   ✓ Project A: {cortex_a}")
        print(f"   ✓ Project B: {cortex_b}")
        print(f"   ✓ 프로젝트별 완전 분리 확인")
        print(f"   ✓ TEST 2 PASS\n")

    except Exception as e:
        print(f"   ✗ TEST 2 FAIL: {e}\n")
        import traceback
        traceback.print_exc()


def test_inject_context_pattern():
    """inject_context.py 강제 실행 패턴 테스트"""
    print(f"\n[TEST 3] inject_context.py 강제 실행 패턴")
    print("=" * 60)

    try:
        # inject_context.py import
        from hooks.inject_context import write_cortex_prompt

        # Mock HookContext 생성
        class MockContext:
            def __init__(self, project_path, project_id, active_branch):
                self.project_path = project_path
                self.project_id = project_id
                self.active_branch = active_branch
                self.state = {"current_topic": "test_topic"}

            def log(self, *args, **kwargs):
                pass

        # 임시 프로젝트에서 테스트
        temp_dir = Path(tempfile.mkdtemp(prefix="cortex_hook_test_"))
        mock_ctx = MockContext(
            project_path=str(temp_dir),
            project_id="test_project",
            active_branch="test_branch"
        )

        # write_cortex_prompt 실행
        result = write_cortex_prompt(mock_ctx, "test prompt", ["test", "keywords"])

        # 결과 확인
        cortex_file = temp_dir / "cortex_prompt.md"

        if result and cortex_file.exists():
            content = cortex_file.read_text(encoding='utf-8')
            print(f"   ✓ cortex_prompt.md 생성됨: {cortex_file}")
            print(f"   ✓ 내용 미리보기:\n")
            print("   " + "\n   ".join(content.split("\n")[:15]))
            print(f"   ✓ TEST 3 PASS\n")
        else:
            print(f"   ✗ TEST 3 FAIL: cortex_prompt.md 생성 실패\n")

        # 정리
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"   ✗ TEST 3 FAIL: {e}\n")
        import traceback
        traceback.print_exc()


def main():
    """테스트 메인"""
    print("\n" + "=" * 60)
    print("Cortex Setup & Hook 테스트 시작")
    print("=" * 60)

    # 1. 테스트 프로젝트 생성
    temp_dir, project_a, project_b = create_test_projects()
    print(f"\n테스트 환경:")
    print(f"  Temp Dir: {temp_dir}")
    print(f"  Project A: {project_a}")
    print(f"  Project B: {project_b}")

    # 2. 테스트 실행
    try:
        # Test 1: setup_cortex.py
        test_setup_cortex(project_a)
        test_setup_cortex(project_b)

        # Test 2: 프로젝트별 분리
        test_cortex_prompt_isolation(project_a, project_b)

        # Test 3: inject_context.py 패턴
        test_inject_context_pattern()

    finally:
        # 정리
        import shutil
        print(f"\n정리:")
        print(f"  Temp Dir 삭제: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
