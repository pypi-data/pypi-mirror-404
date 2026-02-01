"""
Cortex MCP - Backup Manager (Phase 7)
스냅샷 생성, 복구, 히스토리 관리

기능:
- 수동/자동 스냅샷 생성
- 특정 시점으로 복원
- 버전 히스토리 관리
- 스냅샷 비교
"""

import hashlib
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from config import config

logger = logging.getLogger(__name__)

# Telemetry (사용 지표 자동 수집)
try:
    from core.telemetry_decorator import track_call

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

    # Noop decorator when telemetry not available
    def track_call(module_name: str):
        def decorator(func):
            return func

        return decorator


class BackupManager:
    """백업 및 스냅샷 관리자"""

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        Args:
            memory_dir: 메모리 디렉토리 경로 (기본값: config.memory_dir)
        """
        self.memory_dir = memory_dir if memory_dir is not None else config.memory_dir
        self.backup_dir = config.cortex_home / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_snapshots_per_project = 20  # 프로젝트당 최대 스냅샷 수

    @track_call("backup_manager")
    def create_snapshot(
        self,
        project_id: str,
        description: str = "",
        snapshot_type: str = "manual",
        branch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        스냅샷 생성

        Args:
            project_id: 프로젝트 ID
            description: 스냅샷 설명
            snapshot_type: 스냅샷 타입 (manual, auto, git_commit)
            branch_id: 특정 브랜치만 스냅샷 (None이면 전체)

        Returns:
            생성 결과
        """
        project_dir = self.memory_dir / project_id

        if not project_dir.exists():
            return {"success": False, "error": f"Project '{project_id}' not found"}

        try:
            # 스냅샷 ID 생성 (밀리초 포함으로 고유성 보장)
            timestamp = datetime.now(timezone.utc)
            snapshot_id = f"snap_{timestamp.strftime('%Y%m%d_%H%M%S%f')[:20]}_{snapshot_type[:4]}"

            # 스냅샷 디렉토리 생성
            snapshot_dir = self.backup_dir / project_id / snapshot_id
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # 데이터 복사
            if branch_id:
                # 특정 브랜치만 복사
                source_dir = project_dir / "contexts" / branch_id
                if source_dir.exists():
                    dest_dir = snapshot_dir / "contexts" / branch_id
                    shutil.copytree(source_dir, dest_dir)

                # 인덱스 파일에서 해당 브랜치 정보만 추출
                index_file = project_dir / "_index.json"
                if index_file.exists():
                    with open(index_file, "r", encoding="utf-8") as f:
                        index_data = json.load(f)

                    branch_index = {
                        "project_id": project_id,
                        "branches": {branch_id: index_data.get("branches", {}).get(branch_id, {})},
                    }
                    with open(snapshot_dir / "_index.json", "w", encoding="utf-8") as f:
                        json.dump(branch_index, f, ensure_ascii=False, indent=2)
            else:
                # 전체 프로젝트 복사
                for item in project_dir.iterdir():
                    if item.is_file():
                        shutil.copy2(item, snapshot_dir / item.name)
                    elif item.is_dir():
                        shutil.copytree(item, snapshot_dir / item.name)

            # 메타데이터 생성
            metadata = {
                "snapshot_id": snapshot_id,
                "project_id": project_id,
                "branch_id": branch_id,
                "description": description,
                "snapshot_type": snapshot_type,
                "created_at": timestamp.isoformat(),
                "checksum": self._calculate_checksum(snapshot_dir),
                "file_count": sum(1 for _ in snapshot_dir.rglob("*") if _.is_file()),
                "size_bytes": sum(f.stat().st_size for f in snapshot_dir.rglob("*") if f.is_file()),
            }

            # 메타데이터 저장
            with open(snapshot_dir / "_snapshot_meta.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 오래된 스냅샷 정리
            self._cleanup_old_snapshots(project_id)

            logger.info(f"Snapshot created: {snapshot_id} for project {project_id}")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "project_id": project_id,
                "created_at": timestamp.isoformat(),
                "description": description,
                "file_count": metadata["file_count"],
                "size_bytes": metadata["size_bytes"],
            }

        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return {"success": False, "error": str(e)}

    @track_call("backup_manager")
    def restore_snapshot(
        self, project_id: str, snapshot_id: str, overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        스냅샷에서 복원

        Args:
            project_id: 프로젝트 ID
            snapshot_id: 복원할 스냅샷 ID
            overwrite: 기존 데이터 덮어쓰기 여부 (True: 경고 없이 덮어쓰기)

        Returns:
            복원 결과

        WARNING:
            이 작업은 현재 프로젝트 데이터를 완전히 대체합니다.
            복원 전 자동으로 현재 상태를 백업하지만,
            중요한 작업 중에는 수동 백업을 권장합니다.
        """
        snapshot_dir = self.backup_dir / project_id / snapshot_id

        if not snapshot_dir.exists():
            return {"success": False, "error": f"Snapshot '{snapshot_id}' not found"}

        # 스냅샷 메타데이터 읽기 (복원 전 정보 제공)
        meta_file = snapshot_dir / "_snapshot_meta.json"
        snapshot_info = {}
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    snapshot_meta = json.load(f)
                    snapshot_info = {
                        "created_at": snapshot_meta.get("created_at"),
                        "description": snapshot_meta.get("description"),
                        "snapshot_type": snapshot_meta.get("snapshot_type"),
                        "file_count": snapshot_meta.get("file_count"),
                    }
            except Exception:
                pass

        # 복원 확인 메시지 (overwrite=False일 때만)
        if not overwrite:
            logger.warning(
                f"[RESTORE_WARNING] Preparing to restore snapshot '{snapshot_id}'\n"
                f"  - Created: {snapshot_info.get('created_at', 'unknown')}\n"
                f"  - Description: {snapshot_info.get('description', 'N/A')}\n"
                f"  - Type: {snapshot_info.get('snapshot_type', 'unknown')}\n"
                f"  - Files: {snapshot_info.get('file_count', '?')}\n"
                f"  - Current data will be backed up automatically before restore.\n"
                f"  - To skip this check, use overwrite=True parameter."
            )

        try:
            project_dir = self.memory_dir / project_id

            # 기존 데이터 백업 (복원 전 자동 스냅샷)
            if project_dir.exists() and not overwrite:
                pre_restore_snapshot = self.create_snapshot(
                    project_id,
                    description=f"Auto backup before restore from {snapshot_id}",
                    snapshot_type="pre_restore",
                )
                if not pre_restore_snapshot.get("success"):
                    return {"success": False, "error": "Failed to create pre-restore backup"}

            # 기존 데이터 삭제
            if project_dir.exists():
                shutil.rmtree(project_dir)

            # 스냅샷에서 복원
            project_dir.mkdir(parents=True, exist_ok=True)

            for item in snapshot_dir.iterdir():
                if item.name == "_snapshot_meta.json":
                    continue  # 메타데이터는 복원하지 않음
                if item.is_file():
                    shutil.copy2(item, project_dir / item.name)
                elif item.is_dir():
                    shutil.copytree(item, project_dir / item.name)

            # ========================================================================
            # 즉시 검증 (변경에 대한 책임)
            # ========================================================================
            try:
                # 1. 스냅샷 메타데이터 읽기
                meta_file = snapshot_dir / "_snapshot_meta.json"
                if not meta_file.exists():
                    raise Exception("Snapshot metadata not found")

                with open(meta_file, "r", encoding="utf-8") as f:
                    snapshot_metadata = json.load(f)

                expected_checksum = snapshot_metadata.get("checksum")
                expected_file_count = snapshot_metadata.get("file_count")

                # 2. 복원된 데이터의 checksum 계산
                actual_checksum = self._calculate_checksum(project_dir)
                actual_file_count = sum(1 for _ in project_dir.rglob("*") if _.is_file())

                # 3. 검증
                verification_errors = []

                if actual_checksum != expected_checksum:
                    verification_errors.append(
                        f"Checksum mismatch: expected={expected_checksum}, actual={actual_checksum}"
                    )

                if actual_file_count != expected_file_count:
                    verification_errors.append(
                        f"File count mismatch: expected={expected_file_count}, actual={actual_file_count}"
                    )

                # 4. 검증 실패 시 롤백
                if verification_errors:
                    logger.error(f"Snapshot restore verification failed: {verification_errors}")

                    # pre_restore 스냅샷으로 롤백 (있는 경우)
                    rollback_performed = False
                    if pre_restore_snapshot and pre_restore_snapshot.get("success"):
                        try:
                            pre_restore_id = pre_restore_snapshot["snapshot_id"]
                            pre_restore_dir = self.backup_dir / project_id / pre_restore_id

                            if pre_restore_dir.exists():
                                # 복원 실패한 데이터 삭제
                                if project_dir.exists():
                                    shutil.rmtree(project_dir)

                                # pre_restore 스냅샷에서 복원
                                project_dir.mkdir(parents=True, exist_ok=True)

                                for item in pre_restore_dir.iterdir():
                                    if item.name == "_snapshot_meta.json":
                                        continue
                                    if item.is_file():
                                        shutil.copy2(item, project_dir / item.name)
                                    elif item.is_dir():
                                        shutil.copytree(item, project_dir / item.name)

                                rollback_performed = True
                                logger.info(f"Rolled back to pre-restore snapshot: {pre_restore_id}")

                        except Exception as rollback_error:
                            logger.error(f"Rollback failed: {rollback_error}")

                    return {
                        "success": False,
                        "error": "Snapshot restore verification failed",
                        "verification_failed": "integrity_check",
                        "verification_errors": verification_errors,
                        "rollback_performed": rollback_performed,
                    }

            except Exception as verify_error:
                logger.error(f"Snapshot restore verification error: {verify_error}")

                # 검증 중 오류 발생 시 롤백
                rollback_performed = False
                if pre_restore_snapshot and pre_restore_snapshot.get("success"):
                    try:
                        pre_restore_id = pre_restore_snapshot["snapshot_id"]
                        pre_restore_dir = self.backup_dir / project_id / pre_restore_id

                        if pre_restore_dir.exists():
                            # 복원 실패한 데이터 삭제
                            if project_dir.exists():
                                shutil.rmtree(project_dir)

                            # pre_restore 스냅샷에서 복원
                            project_dir.mkdir(parents=True, exist_ok=True)

                            for item in pre_restore_dir.iterdir():
                                if item.name == "_snapshot_meta.json":
                                    continue
                                if item.is_file():
                                    shutil.copy2(item, project_dir / item.name)
                                elif item.is_dir():
                                    shutil.copytree(item, project_dir / item.name)

                            rollback_performed = True
                            logger.info(f"Rolled back to pre-restore snapshot after error: {pre_restore_id}")

                    except Exception as rollback_error:
                        logger.error(f"Rollback after verification error failed: {rollback_error}")

                return {
                    "success": False,
                    "error": f"Snapshot restore verification error: {str(verify_error)}",
                    "verification_failed": "verification_error",
                    "rollback_performed": rollback_performed,
                }

            # 복원 기록 추가
            self._add_restore_record(project_id, snapshot_id)

            logger.info(f"Restored snapshot {snapshot_id} for project {project_id}")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "project_id": project_id,
                "restored_at": datetime.now(timezone.utc).isoformat(),
                "message": f"Successfully restored from snapshot '{snapshot_id}'",
                "verified": True,  # 검증 완료 표시
            }

        except Exception as e:
            logger.error(f"Failed to restore snapshot: {e}")
            return {"success": False, "error": str(e)}

    @track_call("backup_manager")
    def list_snapshots(
        self, project_id: str, snapshot_type: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """
        스냅샷 목록 조회

        Args:
            project_id: 프로젝트 ID
            snapshot_type: 필터링할 스냅샷 타입
            limit: 최대 결과 수

        Returns:
            스냅샷 목록
        """
        project_backup_dir = self.backup_dir / project_id

        if not project_backup_dir.exists():
            return {"snapshots": [], "count": 0, "project_id": project_id}

        snapshots = []

        for snapshot_dir in sorted(project_backup_dir.iterdir(), reverse=True):
            if not snapshot_dir.is_dir():
                continue

            meta_file = snapshot_dir / "_snapshot_meta.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)

                    # 타입 필터링
                    if snapshot_type and metadata.get("snapshot_type") != snapshot_type:
                        continue

                    snapshots.append(metadata)

                    if len(snapshots) >= limit:
                        break
                except:
                    continue

        return {"snapshots": snapshots, "count": len(snapshots), "project_id": project_id}

    def get_snapshot_info(self, project_id: str, snapshot_id: str) -> Dict[str, Any]:
        """스냅샷 상세 정보 조회"""
        snapshot_dir = self.backup_dir / project_id / snapshot_id
        meta_file = snapshot_dir / "_snapshot_meta.json"

        if not meta_file.exists():
            return {"success": False, "error": f"Snapshot '{snapshot_id}' not found"}

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # 파일 목록 추가
            files = []
            for f in snapshot_dir.rglob("*"):
                if f.is_file() and f.name != "_snapshot_meta.json":
                    files.append(
                        {
                            "path": str(f.relative_to(snapshot_dir)),
                            "size": f.stat().st_size,
                        }
                    )

            metadata["files"] = files
            metadata["success"] = True

            return metadata

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_snapshot(self, project_id: str, snapshot_id: str) -> Dict[str, Any]:
        """스냅샷 삭제"""
        snapshot_dir = self.backup_dir / project_id / snapshot_id

        if not snapshot_dir.exists():
            return {"success": False, "error": f"Snapshot '{snapshot_id}' not found"}

        try:
            shutil.rmtree(snapshot_dir)
            logger.info(f"Deleted snapshot {snapshot_id} for project {project_id}")

            return {
                "success": True,
                "snapshot_id": snapshot_id,
                "message": f"Snapshot '{snapshot_id}' deleted",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def compare_snapshots(
        self, project_id: str, snapshot_id_1: str, snapshot_id_2: str
    ) -> Dict[str, Any]:
        """
        두 스냅샷 비교

        Returns:
            차이점 정보
        """
        dir1 = self.backup_dir / project_id / snapshot_id_1
        dir2 = self.backup_dir / project_id / snapshot_id_2

        if not dir1.exists() or not dir2.exists():
            return {"success": False, "error": "One or both snapshots not found"}

        try:
            files1 = {str(f.relative_to(dir1)): f for f in dir1.rglob("*") if f.is_file()}
            files2 = {str(f.relative_to(dir2)): f for f in dir2.rglob("*") if f.is_file()}

            # 추가된 파일
            added = [f for f in files2.keys() if f not in files1 and f != "_snapshot_meta.json"]

            # 삭제된 파일
            removed = [f for f in files1.keys() if f not in files2 and f != "_snapshot_meta.json"]

            # 수정된 파일
            modified = []
            for f in files1.keys():
                if f in files2 and f != "_snapshot_meta.json":
                    if files1[f].stat().st_size != files2[f].stat().st_size:
                        modified.append(f)
                    elif self._file_checksum(files1[f]) != self._file_checksum(files2[f]):
                        modified.append(f)

            return {
                "success": True,
                "snapshot_1": snapshot_id_1,
                "snapshot_2": snapshot_id_2,
                "added": added,
                "removed": removed,
                "modified": modified,
                "total_changes": len(added) + len(removed) + len(modified),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_history(self, project_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        프로젝트의 변경 히스토리 조회

        스냅샷과 복원 기록을 통합하여 타임라인 형태로 반환
        """
        history = []

        # 스냅샷 기록
        snapshots = self.list_snapshots(project_id, limit=limit)
        for snap in snapshots.get("snapshots", []):
            history.append(
                {
                    "type": "snapshot",
                    "id": snap.get("snapshot_id"),
                    "timestamp": snap.get("created_at"),
                    "description": snap.get("description", ""),
                    "snapshot_type": snap.get("snapshot_type"),
                }
            )

        # 복원 기록
        restore_file = self.backup_dir / project_id / "_restore_history.json"
        if restore_file.exists():
            try:
                with open(restore_file, "r", encoding="utf-8") as f:
                    restore_data = json.load(f)
                for record in restore_data.get("records", [])[-limit:]:
                    history.append(
                        {
                            "type": "restore",
                            "id": record.get("snapshot_id"),
                            "timestamp": record.get("restored_at"),
                            "description": f"Restored from {record.get('snapshot_id')}",
                        }
                    )
            except:
                pass

        # 시간순 정렬
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {"project_id": project_id, "history": history[:limit], "count": len(history[:limit])}

    def _calculate_checksum(self, directory: Path) -> str:
        """디렉토리 체크섬 계산"""
        hasher = hashlib.sha256()

        for file_path in sorted(directory.rglob("*")):
            if file_path.is_file() and file_path.name != "_snapshot_meta.json":
                hasher.update(str(file_path.relative_to(directory)).encode())
                hasher.update(str(file_path.stat().st_size).encode())

        return hasher.hexdigest()

    def _file_checksum(self, file_path: Path) -> str:
        """파일 체크섬 계산"""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _cleanup_old_snapshots(self, project_id: str):
        """오래된 스냅샷 정리"""
        project_backup_dir = self.backup_dir / project_id

        if not project_backup_dir.exists():
            return

        snapshots = []
        for snapshot_dir in project_backup_dir.iterdir():
            if snapshot_dir.is_dir() and snapshot_dir.name.startswith("snap_"):
                meta_file = snapshot_dir / "_snapshot_meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        snapshots.append((snapshot_dir, metadata.get("created_at", "")))
                    except:
                        pass

        # 생성일 기준 정렬
        snapshots.sort(key=lambda x: x[1], reverse=True)

        # 최대 개수 초과분 삭제
        for snapshot_dir, _ in snapshots[self.max_snapshots_per_project :]:
            try:
                shutil.rmtree(snapshot_dir)
                logger.info(f"Cleaned up old snapshot: {snapshot_dir.name}")
            except:
                pass

    def _add_restore_record(self, project_id: str, snapshot_id: str):
        """복원 기록 추가"""
        restore_file = self.backup_dir / project_id / "_restore_history.json"

        records = {"records": []}
        if restore_file.exists():
            try:
                with open(restore_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except:
                pass

        records["records"].append(
            {"snapshot_id": snapshot_id, "restored_at": datetime.now(timezone.utc).isoformat()}
        )

        # 최근 50개만 유지
        records["records"] = records["records"][-50:]

        with open(restore_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)


# 전역 인스턴스
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """BackupManager 싱글톤"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


# ============================================================================
# MCP Tool Interface Functions (4개)
# memory_manager.py에서 호출하는 모듈 레벨 함수들
# ============================================================================


def create_snapshot(
    project_id: str,
    branch_id: Optional[str] = None,
    description: Optional[str] = None,
    snapshot_type: str = "manual",
) -> Dict[str, Any]:
    """
    프로젝트 스냅샷 생성 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        branch_id: 특정 브랜치만 스냅샷 (선택)
        description: 스냅샷 설명
        snapshot_type: 스냅샷 유형 (manual/auto/git_commit)

    Returns:
        스냅샷 생성 결과
    """
    manager = get_backup_manager()

    # BackupManager.create_snapshot의 파라미터 순서에 맞춤
    return manager.create_snapshot(
        project_id=project_id,
        description=description or "",
        snapshot_type=snapshot_type,
        branch_id=branch_id,
    )


def restore_snapshot(project_id: str, snapshot_id: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    스냅샷에서 복원 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        snapshot_id: 복원할 스냅샷 ID
        overwrite: 자동 백업 없이 덮어쓰기

    Returns:
        복원 결과
    """
    manager = get_backup_manager()
    return manager.restore_snapshot(
        project_id=project_id, snapshot_id=snapshot_id, overwrite=overwrite
    )


def list_snapshots(
    project_id: str, snapshot_type: Optional[str] = None, limit: int = 20
) -> Dict[str, Any]:
    """
    스냅샷 목록 조회 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        snapshot_type: 특정 타입만 필터링 (선택)
        limit: 최대 결과 수

    Returns:
        스냅샷 목록
    """
    manager = get_backup_manager()
    return manager.list_snapshots(project_id=project_id, snapshot_type=snapshot_type, limit=limit)


def get_backup_history(project_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    백업 히스토리 조회 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        limit: 최대 결과 수

    Returns:
        백업 히스토리 타임라인
    """
    manager = get_backup_manager()
    # BackupManager.get_history를 호출
    return manager.get_history(project_id=project_id, limit=limit)
