#!/usr/bin/env python3
"""
Semantic Web Rebuilder

Reference History의 co_occurrence 데이터와 맥락 파일을 기반으로
시맨틱 웹 관계를 재구축합니다.

작업 순서:
1. co_occurrence에서 RELATED_TO 관계 추출 (2번 방식)
2. 맥락 파일의 ontology_category로 PART_OF 관계 추출 (1번 방식 보완)
3. 브랜치 계층 구조에서 PART_OF 관계 추출

Created: 2026-01-14
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# config.py에서 경로 함수 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_cortex_path, CORTEX_HOME

# Cortex 메모리 경로 - CORTEX_HOME 환경변수 존중
CORTEX_DIR = Path(CORTEX_HOME)
MEMORY_DIR = get_cortex_path("memory")


def load_json(path: Path) -> Dict:
    """JSON 파일 로드"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict) -> None:
    """JSON 파일 저장"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_yaml_frontmatter(content: str) -> Dict:
    """YAML frontmatter 추출"""
    if not content.startswith("---"):
        return {}

    try:
        end_idx = content.index("---", 3)
        yaml_content = content[3:end_idx].strip()

        result = {}
        for line in yaml_content.split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip("'\"")
                result[key] = value
        return result
    except (ValueError, Exception):
        return {}


def build_relations_from_co_occurrence(
    co_occurrence: Dict[str, Dict[str, int]]
) -> List[Dict]:
    """
    co_occurrence 데이터에서 RELATED_TO 관계 추출

    Args:
        co_occurrence: {context_a: {context_b: count, ...}, ...}

    Returns:
        관계 리스트
    """
    relations = []
    seen_pairs = set()

    for source, targets in co_occurrence.items():
        for target, count in targets.items():
            # 중복 방지 (양방향)
            pair = tuple(sorted([source, target]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            # confidence 계산: count 기반 (최대 1.0)
            confidence = min(1.0, count / 10.0 + 0.3)

            relations.append({
                "source": source,
                "target": target,
                "relation_type": "RELATED_TO",
                "confidence": round(confidence, 2),
                "evidence": f"co_occurrence_count:{count}",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

    return relations


def build_relations_from_context_files(
    contexts_dir: Path,
    branch_mapping: Dict[str, str]
) -> Tuple[List[Dict], Dict[str, Set[str]]]:
    """
    맥락 파일에서 관계 추출

    1. ontology_category -> 같은 카테고리면 RELATED_TO
    2. branch_id -> 같은 브랜치면 PART_OF

    Returns:
        (관계 리스트, 카테고리별 맥락 매핑)
    """
    relations = []
    category_contexts = defaultdict(set)
    branch_contexts = defaultdict(set)

    if not contexts_dir.exists():
        return relations, category_contexts

    # 모든 .md 파일 수집
    for md_file in contexts_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            meta = extract_yaml_frontmatter(content)

            context_id = md_file.stem
            category = meta.get("ontology_category", "uncategorized")
            branch_id = meta.get("branch_id", "unknown")

            category_contexts[category].add(context_id)
            branch_contexts[branch_id].add(context_id)
        except Exception as e:
            print(f"  [WARN] 파일 읽기 실패: {md_file.name} - {e}")

    # 같은 브랜치 내 맥락들은 PART_OF 관계
    for branch_id, contexts in branch_contexts.items():
        if len(contexts) < 2:
            continue

        contexts_list = list(contexts)
        # 첫 번째 맥락을 대표로 설정
        representative = contexts_list[0]

        for ctx in contexts_list[1:]:
            relations.append({
                "source": ctx,
                "target": representative,
                "relation_type": "PART_OF",
                "confidence": 0.8,
                "evidence": f"same_branch:{branch_id}",
                "created_at": datetime.now(timezone.utc).isoformat()
            })

    # 같은 카테고리 내 맥락들은 RELATED_TO 관계 (약한)
    for category, contexts in category_contexts.items():
        if category == "uncategorized" or len(contexts) < 2:
            continue

        contexts_list = list(contexts)
        # 너무 많으면 상위 10개만 연결
        if len(contexts_list) > 10:
            contexts_list = contexts_list[:10]

        for i, ctx_a in enumerate(contexts_list):
            for ctx_b in contexts_list[i+1:]:
                relations.append({
                    "source": ctx_a,
                    "target": ctx_b,
                    "relation_type": "RELATED_TO",
                    "confidence": 0.5,
                    "evidence": f"same_category:{category}",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })

    return relations, category_contexts


def build_semantic_web(project_id: str) -> Dict:
    """
    프로젝트의 시맨틱 웹 재구축
    """
    project_dir = MEMORY_DIR / project_id

    if not project_dir.exists():
        print(f"[ERROR] 프로젝트 디렉토리 없음: {project_dir}")
        return {}

    print(f"[INFO] 프로젝트: {project_id}")
    print(f"[INFO] 경로: {project_dir}")

    # 1. Reference History 로드
    ref_history_path = project_dir / "_reference_history.json"
    ref_history = load_json(ref_history_path)

    co_occurrence = ref_history.get("co_occurrence", {})
    print(f"[INFO] co_occurrence 항목 수: {len(co_occurrence)}")

    # 2. 인덱스 로드
    index_path = project_dir / "_index.json"
    index = load_json(index_path)

    branches = index.get("branches", {})
    print(f"[INFO] 브랜치 수: {len(branches)}")

    # 브랜치 ID -> 토픽 매핑
    branch_mapping = {
        bid: meta.get("branch_topic", bid)
        for bid, meta in branches.items()
    }

    # 3. co_occurrence에서 관계 추출 (2번 방식)
    print("[INFO] co_occurrence에서 관계 추출 중...")
    co_relations = build_relations_from_co_occurrence(co_occurrence)
    print(f"[INFO] co_occurrence 관계 수: {len(co_relations)}")

    # 4. 맥락 파일에서 관계 추출 (1번 방식 보완)
    contexts_dir = project_dir / "contexts"
    print("[INFO] 맥락 파일에서 관계 추출 중...")
    file_relations, category_contexts = build_relations_from_context_files(
        contexts_dir, branch_mapping
    )
    print(f"[INFO] 파일 기반 관계 수: {len(file_relations)}")
    print(f"[INFO] 카테고리 수: {len(category_contexts)}")

    # 5. 관계 병합 (중복 제거)
    all_relations = co_relations + file_relations

    # 중복 제거
    unique_relations = {}
    for rel in all_relations:
        key = (rel["source"], rel["target"], rel["relation_type"])
        if key not in unique_relations:
            unique_relations[key] = rel
        else:
            # 더 높은 confidence 유지
            if rel["confidence"] > unique_relations[key]["confidence"]:
                unique_relations[key] = rel

    final_relations = list(unique_relations.values())
    print(f"[INFO] 최종 관계 수: {len(final_relations)}")

    # 6. 노드 목록 생성
    nodes = set()
    for rel in final_relations:
        nodes.add(rel["source"])
        nodes.add(rel["target"])

    # 7. 시맨틱 웹 구조 생성
    semantic_web = {
        "version": "1.0",
        "project_id": project_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "statistics": {
            "total_nodes": len(nodes),
            "total_relations": len(final_relations),
            "relation_types": {
                "RELATED_TO": sum(1 for r in final_relations if r["relation_type"] == "RELATED_TO"),
                "PART_OF": sum(1 for r in final_relations if r["relation_type"] == "PART_OF"),
                "DEPENDS_ON": sum(1 for r in final_relations if r["relation_type"] == "DEPENDS_ON"),
            }
        },
        "nodes": {
            node: {
                "id": node,
                "category": None,  # 나중에 채워질 수 있음
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            for node in nodes
        },
        "relations": final_relations
    }

    return semantic_web


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Web Rebuilder")
    parser.add_argument(
        "--project",
        type=str,
        default="cortex-mcp",
        help="프로젝트 ID (기본값: cortex-mcp)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 저장하지 않고 결과만 출력"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Semantic Web Rebuilder")
    print("=" * 60)

    # 시맨틱 웹 구축
    semantic_web = build_semantic_web(args.project)

    if not semantic_web:
        print("[ERROR] 시맨틱 웹 구축 실패")
        return 1

    # 결과 출력
    print()
    print("=" * 60)
    print("결과 요약")
    print("=" * 60)
    stats = semantic_web.get("statistics", {})
    print(f"총 노드 수: {stats.get('total_nodes', 0)}")
    print(f"총 관계 수: {stats.get('total_relations', 0)}")
    print(f"  - RELATED_TO: {stats.get('relation_types', {}).get('RELATED_TO', 0)}")
    print(f"  - PART_OF: {stats.get('relation_types', {}).get('PART_OF', 0)}")
    print(f"  - DEPENDS_ON: {stats.get('relation_types', {}).get('DEPENDS_ON', 0)}")

    if args.dry_run:
        print()
        print("[DRY-RUN] 실제 저장하지 않음")
        return 0

    # 저장
    output_path = MEMORY_DIR / args.project / "_semantic_web.json"
    save_json(output_path, semantic_web)
    print()
    print(f"[SUCCESS] 저장 완료: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
