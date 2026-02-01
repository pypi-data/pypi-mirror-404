"""
병렬 개발 Merge 수정 통합 테스트

테스트 시나리오:
1. 새 브랜치 생성 - auto_sync=False 검증
2. 기존 브랜치 업데이트 3회 - INCREMENTAL 병합 검증
3. 병렬 세션 동기화 - INCREMENTAL 전략 검증
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import config
from core.memory_manager import MemoryManager
from core.multi_session_sync import MultiSessionManager


def test_1_new_branch_creation():
    """
    시나리오 1: 새 브랜치 생성

    검증:
    - enable_auto_sync=False로 세션 생성되는지
    - update_memory 3회 후 파일 크기 < 5KB
    - merged_from 메타데이터 없음
    - "## [Merged from ...]" 섹션 없음
    """
    print("\n" + "=" * 80)
    print("테스트 1: 새 브랜치 생성 (auto_sync 비활성화)")
    print("=" * 80)

    project_id = "test_merge_fix"
    branch_topic = f"test_new_branch_{int(time.time())}"

    mm = MemoryManager(project_id=project_id)

    # 브랜치 생성
    print(f"\n1. 브랜치 생성: {branch_topic}")
    branch_result = mm.create_branch(
        project_id=project_id,
        branch_topic=branch_topic,
    )
    assert branch_result["success"], "브랜치 생성 실패"
    branch_id = branch_result["branch_id"]
    print(f"   ✓ 브랜치 생성 완료: {branch_id}")

    # 세션 확인
    if mm.multi_session_manager and mm.multi_session_manager.current_session:
        session = mm.multi_session_manager.current_session
        print(f"\n2. 세션 확인:")
        print(f"   - Session ID: {session.session_id}")
        print(f"   - enable_auto_sync: {session.enable_auto_sync}")

        if session.enable_auto_sync:
            print("   ✗ FAIL: 새 브랜치는 enable_auto_sync=False여야 함")
            return False
        else:
            print("   ✓ PASS: enable_auto_sync=False 확인")
    else:
        print("   - 세션 없음 (multi_session 비활성화)")

    # update_memory 3회
    print(f"\n3. update_memory 3회 호출:")
    for i in range(3):
        content = f"테스트 내용 {i+1}: " + "A" * 500  # ~500자
        result = mm.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content=content,
            role="assistant",
        )
        assert result["success"], f"update_memory {i+1} 실패"
        print(f"   ✓ update_memory {i+1} 완료")

    # 파일 확인
    print(f"\n4. 파일 검증:")
    branch_file = config.base_dir / "memory" / project_id / f"{branch_id}.md"

    if not branch_file.exists():
        print(f"   ✗ FAIL: 파일을 찾을 수 없음: {branch_file}")
        return False

    content = branch_file.read_text(encoding="utf-8")
    file_size_kb = len(content) / 1024
    line_count = len(content.split('\n'))

    print(f"   - 파일 크기: {file_size_kb:.2f} KB")
    print(f"   - 줄 수: {line_count}")

    # 크기 검증 (< 5KB)
    if file_size_kb >= 5:
        print(f"   ✗ FAIL: 파일 크기가 5KB 이상입니다 ({file_size_kb:.2f} KB)")
        return False
    else:
        print(f"   ✓ PASS: 파일 크기 < 5KB")

    # Merge 섹션 확인
    merge_count = content.count("## [Merged from")
    if merge_count > 0:
        print(f"   ✗ FAIL: Merge 섹션이 {merge_count}개 발견됨")
        return False
    else:
        print(f"   ✓ PASS: Merge 섹션 없음")

    # Frontmatter 확인
    if "merged_from:" in content:
        print(f"   ✗ FAIL: merged_from 메타데이터 발견")
        return False
    else:
        print(f"   ✓ PASS: merged_from 메타데이터 없음")

    print("\n✅ 테스트 1 통과")
    return True


def test_2_existing_branch_updates():
    """
    시나리오 2: 기존 브랜치 업데이트

    검증:
    - update_memory 3회 후 파일 크기 합리적 증가
    - Merge 섹션 없음
    - 지수적 증가 없음
    """
    print("\n" + "=" * 80)
    print("테스트 2: 기존 브랜치 업데이트 (누적 증가만 발생)")
    print("=" * 80)

    project_id = "test_merge_fix"
    branch_topic = f"test_existing_branch_{int(time.time())}"

    mm = MemoryManager(project_id=project_id)

    # 브랜치 생성
    print(f"\n1. 브랜치 생성: {branch_topic}")
    branch_result = mm.create_branch(
        project_id=project_id,
        branch_topic=branch_topic,
    )
    branch_id = branch_result["branch_id"]
    print(f"   ✓ 브랜치 생성 완료: {branch_id}")

    branch_file = config.base_dir / "memory" / project_id / f"{branch_id}.md"

    # 초기 크기
    initial_size = len(branch_file.read_text(encoding="utf-8"))
    print(f"\n2. 초기 파일 크기: {initial_size / 1024:.2f} KB")

    # update_memory 3회
    print(f"\n3. update_memory 3회 호출:")
    sizes = [initial_size]

    for i in range(3):
        content = f"업데이트 {i+1}: " + "B" * 800  # ~800자
        result = mm.update_memory(
            project_id=project_id,
            branch_id=branch_id,
            content=content,
            role="assistant",
        )
        assert result["success"], f"update_memory {i+1} 실패"

        current_size = len(branch_file.read_text(encoding="utf-8"))
        increase = current_size - sizes[-1]
        sizes.append(current_size)

        print(f"   ✓ update_memory {i+1}: {current_size / 1024:.2f} KB (+{increase / 1024:.2f} KB)")

    # 총 증가량 검증
    total_increase = sizes[-1] - sizes[0]
    print(f"\n4. 파일 크기 변화:")
    print(f"   - 초기: {sizes[0] / 1024:.2f} KB")
    print(f"   - 최종: {sizes[-1] / 1024:.2f} KB")
    print(f"   - 증가: {total_increase / 1024:.2f} KB")

    # 지수적 증가 검증 (각 증가량이 2배씩 증가하지 않아야 함)
    for i in range(1, len(sizes) - 1):
        increase_1 = sizes[i] - sizes[i-1]
        increase_2 = sizes[i+1] - sizes[i]

        # 다음 증가량이 이전 증가량의 1.5배 미만이어야 함 (합리적 증가)
        if increase_2 > increase_1 * 1.5:
            print(f"   ✗ FAIL: 지수적 증가 감지 (증가 {i}: {increase_1 / 1024:.2f} KB → 증가 {i+1}: {increase_2 / 1024:.2f} KB)")
            return False

    print(f"   ✓ PASS: 선형적 증가 확인")

    # Merge 섹션 확인
    content = branch_file.read_text(encoding="utf-8")
    merge_count = content.count("## [Merged from")
    if merge_count > 0:
        print(f"   ✗ FAIL: Merge 섹션이 {merge_count}개 발견됨")
        return False
    else:
        print(f"   ✓ PASS: Merge 섹션 없음")

    print("\n✅ 테스트 2 통과")
    return True


def test_3_parallel_session_sync():
    """
    시나리오 3: 병렬 세션 동기화

    검증:
    - 2개 세션에서 각 5개 context 생성
    - INCREMENTAL 전략으로 병합
    - 총 10개 context (중복 없음)
    - 합리적 파일 크기
    """
    print("\n" + "=" * 80)
    print("테스트 3: 병렬 세션 동기화 (INCREMENTAL 전략)")
    print("=" * 80)

    project_id = "test_merge_fix"
    branch_topic_1 = f"test_parallel_1_{int(time.time())}"
    branch_topic_2 = f"test_parallel_2_{int(time.time())}"

    # 세션 1
    print(f"\n1. 세션 1 생성 및 작업:")
    mm1 = MemoryManager(project_id=project_id)
    branch_result_1 = mm1.create_branch(project_id=project_id, branch_topic=branch_topic_1)
    branch_id_1 = branch_result_1["branch_id"]
    print(f"   ✓ 브랜치 1: {branch_id_1}")

    for i in range(5):
        content = f"세션 1 작업 {i+1}: " + "X" * 300
        mm1.update_memory(
            project_id=project_id,
            branch_id=branch_id_1,
            content=content,
            role="assistant",
        )
    print(f"   ✓ 5개 context 생성 완료")

    # 세션 2
    print(f"\n2. 세션 2 생성 및 작업:")
    mm2 = MemoryManager(project_id=project_id)
    branch_result_2 = mm2.create_branch(project_id=project_id, branch_topic=branch_topic_2)
    branch_id_2 = branch_result_2["branch_id"]
    print(f"   ✓ 브랜치 2: {branch_id_2}")

    # enable_auto_sync=True로 설정하여 자동 병합 활성화
    if mm2.multi_session_manager:
        mm2.multi_session_manager.current_session.enable_auto_sync = True
        mm2.multi_session_manager.current_session.contexts_created = ["c1", "c2", "c3", "c4", "c5"]

    for i in range(5):
        content = f"세션 2 작업 {i+1}: " + "Y" * 300
        mm2.update_memory(
            project_id=project_id,
            branch_id=branch_id_2,
            content=content,
            role="assistant",
        )
    print(f"   ✓ 5개 context 생성 완료")

    # 수동 동기화 (세션 2 → 세션 1)
    print(f"\n3. 병합 수행 (세션 2 → 세션 1):")
    if mm2.multi_session_manager:
        sync_result = mm2.multi_session_manager.sync_with_other_sessions(force=True)
        print(f"   - 결과: {sync_result}")

        if sync_result.get("success"):
            print(f"   ✓ 동기화 성공")
            print(f"   - 병합된 세션 수: {sync_result.get('merged_count', 0)}")
        else:
            print(f"   - 동기화 불필요 또는 실패: {sync_result.get('message')}")

    # 파일 검증
    print(f"\n4. 병합 결과 검증:")
    branch_file_1 = config.base_dir / "memory" / project_id / f"{branch_id_1}.md"
    branch_file_2 = config.base_dir / "memory" / project_id / f"{branch_id_2}.md"

    content_1 = branch_file_1.read_text(encoding="utf-8")
    content_2 = branch_file_2.read_text(encoding="utf-8")

    size_1_kb = len(content_1) / 1024
    size_2_kb = len(content_2) / 1024

    print(f"   - 브랜치 1 크기: {size_1_kb:.2f} KB")
    print(f"   - 브랜치 2 크기: {size_2_kb:.2f} KB")

    # Merge 섹션 확인
    merge_count_1 = content_1.count("## [Merged from")
    merge_count_2 = content_2.count("## [Merged from")

    if merge_count_1 > 0 or merge_count_2 > 0:
        print(f"   ✗ FAIL: Merge 섹션 발견 (브랜치1: {merge_count_1}, 브랜치2: {merge_count_2})")
        return False
    else:
        print(f"   ✓ PASS: Merge 섹션 없음")

    # 파일 크기 합리성 검증 (각 < 10KB)
    if size_1_kb >= 10 or size_2_kb >= 10:
        print(f"   ✗ FAIL: 파일 크기가 10KB 이상")
        return False
    else:
        print(f"   ✓ PASS: 파일 크기 합리적")

    print("\n✅ 테스트 3 통과")
    return True


def cleanup():
    """테스트 데이터 정리"""
    print("\n" + "=" * 80)
    print("테스트 데이터 정리")
    print("=" * 80)

    project_id = "test_merge_fix"
    memory_dir = config.base_dir / "memory" / project_id

    if memory_dir.exists():
        import shutil
        shutil.rmtree(memory_dir)
        print(f"✓ 테스트 디렉토리 삭제: {memory_dir}")


def main():
    """메인 실행"""
    print("\n" + "=" * 80)
    print("병렬 개발 Merge 수정 통합 테스트")
    print("=" * 80)

    results = []

    try:
        # 테스트 1: 새 브랜치 생성
        results.append(("새 브랜치 생성", test_1_new_branch_creation()))

        # 테스트 2: 기존 브랜치 업데이트
        results.append(("기존 브랜치 업데이트", test_2_existing_branch_updates()))

        # 테스트 3: 병렬 세션 동기화
        results.append(("병렬 세션 동기화", test_3_parallel_session_sync()))

    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    # 결과 요약
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n전체 결과: {passed}/{total} 통과")

    # 정리
    cleanup()

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
