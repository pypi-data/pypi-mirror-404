#!/usr/bin/env python3
"""
Phase 4: Git Integration 테스트
Git 브랜치와 Cortex 브랜치 연동 기능 검증
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.git_sync import GitSync, get_git_sync
from core.memory_manager import MemoryManager


def test_git_sync():
    """Git Sync 모듈 테스트"""
    print("=" * 50)
    print("Phase 4: Git Integration 테스트")
    print("=" * 50)

    # 테스트용 프로젝트 ID
    test_project_id = "__test_git_sync"

    # GitSync 인스턴스 생성
    git_sync = get_git_sync(test_project_id)
    memory_manager = MemoryManager()

    # 테스트용 Git 저장소 경로 (cortex_mcp 프로젝트의 상위 디렉토리 - Git 저장소가 있는지 확인)
    # 실제 Git 저장소가 없을 수 있으므로 테스트용 시나리오 실행

    # 1. 현재 Git 저장소 위치 찾기
    test_repo_path = str(project_root.parent)  # cortex_mcp의 상위 디렉토리

    print(f"\n1. 테스트 저장소 경로: {test_repo_path}")

    # Git 디렉토리 확인
    git_dir = Path(test_repo_path) / ".git"
    is_git_repo = git_dir.exists()

    print(f"   Git 저장소 여부: {is_git_repo}")

    if is_git_repo:
        # 실제 Git 저장소가 있는 경우 테스트
        print("\n2. 현재 Git 브랜치 확인")
        branch_result = git_sync.get_current_git_branch(test_repo_path)
        print(f"   결과: {branch_result}")

        if branch_result["success"]:
            current_branch = branch_result["git_branch"]
            print(f"   현재 브랜치: {current_branch}")

            print("\n3. Git 브랜치 연동")
            link_result = git_sync.link_git_branch(
                repo_path=test_repo_path, git_branch=current_branch, auto_create=True
            )
            print(f"   결과: {link_result}")

            print("\n4. Git 저장소 전체 정보")
            info_result = git_sync.get_git_info(test_repo_path)
            print(f"   현재 브랜치: {info_result.get('current_branch')}")
            print(f"   커밋 해시: {info_result.get('commit_hash')}")
            print(f"   로컬 브랜치 수: {len(info_result.get('local_branches', []))}")
            print(f"   Cortex 연동 수: {info_result.get('cortex_linked_count')}")

            print("\n5. 연동된 브랜치 목록")
            list_result = git_sync.list_linked_branches(test_repo_path)
            print(f"   연동 브랜치 수: {list_result.get('count')}")
            for branch in list_result.get("branches", []):
                print(f"   - {branch.get('git_branch')} -> {branch.get('cortex_branch_id')}")

            print("\n6. 연동된 Cortex 브랜치 조회")
            linked_result = git_sync.get_linked_cortex_branch(test_repo_path)
            print(f"   결과: {linked_result}")

            print("\n7. 브랜치 변경 감지 테스트 (변경 없음 예상)")
            change_result = git_sync.check_branch_change(test_repo_path)
            print(f"   변경 여부: {change_result.get('changed')}")
            print(f"   메시지: {change_result.get('message')}")

    else:
        # Git 저장소가 없는 경우 Mock 테스트
        print("\n[Git 저장소 없음 - Mock 테스트 실행]")

        print("\n2. Git 저장소 확인 (없음 예상)")
        result = git_sync.get_current_git_branch(test_repo_path)
        print(f"   결과: {result}")
        assert result["success"] == False, "Git 저장소가 없으면 False여야 함"

        print("\n3. 매핑 직접 테스트")
        # 내부 매핑 함수 테스트
        git_sync._set_mapping("/fake/repo", "main", "cortex_main_123")
        git_sync._save_mapping()

        mapping = git_sync._get_mapping("/fake/repo", "main")
        print(f"   저장된 매핑: {mapping}")
        assert mapping is not None, "매핑이 저장되어야 함"
        assert mapping["cortex_branch_id"] == "cortex_main_123"

        print("\n4. 연동 목록 테스트")
        list_result = git_sync.list_linked_branches()
        print(f"   연동 수: {list_result.get('count')}")

    # 테스트 결과
    print("\n" + "=" * 50)
    print("Phase 4 테스트 완료!")
    print("=" * 50)

    return True


def test_git_sync_without_repo():
    """Git 저장소 없이 기본 기능 테스트"""
    print("\n" + "=" * 50)
    print("Git Sync 기본 기능 테스트 (저장소 없이)")
    print("=" * 50)

    git_sync = get_git_sync("__test_basic")

    # 1. 존재하지 않는 경로 테스트
    print("\n1. 존재하지 않는 경로 테스트")
    result = git_sync.get_current_git_branch("/nonexistent/path")
    print(f"   결과: {result}")
    assert result["success"] == False

    # 2. 매핑 저장/로드 테스트
    print("\n2. 매핑 저장/로드 테스트")
    git_sync._set_mapping("/test/repo1", "main", "cortex_main_001")
    git_sync._set_mapping("/test/repo1", "develop", "cortex_develop_001")
    git_sync._set_mapping("/test/repo2", "main", "cortex_main_002")
    git_sync._save_mapping()

    # 리로드
    git_sync2 = get_git_sync("__test_basic")
    mapping1 = git_sync2._get_mapping("/test/repo1", "main")
    mapping2 = git_sync2._get_mapping("/test/repo1", "develop")
    mapping3 = git_sync2._get_mapping("/test/repo2", "main")

    print(f"   /test/repo1::main -> {mapping1.get('cortex_branch_id') if mapping1 else None}")
    print(f"   /test/repo1::develop -> {mapping2.get('cortex_branch_id') if mapping2 else None}")
    print(f"   /test/repo2::main -> {mapping3.get('cortex_branch_id') if mapping3 else None}")

    assert mapping1 and mapping1["cortex_branch_id"] == "cortex_main_001"
    assert mapping2 and mapping2["cortex_branch_id"] == "cortex_develop_001"
    assert mapping3 and mapping3["cortex_branch_id"] == "cortex_main_002"

    # 3. 연동 목록 테스트
    print("\n3. 연동 목록 테스트")
    list_result = git_sync2.list_linked_branches()
    print(f"   총 연동 수: {list_result.get('count')}")

    filtered_result = git_sync2.list_linked_branches("/test/repo1")
    print(f"   /test/repo1 연동 수: {filtered_result.get('count')}")

    # 4. 연동 해제 테스트
    print("\n4. 연동 해제 테스트")
    unlink_result = git_sync2.unlink_git_branch("/test/repo1", "develop")
    print(f"   결과: {unlink_result}")

    # 확인
    mapping_after = git_sync2._get_mapping("/test/repo1", "develop")
    print(f"   해제 후 매핑: {mapping_after}")
    assert mapping_after is None, "연동 해제 후 매핑이 없어야 함"

    print("\n기본 기능 테스트 완료!")
    return True


if __name__ == "__main__":
    try:
        # 기본 기능 테스트
        test_git_sync_without_repo()

        # Git 저장소 테스트 (있는 경우)
        test_git_sync()

        print("\n" + "=" * 50)
        print("✓ 모든 테스트 통과!")
        print("=" * 50)

    except Exception as e:
        import traceback

        print(f"\n✗ 테스트 실패: {e}")
        traceback.print_exc()
        sys.exit(1)
