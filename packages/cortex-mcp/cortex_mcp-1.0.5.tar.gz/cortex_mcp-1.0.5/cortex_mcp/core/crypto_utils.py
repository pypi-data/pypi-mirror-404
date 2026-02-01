"""
Cortex MCP - Crypto Utils
라이센스키 기반 E2E 암호화/복호화

기능:
- AES-256-GCM 암호화
- 라이센스 키 기반 키 유도 (PBKDF2)
- 안전한 IV 생성
"""

import base64
import hashlib
import os
from typing import Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoUtils:
    """암호화 유틸리티 - AES-256-GCM"""

    # 고정 Salt (애플리케이션 레벨)
    # 실제 배포 시 환경 변수나 별도 설정으로 관리
    SALT_PREFIX = b"cortex_mcp_v1_"

    def __init__(self, license_key: str):
        """
        Args:
            license_key: 사용자 라이센스 키
        """
        self.license_key = license_key
        self._encryption_key = self._derive_key(license_key)

    def _derive_key(self, license_key: str) -> bytes:
        """
        라이센스 키에서 암호화 키 유도 (PBKDF2)

        Args:
            license_key: 라이센스 키

        Returns:
            32바이트 AES-256 키
        """
        # 라이센스 키 해시를 Salt로 사용
        key_hash = hashlib.sha256(license_key.encode()).digest()
        salt = self.SALT_PREFIX + key_hash[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )

        return kdf.derive(license_key.encode())

    def encrypt(self, plaintext: Union[str, bytes]) -> bytes:
        """
        데이터 암호화 (AES-256-GCM)

        Args:
            plaintext: 암호화할 데이터

        Returns:
            IV(12bytes) + 암호문 + 태그(16bytes)
        """
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # 랜덤 IV 생성 (12 bytes for GCM)
        iv = os.urandom(12)

        # 암호화
        aesgcm = AESGCM(self._encryption_key)
        ciphertext = aesgcm.encrypt(iv, plaintext, None)

        # IV + 암호문 결합
        return iv + ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        데이터 복호화

        Args:
            ciphertext: IV + 암호문 + 태그

        Returns:
            복호화된 원본 데이터
        """
        # IV 추출 (처음 12 bytes)
        iv = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]

        # 복호화
        aesgcm = AESGCM(self._encryption_key)
        plaintext = aesgcm.decrypt(iv, actual_ciphertext, None)

        return plaintext

    def encrypt_to_base64(self, plaintext: Union[str, bytes]) -> str:
        """Base64 인코딩된 암호문 반환"""
        encrypted = self.encrypt(plaintext)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_from_base64(self, ciphertext_b64: str) -> bytes:
        """Base64 인코딩된 암호문 복호화"""
        ciphertext = base64.b64decode(ciphertext_b64)
        return self.decrypt(ciphertext)

    @staticmethod
    def validate_license_key(license_key: str) -> bool:
        """
        라이센스 키 형식 검증

        Args:
            license_key: 검증할 라이센스 키

        Returns:
            유효 여부
        """
        # 기본 형식 검증 (최소 16자)
        if not license_key or len(license_key) < 16:
            return False

        # 추가 검증 로직 (체크섬, 패턴 등)
        # 실제 구현 시 라이센스 서버 연동 또는 오프라인 검증 로직 추가
        return True

    def generate_file_hash(self, data: bytes) -> str:
        """파일 무결성 해시 생성 (SHA-256)"""
        return hashlib.sha256(data).hexdigest()

    def verify_file_hash(self, data: bytes, expected_hash: str) -> bool:
        """파일 무결성 검증"""
        return self.generate_file_hash(data) == expected_hash
