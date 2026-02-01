#!/usr/bin/env python3
"""
Cortex 프로젝트별 설치 스크립트

프로젝트 루트에 cortex_prompt.md를 생성하고,
클라이언트별로 자동 설정을 수행합니다.
"""

import platform
import sys
from pathlib import Path


def print_welcome():
    """환영 메시지"""
    print()
    print("━" * 70)
    print(" Cortex 초기 설정")
    print("━" * 70)
    print()
    print("Cortex는 AI와의 대화 맥락을 프로젝트별로 자동 관리합니다.")
    print()
    print("주요 기능:")
    print("  • 프로젝트 전환 시 맥락 자동 유지")
    print("  • 관련 브랜치 자동 로드")
    print("  • Zero-Effort (사용자 개입 최소화)")
    print()
    print("이 설정은 프로젝트당 1회만 실행하면 됩니다.")
    print()
    print("━" * 70)
    print()


def detect_ai_client(project_root: Path) -> str:
    """
    AI 클라이언트 자동 감지

    Args:
        project_root: 프로젝트 루트 경로

    Returns:
        클라이언트 이름
    """
    if (project_root / "CLAUDE.md").exists():
        return "claude-code"
    elif (project_root / ".clinerules").exists():
        return "cline"
    elif (project_root / ".continuerules").exists():
        return "continue"
    elif (project_root / ".cursorrules").exists():
        return "cursor"
    else:
        # UI 기반 클라이언트로 추정
        return "claude-desktop"


def safe_file_write(file_path: Path, content: str, mode: str = 'w') -> bool:
    """
    안전한 파일 쓰기 (권한 오류 처리)

    Args:
        file_path: 파일 경로
        content: 쓸 내용
        mode: 쓰기 모드 ('w' 또는 'a')

    Returns:
        성공 여부
    """
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        return True
    except PermissionError:
        print(f"❌ 권한 오류: {file_path}")
        print(f"   수동으로 다음 내용을 추가하세요:")
        print(f"   {content}")
        return False
    except Exception as e:
        print(f"❌ 파일 쓰기 실패: {e}")
        return False


def auto_add_reference(client: str, project_root: Path) -> bool:
    """
    클라이언트별 자동 참조 추가

    Args:
        client: 클라이언트 이름
        project_root: 프로젝트 루트

    Returns:
        자동 추가 성공 여부
    """
    ref_line = "\nRead and follow ./cortex_prompt.md\n"

    file_map = {
        "claude-code": "CLAUDE.md",
        "cline": ".clinerules",
        "continue": ".continuerules",
        "cursor": ".cursorrules"
    }

    if client not in file_map:
        return False  # 수동 설정 필요

    target_file = project_root / file_map[client]

    # 파일 생성 또는 업데이트
    if target_file.exists():
        content = target_file.read_text(encoding='utf-8')
        if "cortex_prompt.md" in content:
            print(f"ℹ️  이미 설정됨: {file_map[client]}")
            return True

        success = safe_file_write(target_file, ref_line, mode='a')
        if success:
            print(f"✅ {file_map[client]}에 자동 추가")
        return success
    else:
        success = safe_file_write(target_file, ref_line)
        if success:
            print(f"✅ {file_map[client]} 생성 및 설정")
        return success


def print_manual_guide(client: str, os_type: str):
    """
    수동 설정 안내 출력

    Args:
        client: 클라이언트 이름
        os_type: OS 타입
    """
    print()
    print("━" * 70)
    print("⚠️  수동 설정 필요 (Claude Desktop)")
    print("━" * 70)
    print()
    print("Claude Desktop의 Custom Instructions에 다음 한 줄을 추가하세요:")
    print()
    print("  Read and follow ./cortex_prompt.md")
    print()
    print("설정 위치:")
    if os_type == "Darwin":
        print("  Claude Desktop → Preferences (⌘,) → Custom Instructions")
    elif os_type == "Windows":
        print("  Claude Desktop → Settings → Custom Instructions")
    else:
        print("  Claude Desktop → Settings → Custom Instructions")
    print()
    print("━" * 70)
    print()


def setup_git_management(project_root: Path):
    """
    Git 관리 옵션 설정

    Args:
        project_root: 프로젝트 루트
    """
    print()
    print("━" * 70)
    print(" Git 관리 옵션")
    print("━" * 70)
    print()
    print("cortex_prompt.md를 Git으로 관리할까요?")
    print()
    print("  1. 아니요 (개인 맥락만, .gitignore 추가)")
    print("     → 개인 작업 내용, Git에 포함 안됨")
    print()
    print("  2. 예 (팀 공유, Git 추적)")
    print("     → 팀원과 맥락 공유, Git에 포함됨")
    print()

    choice = input("선택 [1/2]: ").strip()

    gitignore = project_root / ".gitignore"

    if choice == "1":
        # .gitignore 업데이트
        gitignore_content = "\n# Cortex 개인 맥락\ncortex_prompt.md\n"

        if gitignore.exists():
            content = gitignore.read_text(encoding='utf-8')
            if "cortex_prompt.md" not in content:
                success = safe_file_write(gitignore, gitignore_content, mode='a')
                if success:
                    print("✅ .gitignore 업데이트 (개인 맥락)")
            else:
                print("ℹ️  .gitignore에 이미 추가되어 있음")
        else:
            success = safe_file_write(gitignore, gitignore_content)
            if success:
                print("✅ .gitignore 생성 (개인 맥락)")
    else:
        print("ℹ️  cortex_prompt.md를 Git으로 추적 (팀 공유)")


def setup_project():
    """
    프로젝트별 Cortex 설정
    """
    # 환영 메시지
    print_welcome()

    # 1. 환경 감지
    os_type = platform.system()
    project_root = Path.cwd()
    client = detect_ai_client(project_root)

    print(f"🔍 환경 감지:")
    print(f"   OS: {os_type}")
    print(f"   Client: {client}")
    print(f"   Project: {project_root.name}")
    print(f"   Path: {project_root}")
    print()

    # 2. cortex_prompt.md 생성
    cortex_prompt = project_root / "cortex_prompt.md"

    if not cortex_prompt.exists():
        initial_content = """# CORTEX CONTEXT (Auto-managed)

Last updated: (Not yet)

---

## Current Branch

(Cortex will update this automatically)

---

## Instructions

Cortex will update this file automatically with:
- Current branch context
- Auto-loaded related branches
- Project-specific memory

No manual editing needed.
"""
        success = safe_file_write(cortex_prompt, initial_content)
        if success:
            print("✅ cortex_prompt.md 생성")
    else:
        print("ℹ️  cortex_prompt.md 이미 존재")

    # 3. 클라이언트별 처리
    auto_success = auto_add_reference(client, project_root)

    if not auto_success:
        # 수동 설정 안내
        print_manual_guide(client, os_type)

    # 4. Git 관리 옵션
    setup_git_management(project_root)

    # 5. 완료
    print()
    print("━" * 70)
    print("✅ 설정 완료!")
    print("━" * 70)
    print()

    if not auto_success:
        print("⚠️  설정 완료 후 Claude Desktop을 재시작하세요.")
        print()
    else:
        print("이제 Cortex가 자동으로 맥락을 관리합니다.")
        print()

    print("다음 단계:")
    print("  1. AI 클라이언트 시작/재시작")
    print("  2. 프로젝트에서 작업 시작")
    print("  3. Cortex가 자동으로 맥락 저장 및 로드")
    print()


if __name__ == "__main__":
    try:
        setup_project()
    except KeyboardInterrupt:
        print()
        print("❌ 설정 취소됨")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
