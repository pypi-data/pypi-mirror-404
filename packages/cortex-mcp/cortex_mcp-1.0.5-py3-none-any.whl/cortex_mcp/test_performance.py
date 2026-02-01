"""
성능 테스트: update_memory 병목 지점 파악
"""
import sys
import tempfile
from pathlib import Path

# Add cortex_mcp to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_manager import MemoryManager
from config import config

def test_update_memory_performance():
    """update_memory 성능 측정"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config.base_dir = Path(tmpdir)
        config.ensure_directories()

        project_id = "perf_test"
        mm = MemoryManager(project_id=project_id)

        # 브랜치 생성
        result = mm.create_branch(
            project_id=project_id,
            branch_topic="Performance Test"
        )
        branch_id = result["branch_id"]

        # 여러 번 update_memory 호출하여 평균 성능 측정
        print("\n=== update_memory 성능 테스트 시작 ===\n")

        for i in range(3):
            print(f"\n--- Test {i+1}/3 ---")
            result = mm.update_memory(
                project_id=project_id,
                branch_id=branch_id,
                content=f"Test content {i+1}: This is a performance test to measure update_memory execution time.",
                role="assistant"
            )
            print(f"Success: {result['success']}")
            print(f"Background indexing started: {result.get('background_indexing_started', False)}")

        print("\n=== 테스트 완료 ===")
        print("\n로그 파일 확인: tail -100 ~/.cortex/logs/cortex.log | grep PERF")

if __name__ == "__main__":
    test_update_memory_performance()
