"""
Cortex MCP - GitHub OAuth Authentication
GitHub OAuth 로그인 구현
"""

import os
from typing import Any, Dict, Optional

import requests

# GitHub OAuth 설정 (환경 변수에서 로드)
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")


class GitHubOAuth:
    """GitHub OAuth 인증"""

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    API_URL = "https://api.github.com"

    def __init__(
        self, client_id: str = GITHUB_CLIENT_ID, client_secret: str = GITHUB_CLIENT_SECRET
    ):
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorization_url(self, redirect_uri: str = GITHUB_REDIRECT_URI) -> str:
        """GitHub OAuth 인증 URL 생성"""
        return f"{self.AUTHORIZE_URL}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope=user:email"

    def get_access_token(self, code: str, redirect_uri: str = GITHUB_REDIRECT_URI) -> Optional[str]:
        """
        Authorization code로 access token 교환

        Args:
            code: GitHub에서 받은 authorization code
            redirect_uri: 리다이렉트 URI

        Returns:
            access_token 또는 None
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        headers = {"Accept": "application/json"}

        try:
            response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            result = response.json()

            if "access_token" in result:
                return result["access_token"]
            else:
                print(
                    f"Error getting access token: {result.get('error_description', 'Unknown error')}"
                )
                return None

        except Exception as e:
            print(f"Exception getting access token: {e}")
            return None

    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Access token으로 사용자 정보 조회

        Args:
            access_token: GitHub access token

        Returns:
            사용자 정보 딕셔너리 또는 None
        """
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        try:
            # 사용자 기본 정보
            response = requests.get(f"{self.API_URL}/user", headers=headers, timeout=10)
            response.raise_for_status()

            user_data = response.json()

            return {
                "github_id": user_data.get("id"),
                "github_login": user_data.get("login"),
                "email": user_data.get("email"),
                "avatar_url": user_data.get("avatar_url"),
                "name": user_data.get("name"),
            }

        except Exception as e:
            print(f"Exception getting user info: {e}")
            return None

    def authenticate(
        self, code: str, redirect_uri: str = GITHUB_REDIRECT_URI
    ) -> Optional[Dict[str, Any]]:
        """
        전체 OAuth 플로우 처리

        Args:
            code: GitHub authorization code
            redirect_uri: 리다이렉트 URI

        Returns:
            사용자 정보 또는 None
        """
        # 1. Access token 획득
        access_token = self.get_access_token(code, redirect_uri)
        if not access_token:
            return None

        # 2. 사용자 정보 조회
        user_info = self.get_user_info(access_token)
        if not user_info:
            return None

        return user_info


# 싱글톤 인스턴스
_github_oauth: Optional[GitHubOAuth] = None


def get_github_oauth() -> GitHubOAuth:
    """GitHubOAuth 싱글톤 인스턴스 반환"""
    global _github_oauth
    if _github_oauth is None:
        _github_oauth = GitHubOAuth()
    return _github_oauth
