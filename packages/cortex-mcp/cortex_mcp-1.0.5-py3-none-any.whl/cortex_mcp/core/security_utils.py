"""
Cortex MCP - Security Utilities

보안 유틸리티 모듈:
- Path Traversal 방어
- 입력 검증 (Sanitization)
- 파일 시스템 보안
- 파일/디렉토리 권한 관리

Created: 2026-01-12
"""

import os
import re
import stat
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


# === Path Traversal 방어 ===

# 허용되는 문자 패턴 (알파벳, 숫자, 언더스코어, 하이픈, 점)
SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

# 위험한 패턴
DANGEROUS_PATTERNS = [
    r'\.\.',           # 상위 디렉토리 이동
    r'/\.\./',         # 중간에 ..
    r'^\.\.',          # 시작이 ..
    r'\.\.$',          # 끝이 ..
    r'~',              # 홈 디렉토리 확장
    r'\$',             # 환경변수 확장
    r'%',              # URL 인코딩 시도
    r'\\',             # Windows 경로 구분자
    r'\x00',           # Null byte injection
    r'^/',             # 절대 경로 시작
]


def validate_safe_id(value: str, field_name: str = "id") -> Tuple[bool, Optional[str]]:
    """
    ID 값의 안전성 검증 (project_id, branch_id 등).

    Args:
        value: 검증할 값
        field_name: 필드명 (에러 메시지용)

    Returns:
        (is_valid, error_message)
        - is_valid: 유효 여부
        - error_message: 에러 메시지 (유효하면 None)

    Examples:
        >>> validate_safe_id("my_project")
        (True, None)
        >>> validate_safe_id("../../../etc/passwd")
        (False, "id contains dangerous pattern: '..'")
    """
    if not value:
        return False, f"{field_name} cannot be empty"

    if len(value) > 255:
        return False, f"{field_name} is too long (max 255 chars)"

    # 위험한 패턴 검사
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, value):
            return False, f"{field_name} contains dangerous pattern: '{pattern}'"

    # 안전한 문자만 허용
    if not SAFE_ID_PATTERN.match(value):
        return False, f"{field_name} contains invalid characters (allowed: a-zA-Z0-9_-.)"

    return True, None


def sanitize_path_component(value: str) -> str:
    """
    경로 구성요소 정리 (위험한 문자 제거).

    Args:
        value: 정리할 값

    Returns:
        정리된 안전한 값

    Examples:
        >>> sanitize_path_component("my../project")
        'my__project'
        >>> sanitize_path_component("test/../../../etc")
        'test______etc'
    """
    if not value:
        return ""

    # 위험한 패턴 치환
    result = value
    result = result.replace("..", "__")
    result = result.replace("/", "_")
    result = result.replace("\\", "_")
    result = result.replace("~", "_")
    result = result.replace("$", "_")
    result = result.replace("%", "_")
    result = result.replace("\x00", "")

    # 안전한 문자만 유지
    result = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', result)

    # 연속된 언더스코어 정리
    result = re.sub(r'_+', '_', result)

    # 앞뒤 언더스코어 제거
    result = result.strip('_')

    return result[:255] if result else "unnamed"


def safe_join_path(base_dir: str, *parts: str) -> Path:
    """
    안전한 경로 결합 (Path Traversal 방지).

    base_dir 외부로 벗어나는 경로 생성을 방지합니다.

    Args:
        base_dir: 기본 디렉토리 (절대 경로)
        *parts: 결합할 경로 부분들

    Returns:
        안전한 절대 경로

    Raises:
        ValueError: base_dir 외부로 벗어나는 경로인 경우

    Examples:
        >>> safe_join_path("/data", "project", "file.txt")
        PosixPath('/data/project/file.txt')
        >>> safe_join_path("/data", "../etc/passwd")
        ValueError: Path escapes base directory
    """
    base = Path(base_dir).resolve()

    # 각 부분 정리
    safe_parts = [sanitize_path_component(p) for p in parts if p]

    # 경로 결합
    target = base.joinpath(*safe_parts).resolve()

    # base_dir 내에 있는지 확인
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(
            f"Path escapes base directory: {target} is not under {base}"
        )

    return target


def validate_file_path(file_path: str, allowed_base: str) -> Tuple[bool, Optional[str]]:
    """
    파일 경로 유효성 검증.

    Args:
        file_path: 검증할 파일 경로
        allowed_base: 허용된 기본 디렉토리

    Returns:
        (is_valid, error_message)
    """
    try:
        target = Path(file_path).resolve()
        base = Path(allowed_base).resolve()

        # base 내에 있는지 확인
        target.relative_to(base)
        return True, None

    except ValueError:
        return False, f"Path {file_path} is outside allowed directory {allowed_base}"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


# === 파일 시스템 권한 관리 ===

def secure_directory_permissions(dir_path: str, mode: int = 0o700) -> bool:
    """
    디렉토리 권한을 안전하게 설정 (기본 700).

    Args:
        dir_path: 디렉토리 경로
        mode: 권한 모드 (기본: 0o700 - 소유자만 읽기/쓰기/실행)

    Returns:
        성공 여부
    """
    try:
        path = Path(dir_path)

        if not path.exists():
            path.mkdir(parents=True, mode=mode)
            logger.info(f"Created secure directory: {dir_path} (mode={oct(mode)})")
        else:
            os.chmod(dir_path, mode)
            logger.info(f"Set directory permissions: {dir_path} (mode={oct(mode)})")

        return True

    except Exception as e:
        logger.error(f"Failed to set directory permissions: {dir_path}: {e}")
        return False


