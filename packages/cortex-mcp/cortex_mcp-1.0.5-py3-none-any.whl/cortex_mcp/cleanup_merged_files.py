"""
손상된 브랜치 파일 정리 스크립트

CONCATENATE 전략으로 인해 "## [Merged from ...]" 섹션이 반복적으로 추가되어
파일 크기가 기하급수적으로 증가한 파일들을 정리합니다.

작업:
1. YAML frontmatter 보존
2. "## [Merged from ...]" 섹션 및 그 내용 제거
3. 원본 백업 (.backup 확장자)
4. 정리된 파일로 교체
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import config


def clean_merged_content(content: str) -> str:
    """
    Merged 섹션 제거

    Args:
        content: 원본 파일 내용

    Returns:
        정리된 파일 내용
    """
    lines = content.split('\n')
    cleaned_lines = []
    skip_until_next_section = False
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        # YAML frontmatter 처리
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count <= 2:  # 첫 frontmatter만 유지
                in_frontmatter = not in_frontmatter
                cleaned_lines.append(line)
                continue
            else:
                skip_until_next_section = True  # 2번째 이후 frontmatter 스킵
                continue

        # frontmatter 내부는 항상 유지
        if in_frontmatter:
            cleaned_lines.append(line)
            continue

        # "## [Merged from ...]" 섹션 감지
        if re.match(r'^##\s+\[Merged from\s+.+\]', line):
            skip_until_next_section = True
            continue

        # 다음 ## 또는 # 섹션이 나오면 스킵 종료
        if skip_until_next_section:
            if re.match(r'^#\s+', line):  # # 로 시작하는 섹션
                skip_until_next_section = False
                cleaned_lines.append(line)
            # 계속 스킵
            continue

        # 정상 라인 추가
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def cleanup_file(file_path: Path, dry_run: bool = False) -> dict:
    """
    파일 정리

    Args:
        file_path: 파일 경로
        dry_run: True면 실제 수정하지 않음

    Returns:
        결과 정보
    """
    try:
        # 원본 읽기
        original_content = file_path.read_text(encoding='utf-8')
        original_lines = len(original_content.split('\n'))
        original_size = len(original_content)

        # Merge 헤더 개수 확인
        merge_count = len(re.findall(r'^##\s+\[Merged from\s+.+\]', original_content, re.MULTILINE))

        if merge_count == 0:
            return {
                'success': True,
                'skipped': True,
                'message': 'No merge sections found',
                'original_lines': original_lines,
                'original_size': original_size,
            }

        # 정리
        cleaned_content = clean_merged_content(original_content)
        cleaned_lines = len(cleaned_content.split('\n'))
        cleaned_size = len(cleaned_content)

        # 감소율 계산
        size_reduction = ((original_size - cleaned_size) / original_size * 100) if original_size > 0 else 0
        lines_reduction = ((original_lines - cleaned_lines) / original_lines * 100) if original_lines > 0 else 0

        if not dry_run:
            # 백업 생성
            backup_path = file_path.with_suffix('.md.backup')
            backup_path.write_text(original_content, encoding='utf-8')

            # 정리된 파일 저장
            file_path.write_text(cleaned_content, encoding='utf-8')

        return {
            'success': True,
            'skipped': False,
            'merge_count': merge_count,
            'original_lines': original_lines,
            'original_size': original_size,
            'cleaned_lines': cleaned_lines,
            'cleaned_size': cleaned_size,
            'size_reduction': size_reduction,
            'lines_reduction': lines_reduction,
            'dry_run': dry_run,
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


def main():
    """메인 실행"""
    project_id = "4d8e58aea4b0"
    memory_dir = config.base_dir / "memory" / project_id

    if not memory_dir.exists():
        print(f"디렉토리를 찾을 수 없습니다: {memory_dir}")
        return

    # .md 파일 목록
    md_files = list(memory_dir.glob("*.md"))

    if not md_files:
        print("처리할 .md 파일이 없습니다.")
        return

    print(f"\n총 {len(md_files)}개 파일 발견")
    print("\n=== DRY RUN MODE (실제 수정하지 않음) ===\n")

    results = []
    for md_file in md_files:
        result = cleanup_file(md_file, dry_run=True)
        results.append((md_file.name, result))

    # 결과 출력
    print("\n파일별 분석 결과:")
    print("-" * 100)
    print(f"{'파일명':<60} {'Merge 수':<10} {'원본 줄수':<12} {'정리 후':<12} {'감소율':<10}")
    print("-" * 100)

    total_original_size = 0
    total_cleaned_size = 0
    files_to_clean = 0

    for name, result in results:
        if result.get('skipped'):
            print(f"{name:<60} {'없음':<10} {result['original_lines']:<12} {'변경없음':<12} {'0%':<10}")
        elif result.get('success'):
            print(
                f"{name:<60} "
                f"{result['merge_count']:<10} "
                f"{result['original_lines']:<12} "
                f"{result['cleaned_lines']:<12} "
                f"{result['lines_reduction']:.1f}%"
            )
            total_original_size += result['original_size']
            total_cleaned_size += result['cleaned_size']
            files_to_clean += 1
        else:
            print(f"{name:<60} {'ERROR':<10} {result.get('error', 'Unknown')}")

    print("-" * 100)
    print(f"\n통계:")
    print(f"  - 정리 필요 파일: {files_to_clean}개")
    print(f"  - 전체 원본 크기: {total_original_size / 1024 / 1024:.2f} MB")
    print(f"  - 정리 후 크기: {total_cleaned_size / 1024 / 1024:.2f} MB")
    print(f"  - 절감 크기: {(total_original_size - total_cleaned_size) / 1024 / 1024:.2f} MB")
    print(f"  - 절감율: {((total_original_size - total_cleaned_size) / total_original_size * 100):.1f}%")

    # 실행 확인 (자동 진행)
    print("\n자동으로 정리를 시작합니다...")
    response = 'y'

    print("\n=== 실제 정리 시작 ===\n")

    success_count = 0
    for md_file in md_files:
        result = cleanup_file(md_file, dry_run=False)
        if result.get('success') and not result.get('skipped'):
            print(f"✓ {md_file.name}: {result['lines_reduction']:.1f}% 감소")
            success_count += 1
        elif result.get('skipped'):
            print(f"- {md_file.name}: 변경 없음")
        else:
            print(f"✗ {md_file.name}: {result.get('error', 'Unknown error')}")

    print(f"\n완료: {success_count}개 파일 정리됨")
    print(f"백업 파일은 .md.backup 확장자로 저장되었습니다.")


if __name__ == '__main__':
    main()
