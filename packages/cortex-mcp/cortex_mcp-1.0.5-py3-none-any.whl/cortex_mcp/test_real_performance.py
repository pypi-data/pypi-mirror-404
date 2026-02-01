"""
실제 사용자 환경에서의 update_memory 성능 테스트
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_manager import MemoryManager
from config import config
import time

# 실제 프로젝트 사용
project_id = "4d8e58aea4b0"
branch_id = "RAG_인덱싱_Fallback_및_사용자_알림_구현_20260104_05475481957"

# 실제 사용자의 긴 텍스트 (이전 맥락 업데이트와 유사)
content = """# 성능 테스트

## 작업 배경

사용자가 update_memory 함수의 성능 문제를 제기했습니다.
현재 1분 가까이 걸리는 문제가 있으며, 근본 원인을 파악해야 합니다.

## 수정 내용

1. memory_manager.py에 성능 측정 로그 추가
2. 각 작업별 실행 시간 측정
3. 병목 지점 파악

## 예상 원인

- 요약 생성이 긴 텍스트에서 오래 걸림
- 온톨로지 분류가 임베딩 생성으로 시간 소요
- Phase 9 검증이 실행되고 있을 가능성
- RAG 인덱싱이 실제로는 동기적으로 실행

""" * 5  # 텍스트를 5배로 늘려서 실제 사용과 유사하게

print("[실제 환경 테스트] 시작")
print(f"프로젝트 ID: {project_id}")
print(f"브랜치 ID: {branch_id[:50]}...")
print(f"텍스트 길이: {len(content)} 문자")
print()

mm = MemoryManager(project_id=project_id)

start = time.perf_counter()
result = mm.update_memory(
    project_id=project_id,
    branch_id=branch_id,
    content=content,
    role="assistant"
)
elapsed = time.perf_counter() - start

print(f"\n[결과]")
print(f"전체 실행 시간: {elapsed*1000:.1f}ms")
print(f"Success: {result['success']}")
print(f"Summary updated: {result.get('summary_updated', False)}")
print(f"Ontology updated: {result.get('ontology_updated', False)}")
print(f"Background indexing: {result.get('background_indexing_started', False)}")
print(f"Grounding score: {result.get('grounding_score', 'N/A')}")
