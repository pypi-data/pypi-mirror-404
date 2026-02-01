"""
Cortex MCP - Cloud Sync Module
Google Drive 동기화 모듈

기능:
- Google Drive 업로드/다운로드
- 라이센스키 기반 E2E 암호화
- 환경 독립적 맥락 복구
"""

import io
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent.parent))
from config import config

from .crypto_utils import CryptoUtils


class CloudSync:
    """클라우드 동기화 - Google Drive 연동"""

    def __init__(self, license_key: Optional[str] = None):
        self.memory_dir = config.memory_dir
        self.drive_folder = config.google_drive_folder
        self.license_key = license_key
        self.crypto = CryptoUtils(license_key) if license_key else None

        # Google API 클라이언트 (지연 초기화)
        self._drive_service = None

    def _init_drive_service(self):
        """Google Drive API 서비스 초기화"""
        if self._drive_service is None:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            creds = None

            token_path = config.base_dir / "token.json"
            credentials_path = config.base_dir / "credentials.json"

            # 기존 토큰 확인
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # 토큰 갱신 또는 새로 인증
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path.exists():
                        raise FileNotFoundError(
                            f"Google API 자격 증명 파일이 필요합니다: {credentials_path}"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # 토큰 저장
                token_path.write_text(creds.to_json())

            self._drive_service = build("drive", "v3", credentials=creds)

        return self._drive_service

    def _get_or_create_folder(self) -> str:
        """Cortex 전용 폴더 ID 가져오기 (없으면 생성)"""
        service = self._init_drive_service()

        # 폴더 검색
        query = f"name='{self.drive_folder}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
        folders = results.get("files", [])

        if folders:
            return folders[0]["id"]

        # 폴더 생성
        file_metadata = {
            "name": self.drive_folder,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        return folder.get("id")

    def sync_to_cloud(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        로컬 메모리를 Google Drive에 업로드

        Args:
            project_id: 특정 프로젝트만 동기화 (없으면 전체)

        Returns:
            동기화 결과
        """
        if not self.license_key:
            return {"success": False, "error": "라이센스 키가 필요합니다."}

        service = self._init_drive_service()
        folder_id = self._get_or_create_folder()

        # 동기화할 파일 목록
        if project_id:
            project_dirs = [self.memory_dir / project_id]
        else:
            project_dirs = [d for d in self.memory_dir.iterdir() if d.is_dir()]

        uploaded_files = []

        for project_dir in project_dirs:
            if not project_dir.exists():
                continue

            for md_file in project_dir.glob("*.md"):
                # 파일 내용 읽기
                content = md_file.read_bytes()

                # 암호화
                encrypted_content = self.crypto.encrypt(content)

                # 메타데이터 생성
                backup_name = f"{project_dir.name}_{md_file.name}.enc"

                # 기존 파일 확인
                query = f"name='{backup_name}' and '{folder_id}' in parents and trashed=false"
                existing = service.files().list(q=query, fields="files(id)").execute()

                from googleapiclient.http import MediaIoBaseUpload

                media = MediaIoBaseUpload(
                    io.BytesIO(encrypted_content),
                    mimetype="application/octet-stream",
                    resumable=True,
                )

                if existing.get("files"):
                    # 업데이트
                    file_id = existing["files"][0]["id"]
                    service.files().update(fileId=file_id, media_body=media).execute()
                else:
                    # 새로 업로드
                    file_metadata = {"name": backup_name, "parents": [folder_id]}
                    service.files().create(
                        body=file_metadata, media_body=media, fields="id"
                    ).execute()

                uploaded_files.append(backup_name)

        # Save sync status to local file for dashboard display
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        status_file = config.base_dir / "cloud_sync_status.json"
        try:
            with open(status_file, 'w') as f:
                json.dump({
                    "last_sync": sync_timestamp,
                    "uploaded_count": len(uploaded_files),
                    "success": True
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cloud sync status: {e}")

        return {
            "success": True,
            "uploaded_count": len(uploaded_files),
            "files": uploaded_files,
            "timestamp": sync_timestamp,
        }

    def sync_from_cloud(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Google Drive에서 로컬로 복원

        Args:
            project_id: 특정 프로젝트만 복원 (없으면 전체)

        Returns:
            복원 결과
        """
        if not self.license_key:
            return {"success": False, "error": "라이센스 키가 필요합니다."}

        service = self._init_drive_service()
        folder_id = self._get_or_create_folder()

        # 클라우드의 파일 목록
        query = f"'{folder_id}' in parents and trashed=false"
        if project_id:
            query += f" and name contains '{project_id}_'"

        results = service.files().list(q=query, fields="files(id, name)").execute()

        files = results.get("files", [])
        restored_files = []

        for file_info in files:
            if not file_info["name"].endswith(".enc"):
                continue

            # 파일 다운로드
            from googleapiclient.http import MediaIoBaseDownload

            request = service.files().get_media(fileId=file_info["id"])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                _, done = downloader.next_chunk()

            # 복호화
            encrypted_content = fh.getvalue()
            try:
                decrypted_content = self.crypto.decrypt(encrypted_content)
            except Exception as e:
                continue  # 복호화 실패 시 건너뛰기

            # 파일명 파싱 (project_id_filename.md.enc)
            backup_name = file_info["name"][:-4]  # .enc 제거
            parts = backup_name.split("_", 1)
            if len(parts) != 2:
                continue

            proj_id, filename = parts

            # 로컬에 저장
            project_dir = self.memory_dir / proj_id
            project_dir.mkdir(parents=True, exist_ok=True)

            local_path = project_dir / filename

            # 충돌 감지: 로컬 파일이 있으면 백업
            if local_path.exists():
                backup_path = local_path.with_suffix(local_path.suffix + ".backup")
                local_path.rename(backup_path)
                logger.warning(
                    f"Conflict detected: Local file backed up to {backup_path.name}"
                )

            local_path.write_bytes(decrypted_content)

            restored_files.append(str(local_path))

        # Save sync status to local file for dashboard display
        sync_timestamp = datetime.now(timezone.utc).isoformat()
        status_file = config.base_dir / "cloud_sync_status.json"
        try:
            with open(status_file, 'w') as f:
                json.dump({
                    "last_sync": sync_timestamp,
                    "restored_count": len(restored_files),
                    "success": True
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cloud sync status: {e}")

        return {
            "success": True,
            "restored_count": len(restored_files),
            "files": restored_files,
            "timestamp": sync_timestamp,
        }

    def list_cloud_backups(self) -> List[Dict[str, Any]]:
        """클라우드 백업 목록 조회"""
        service = self._init_drive_service()
        folder_id = self._get_or_create_folder()

        query = f"'{folder_id}' in parents and trashed=false"
        results = (
            service.files().list(q=query, fields="files(id, name, modifiedTime, size)").execute()
        )

        return results.get("files", [])
