"""
Cortex MCP - Project Config Module (.cortexrc 관리)
프로젝트 고유 ID를 .cortexrc 파일로 관리하여 PC 마이그레이션 시에도 일관성 유지

핵심 기능:
- .cortexrc 파일 생성/읽기/업데이트
- Git remote URL 기반 자동 ID 생성
- Hybrid 방식: .cortexrc > Git URL > Random ID

PC 마이그레이션 시나리오:
1. 기존 PC: .cortexrc를 Git에 커밋
2. 새 PC: Git clone 시 .cortexrc도 함께 클론됨
3. Cortex 초기화 시 .cortexrc 읽어서 동일한 project_id 사용
"""

import hashlib
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class ProjectConfig:
    """프로젝트 설정 관리 (.cortexrc)"""

    CONFIG_FILENAME = ".cortexrc"

    def __init__(self, project_path: str):
        """
        Args:
            project_path: 프로젝트 루트 경로
        """
        self.project_path = Path(project_path).resolve()
        self.config_file = self.project_path / self.CONFIG_FILENAME

    def get_project_id(self) -> str:
        """
        프로젝트 ID 가져오기 (Hybrid 방식)

        우선순위:
        1. .cortexrc 파일이 있으면 → 파일의 project_id 사용
        2. Git remote가 있으면 → Git URL 해시 사용
        3. 둘 다 없으면 → 랜덤 ID 생성 후 .cortexrc에 저장

        Returns:
            프로젝트 고유 ID (12자리 16진수)
        """
        # 1. .cortexrc 파일 확인
        if self.config_file.exists():
            try:
                config = self.load_config()
                project_id = config.get("project_id")
                if project_id:
                    logger.info(f"Loaded project_id from .cortexrc: {project_id}")
                    return project_id
            except Exception as e:
                logger.warning(f"Failed to read .cortexrc: {e}")

        # 2. Git remote URL 확인
        git_project_id = self._get_git_based_id()
        if git_project_id:
            logger.info(f"Generated project_id from Git remote: {git_project_id}")
            # .cortexrc에 저장
            self.save_config(
                project_id=git_project_id,
                source="git_remote",
            )
            return git_project_id

        # 3. 랜덤 ID 생성
        random_id = self._generate_random_id()
        logger.info(f"Generated random project_id: {random_id}")
        # .cortexrc에 저장
        self.save_config(
            project_id=random_id,
            source="random",
        )
        return random_id

    def load_config(self) -> Dict:
        """
        .cortexrc 파일 읽기

        Returns:
            설정 딕셔너리
        """
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load .cortexrc: {e}")
            return {}

    def save_config(
        self,
        project_id: str,
        project_name: Optional[str] = None,
        source: str = "manual",
    ) -> None:
        """
        .cortexrc 파일 저장

        Args:
            project_id: 프로젝트 고유 ID
            project_name: 프로젝트 이름 (선택)
            source: ID 생성 방식 (git_remote, random, manual)
        """
        config = {
            "project_id": project_id,
            "project_name": project_name or self.project_path.name,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved .cortexrc: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save .cortexrc: {e}")

    def update_config(self, **kwargs) -> None:
        """
        .cortexrc 파일 업데이트 (기존 값 유지)

        Args:
            **kwargs: 업데이트할 필드
        """
        config = self.load_config()
        config.update(kwargs)
        config["last_updated"] = datetime.now(timezone.utc).isoformat()

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated .cortexrc: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to update .cortexrc: {e}")

    def _get_git_based_id(self) -> Optional[str]:
        """
        Git remote URL 기반 프로젝트 ID 생성

        Returns:
            Git URL 해시 (12자리) 또는 None
        """
        try:
            # Git remote URL 가져오기
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if remote_url:
                    # URL 정규화 (.git 제거)
                    remote_url = remote_url.rstrip("/")
                    if remote_url.endswith(".git"):
                        remote_url = remote_url[:-4]

                    # SHA256 해시 생성 (첫 12자리)
                    hash_obj = hashlib.sha256(remote_url.encode())
                    return hash_obj.hexdigest()[:12]

        except Exception as e:
            logger.debug(f"Git remote not found or error: {e}")

        return None

    def _generate_random_id(self) -> str:
        """
        랜덤 프로젝트 ID 생성

        Returns:
            랜덤 해시 (12자리)
        """
        import secrets

        random_bytes = secrets.token_bytes(16)
        return hashlib.sha256(random_bytes).hexdigest()[:12]

    def ensure_config_exists(self) -> str:
        """
        .cortexrc 파일이 없으면 생성

        Returns:
            프로젝트 ID
        """
        return self.get_project_id()


def get_project_id(project_path: str) -> str:
    """
    프로젝트 ID 가져오기 (Helper 함수)

    Args:
        project_path: 프로젝트 루트 경로

    Returns:
        프로젝트 고유 ID
    """
    config = ProjectConfig(project_path)
    return config.get_project_id()


def create_cortexrc(project_path: str, project_id: Optional[str] = None) -> str:
    """
    .cortexrc 파일 생성 (Helper 함수)

    Args:
        project_path: 프로젝트 루트 경로
        project_id: 프로젝트 ID (없으면 자동 생성)

    Returns:
        생성된 프로젝트 ID
    """
    config = ProjectConfig(project_path)

    if project_id:
        # 수동 ID 지정
        config.save_config(project_id=project_id, source="manual")
        return project_id
    else:
        # 자동 ID 생성
        return config.get_project_id()
