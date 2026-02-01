# cortex_mcp/core/branch_matcher.py
"""
브랜치 유틸리티 모듈 (v3 - 벤더 독립)

기능:
- 프로젝트의 브랜치 목록 조회
- AI가 브랜치 선택 시 참고할 정보 제공

NOTE: 브랜치 자동 매칭 기능 제거됨 (벤더 독립성 확보)
      AI가 update_memory 호출 전에 적절한 branch_id를 결정해서 전달해야 함

작성일: 2026-01-17
업데이트: 2026-01-17 (벤더 독립 - AISimilarityJudge 제거)
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


# 상수
MISC_BRANCH_ID = "misc"
MISC_BRANCH_TOPIC = "기타 (분류되지 않은 대화)"


def get_active_branches(memory_dir: Path, project_id: str) -> List[Dict[str, Any]]:
    """
    프로젝트의 active 브랜치 목록 조회

    Args:
        memory_dir: 메모리 저장 디렉토리 (예: ~/.cortex/memory)
        project_id: 프로젝트 ID

    Returns:
        브랜치 목록: [{"branch_id": str, "branch_topic": str, "last_update": str}, ...]
    """
    project_dir = Path(memory_dir) / project_id
    index_file = project_dir / "_index.json"

    if not index_file.exists():
        return []

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            index = json.load(f)

        branches = []
        for branch_id, info in index.get("branches", {}).items():
            if info.get("status") == "active":
                branches.append({
                    "branch_id": branch_id,
                    "branch_topic": info.get("branch_topic", ""),
                    "last_update": info.get("last_update", "")
                })

        logger.debug(f"[BranchUtil] {project_id}: {len(branches)}개 active 브랜치")
        return branches

    except Exception as e:
        logger.error(f"[BranchUtil] 브랜치 목록 로드 실패: {e}")
        return []


def format_branches_for_ai(branches: List[Dict[str, Any]]) -> str:
    """
    AI가 브랜치를 선택할 수 있도록 포맷팅된 문자열 반환

    Args:
        branches: get_active_branches() 결과

    Returns:
        포맷팅된 브랜치 목록 문자열
    """
    if not branches:
        return "활성 브랜치 없음. 새 브랜치를 생성하거나 misc 브랜치를 사용하세요."

    lines = ["## 활성 브랜치 목록", ""]
    for b in branches:
        branch_id = b.get("branch_id", "unknown")
        topic = b.get("branch_topic", "(주제 없음)")
        lines.append(f"- **{branch_id}**: {topic}")

    lines.append("")
    lines.append("적절한 브랜치가 없으면 branch_id='misc' 또는 새 브랜치 생성을 요청하세요.")

    return "\n".join(lines)


# ============================================================================
# DEPRECATED: 아래 클래스들은 벤더 독립성을 위해 더 이상 사용되지 않음
# ============================================================================

class BranchMatcher:
    """
    DEPRECATED: 이 클래스는 더 이상 사용되지 않습니다.

    벤더 독립성 확보를 위해 자동 매칭 기능이 제거되었습니다.
    AI가 update_memory 호출 전에 적절한 branch_id를 결정해서 전달해야 합니다.

    대신 사용:
    - get_active_branches(): 브랜치 목록 조회
    - format_branches_for_ai(): AI용 포맷팅
    """

    SIMILARITY_THRESHOLD = 0.7
    MISC_BRANCH_ID = "misc"
    MISC_BRANCH_TOPIC = "기타 (분류되지 않은 대화)"

    def __init__(self, memory_dir: Path):
        import warnings
        warnings.warn(
            "BranchMatcher는 deprecated되었습니다. "
            "get_active_branches() 함수를 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        self.memory_dir = Path(memory_dir)

    def find_best_branch(self, project_id: str, content: str, exclude_misc: bool = True):
        """
        DEPRECATED: 항상 misc 반환

        AI가 브랜치를 선택해야 합니다.
        """
        import warnings
        warnings.warn(
            "find_best_branch()는 deprecated되었습니다. "
            "AI가 get_active_branches() 결과를 보고 branch_id를 결정해야 합니다.",
            DeprecationWarning,
            stacklevel=2
        )
        return (self.MISC_BRANCH_ID, 0.0, False)

    def _get_active_branches(self, project_id: str) -> List[Dict[str, Any]]:
        """DEPRECATED: get_active_branches() 함수 사용"""
        return get_active_branches(self.memory_dir, project_id)


# 하위 호환성을 위한 헬퍼
def get_branch_matcher(memory_dir: Path) -> BranchMatcher:
    """DEPRECATED: get_active_branches() 함수를 직접 사용하세요"""
    return BranchMatcher(memory_dir)
