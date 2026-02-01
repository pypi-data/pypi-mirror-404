#!/usr/bin/env python3
"""
Cortex MCP - 미등록 브랜치 복구 스크립트

contexts/ 폴더에 존재하지만 _index.json에 등록되지 않은 브랜치들을 자동으로 등록합니다.

사용법:
    python recover_unregistered_branches.py [project_id]

    project_id를 지정하지 않으면 모든 프로젝트를 스캔합니다.

예시:
    python recover_unregistered_branches.py 4d8e58aea4b0
    python recover_unregistered_branches.py  # 모든 프로젝트 스캔
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# config.py에서 경로 함수 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_cortex_path


def get_memory_dir() -> Path:
    """Cortex 메모리 디렉토리 경로 반환 - CORTEX_HOME 환경변수 존중"""
    return get_cortex_path("memory")


def load_project_index(project_dir: Path) -> Dict[str, Any]:
    """프로젝트 인덱스 로드"""
    index_file = project_dir / "_index.json"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"project_id": project_dir.name, "branches": {}}


def save_project_index(project_dir: Path, index: Dict[str, Any]) -> None:
    """프로젝트 인덱스 저장"""
    index_file = project_dir / "_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def extract_frontmatter(md_file: Path) -> Dict[str, Any]:
    """
    마크다운 파일에서 YAML frontmatter 추출

    Returns:
        frontmatter dict (없으면 빈 dict)
    """
    try:
        content = md_file.read_text(encoding="utf-8")

        # YAML frontmatter 패턴: --- ... ---
        pattern = r'^---\s*\n(.*?)\n---'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return {}

        yaml_content = match.group(1)

        # 간단한 YAML 파싱 (key: value 형식)
        result = {}
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:
                    result[key] = value

        return result
    except Exception as e:
        print(f"  [WARN] Failed to extract frontmatter from {md_file}: {e}")
        return {}


def count_contexts(branch_dir: Path) -> int:
    """브랜치 디렉토리 내 컨텍스트 파일 개수 반환"""
    md_files = list(branch_dir.glob("*.md"))
    # _index.md, _branch_index.json 등 제외
    context_files = [f for f in md_files if not f.name.startswith("_")]
    return len(context_files)


def get_branch_creation_time(branch_dir: Path) -> str:
    """
    브랜치 생성 시간 추정

    1. _index.md frontmatter의 created_at
    2. 가장 오래된 파일의 생성 시간
    3. 브랜치 디렉토리의 생성 시간
    """
    # 1. _index.md에서 추출 시도
    index_md = branch_dir / "_index.md"
    if index_md.exists():
        fm = extract_frontmatter(index_md)
        if "created_at" in fm:
            return fm["created_at"]

    # 2. 가장 오래된 파일 시간
    md_files = list(branch_dir.glob("*.md"))
    if md_files:
        oldest = min(md_files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(oldest.stat().st_mtime, tz=timezone.utc).isoformat()

    # 3. 디렉토리 시간
    return datetime.fromtimestamp(branch_dir.stat().st_mtime, tz=timezone.utc).isoformat()


def get_branch_topic(branch_dir: Path, branch_id: str) -> str:
    """
    브랜치 주제 추출

    1. _index.md frontmatter의 branch_topic
    2. 브랜치 ID에서 추출
    """
    # 1. _index.md에서 추출 시도
    index_md = branch_dir / "_index.md"
    if index_md.exists():
        fm = extract_frontmatter(index_md)
        if "branch_topic" in fm:
            return fm["branch_topic"]

    # 2. branch_id에서 추출 (타임스탬프 제거)
    # 형식: branch_{uuid}_{timestamp} 또는 {topic}_{timestamp}
    if branch_id.startswith("branch_"):
        return f"Auto-recovered branch: {branch_id[:30]}"

    # 타임스탬프 패턴 제거
    topic = re.sub(r'_\d{8}_\d{6,}$', '', branch_id)
    return topic if topic else branch_id


def recover_unregistered_branches(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    미등록 브랜치 복구

    Args:
        project_id: 특정 프로젝트 ID (None이면 모든 프로젝트 스캔)

    Returns:
        복구 결과 dict
    """
    memory_dir = get_memory_dir()

    if not memory_dir.exists():
        return {"error": f"Memory directory not found: {memory_dir}"}

    results = {
        "scanned_projects": [],
        "recovered_branches": [],
        "errors": [],
        "summary": {}
    }

    # 프로젝트 목록
    if project_id:
        project_dirs = [memory_dir / project_id]
        if not project_dirs[0].exists():
            return {"error": f"Project not found: {project_id}"}
    else:
        project_dirs = [d for d in memory_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]

    total_recovered = 0

    for project_dir in project_dirs:
        project_id = project_dir.name
        print(f"\n[INFO] Scanning project: {project_id}")
        results["scanned_projects"].append(project_id)

        # contexts 디렉토리 확인
        contexts_dir = project_dir / "contexts"
        if not contexts_dir.exists():
            print(f"  [SKIP] No contexts directory")
            continue

        # 프로젝트 인덱스 로드
        index = load_project_index(project_dir)
        registered_branches = set(index.get("branches", {}).keys())

        # contexts/ 내 모든 디렉토리 스캔
        recovered_in_project = []
        for branch_dir in contexts_dir.iterdir():
            if not branch_dir.is_dir():
                continue

            branch_id = branch_dir.name

            # 이미 등록된 브랜치는 스킵
            if branch_id in registered_branches:
                continue

            # 미등록 브랜치 발견!
            print(f"  [FOUND] Unregistered branch: {branch_id}")

            try:
                # 브랜치 메타데이터 생성
                branch_topic = get_branch_topic(branch_dir, branch_id)
                created_at = get_branch_creation_time(branch_dir)
                context_count = count_contexts(branch_dir)

                branch_metadata = {
                    "branch_id": branch_id,
                    "branch_topic": branch_topic,
                    "parent_branch": None,
                    "created_at": created_at,
                    "status": "active",
                    "context_count": context_count,
                    "auto_created": False,
                    "recovered": True,
                    "recovered_at": datetime.now(timezone.utc).isoformat()
                }

                # 인덱스에 등록
                if "branches" not in index:
                    index["branches"] = {}
                index["branches"][branch_id] = branch_metadata

                recovered_in_project.append({
                    "project_id": project_id,
                    "branch_id": branch_id,
                    "branch_topic": branch_topic,
                    "context_count": context_count
                })

                print(f"    -> Recovered: topic='{branch_topic}', contexts={context_count}")

            except Exception as e:
                error_msg = f"Failed to recover {branch_id} in {project_id}: {e}"
                print(f"  [ERROR] {error_msg}")
                results["errors"].append(error_msg)

        # 인덱스 저장
        if recovered_in_project:
            save_project_index(project_dir, index)
            print(f"  [SAVED] Index updated with {len(recovered_in_project)} branches")

        results["recovered_branches"].extend(recovered_in_project)
        total_recovered += len(recovered_in_project)

    # 요약
    results["summary"] = {
        "total_projects_scanned": len(results["scanned_projects"]),
        "total_branches_recovered": total_recovered,
        "total_errors": len(results["errors"])
    }

    return results


def main():
    """메인 함수"""
    print("=" * 60)
    print("Cortex MCP - Unregistered Branch Recovery Script")
    print("=" * 60)

    # 인자 파싱
    project_id = sys.argv[1] if len(sys.argv) > 1 else None

    if project_id:
        print(f"Target project: {project_id}")
    else:
        print("Target: All projects")

    # 복구 실행
    results = recover_unregistered_branches(project_id)

    # 결과 출력
    print("\n" + "=" * 60)
    print("Recovery Results")
    print("=" * 60)

    if "error" in results:
        print(f"[ERROR] {results['error']}")
        return 1

    summary = results["summary"]
    print(f"Projects scanned: {summary['total_projects_scanned']}")
    print(f"Branches recovered: {summary['total_branches_recovered']}")
    print(f"Errors: {summary['total_errors']}")

    if results["recovered_branches"]:
        print("\nRecovered branches:")
        for branch in results["recovered_branches"]:
            print(f"  - {branch['project_id']}/{branch['branch_id']}")
            print(f"    Topic: {branch['branch_topic']}")
            print(f"    Contexts: {branch['context_count']}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("\n[DONE] Recovery complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
