"""
Cortex MCP - Index Handler
프로젝트/브랜치 인덱스 파일 I/O

기능:
- 프로젝트 인덱스 로드/저장
- 브랜치 인덱스 로드/저장
- 파일 잠금 지원
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import portalocker

logger = logging.getLogger(__name__)

# 타임아웃 설정
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from config import TimeoutConfig
except ImportError:
    class TimeoutConfig:
        FILE_LOCK_TIMEOUT = 5


class IndexHandler:
    """프로젝트/브랜치 인덱스 핸들러"""

    def __init__(self, memory_dir: Path):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
        """
        self.memory_dir = memory_dir

    def load_project_index(self, project_id: str) -> Dict:
        """프로젝트 인덱스 파일 로드"""
        project_dir = self.memory_dir / project_id
        index_file = project_dir / "_index.json"

        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        return {"version": "2.0", "revision": 0, "branches": {}}

    def save_json_with_lock(self, file_path: Path, data: Dict, max_retries: int = 3):
        """
        파일 잠금을 사용하여 JSON 파일을 안전하게 저장

        Args:
            file_path: 저장할 파일 경로
            data: 저장할 데이터
            max_retries: 최대 재시도 횟수
        """
        for attempt in range(max_retries):
            try:
                # 부모 디렉토리 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 파일 잠금 및 저장
                with portalocker.Lock(file_path, mode='w', encoding='utf-8', timeout=TimeoutConfig.FILE_LOCK_TIMEOUT) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return  # 성공
            except portalocker.exceptions.LockException:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    raise Exception(f"Failed to acquire lock on {file_path} after {max_retries} attempts")
            except Exception as e:
                raise Exception(f"Failed to save {file_path}: {e}")

    def save_project_index(self, project_id: str, index: Dict):
        """프로젝트 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)"""
        project_dir = self.memory_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        index_file = project_dir / "_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.save_json_with_lock(index_file, index)

    def load_branch_index(self, project_id: str, branch_id: str) -> Dict:
        """브랜치 인덱스 파일 로드"""
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        index_file = branch_dir / "_branch_index.json"

        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        return {
            "branch_id": branch_id,
            "branch_topic": "",
            "contexts": [],
            "nodes": [],
            "revision": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_branch_index(self, project_id: str, branch_id: str, index: Dict):
        """브랜치 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)"""
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        branch_dir.mkdir(parents=True, exist_ok=True)

        index_file = branch_dir / "_branch_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.save_json_with_lock(index_file, index)

    def update_project_index_branch(
        self,
        project_id: str,
        branch_id: str,
        branch_info: Dict[str, Any]
    ) -> bool:
        """
        프로젝트 인덱스의 브랜치 정보 업데이트

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            branch_info: 브랜치 정보

        Returns:
            성공 여부
        """
        try:
            index = self.load_project_index(project_id)
            if "branches" not in index:
                index["branches"] = {}
            index["branches"][branch_id] = branch_info
            self.save_project_index(project_id, index)
            return True
        except Exception as e:
            logger.error(f"프로젝트 인덱스 브랜치 업데이트 실패: {e}")
            return False

    def remove_branch_from_index(self, project_id: str, branch_id: str) -> bool:
        """
        프로젝트 인덱스에서 브랜치 제거

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            성공 여부
        """
        try:
            index = self.load_project_index(project_id)
            if "branches" in index and branch_id in index["branches"]:
                del index["branches"][branch_id]
                self.save_project_index(project_id, index)
            return True
        except Exception as e:
            logger.error(f"프로젝트 인덱스 브랜치 제거 실패: {e}")
            return False


# 모듈 레벨 팩토리 함수
def create_index_handler(memory_dir: Path) -> IndexHandler:
    """IndexHandler 인스턴스 생성"""
    return IndexHandler(memory_dir)
