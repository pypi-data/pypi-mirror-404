"""
Atomic File Write - 원자적 파일 쓰기 유틸리티

목적:
- 파일 쓰기 중 크래시 발생 시에도 데이터 손상 방지
- 임시 파일 + rename 패턴으로 원자성 보장

핵심 원칙:
1. 임시 파일에 먼저 쓰기
2. 성공하면 원본 파일로 rename (POSIX 원자적 작업)
3. 실패하면 임시 파일 삭제, 원본 유지

사용 예:
    from core.atomic_write import atomic_write

    atomic_write("/path/to/file.md", "새로운 내용")

작성자: Cortex Team
일자: 2026-01-03
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def atomic_write(
    file_path: str,
    content: str,
    encoding: str = 'utf-8',
    use_fsync: bool = False
) -> None:
    """
    원자적 파일 쓰기

    파일 쓰기 중 크래시가 발생해도 기존 파일은 손상되지 않습니다.
    임시 파일에 먼저 작성한 후, 성공하면 원본으로 rename합니다.

    Args:
        file_path: 쓸 파일 경로
        content: 파일 내용
        encoding: 인코딩 (기본: utf-8)
        use_fsync: 디스크 동기화 사용 여부 (기본: False)
            - True: 느리지만 100% 안전 (데이터베이스, 금융 등)
            - False: 빠르지만 정전 시 데이터 손실 가능 (일반 작업)

    Raises:
        IOError: 파일 쓰기 실패 시
        OSError: rename 실패 시

    동작 흐름:
        1. 같은 디렉토리에 임시 파일 생성
        2. 임시 파일에 내용 쓰기
        3. (선택) fsync로 디스크 동기화
        4. 임시 파일을 원본 파일로 rename (원자적)
        5. 실패 시 임시 파일 삭제
    """
    file_path = Path(file_path)

    # 부모 디렉토리 확인 및 생성
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 임시 파일을 같은 디렉토리에 생성 (rename 성능 최적화)
    # NamedTemporaryFile은 close 시 자동 삭제되므로 delete=False 사용
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding=encoding,
            dir=file_path.parent,
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            delete=False  # 수동 삭제 (rename 전까지 유지)
        ) as tmp_file:
            temp_path = tmp_file.name

            # 1. 임시 파일에 쓰기
            tmp_file.write(content)
            tmp_file.flush()  # 버퍼 → OS 버퍼

            # 2. (선택) 디스크 동기화
            if use_fsync:
                os.fsync(tmp_file.fileno())  # OS 버퍼 → 디스크

        # 3. 원자적 rename
        # os.replace()는 POSIX 원자적 연산 (Windows도 지원)
        os.replace(temp_path, file_path)

        logger.debug(f"[ATOMIC WRITE] 성공: {file_path} ({len(content)} bytes)")

    except Exception as e:
        # 실패 시 임시 파일 정리
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"[ATOMIC WRITE] 임시 파일 정리: {temp_path}")
            except Exception as cleanup_error:
                logger.warning(f"[ATOMIC WRITE] 임시 파일 정리 실패: {cleanup_error}")

        # 원본 에러 재발생
        logger.error(f"[ATOMIC WRITE ERROR] {file_path}: {e}", exc_info=True)
        raise IOError(f"Atomic write failed for {file_path}: {e}")


def safe_read(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    안전한 파일 읽기

    Args:
        file_path: 읽을 파일 경로
        encoding: 인코딩 (기본: utf-8)

    Returns:
        파일 내용 (파일 없으면 None)

    Note:
        atomic_write와 함께 사용하면 Read-Write 원자성 보장
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        logger.debug(f"[SAFE READ] 파일 없음: {file_path}")
        return None
    except Exception as e:
        logger.error(f"[SAFE READ ERROR] {file_path}: {e}", exc_info=True)
        return None


# 편의 함수: YAML Frontmatter 포함 파일 쓰기
def atomic_write_with_frontmatter(
    file_path: str,
    content: str,
    metadata: dict,
    encoding: str = 'utf-8'
) -> None:
    """
    YAML Frontmatter 포함 원자적 파일 쓰기

    Args:
        file_path: 쓸 파일 경로
        content: 본문 내용
        metadata: YAML frontmatter 딕셔너리
        encoding: 인코딩

    사용 예:
        atomic_write_with_frontmatter(
            "/path/to/context.md",
            "본문 내용",
            {"status": "active", "project_id": "test"}
        )
    """
    import yaml

    # YAML frontmatter 생성
    frontmatter = yaml.dump(metadata, allow_unicode=True, sort_keys=False)

    # 전체 내용 조합
    full_content = f"---\n{frontmatter}---\n\n{content}"

    # 원자적 쓰기
    atomic_write(file_path, full_content, encoding=encoding)
