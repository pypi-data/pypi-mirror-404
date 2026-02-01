"""
Cortex MCP - License Manager (v2.0)

라이센스 인증, 기기 바인딩, Tier 파라미터 관리

업데이트 내용 (v2.0):
- 3-Tier 모델: Free / Tier 1 (Pro) / Tier 2 (Premium)
- Trial: 30일 (Tier 2 전체 기능)
- 72시간 오프라인 캐싱
- 라이센스 파라미터 (ONTOLOGY_ON, MULTI_PC_SYNC 등)
- alpha_logger 연동
"""

import hashlib
import json
import logging
import os
import platform
import secrets
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_DIR = Path(__file__).parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# config 모듈을 명시적으로 import
import config as config_module
config = config_module.config

from .alpha_logger import LogModule, get_alpha_logger

logger = logging.getLogger(__name__)


# ============================================================================
# 상수
# ============================================================================

# 오프라인 캐시 유효 시간 (72시간)
OFFLINE_CACHE_HOURS = 72

# Trial 기간 (30일)
TRIAL_DAYS = 30

# Trial 만료 알림 (3일 전)
TRIAL_WARNING_DAYS = 3

# 서버 API URL (Website 라이센스 검증)
LICENSE_API_BASE_URL = os.getenv(
    "CORTEX_LICENSE_API_URL",
    "https://cortex-mcp.com/api/license"
)

# 서버 요청 타임아웃 (초)
LICENSE_API_TIMEOUT = 10


# ============================================================================
# 라이센스 타입 및 상태
# ============================================================================


class LicenseType(Enum):
    """라이센스 타입 (v2.1 - Closed/Open Beta)"""

    # 베타 단계
    ADMIN = "admin"  # 관리자 (무제한)
    CLOSED_BETA = "closed_beta"  # 클로즈드 베타 (전체 기능, 논문용 데이터 수집)
    OPEN_BETA = "open_beta"  # 오픈 베타 (전체 기능, 일반 사용자)

    # 정식 출시 후 (미래)
    FREE = "free"  # 무료 티어
    TRIAL = "trial"  # 체험판 (30일, Tier 2 기능)
    TIER_1_PRO = "tier_1_pro"  # Pro ($15/월)
    TIER_2_PREMIUM = "tier_2_premium"  # Premium ($20/월)
    BLOCKED = "blocked"  # 차단됨

    # 레거시 지원 (기존 베타 사용자)
    BETA_FREE = "beta_free"  # 베타 무료 (30명 한정, 1년)
    MONTHLY = "monthly"  # 월간 구독 (레거시)
    YEARLY = "yearly"  # 연간 구독 (레거시)
    LIFETIME = "lifetime"  # 평생 라이센스 (레거시)


class LicenseStatus(Enum):
    """라이센스 상태"""

    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"
    INVALID = "invalid"
    DEVICE_MISMATCH = "device_mismatch"
    TRIAL_EXPIRING = "trial_expiring"  # Trial 만료 임박


# ============================================================================
# 라이센스 파라미터 (Tier별)
# ============================================================================


@dataclass
class LicenseParams:
    """라이센스 파라미터"""

    ONTOLOGY_ON: bool = False
    MAX_BRANCHES: int = 5
    MULTI_PC_SYNC: bool = False
    BRANCHING_CONFIRM_REQUIRED: bool = True
    MAX_RAG_SEARCHES_PER_DAY: int = 20  # Free 티어 제한
    MAX_CONTEXTS: int = 100  # Free 티어 제한

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ONTOLOGY_ON": self.ONTOLOGY_ON,
            "MAX_BRANCHES": self.MAX_BRANCHES if self.MAX_BRANCHES > 0 else "unlimited",
            "MULTI_PC_SYNC": self.MULTI_PC_SYNC,
            "BRANCHING_CONFIRM_REQUIRED": self.BRANCHING_CONFIRM_REQUIRED,
            "MAX_RAG_SEARCHES_PER_DAY": (
                self.MAX_RAG_SEARCHES_PER_DAY if self.MAX_RAG_SEARCHES_PER_DAY > 0 else "unlimited"
            ),
            "MAX_CONTEXTS": self.MAX_CONTEXTS if self.MAX_CONTEXTS > 0 else "unlimited",
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "LicenseParams":
        max_branches = data.get("MAX_BRANCHES", 5)
        if max_branches == "unlimited":
            max_branches = -1

        max_rag = data.get("MAX_RAG_SEARCHES_PER_DAY", 20)
        if max_rag == "unlimited":
            max_rag = -1

        max_contexts = data.get("MAX_CONTEXTS", 100)
        if max_contexts == "unlimited":
            max_contexts = -1

        return cls(
            ONTOLOGY_ON=data.get("ONTOLOGY_ON", False),
            MAX_BRANCHES=max_branches,
            MULTI_PC_SYNC=data.get("MULTI_PC_SYNC", False),
            BRANCHING_CONFIRM_REQUIRED=data.get("BRANCHING_CONFIRM_REQUIRED", True),
            MAX_RAG_SEARCHES_PER_DAY=max_rag,
            MAX_CONTEXTS=max_contexts,
        )


# Tier별 기본 파라미터
TIER_PARAMS = {
    # 베타 단계
    LicenseType.ADMIN: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,  # unlimited
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,  # unlimited
        MAX_CONTEXTS=-1,  # unlimited
    ),
    LicenseType.CLOSED_BETA: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,  # unlimited
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,  # unlimited
        MAX_CONTEXTS=-1,  # unlimited
    ),
    LicenseType.OPEN_BETA: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,  # unlimited
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,  # unlimited
        MAX_CONTEXTS=-1,  # unlimited
    ),
    # 정식 출시 후
    LicenseType.FREE: LicenseParams(
        ONTOLOGY_ON=False,
        MAX_BRANCHES=5,
        MULTI_PC_SYNC=False,
        BRANCHING_CONFIRM_REQUIRED=True,
        MAX_RAG_SEARCHES_PER_DAY=20,
        MAX_CONTEXTS=100,
    ),
    LicenseType.TRIAL: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,  # unlimited
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,  # unlimited
        MAX_CONTEXTS=-1,  # unlimited
    ),
    LicenseType.TIER_1_PRO: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=20,
        MULTI_PC_SYNC=False,
        BRANCHING_CONFIRM_REQUIRED=True,  # 클릭 세금
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
    LicenseType.TIER_2_PREMIUM: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,  # unlimited
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,  # Zero-Effort
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
    # 레거시 타입 → Tier 2와 동일하게 처리
    LicenseType.BETA_FREE: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
    LicenseType.MONTHLY: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=20,
        MULTI_PC_SYNC=False,
        BRANCHING_CONFIRM_REQUIRED=True,
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
    LicenseType.YEARLY: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
    LicenseType.LIFETIME: LicenseParams(
        ONTOLOGY_ON=True,
        MAX_BRANCHES=-1,
        MULTI_PC_SYNC=True,
        BRANCHING_CONFIRM_REQUIRED=False,
        MAX_RAG_SEARCHES_PER_DAY=-1,
        MAX_CONTEXTS=-1,
    ),
}


