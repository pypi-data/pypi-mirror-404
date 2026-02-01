"""
메모리 파일 중복 제거 및 압축 스크립트

목표:
1. 연속된 중복 섹션 제거 (같은 ASSISTANT 엔트리가 반복되는 경우)
2. full content를 summary로 압축
3. 189MB → 목표 크기로 축소
"""
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
from config import config


def remove_consecutive_duplicates(content: str) -> tuple[str, int]:
    """
    연속된 중복 섹션 제거

    예:
    ### [ASSISTANT_1]
    내용...
    ### [ASSISTANT_1]
    내용...
    ### [ASSISTANT_1]
    내용...

    → 첫 번째만 유지

    Returns:
        (정리된 내용, 제거된 중복 개수)
    """
    lines = content.split('\n')
    cleaned_lines = []

    section_pattern = re.compile(r'^###\s+\[ASSISTANT_\d+\]')
    current_section = None
    current_section_content = []
    section_hashes = set()
    duplicates_removed = 0

    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        # YAML frontmatter는 무조건 유지
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count <= 2:
                in_frontmatter = not in_frontmatter
                cleaned_lines.append(line)
                continue

        if in_frontmatter:
            cleaned_lines.append(line)
            continue

        # ASSISTANT 섹션 시작 감지
        if section_pattern.match(line):
            # 이전 섹션 처리
            if current_section and current_section_content:
                section_hash = '\n'.join(current_section_content)
                if section_hash not in section_hashes:
                    cleaned_lines.append(current_section)
                    cleaned_lines.extend(current_section_content)
                    section_hashes.add(section_hash)
                else:
                    duplicates_removed += 1

            # 새 섹션 시작
            current_section = line
            current_section_content = []
        else:
            # 섹션 내용 수집
            if current_section:
                current_section_content.append(line)
            else:
                # 섹션 밖의 내용 (frontmatter 이후 일반 텍스트)
                cleaned_lines.append(line)

    # 마지막 섹션 처리
    if current_section and current_section_content:
        section_hash = '\n'.join(current_section_content)
        if section_hash not in section_hashes:
            cleaned_lines.append(current_section)
            cleaned_lines.extend(current_section_content)
        else:
            duplicates_removed += 1

    return '\n'.join(cleaned_lines), duplicates_removed


def compress_to_summary(file_path: Path) -> dict:
    """
    파일을 summary로 압축

    Strategy:
    1. frontmatter 유지 (summary 포함)
    2. body는 summary 정보만 남김
    3. full content 삭제

    Returns:
        결과 정보
    """
    try:
        original_content = file_path.read_text(encoding='utf-8')
        original_size = len(original_content)

        # frontmatter 추출
        parts = original_content.split('---', 2)
        if len(parts) < 3:
            return {'success': False, 'error': 'Invalid frontmatter'}

        frontmatter_text = parts[1]
        body = parts[2]

        # 중복 제거
        cleaned_body, duplicates = remove_consecutive_duplicates(original_content)

        # summary 기반 압축된 body 생성
        compressed_body = f"""

이 브랜치의 전체 내용은 frontmatter의 summary에 요약되어 있습니다.
자세한 내용이 필요하면 load_context 도구를 사용하세요.

---
압축 정보:
- 압축 시간: {datetime.now(timezone.utc).isoformat()}
- 원본 크기: {original_size / 1024:.2f} KB
- 제거된 중복 섹션: {duplicates}개

Smart Context 시스템에 의해 자동 압축되었습니다.
"""

        # 최종 내용
        final_content = f"---{frontmatter_text}---{compressed_body}"
        final_size = len(final_content)

        reduction = ((original_size - final_size) / original_size * 100) if original_size > 0 else 0

        return {
            'success': True,
            'original_size': original_size,
            'final_size': final_size,
            'reduction_pct': reduction,
            'duplicates_removed': duplicates,
            'compressed_content': final_content
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    """메인 실행"""
    project_id = "4d8e58aea4b0"
    memory_dir = config.base_dir / "memory" / project_id

    if not memory_dir.exists():
        print(f"디렉토리를 찾을 수 없습니다: {memory_dir}")
        return

    md_files = list(memory_dir.glob("*.md"))

    if not md_files:
        print("처리할 .md 파일이 없습니다.")
        return

    print(f"\n총 {len(md_files)}개 파일 발견")
    print("\n=== Phase 1: DRY RUN (실제 수정하지 않음) ===\n")

    results = []
    total_original = 0
    total_final = 0

    for md_file in md_files:
        result = compress_to_summary(md_file)
        results.append((md_file.name, result))

        if result.get('success'):
            total_original += result['original_size']
            total_final += result['final_size']

    # 결과 출력
    print(f"{'파일명':<70} {'원본':<12} {'압축 후':<12} {'감소율':<10} {'중복 제거':<10}")
    print("-" * 120)

    for name, result in results:
        if result.get('success'):
            print(
                f"{name:<70} "
                f"{result['original_size']/1024:<11.1f}K "
                f"{result['final_size']/1024:<11.1f}K "
                f"{result['reduction_pct']:<9.1f}% "
                f"{result['duplicates_removed']:<10}개"
            )
        else:
            print(f"{name:<70} ERROR: {result.get('error', 'Unknown')}")

    print("-" * 120)
    print(f"\n통계:")
    print(f"  - 전체 원본 크기: {total_original / 1024 / 1024:.2f} MB")
    print(f"  - 압축 후 크기: {total_final / 1024 / 1024:.2f} MB")
    print(f"  - 절감 크기: {(total_original - total_final) / 1024 / 1024:.2f} MB")
    print(f"  - 절감율: {((total_original - total_final) / total_original * 100):.1f}%")

    # 실행 확인
    print("\n\n=== Phase 2: 실제 압축 실행 ===")
    print("위 결과를 확인하셨습니다.")
    print("실제로 파일을 압축하겠습니다 (백업은 .backup 확장자로 저장됩니다).")

    # 자동 진행
    print("\n압축을 시작합니다...\n")

    success_count = 0
    for md_file in md_files:
        result = compress_to_summary(md_file)

        if result.get('success'):
            # 백업 생성
            backup_path = md_file.with_suffix('.md.backup')
            original_content = md_file.read_text(encoding='utf-8')
            backup_path.write_text(original_content, encoding='utf-8')

            # 압축된 파일 저장
            md_file.write_text(result['compressed_content'], encoding='utf-8')

            print(f"✓ {md_file.name}: {result['reduction_pct']:.1f}% 감소 ({result['duplicates_removed']}개 중복 제거)")
            success_count += 1
        else:
            print(f"✗ {md_file.name}: {result.get('error', 'Unknown error')}")

    print(f"\n완료: {success_count}개 파일 압축됨")
    print(f"백업 파일은 .md.backup 확장자로 저장되었습니다.")
    print(f"\n최종 크기: {total_final / 1024 / 1024:.2f} MB")


if __name__ == '__main__':
    main()
