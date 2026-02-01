"""
Cortex MCP - File I/O Utilities

파일 입출력 관련 유틸리티 함수:
- MD 파일 생성/파싱 (YAML Frontmatter)
- JSON 파일 로드/저장 (파일 잠금)
- 감사 로그 기록
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import portalocker
import yaml

logger = logging.getLogger(__name__)


class FileIO:
    """파일 I/O 유틸리티 클래스"""

    def __init__(self, memory_dir: Path, logs_dir: Path):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            logs_dir: 로그 저장 디렉토리
        """
        self.memory_dir = memory_dir
        self.logs_dir = logs_dir

    def create_md_content(self, frontmatter: Dict, body: str) -> str:
        """
        YAML Frontmatter + Body 형식의 MD 파일 생성

        Args:
            frontmatter: YAML frontmatter 데이터
            body: 본문 내용

        Returns:
            생성된 MD 파일 내용
        """
        yaml_content = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
        return f"---\n{yaml_content}---\n{body}"

    def parse_md_file(self, file_path: Path) -> Tuple[Dict, str]:
        """
        MD 파일에서 Frontmatter와 Body 분리

        Args:
            file_path: MD 파일 경로

        Returns:
            (frontmatter, body) 튜플
        """
        content = file_path.read_text(encoding="utf-8")

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
                return frontmatter, body

        return {}, content

    def save_json_with_lock(self, file_path: Path, data: Dict, max_retries: int = 3):
        """
        파일 잠금을 사용하여 JSON 파일을 안전하게 저장

        Args:
            file_path: 저장할 파일 경로
            data: 저장할 데이터
            max_retries: 최대 재시도 횟수

        Raises:
            Exception: 파일 잠금 실패 또는 저장 실패 시
        """
        for attempt in range(max_retries):
            try:
                # 부모 디렉토리 생성
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # 파일 잠금 및 저장
                with portalocker.Lock(file_path, mode='w', encoding='utf-8', timeout=5) as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return  # 성공
            except portalocker.exceptions.LockException:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # 점진적 대기
                    continue
                else:
                    raise Exception(
                        f"Failed to acquire lock on {file_path} after {max_retries} attempts"
                    )
            except Exception as e:
                raise Exception(f"Failed to save {file_path}: {e}")

    def load_project_index(self, project_id: str) -> Dict:
        """
        프로젝트 인덱스 파일 로드

        Args:
            project_id: 프로젝트 ID

        Returns:
            프로젝트 인덱스 데이터
        """
        project_dir = self.memory_dir / project_id
        index_file = project_dir / "_index.json"

        if index_file.exists():
            try:
                return json.loads(index_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        return {"version": "2.0", "revision": 0, "branches": {}}

    def save_project_index(self, project_id: str, index: Dict):
        """
        프로젝트 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)

        Args:
            project_id: 프로젝트 ID
            index: 저장할 인덱스 데이터
        """
        project_dir = self.memory_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        index_file = project_dir / "_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.save_json_with_lock(index_file, index)

    def load_branch_index(self, project_id: str, branch_id: str) -> Dict:
        """
        브랜치 인덱스 파일 로드

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID

        Returns:
            브랜치 인덱스 데이터
        """
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
        """
        브랜치 인덱스 파일 저장 (파일 잠금 사용 + 낙관적 잠금)

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            index: 저장할 인덱스 데이터
        """
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        branch_dir.mkdir(parents=True, exist_ok=True)

        index_file = branch_dir / "_branch_index.json"

        # 낙관적 잠금: revision 자동 증가
        current_revision = index.get("revision", 0)
        index["revision"] = current_revision + 1
        index["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.save_json_with_lock(index_file, index)

    def log_audit(self, action: str, data: Dict[str, Any]):
        """
        감사 로그 기록

        Args:
            action: 수행된 작업
            data: 로그 데이터
        """
        audit_file = self.logs_dir / "audit.json"

        try:
            audit_data = json.loads(audit_file.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            audit_data = {"version": "1.0.0", "entries": []}

        audit_data["entries"].append(
            {"timestamp": datetime.now(timezone.utc).isoformat(), "action": action, "data": data}
        )

        audit_file.write_text(
            json.dumps(audit_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