# ============================================================================
# 라이센스 매니저 (v2.0)
# ============================================================================


class LicenseManager:
    """라이센스 관리자 (v2.0)"""

    # 베타 무료 라이센스 최대 수 (레거시 지원)
    MAX_BETA_FREE = 30

    # 허용되는 기기 수 (모든 타입 무제한)
    MAX_DEVICES_DEFAULT = -1  # 무제한
    MAX_DEVICES_TIER_2 = -1  # 무제한

    # 부정 사용 감지 임계치
    ABUSE_THRESHOLD = 3

    def __init__(self):
        self.license_dir = config.cortex_home / "licenses"
        self.license_dir.mkdir(parents=True, exist_ok=True)

        # 라이센스 데이터 파일
        self.license_db_path = self.license_dir / "license_db.json"
        self.blocked_list_path = self.license_dir / "blocked.json"

        # 로컬 라이센스 캐시
        self.local_license_path = self.license_dir / "local_license.json"

        # 알파 로거
        self.alpha_logger = get_alpha_logger()

        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """데이터베이스 파일 초기화"""
        if not self.license_db_path.exists():
            self._save_db(
                {
                    "licenses": {},
                    "beta_free_count": 0,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "version": "2.0",
                }
            )

        if not self.blocked_list_path.exists():
            with open(self.blocked_list_path, "w", encoding="utf-8") as f:
                json.dump({"blocked_licenses": [], "blocked_devices": []}, f)

    def _load_db(self) -> Dict:
        """라이센스 DB 로드"""
        try:
            with open(self.license_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"licenses": {}, "beta_free_count": 0, "version": "2.0"}

    def _save_db(self, db: Dict):
        """라이센스 DB 저장"""
        with open(self.license_db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    def _load_blocked(self) -> Dict:
        """차단 목록 로드"""
        try:
            with open(self.blocked_list_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"blocked_licenses": [], "blocked_devices": []}

    def _save_blocked(self, blocked: Dict):
        """차단 목록 저장"""
        with open(self.blocked_list_path, "w", encoding="utf-8") as f:
            json.dump(blocked, f, ensure_ascii=False, indent=2)

    def get_device_id(self) -> str:
        """
        현재 기기의 고유 ID 생성

        조합 요소:
        - MAC 주소
        - CPU ID
        - 플랫폼 정보
        """
        components = []

        # 1. 플랫폼 정보
        components.append(platform.node())
        components.append(platform.system())
        components.append(platform.machine())

        # 2. MAC 주소 (uuid 기반)
        try:
            import uuid

            mac = ":".join(
                ["{:02x}".format((uuid.getnode() >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][
                    ::-1
                ]
            )
            components.append(mac)
        except:
            pass

        # 3. CPU 정보
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True
                )
                components.append(result.stdout.strip())
            elif platform.system() == "Linux":
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            components.append(line.split(":")[1].strip())
                            break
        except:
            pass

        # 4. 사용자 이름
        try:
            components.append(os.getlogin())
        except:
            pass

        # 해시 생성
        combined = "|".join(components)
        device_hash = hashlib.sha256(combined.encode()).hexdigest()[:32]

        return f"DEV_{device_hash}"

    def get_tier_params(self, license_type: LicenseType) -> LicenseParams:
        """Tier별 파라미터 반환"""
        return TIER_PARAMS.get(license_type, TIER_PARAMS[LicenseType.FREE])

    def generate_license_key(
        self,
        license_type: LicenseType,
        user_email: str,
        days_valid: Optional[int] = None,
        referral_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        새 라이센스 키 생성

        Args:
            license_type: 라이센스 타입
            user_email: 사용자 이메일
            days_valid: 유효 기간 (일), None이면 기본값
            referral_code: 레퍼럴 코드 (있으면 Trial +15일)

        Returns:
            생성된 라이센스 정보
        """
        db = self._load_db()

        # 베타 무료 제한 확인 (레거시)
        if license_type == LicenseType.BETA_FREE:
            if db.get("beta_free_count", 0) >= self.MAX_BETA_FREE:
                return {
                    "success": False,
                    "error": f"Beta free licenses limit reached ({self.MAX_BETA_FREE})",
                }

        # 라이센스 키 생성: CORTEX-XXXX-XXXX-XXXX-XXXX
        key_parts = [secrets.token_hex(2).upper() for _ in range(4)]
        license_key = f"CORTEX-{'-'.join(key_parts)}"

        # 만료일 계산
        created_at = datetime.now(timezone.utc)

        # 타입별 기본 유효 기간
        default_days = {
            # 베타 단계
            LicenseType.ADMIN: None,  # 평생 (관리자)
            LicenseType.CLOSED_BETA: 365,  # 1년 (클로즈드 베타)
            LicenseType.OPEN_BETA: 365,  # 1년 (오픈 베타)
            # 정식 출시 후
            LicenseType.FREE: None,  # 평생 (무료 기능만)
            LicenseType.TRIAL: TRIAL_DAYS,  # 30일
            LicenseType.TIER_1_PRO: 30,  # 월간 구독
            LicenseType.TIER_2_PREMIUM: 30,  # 월간 구독
            # 레거시
            LicenseType.BETA_FREE: 365,  # 1년 (레거시)
            LicenseType.MONTHLY: 30,  # 레거시
            LicenseType.YEARLY: 365,  # 레거시
            LicenseType.LIFETIME: None,  # 평생
        }

        # 레퍼럴 코드로 Trial 연장
        trial_extension = 0
        if license_type == LicenseType.TRIAL and referral_code:
            trial_extension = 15  # +15일

        if days_valid is not None:
            expires_at = created_at + timedelta(days=days_valid + trial_extension)
        elif license_type in default_days and default_days[license_type]:
            expires_at = created_at + timedelta(days=default_days[license_type] + trial_extension)
        else:
            expires_at = None  # 평생

        # 최대 기기 수
        max_devices = self.MAX_DEVICES_DEFAULT
        if license_type in [
            LicenseType.ADMIN,
            LicenseType.CLOSED_BETA,
            LicenseType.OPEN_BETA,  # 베타 단계
            LicenseType.TIER_2_PREMIUM,
            LicenseType.TRIAL,  # 정식
            LicenseType.BETA_FREE,
            LicenseType.YEARLY,
            LicenseType.LIFETIME,  # 레거시
        ]:
            max_devices = self.MAX_DEVICES_TIER_2

        # 라이센스 데이터
        license_data = {
            "license_key": license_key,
            "license_type": license_type.value,
            "user_email": user_email,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "bound_devices": [],
            "max_devices": max_devices,
            "status": "active",
            "abuse_attempts": [],
            "last_validated": None,
            "params": self.get_tier_params(license_type).to_dict(),
            "referral_code": referral_code,
            "paddle_subscription_id": None,  # Paddle 연동 시 사용
            "version": "2.0",
        }

        # DB 저장
        db["licenses"][license_key] = license_data
        if license_type == LicenseType.BETA_FREE:
            db["beta_free_count"] = db.get("beta_free_count", 0) + 1

        self._save_db(db)

        # 로그 기록
        self.alpha_logger.log_license(
            action="generate", license_tier=license_type.value, success=True
        )

        logger.info(f"License created: {license_key} for {user_email}")

        return {
            "success": True,
            "license_key": license_key,
            "license_type": license_type.value,
            "user_email": user_email,
            "expires_at": expires_at.isoformat() if expires_at else "lifetime",
            "params": license_data["params"],
            "trial_extended": trial_extension > 0,
        }

    def start_trial(self, user_email: str, referral_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Trial 시작 (30일, Tier 2 기능)

        Args:
            user_email: 사용자 이메일
            referral_code: 레퍼럴 코드 (있으면 +15일)

        Returns:
            생성된 Trial 라이센스 정보
        """
        return self.generate_license_key(
            license_type=LicenseType.TRIAL, user_email=user_email, referral_code=referral_code
        )

    def activate_license(self, license_key: str, device_id: Optional[str] = None) -> Dict[str, Any]:
        """
        라이센스 활성화 (기기 바인딩)

        Args:
            license_key: 라이센스 키
            device_id: 기기 ID (None이면 현재 기기)

        Returns:
            활성화 결과 + 라이센스 파라미터
        """
        import time

        start_time = time.time()

        if device_id is None:
            device_id = self.get_device_id()

        # 차단 확인
        blocked = self._load_blocked()
        if license_key in blocked.get("blocked_licenses", []):
            self._log_activation(license_key, "blocked", False, start_time)
            return {
                "success": False,
                "status": LicenseStatus.BLOCKED.value,
                "error": "This license has been permanently blocked due to abuse",
            }

        if device_id in blocked.get("blocked_devices", []):
            self._log_activation(license_key, "device_blocked", False, start_time)
            return {
                "success": False,
                "status": LicenseStatus.BLOCKED.value,
                "error": "This device has been blocked",
            }

        db = self._load_db()

        # 라이센스 존재 확인
        if license_key not in db["licenses"]:
            self._log_activation(license_key, "invalid", False, start_time)
            return {
                "success": False,
                "status": LicenseStatus.INVALID.value,
                "error": "Invalid license key",
            }

        license_data = db["licenses"][license_key]

        # 상태 확인
        if license_data["status"] == "blocked":
            self._log_activation(license_key, "blocked", False, start_time)
            return {
                "success": False,
                "status": LicenseStatus.BLOCKED.value,
                "error": "License is blocked",
            }

        # 만료 확인
        if license_data["expires_at"]:
            expires_at = datetime.fromisoformat(license_data["expires_at"])
            # naive datetime인 경우 UTC로 가정
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)

            if now > expires_at:
                # Trial 만료 → Free 티어로 전환
                license_type = LicenseType(license_data["license_type"])
                if license_type == LicenseType.TRIAL:
                    return self._convert_to_free(license_key, device_id, db, start_time)

                self._log_activation(license_key, "expired", False, start_time)
                return {
                    "success": False,
                    "status": LicenseStatus.EXPIRED.value,
                    "error": "License has expired",
                }

            # Trial 만료 임박 알림 (3일 전)
            days_remaining = (expires_at - now).days
            trial_warning = None
            if days_remaining <= TRIAL_WARNING_DAYS:
                trial_warning = f"Trial expires in {days_remaining} days. Upgrade to continue using premium features."

        else:
            trial_warning = None

        # 기기 바인딩 확인
        bound_devices = license_data.get("bound_devices", [])
        max_devices = license_data.get("max_devices", 1)

        if device_id in bound_devices:
            # 이미 바인딩된 기기 - OK
            license_data["last_validated"] = datetime.now(timezone.utc).isoformat()
            db["licenses"][license_key] = license_data
            self._save_db(db)

            # 로컬 캐시 저장 (72시간)
            self._save_local_cache(license_key, device_id, license_data)

            self._log_activation(license_key, "cache_hit", True, start_time)

            result = {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": license_data["license_type"],
                "expires_at": license_data["expires_at"],
                "params": license_data.get(
                    "params", self.get_tier_params(LicenseType.FREE).to_dict()
                ),
            }
            if trial_warning:
                result["warning"] = trial_warning
                result["status"] = LicenseStatus.TRIAL_EXPIRING.value

            return result

        # 새 기기 바인딩 시도
        if max_devices != -1 and len(bound_devices) >= max_devices:
            # 부정 사용 시도 기록
            abuse_attempts = license_data.get("abuse_attempts", [])
            abuse_attempts.append(
                {
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "existing_devices": bound_devices,
                }
            )
            license_data["abuse_attempts"] = abuse_attempts

            # 임계치 초과 시 자동 차단
            if len(abuse_attempts) >= self.ABUSE_THRESHOLD:
                license_data["status"] = "blocked"
                blocked["blocked_licenses"].append(license_key)
                self._save_blocked(blocked)

                logger.warning(f"License blocked due to abuse: {license_key}")

                db["licenses"][license_key] = license_data
                self._save_db(db)

                self._log_activation(license_key, "abuse_blocked", False, start_time)

                return {
                    "success": False,
                    "status": LicenseStatus.BLOCKED.value,
                    "error": "License has been blocked due to suspected sharing. Contact support.",
                }

            db["licenses"][license_key] = license_data
            self._save_db(db)

            self._log_activation(license_key, "device_mismatch", False, start_time)

            return {
                "success": False,
                "status": LicenseStatus.DEVICE_MISMATCH.value,
                "error": f"License is already bound to another device. Attempts: {len(abuse_attempts)}/{self.ABUSE_THRESHOLD}",
                "warning": "Continued attempts will result in permanent license block",
            }

        # 첫 기기 바인딩
        bound_devices.append(device_id)
        license_data["bound_devices"] = bound_devices
        license_data["last_validated"] = datetime.now(timezone.utc).isoformat()

        db["licenses"][license_key] = license_data
        self._save_db(db)

        # 로컬 캐시 저장
        self._save_local_cache(license_key, device_id, license_data)

        self._log_activation(license_key, "new_binding", True, start_time)

        logger.info(f"License activated: {license_key} on device {device_id[:10]}...")

        result = {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": license_data["license_type"],
            "expires_at": license_data["expires_at"],
            "params": license_data.get("params", self.get_tier_params(LicenseType.FREE).to_dict()),
            "message": "License successfully activated on this device",
        }
        if trial_warning:
            result["warning"] = trial_warning

        return result

    def _convert_to_free(
        self, license_key: str, device_id: str, db: Dict, start_time: float
    ) -> Dict[str, Any]:
        """Trial 만료 시 Free 티어로 전환"""
        license_data = db["licenses"][license_key]

        # Free 파라미터로 변경
        free_params = self.get_tier_params(LicenseType.FREE)
        license_data["params"] = free_params.to_dict()
        license_data["license_type"] = LicenseType.FREE.value
        license_data["converted_at"] = datetime.now(timezone.utc).isoformat()
        license_data["original_type"] = "trial"

        db["licenses"][license_key] = license_data
        self._save_db(db)

        # 로컬 캐시 업데이트
        self._save_local_cache(license_key, device_id, license_data)

        self._log_activation(license_key, "trial_to_free", True, start_time)

        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": LicenseType.FREE.value,
            "expires_at": None,
            "params": free_params.to_dict(),
            "message": "Trial has expired. Converted to Free tier. Upgrade to continue using premium features.",
        }

    def _save_local_cache(self, license_key: str, device_id: str, license_data: Dict):
        """로컬 라이센스 캐시 저장 (72시간 오프라인 지원)"""
        local_data = {
            "license_key": license_key,
            "device_id": device_id,
            "license_type": license_data["license_type"],
            "expires_at": license_data["expires_at"],
            "params": license_data.get("params", {}),
            "last_validated": license_data.get("last_validated"),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "cache_valid_until": (
                datetime.now(timezone.utc) + timedelta(hours=OFFLINE_CACHE_HOURS)
            ).isoformat(),
        }
        with open(self.local_license_path, "w", encoding="utf-8") as f:
            json.dump(local_data, f, ensure_ascii=False, indent=2)

    def _log_activation(self, license_key: str, action: str, success: bool, start_time: float):
        """활성화 로그 기록"""
        import time

        latency_ms = (time.time() - start_time) * 1000

        self.alpha_logger.log_license(
            action=action,
            license_tier=license_key[:20] if license_key else None,
            success=success,
            latency_ms=latency_ms,
        )

    def validate_offline(self) -> Dict[str, Any]:
        """
        오프라인 라이센스 검증 (72시간 캐시)

        Returns:
            검증 결과 + 파라미터
        """
        import time

        start_time = time.time()

        if not self.local_license_path.exists():
            # 캐시 없음 → Free 티어
            self.alpha_logger.log_license(
                action="cache_miss",
                license_tier="free",
                success=True,
                cache_used=False,
                latency_ms=(time.time() - start_time) * 1000,
            )
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "offline": True,
                "message": "No license found. Using Free tier.",
            }

        try:
            with open(self.local_license_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except:
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "offline": True,
                "message": "License cache corrupted. Using Free tier.",
            }

        # 기기 ID 확인
        current_device = self.get_device_id()
        if local_data.get("device_id") != current_device:
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "offline": True,
                "message": "License is for another device. Using Free tier.",
            }

        # 캐시 유효성 확인 (72시간)
        cache_valid_until = local_data.get("cache_valid_until")
        if cache_valid_until:
            valid_until = datetime.fromisoformat(cache_valid_until)
            if datetime.now(timezone.utc) > valid_until:
                # 캐시 만료 → Free 티어로 폴백
                self.alpha_logger.log_license(
                    action="cache_expired",
                    license_tier="free",
                    success=True,
                    cache_used=False,
                    latency_ms=(time.time() - start_time) * 1000,
                )
                return {
                    "success": True,
                    "status": LicenseStatus.ACTIVE.value,
                    "license_type": LicenseType.FREE.value,
                    "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                    "offline": True,
                    "message": "License cache expired. Connect to internet to restore premium features.",
                }

        # 라이센스 만료 확인
        if local_data.get("expires_at"):
            expires_at = datetime.fromisoformat(local_data["expires_at"])
            # naive datetime인 경우 UTC로 가정
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return {
                    "success": True,
                    "status": LicenseStatus.ACTIVE.value,
                    "license_type": LicenseType.FREE.value,
                    "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                    "offline": True,
                    "message": "License has expired. Using Free tier.",
                }

        # 캐시 유효 → 저장된 파라미터 사용
        self.alpha_logger.log_license(
            action="cache_valid",
            license_tier=local_data.get("license_type", "free"),
            success=True,
            cache_used=True,
            latency_ms=(time.time() - start_time) * 1000,
        )

        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": local_data.get("license_type"),
            "expires_at": local_data.get("expires_at"),
            "params": local_data.get("params", self.get_tier_params(LicenseType.FREE).to_dict()),
            "offline": True,
            "cache_valid_until": cache_valid_until,
        }

    def get_current_params(self) -> LicenseParams:
        """
        현재 유효한 라이센스 파라미터 반환

        Returns:
            LicenseParams 객체
        """
        # 오프라인 검증으로 현재 파라미터 확인
        result = self.validate_offline()
        params_dict = result.get("params", {})
        return LicenseParams.from_dict(params_dict)

    def is_ontology_enabled(self) -> bool:
        """온톨로지 활성화 여부"""
        return self.get_current_params().ONTOLOGY_ON

    def is_multi_pc_enabled(self) -> bool:
        """Multi-PC 동기화 활성화 여부"""
        return self.get_current_params().MULTI_PC_SYNC

    def requires_confirmation(self) -> bool:
        """브랜칭 확인 필요 여부 (클릭 세금)"""
        return self.get_current_params().BRANCHING_CONFIRM_REQUIRED

    def validate_local_license(self) -> Dict[str, Any]:
        """
        로컬 라이센스 검증 (main.py에서 사용)

        Returns:
            검증 결과 딕셔너리
        """
        # 로컬 라이센스 파일 존재 여부 확인
        if not self.local_license_path.exists():
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "message": "No license found. Using Free tier.",
            }

        # 로컬 라이센스 파일 읽기
        try:
            with open(self.local_license_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # 파일 손상 시 Free tier로 fallback
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "message": "License file corrupted. Using Free tier.",
            }

        # device_id 변조 감지
        current_device_id = self.get_device_id()
        cached_device_id = local_data.get("device_id")

        if cached_device_id and cached_device_id != current_device_id:
            return {
                "success": False,
                "status": LicenseStatus.DEVICE_MISMATCH.value,
                "error": "Local license file has been tampered with.",
            }

        # 기존 오프라인 검증 수행
        return self.validate_offline()

    def block_license(self, license_key: str, reason: str = "") -> Dict[str, Any]:
        """라이센스 영구 차단"""
        db = self._load_db()
        blocked = self._load_blocked()

        if license_key not in db["licenses"]:
            return {"success": False, "error": "License not found"}

        db["licenses"][license_key]["status"] = "blocked"
        db["licenses"][license_key]["blocked_at"] = datetime.now(timezone.utc).isoformat()
        db["licenses"][license_key]["block_reason"] = reason

        if license_key not in blocked["blocked_licenses"]:
            blocked["blocked_licenses"].append(license_key)

        self._save_db(db)
        self._save_blocked(blocked)

        self.alpha_logger.log_license(action="block", license_tier=license_key[:20], success=True)

        logger.warning(f"License blocked: {license_key}, reason: {reason}")

        return {"success": True, "message": f"License {license_key} has been permanently blocked"}

    def get_license_info(self, license_key: str) -> Dict[str, Any]:
        """라이센스 정보 조회"""
        db = self._load_db()

        if license_key not in db["licenses"]:
            return {"success": False, "error": "License not found"}

        data = db["licenses"][license_key]

        return {
            "success": True,
            "license_key": license_key,
            "license_type": data["license_type"],
            "user_email": data["user_email"],
            "status": data["status"],
            "created_at": data["created_at"],
            "expires_at": data["expires_at"],
            "bound_devices_count": len(data.get("bound_devices", [])),
            "params": data.get("params", {}),
            "abuse_attempts_count": len(data.get("abuse_attempts", [])),
        }

    def upgrade_license(
        self,
        license_key: str,
        new_type: LicenseType,
        days_valid: Optional[int] = None,
        paddle_subscription_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        라이센스 업그레이드

        Args:
            license_key: 기존 라이센스 키
            new_type: 새 라이센스 타입
            days_valid: 유효 기간
            paddle_subscription_id: Paddle 구독 ID

        Returns:
            업그레이드 결과
        """
        db = self._load_db()

        if license_key not in db["licenses"]:
            return {"success": False, "error": "License not found"}

        license_data = db["licenses"][license_key]
        old_type = license_data["license_type"]

        # 새 파라미터 적용
        new_params = self.get_tier_params(new_type)
        license_data["license_type"] = new_type.value
        license_data["params"] = new_params.to_dict()
        license_data["upgraded_at"] = datetime.now(timezone.utc).isoformat()
        license_data["previous_type"] = old_type

        # 만료일 업데이트
        if days_valid:
            license_data["expires_at"] = (
                datetime.now(timezone.utc) + timedelta(days=days_valid)
            ).isoformat()

        # Multi-PC 지원 업데이트
        if new_type in [LicenseType.TIER_2_PREMIUM, LicenseType.TRIAL]:
            license_data["max_devices"] = self.MAX_DEVICES_TIER_2
        else:
            license_data["max_devices"] = self.MAX_DEVICES_DEFAULT

        # Paddle 구독 ID 저장
        if paddle_subscription_id:
            license_data["paddle_subscription_id"] = paddle_subscription_id

        db["licenses"][license_key] = license_data
        self._save_db(db)

        # 로컬 캐시 업데이트
        device_id = self.get_device_id()
        if device_id in license_data.get("bound_devices", []):
            self._save_local_cache(license_key, device_id, license_data)

        self.alpha_logger.log_license(action="upgrade", license_tier=new_type.value, success=True)

        return {
            "success": True,
            "license_key": license_key,
            "old_type": old_type,
            "new_type": new_type.value,
            "params": new_params.to_dict(),
            "expires_at": license_data["expires_at"],
        }

    def downgrade_license(
        self, license_key: str, new_type: LicenseType, keep_device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        라이센스 다운그레이드 (Tier 2 → Tier 1 시 PC 선택 필요)

        Args:
            license_key: 라이센스 키
            new_type: 새 라이센스 타입
            keep_device_id: 유지할 PC의 device_id (Multi-PC → 단일 PC 시)

        Returns:
            다운그레이드 결과
        """
        db = self._load_db()

        if license_key not in db["licenses"]:
            return {"success": False, "error": "License not found"}

        license_data = db["licenses"][license_key]
        old_type = license_data["license_type"]
        bound_devices = license_data.get("bound_devices", [])

        # Multi-PC → 단일 PC 다운그레이드 시 PC 선택 필요
        if (
            old_type in ["tier_2_premium", "trial", "beta_free", "yearly", "lifetime"]
            and new_type in [LicenseType.TIER_1_PRO, LicenseType.MONTHLY, LicenseType.FREE]
            and len(bound_devices) > 1
        ):

            if keep_device_id is None:
                # PC 목록 반환하여 사용자 선택 요청
                return {
                    "success": False,
                    "error": "PC selection required",
                    "requires_device_selection": True,
                    "bound_devices": bound_devices,
                    "message": "Multi-PC sync will be disabled. Please select which device to keep.",
                }

            if keep_device_id not in bound_devices:
                return {"success": False, "error": "Invalid device selection"}

            # 선택한 PC만 유지
            license_data["bound_devices"] = [keep_device_id]

        # 새 파라미터 적용
        new_params = self.get_tier_params(new_type)
        license_data["license_type"] = new_type.value
        license_data["params"] = new_params.to_dict()
        license_data["downgraded_at"] = datetime.now(timezone.utc).isoformat()
        license_data["previous_type"] = old_type
        license_data["max_devices"] = self.MAX_DEVICES_DEFAULT

        db["licenses"][license_key] = license_data
        self._save_db(db)

        # 로컬 캐시 업데이트
        device_id = self.get_device_id()
        if device_id in license_data.get("bound_devices", []):
            self._save_local_cache(license_key, device_id, license_data)

        self.alpha_logger.log_license(action="downgrade", license_tier=new_type.value, success=True)

        return {
            "success": True,
            "license_key": license_key,
            "old_type": old_type,
            "new_type": new_type.value,
            "params": new_params.to_dict(),
            "kept_device": keep_device_id,
            "message": "License downgraded. Other devices can rejoin upon upgrade.",
        }

    def list_all_licenses(self) -> Dict[str, Any]:
        """모든 라이센스 목록"""
        db = self._load_db()

        licenses = []
        for key, data in db["licenses"].items():
            licenses.append(
                {
                    "license_key": key,
                    "license_type": data["license_type"],
                    "user_email": data["user_email"],
                    "status": data["status"],
                    "expires_at": data["expires_at"],
                    "devices": len(data.get("bound_devices", [])),
                    "params": data.get("params", {}),
                }
            )

        return {
            "success": True,
            "total_count": len(licenses),
            "beta_free_count": db.get("beta_free_count", 0),
            "licenses": licenses,
        }

    def bind_github_account(
        self, license_key: str, github_login: str, github_id: int
    ) -> Dict[str, Any]:
        """GitHub 계정 바인딩"""
        db = self._load_db()

        if license_key not in db["licenses"]:
            return {"success": False, "error": "License not found"}

        license_data = db["licenses"][license_key]

        existing_github = license_data.get("github_id")
        if existing_github and existing_github != github_id:
            return {
                "success": False,
                "error": "License is already bound to a different GitHub account",
            }

        license_data["github_id"] = github_id
        license_data["github_login"] = github_login
        license_data["github_bound_at"] = datetime.now(timezone.utc).isoformat()

        db["licenses"][license_key] = license_data
        self._save_db(db)

        logger.info(f"GitHub account @{github_login} bound to license {license_key}")

        return {
            "success": True,
            "message": f"GitHub account @{github_login} successfully bound to license",
            "github_login": github_login,
        }

    def validate_with_github(self, license_key: str, github_id: int) -> Dict[str, Any]:
        """GitHub 인증으로 라이센스 검증"""
        import time

        start_time = time.time()

        db = self._load_db()

        if license_key not in db["licenses"]:
            return {
                "success": False,
                "status": LicenseStatus.INVALID.value,
                "error": "Invalid license key",
            }

        license_data = db["licenses"][license_key]

        bound_github_id = license_data.get("github_id")
        if not bound_github_id:
            return {"success": False, "error": "This license is not bound to a GitHub account."}

        if bound_github_id != github_id:
            return {
                "success": False,
                "status": LicenseStatus.INVALID.value,
                "error": "GitHub account does not match",
            }

        if license_data["status"] == "blocked":
            return {
                "success": False,
                "status": LicenseStatus.BLOCKED.value,
                "error": "License is blocked",
            }

        if license_data["expires_at"]:
            expires_at = datetime.fromisoformat(license_data["expires_at"])
            # naive datetime인 경우 UTC로 가정
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires_at:
                return {
                    "success": False,
                    "status": LicenseStatus.EXPIRED.value,
                    "error": "License has expired",
                }

        # 검증 성공
        license_data["last_validated"] = datetime.now(timezone.utc).isoformat()
        db["licenses"][license_key] = license_data
        self._save_db(db)

        # GitHub 인증 기반 로컬 캐시
        local_data = {
            "license_key": license_key,
            "github_id": github_id,
            "license_type": license_data["license_type"],
            "expires_at": license_data["expires_at"],
            "params": license_data.get("params", {}),
            "last_validated": license_data["last_validated"],
            "auth_method": "github",
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "cache_valid_until": (
                datetime.now(timezone.utc) + timedelta(hours=OFFLINE_CACHE_HOURS)
            ).isoformat(),
        }
        with open(self.local_license_path, "w", encoding="utf-8") as f:
            json.dump(local_data, f, ensure_ascii=False, indent=2)

        self.alpha_logger.log_license(
            action="github_verify",
            license_tier=license_data["license_type"],
            success=True,
            latency_ms=(time.time() - start_time) * 1000,
        )

        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": license_data["license_type"],
            "expires_at": license_data["expires_at"],
            "params": license_data.get("params", {}),
            "github_login": license_data.get("github_login"),
        }

    # ========================================================================
    # 서버 연동 (Website API 통합)
    # ========================================================================

    async def verify_with_server(
        self,
        license_key: str,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Website API를 통해 라이센스 검증 (비동기)

        Args:
            license_key: 라이센스 키 (ctx_xxxx 형식)
            device_id: 디바이스 ID (None이면 자동 생성)

        Returns:
            검증 결과 딕셔너리
        """
        import time
        import aiohttp

        start_time = time.time()

        if device_id is None:
            device_id = self.get_device_id()

        payload = {
            "license_key": license_key,
            "device_id": device_id,
            "device_name": platform.node(),
            "device_os": platform.system()
        }

        try:
            timeout = aiohttp.ClientTimeout(total=LICENSE_API_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{LICENSE_API_BASE_URL}/verify",
                    json=payload
                ) as response:
                    result = await response.json()

                    latency_ms = (time.time() - start_time) * 1000

                    if result.get("valid"):
                        # 서버 검증 성공 - 로컬 캐시 저장
                        self._save_server_cache(license_key, device_id, result)

                        self.alpha_logger.log_license(
                            action="server_verify",
                            license_tier=result.get("tier"),
                            success=True,
                            latency_ms=latency_ms
                        )

                        return {
                            "success": True,
                            "status": LicenseStatus.ACTIVE.value,
                            "license_type": self._map_tier_to_type(result.get("tier")),
                            "tier": result.get("tier"),
                            "params": self._convert_server_params(result.get("parameters", {})),
                            "expires_at": result.get("expires_at"),
                            "trial": result.get("trial", False),
                            "trial_days_remaining": result.get("trial_days_remaining"),
                            "source": "server",
                            "message": result.get("message", "License verified successfully")
                        }
                    else:
                        self.alpha_logger.log_license(
                            action="server_verify_failed",
                            license_tier="unknown",
                            success=False,
                            latency_ms=latency_ms
                        )

                        return {
                            "success": False,
                            "status": LicenseStatus.INVALID.value,
                            "error": result.get("message", "Invalid license"),
                            "source": "server"
                        }

        except aiohttp.ClientError as e:
            # 네트워크 오류 - 로컬 캐시로 폴백
            logger.warning(f"Server verification failed (network): {e}")
            return self._fallback_to_cache(license_key, device_id)

        except Exception as e:
            logger.error(f"Server verification error: {e}")
            return self._fallback_to_cache(license_key, device_id)

    def verify_with_server_sync(
        self,
        license_key: str,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Website API를 통해 라이센스 검증 (동기)

        Args:
            license_key: 라이센스 키
            device_id: 디바이스 ID

        Returns:
            검증 결과 딕셔너리
        """
        import asyncio

        try:
            # 이벤트 루프가 이미 실행 중인지 확인
            try:
                loop = asyncio.get_running_loop()
                # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.verify_with_server(license_key, device_id)
                    )
                    return future.result(timeout=LICENSE_API_TIMEOUT + 5)
            except RuntimeError:
                # 실행 중인 루프가 없으면 새로 생성
                return asyncio.run(self.verify_with_server(license_key, device_id))

        except Exception as e:
            logger.error(f"Sync server verification error: {e}")
            return self._fallback_to_cache(license_key, device_id or self.get_device_id())

    def _save_server_cache(
        self,
        license_key: str,
        device_id: str,
        server_result: Dict
    ):
        """
        서버 검증 결과를 로컬 캐시에 저장

        Args:
            license_key: 라이센스 키
            device_id: 디바이스 ID
            server_result: 서버 응답 결과
        """
        params = self._convert_server_params(server_result.get("parameters", {}))

        cache_data = {
            "license_key": license_key,
            "device_id": device_id,
            "license_type": self._map_tier_to_type(server_result.get("tier")),
            "tier": server_result.get("tier"),
            "expires_at": server_result.get("expires_at"),
            "params": params,
            "trial": server_result.get("trial", False),
            "trial_days_remaining": server_result.get("trial_days_remaining"),
            "source": "server",
            "last_validated": datetime.now(timezone.utc).isoformat(),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "cache_valid_until": (
                datetime.now(timezone.utc) + timedelta(hours=OFFLINE_CACHE_HOURS)
            ).isoformat()
        }

        with open(self.local_license_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Server license cached: tier={server_result.get('tier')}")

    def _convert_server_params(self, server_params: Dict) -> Dict:
        """
        Website 파라미터를 Cortex MCP 형식으로 변환

        Args:
            server_params: 서버에서 받은 파라미터

        Returns:
            Cortex MCP 형식의 파라미터
        """
        return {
            "ONTOLOGY_ON": server_params.get("ontology_on", False),
            "MAX_BRANCHES": server_params.get("max_branches", 5),
            "MULTI_PC_SYNC": server_params.get("multi_pc_sync", False),
            "BRANCHING_CONFIRM_REQUIRED": server_params.get("branching_confirm_required", True),
            "MAX_RAG_SEARCHES_PER_DAY": server_params.get("daily_search_limit", 20),
            "MAX_CONTEXTS": server_params.get("max_contexts", -1)  # 서버 미제공 시 무제한
        }

    def _map_tier_to_type(self, tier: str) -> str:
        """
        Website tier를 Cortex LicenseType 값으로 매핑

        Args:
            tier: Website의 tier 값 (free, pro, premium, enterprise)

        Returns:
            LicenseType 값
        """
        mapping = {
            "free": LicenseType.FREE.value,
            "pro": LicenseType.TIER_1_PRO.value,
            "premium": LicenseType.TIER_2_PREMIUM.value,
            "enterprise": LicenseType.TIER_2_PREMIUM.value,  # Enterprise도 Premium 파라미터 사용
        }
        return mapping.get(tier, LicenseType.FREE.value)

    def _map_status_to_type(self, status: str, tier: str) -> str:
        """
        Website LicenseStatus를 Cortex LicenseType으로 매핑

        Args:
            status: Website의 status 값
            tier: Website의 tier 값

        Returns:
            LicenseType 값
        """
        # 특수 상태 처리
        if status == "beta":
            return LicenseType.CLOSED_BETA.value
        elif status == "lifetime":
            return LicenseType.LIFETIME.value
        elif status == "trial":
            return LicenseType.TRIAL.value
        elif status in ["expired", "cancelled"]:
            return LicenseType.FREE.value

        # 일반 상태는 tier 기반
        return self._map_tier_to_type(tier)

    def _fallback_to_cache(
        self,
        license_key: str,
        device_id: str
    ) -> Dict[str, Any]:
        """
        서버 연결 실패 시 로컬 캐시로 폴백

        Args:
            license_key: 라이센스 키
            device_id: 디바이스 ID

        Returns:
            캐시 기반 검증 결과 또는 Free 티어
        """
        if not self.local_license_path.exists():
            logger.info("No local cache, falling back to Free tier")
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "source": "fallback",
                "message": "Server unavailable. Using Free tier."
            }

        try:
            with open(self.local_license_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Cache read error: {e}")
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "source": "fallback",
                "message": "Cache corrupted. Using Free tier."
            }

        # 디바이스 ID 확인
        if cache_data.get("device_id") != device_id:
            logger.warning("Device ID mismatch in cache")
            return {
                "success": True,
                "status": LicenseStatus.ACTIVE.value,
                "license_type": LicenseType.FREE.value,
                "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                "source": "fallback",
                "message": "Cache for different device. Using Free tier."
            }

        # 캐시 유효성 확인 (72시간)
        cache_valid_until = cache_data.get("cache_valid_until")
        if cache_valid_until:
            valid_until = datetime.fromisoformat(cache_valid_until)
            if datetime.now(timezone.utc) > valid_until:
                logger.info("Cache expired, falling back to Free tier")
                return {
                    "success": True,
                    "status": LicenseStatus.ACTIVE.value,
                    "license_type": LicenseType.FREE.value,
                    "params": self.get_tier_params(LicenseType.FREE).to_dict(),
                    "source": "fallback",
                    "message": "Cache expired. Connect to internet to restore premium features."
                }

        # 캐시 유효 - 저장된 파라미터 사용
        logger.info(f"Using cached license: {cache_data.get('license_type')}")
        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": cache_data.get("license_type"),
            "tier": cache_data.get("tier"),
            "params": cache_data.get("params", self.get_tier_params(LicenseType.FREE).to_dict()),
            "expires_at": cache_data.get("expires_at"),
            "source": "cache",
            "cache_valid_until": cache_valid_until,
            "message": "Using cached license (offline mode)"
        }

    def validate_license_unified(
        self,
        license_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        통합 라이센스 검증 (권장 사용 메서드)

        우선순위:
        1. 제공된 license_key로 서버 검증
        2. 로컬 캐시 확인 (72시간 유효)
        3. 로컬 JSON DB 확인 (레거시)
        4. Free 티어 폴백

        Args:
            license_key: 라이센스 키 (None이면 캐시에서 확인)

        Returns:
            검증 결과 딕셔너리
        """
        device_id = self.get_device_id()

        # 1. license_key 제공 시 서버 검증 우선
        if license_key:
            logger.info("Attempting server verification...")
            result = self.verify_with_server_sync(license_key, device_id)
            if result.get("success") and result.get("source") == "server":
                return result
            # 서버 실패 시 폴백 결과 확인
            if result.get("success"):
                return result

        # 2. 로컬 캐시 확인
        cache_result = self._check_server_cache(device_id)
        if cache_result.get("success"):
            logger.info(f"Using cached license: {cache_result.get('license_type')}")
            return cache_result

        # 3. 로컬 JSON DB 확인 (레거시 지원)
        legacy_result = self.validate_local_license()
        if legacy_result.get("success") and legacy_result.get("license_type") != LicenseType.FREE.value:
            logger.info(f"Using legacy local license: {legacy_result.get('license_type')}")
            return legacy_result

        # 4. Free 티어 폴백
        logger.info("No valid license found, using Free tier")
        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": LicenseType.FREE.value,
            "params": self.get_tier_params(LicenseType.FREE).to_dict(),
            "source": "default",
            "message": "Using Free tier. Activate a license for premium features."
        }

    def _check_server_cache(self, device_id: str) -> Dict[str, Any]:
        """
        서버 캐시 확인 (validate_license_unified에서 사용)

        Args:
            device_id: 디바이스 ID

        Returns:
            캐시 검증 결과
        """
        if not self.local_license_path.exists():
            return {"success": False, "error": "No cache"}

        try:
            with open(self.local_license_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"success": False, "error": "Cache corrupted"}

        # 서버 캐시인지 확인
        if cache_data.get("source") != "server":
            return {"success": False, "error": "Not server cache"}

        # 디바이스 확인
        if cache_data.get("device_id") != device_id:
            return {"success": False, "error": "Device mismatch"}

        # 캐시 유효성 확인
        cache_valid_until = cache_data.get("cache_valid_until")
        if cache_valid_until:
            valid_until = datetime.fromisoformat(cache_valid_until)
            # timezone-naive인 경우 UTC로 가정
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > valid_until:
                return {"success": False, "error": "Cache expired"}

        # 라이센스 만료 확인
        expires_at = cache_data.get("expires_at")
        if expires_at:
            exp_dt = datetime.fromisoformat(expires_at)
            # timezone-naive인 경우 UTC로 가정
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp_dt:
                return {"success": False, "error": "License expired"}

        return {
            "success": True,
            "status": LicenseStatus.ACTIVE.value,
            "license_type": cache_data.get("license_type"),
            "tier": cache_data.get("tier"),
            "params": cache_data.get("params", {}),
            "expires_at": expires_at,
            "source": "cache",
            "cache_valid_until": cache_valid_until
        }


# ============================================================================
# 싱글톤 인스턴스
# ============================================================================

_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """LicenseManager 싱글톤 인스턴스 반환"""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def get_current_license_params() -> Dict[str, Any]:
    """현재 라이센스 파라미터 반환 (편의 함수)"""
    return get_license_manager().get_current_params().to_dict()


def is_ontology_enabled() -> bool:
    """온톨로지 활성화 여부 (편의 함수)"""
    return get_license_manager().is_ontology_enabled()


def is_multi_pc_enabled() -> bool:
    """Multi-PC 활성화 여부 (편의 함수)"""
    return get_license_manager().is_multi_pc_enabled()


def requires_confirmation() -> bool:
    """확인 필요 여부 (편의 함수)"""
    return get_license_manager().requires_confirmation()


# ============================================================================
# 라이센스 검증 데코레이터 (MCP 도구 보호)
# ============================================================================

# 라이센스 검증 캐시 (5분 유효)
_license_cache: Optional[Dict[str, Any]] = None
_license_cache_time: Optional[datetime] = None
CACHE_VALIDITY_MINUTES = 5


def _get_cached_license() -> Optional[Dict[str, Any]]:
    """캐시된 라이센스 검증 결과 반환 (5분 유효)"""
    global _license_cache, _license_cache_time

    if _license_cache is None or _license_cache_time is None:
        return None

    # 캐시 만료 확인
    now = datetime.now(timezone.utc)
    if (now - _license_cache_time).total_seconds() > CACHE_VALIDITY_MINUTES * 60:
        return None

    return _license_cache


def _set_license_cache(result: Dict[str, Any]):
    """라이센스 검증 결과 캐시"""
    global _license_cache, _license_cache_time
    _license_cache = result
    _license_cache_time = datetime.now(timezone.utc)


def require_license(func):
    """
    MCP 도구 실행 전 라이센스 검증 데코레이터

    라이센스가 없거나 만료된 경우 실행 차단
    캐시 메커니즘으로 성능 유지 (5분 캐시)

    Usage:
        @require_license
        async def my_mcp_tool(arg1, arg2):
            # 도구 로직
            pass
    """
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 캐시 확인
        cached = _get_cached_license()
        if cached:
            # 캐시된 결과 사용
            if not cached.get("success"):
                return {
                    "success": False,
                    "error": "License required. Please activate a valid license to use Cortex MCP.",
                    "license_status": cached.get("status"),
                    "cached": True,
                }
        else:
            # 라이센스 검증
            manager = get_license_manager()
            result = manager.validate_local_license()

            # 캐시 저장
            _set_license_cache(result)

            # 검증 실패 시 차단
            if not result.get("success"):
                return {
                    "success": False,
                    "error": "License required. Please activate a valid license to use Cortex MCP.",
                    "license_status": result.get("status"),
                    "message": "Activate with: python scripts/license_cli.py activate --key YOUR-LICENSE-KEY",
                }

        # 라이센스 유효 - 원래 함수 실행
        return await func(*args, **kwargs)

    return wrapper


def invalidate_license_cache():
    """라이센스 캐시 무효화 (라이센스 변경 시 호출)"""
    global _license_cache, _license_cache_time
    _license_cache = None
    _license_cache_time = None
