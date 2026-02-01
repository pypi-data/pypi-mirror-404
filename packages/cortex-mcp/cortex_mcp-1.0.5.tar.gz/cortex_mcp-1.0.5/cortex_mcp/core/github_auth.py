"""
Cortex MCP - GitHub OAuth Authentication (Device Flow)
GitHub 계정 기반 인증 시스템

Device Flow를 사용하여 서버 없이 CLI에서 OAuth 인증 가능
"""

import hashlib
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Cortex OAuth App 설정
# GitHub OAuth App 등록 후 Client ID 설정 필요
# https://github.com/settings/developers 에서 등록
GITHUB_CLIENT_ID = "CORTEX_GITHUB_CLIENT_ID"  # 실제 배포 시 설정
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL = "https://api.github.com/user"


class GitHubAuth:
    """GitHub OAuth 인증 관리자"""

    def __init__(self):
        from config import config

        self.auth_file = config.cortex_home / "github_auth.json"
        self.client_id = GITHUB_CLIENT_ID

    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        auth_data = self._load_auth_data()
        if not auth_data:
            return False

        # 토큰 만료 확인
        expires_at = auth_data.get("expires_at")
        if expires_at:
            try:
                exp_time = datetime.fromisoformat(expires_at)
                if datetime.now(timezone.utc) > exp_time:
                    return False
            except:
                pass

        # 토큰 유효성 확인
        access_token = auth_data.get("access_token")
        if access_token:
            user_info = self._get_user_info(access_token)
            return user_info is not None

        return False

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """현재 인증된 사용자 정보 반환"""
        auth_data = self._load_auth_data()
        if not auth_data:
            return None

        access_token = auth_data.get("access_token")
        if not access_token:
            return None

        return self._get_user_info(access_token)

    def start_device_flow(self) -> Dict[str, Any]:
        """
        Device Flow 시작

        Returns:
            device_code, user_code, verification_uri 등
        """
        if self.client_id == "CORTEX_GITHUB_CLIENT_ID":
            return {
                "success": False,
                "error": "GitHub OAuth App not configured. Please set GITHUB_CLIENT_ID.",
                "setup_required": True,
            }

        try:
            data = urllib.parse.urlencode(
                {"client_id": self.client_id, "scope": "read:user user:email"}
            ).encode()

            req = urllib.request.Request(
                GITHUB_DEVICE_CODE_URL, data=data, headers={"Accept": "application/json"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode())

            return {
                "success": True,
                "device_code": result["device_code"],
                "user_code": result["user_code"],
                "verification_uri": result["verification_uri"],
                "expires_in": result["expires_in"],
                "interval": result.get("interval", 5),
            }

        except Exception as e:
            logger.error(f"Device flow start failed: {e}")
            return {"success": False, "error": str(e)}

    def poll_for_token(
        self, device_code: str, interval: int = 5, timeout: int = 300
    ) -> Dict[str, Any]:
        """
        사용자 인증 완료 대기 및 토큰 획득

        Args:
            device_code: start_device_flow에서 받은 device_code
            interval: 폴링 간격 (초)
            timeout: 최대 대기 시간 (초)
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                data = urllib.parse.urlencode(
                    {
                        "client_id": self.client_id,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    }
                ).encode()

                req = urllib.request.Request(
                    GITHUB_ACCESS_TOKEN_URL, data=data, headers={"Accept": "application/json"}
                )

                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode())

                if "access_token" in result:
                    # 토큰 획득 성공
                    access_token = result["access_token"]

                    # 사용자 정보 조회
                    user_info = self._get_user_info(access_token)
                    if not user_info:
                        return {"success": False, "error": "Failed to get user info"}

                    # 인증 정보 저장
                    auth_data = {
                        "access_token": access_token,
                        "token_type": result.get("token_type", "bearer"),
                        "scope": result.get("scope", ""),
                        "github_id": user_info["id"],
                        "github_login": user_info["login"],
                        "github_email": user_info.get("email"),
                        "authenticated_at": datetime.now(timezone.utc).isoformat(),
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(days=365)
                        ).isoformat(),
                    }

                    self._save_auth_data(auth_data)

                    logger.info(f"GitHub authentication successful: {user_info['login']}")

                    return {
                        "success": True,
                        "github_login": user_info["login"],
                        "github_id": user_info["id"],
                        "github_email": user_info.get("email"),
                    }

                error = result.get("error")
                if error == "authorization_pending":
                    # 아직 사용자가 인증하지 않음
                    time.sleep(interval)
                    continue
                elif error == "slow_down":
                    # 폴링 간격 증가 필요
                    interval += 5
                    time.sleep(interval)
                    continue
                elif error == "expired_token":
                    return {"success": False, "error": "Device code expired. Please try again."}
                elif error == "access_denied":
                    return {"success": False, "error": "User denied access."}
                else:
                    return {"success": False, "error": f"Unknown error: {error}"}

            except Exception as e:
                logger.error(f"Token polling error: {e}")
                time.sleep(interval)
                continue

        return {"success": False, "error": "Authentication timeout"}

    def authenticate_interactive(self) -> Dict[str, Any]:
        """
        대화형 인증 (브라우저 자동 열기)
        """
        print("\n" + "=" * 50)
        print("    GitHub Authentication")
        print("=" * 50)

        # Device Flow 시작
        result = self.start_device_flow()
        if not result["success"]:
            if result.get("setup_required"):
                print("\n[INFO] GitHub OAuth App이 설정되지 않았습니다.")
                print("라이센스 키 기반 인증을 사용합니다.")
                return result
            print(f"\n[ERROR] {result['error']}")
            return result

        user_code = result["user_code"]
        verification_uri = result["verification_uri"]

        print(f"\n  1. 브라우저에서 다음 URL을 엽니다:")
        print(f"     {verification_uri}")
        print(f"\n  2. 다음 코드를 입력하세요:")
        print(f"     {user_code}")
        print("\n  브라우저를 자동으로 엽니다...")
        print("=" * 50)

        # 브라우저 자동 열기
        try:
            webbrowser.open(verification_uri)
        except:
            pass

        # 토큰 대기
        print("\n  인증 완료를 기다리는 중...")
        token_result = self.poll_for_token(result["device_code"], result["interval"])

        if token_result["success"]:
            print(f"\n  인증 성공! GitHub: @{token_result['github_login']}")
        else:
            print(f"\n  인증 실패: {token_result['error']}")

        return token_result

    def logout(self) -> Dict[str, Any]:
        """로그아웃 (인증 정보 삭제)"""
        try:
            if self.auth_file.exists():
                self.auth_file.unlink()
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_auth_hash(self) -> Optional[str]:
        """
        인증 정보 해시 반환 (라이센스 바인딩용)
        """
        auth_data = self._load_auth_data()
        if not auth_data:
            return None

        github_id = auth_data.get("github_id")
        if not github_id:
            return None

        # GitHub ID + 고정 salt로 해시 생성
        hash_input = f"cortex_github_{github_id}_binding"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:32]

    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """GitHub API로 사용자 정보 조회"""
        try:
            req = urllib.request.Request(
                GITHUB_USER_API_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def _load_auth_data(self) -> Optional[Dict[str, Any]]:
        """인증 데이터 로드"""
        if not self.auth_file.exists():
            return None

        try:
            with open(self.auth_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None

    def _save_auth_data(self, data: Dict[str, Any]):
        """인증 데이터 저장"""
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.auth_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 전역 인스턴스
_github_auth: Optional[GitHubAuth] = None


def get_github_auth() -> GitHubAuth:
    """GitHubAuth 싱글톤"""
    global _github_auth
    if _github_auth is None:
        _github_auth = GitHubAuth()
    return _github_auth
