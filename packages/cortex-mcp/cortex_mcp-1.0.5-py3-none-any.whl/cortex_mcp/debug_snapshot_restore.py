#!/usr/bin/env python3
"""
Snapshot Restore 버그 디버그 스크립트

테스트에서 0% 복원 정확도가 나오는 원인을 찾습니다.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.backup_manager import BackupManager
from core.memory_manager import MemoryManager


def calculate_state_hash(memory_dir: Path, project_id: str) -> str:
    """
    전체 상태의 해시값 계산 (테스트와 동일한 로직)
    """
    project_dir = memory_dir / project_id
    if not project_dir.exists():
        return hashlib.md5(b"").hexdigest()

    state_parts = []

    # 1. _index.json 해시
    index_file = project_dir / "_index.json"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
            state_parts.append(json.dumps(index_data, sort_keys=True))

    # 2. 모든 .md 파일 해시
    for md_file in sorted(project_dir.glob("*.md")):
        if md_file.name.startswith("_"):
            continue
        with open(md_file, "r", encoding="utf-8") as f:
            state_parts.append(f.read())

    # 전체 상태 해시 계산
    combined = "".join(state_parts)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()


def list_files(directory: Path, label: str):
    """디렉토리 내 모든 파일 출력"""
    print(f"\n{label}:")
    if not directory.exists():
        print("  (디렉토리 없음)")
        return

    files = sorted(directory.rglob("*"))
    if not files:
        print("  (파일 없음)")
        return

    for f in files:
        if f.is_file():
            rel_path = f.relative_to(directory)
            size = f.stat().st_size
            print(f"  {rel_path}: {size} bytes")


def main():
    print("=" * 80)
    print("Snapshot Restore 디버그 스크립트")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmp:
        temp_path = Path(tmp)
        test_project_id = "debug_snapshot_test"

        print(f"\n임시 디렉토리: {temp_path}")

        # MemoryManager와 BackupManager 초기화
        memory_manager = MemoryManager(
            project_id=test_project_id, memory_dir=temp_path
        )
        backup_manager = BackupManager(memory_dir=temp_path)

        # Step 1: 브랜치와 content 생성
        print("\n[1] 브랜치와 content 생성 중...")
        branches = ["branch_1", "branch_2"]

        for branch_id in branches:
            memory_manager.create_branch(
                project_id=test_project_id, branch_topic=branch_id
            )

            for i in range(2):
                memory_manager.update_memory(
                    project_id=test_project_id,
                    branch_id=branch_id,
                    content=f"{branch_id} content {i+1}",
                    role="assistant",
                    verified=True,
                )

        # Step 2: 초기 상태 확인
        project_dir = temp_path / test_project_id
        list_files(project_dir, "[초기 상태] 프로젝트 파일")

        initial_hash = calculate_state_hash(temp_path, test_project_id)
        print(f"\n초기 상태 해시: {initial_hash}")

        # Step 3: 스냅샷 생성
        print("\n[2] 스냅샷 생성 중...")
        snapshot_result = backup_manager.create_snapshot(
            project_id=test_project_id,
            description="Debug snapshot",
            snapshot_type="manual",
        )

        if not snapshot_result.get("success"):
            print(f"  스냅샷 생성 실패: {snapshot_result.get('error')}")
            return

        snapshot_id = snapshot_result.get("snapshot_id")
        print(f"  스냅샷 ID: {snapshot_id}")

        # 스냅샷 내용 확인
        snapshot_dir = backup_manager.backup_dir / test_project_id / snapshot_id
        list_files(snapshot_dir, "[스냅샷] 백업된 파일")

        # Step 4: 프로젝트 수정
        print("\n[3] 프로젝트 수정 중...")
        memory_manager.update_memory(
            project_id=test_project_id,
            branch_id="branch_1",
            content="MODIFIED CONTENT",
            role="assistant",
            verified=True,
        )

        modified_hash = calculate_state_hash(temp_path, test_project_id)
        print(f"  수정 후 해시: {modified_hash}")
        print(f"  해시 변경됨: {initial_hash != modified_hash}")

        list_files(project_dir, "[수정 후] 프로젝트 파일")

        # Step 5: 스냅샷 복원
        print("\n[4] 스냅샷 복원 중...")
        restore_result = backup_manager.restore_snapshot(
            project_id=test_project_id, snapshot_id=snapshot_id, overwrite=True
        )

        if not restore_result.get("success"):
            print(f"  복원 실패: {restore_result.get('error')}")
            print(f"  검증 실패: {restore_result.get('verification_failed')}")
            print(f"  검증 오류: {restore_result.get('verification_errors')}")
            return

        print(f"  복원 성공")

        # Step 6: 복원 후 상태 확인
        list_files(project_dir, "[복원 후] 프로젝트 파일")

        restored_hash = calculate_state_hash(temp_path, test_project_id)
        print(f"\n복원 후 해시: {restored_hash}")

        # Step 7: 해시 비교
        print("\n" + "=" * 80)
        print("결과:")
        print("=" * 80)
        print(f"초기 해시:   {initial_hash}")
        print(f"복원 후 해시: {restored_hash}")
        print(f"해시 일치:    {initial_hash == restored_hash}")

        if initial_hash != restored_hash:
            print("\n불일치 원인 분석:")

            # 파일 개수 비교
            initial_files = sorted(
                [f for f in project_dir.glob("*.md") if not f.name.startswith("_")]
            )
            print(f"  초기 .md 파일 개수: (상태 생성 직후 확인 필요)")
            print(f"  복원 후 .md 파일 개수: {len(initial_files)}")

            # 파일별 비교
            print("\n  복원된 파일:")
            for f in initial_files:
                size = f.stat().st_size
                print(f"    {f.name}: {size} bytes")


if __name__ == "__main__":
    main()