def secure_file_permissions(file_path: str, mode: int = 0o600) -> bool:
    """
    파일 권한을 안전하게 설정 (기본 600).

    Args:
        file_path: 파일 경로
        mode: 권한 모드 (기본: 0o600 - 소유자만 읽기/쓰기)

    Returns:
        성공 여부
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return False

        os.chmod(file_path, mode)
        logger.debug(f"Set file permissions: {file_path} (mode={oct(mode)})")
        return True

    except Exception as e:
        logger.error(f"Failed to set file permissions: {file_path}: {e}")
        return False


def check_file_permissions(file_path: str) -> dict:
    """
    파일 권한 상태 확인.

    Returns:
        {
            "exists": bool,
            "mode": str (octal),
            "owner_only": bool,
            "world_readable": bool,
            "world_writable": bool,
            "issues": List[str]
        }
    """
    result = {
        "exists": False,
        "mode": None,
        "owner_only": False,
        "world_readable": False,
        "world_writable": False,
        "issues": []
    }

    try:
        if not os.path.exists(file_path):
            return result

        result["exists"] = True
        st = os.stat(file_path)
        mode = st.st_mode

        result["mode"] = oct(stat.S_IMODE(mode))
        result["owner_only"] = (mode & 0o077) == 0
        result["world_readable"] = bool(mode & stat.S_IROTH)
        result["world_writable"] = bool(mode & stat.S_IWOTH)

        # 보안 이슈 체크
        if result["world_readable"]:
            result["issues"].append("World readable - should restrict access")
        if result["world_writable"]:
            result["issues"].append("World writable - CRITICAL security risk")
        if mode & stat.S_ISUID:
            result["issues"].append("SUID bit set - potential security risk")
        if mode & stat.S_ISGID:
            result["issues"].append("SGID bit set - potential security risk")

    except Exception as e:
        result["issues"].append(f"Error checking permissions: {str(e)}")

    return result


def secure_data_directory(data_dir: str) -> bool:
    """
    Cortex 데이터 디렉토리 전체 보안 설정.

    ~/.cortex/ 디렉토리와 하위 디렉토리/파일에 안전한 권한 설정.

    Args:
        data_dir: 데이터 디렉토리 경로

    Returns:
        성공 여부
    """
    try:
        data_path = Path(data_dir)

        if not data_path.exists():
            data_path.mkdir(parents=True, mode=0o700)
            logger.info(f"Created secure data directory: {data_dir}")

        # 디렉토리 권한 700
        for root, dirs, files in os.walk(data_dir):
            # 디렉토리 권한 설정
            os.chmod(root, 0o700)

            # 파일 권한 설정
            for file in files:
                file_path = os.path.join(root, file)
                os.chmod(file_path, 0o600)

        logger.info(f"Secured data directory: {data_dir}")
        return True

    except Exception as e:
        logger.error(f"Failed to secure data directory: {data_dir}: {e}")
        return False


# === 입력 검증 ===

def validate_content_length(content: str, max_length: int = 1_000_000) -> Tuple[bool, Optional[str]]:
    """
    콘텐츠 길이 검증 (DoS 방지).

    Args:
        content: 검증할 콘텐츠
        max_length: 최대 허용 길이 (기본 1MB)

    Returns:
        (is_valid, error_message)
    """
    if not content:
        return True, None

    if len(content) > max_length:
        return False, f"Content too large: {len(content)} bytes (max: {max_length})"

    return True, None


def sanitize_log_message(message: str) -> str:
    """
    로그 메시지에서 민감한 정보 제거.

    Args:
        message: 원본 메시지

    Returns:
        정리된 메시지
    """
    if not message:
        return ""

    # 민감한 패턴 마스킹
    patterns = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\'&\s]+', 'password=***MASKED***'),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\'&\s]+', 'secret=***MASKED***'),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^"\'&\s]+', 'api_key=***MASKED***'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\'&\s]+', 'token=***MASKED***'),
        (r'authorization["\']?\s*[:=]\s*["\']?[^"\'&\s]+', 'authorization=***MASKED***'),
    ]

    result = message
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


# === 검증 데코레이터 ===

def validate_project_id(func):
    """
    project_id 파라미터 검증 데코레이터.

    Usage:
        @validate_project_id
        async def my_tool(project_id: str, ...):
            ...
    """
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        project_id = kwargs.get('project_id')
        if project_id:
            is_valid, error = validate_safe_id(project_id, "project_id")
            if not is_valid:
                raise ValueError(f"Invalid project_id: {error}")
        return await func(*args, **kwargs)

    return wrapper


def validate_branch_id(func):
    """
    branch_id 파라미터 검증 데코레이터.
    """
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        branch_id = kwargs.get('branch_id')
        if branch_id:
            is_valid, error = validate_safe_id(branch_id, "branch_id")
            if not is_valid:
                raise ValueError(f"Invalid branch_id: {error}")
        return await func(*args, **kwargs)

    return wrapper
