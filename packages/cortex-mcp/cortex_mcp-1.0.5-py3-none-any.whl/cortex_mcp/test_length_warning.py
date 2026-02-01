"""
update_memory 길이별 경고 메시지 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.memory_manager import MemoryManager

PROJECT_ID = "4d8e58aea4b0"
BRANCH_ID = "update_memory_성능_근본_개선_17초to2초_20260104_06493552000"

mm = MemoryManager(project_id=PROJECT_ID)

print("\n=== 테스트 1: 짧은 내용 (100자) ===")
short_content = "짧은 테스트 내용입니다. " * 5
print(f"길이: {len(short_content)}자")
result1 = mm.update_memory(
    project_id=PROJECT_ID,
    branch_id=BRANCH_ID,
    content=short_content,
    role="assistant"
)
print(f"결과: {result1.get('success')}")

print("\n=== 테스트 2: 중간 내용 (2500자) ===")
medium_content = "중간 길이 테스트 내용입니다. " * 150
print(f"길이: {len(medium_content)}자")
result2 = mm.update_memory(
    project_id=PROJECT_ID,
    branch_id=BRANCH_ID,
    content=medium_content,
    role="assistant"
)
print(f"결과: {result2.get('success')}")

print("\n=== 테스트 3: 긴 내용 (6000자) ===")
long_content = "긴 테스트 내용입니다. " * 400
print(f"길이: {len(long_content)}자")
result3 = mm.update_memory(
    project_id=PROJECT_ID,
    branch_id=BRANCH_ID,
    content=long_content,
    role="assistant"
)
print(f"결과: {result3.get('success')}")

print("\n로그 확인:")
print("tail -20 ~/.cortex/logs/cortex.log | grep UPDATE_MEMORY")
