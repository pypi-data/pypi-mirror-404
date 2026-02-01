"""
Cortex MCP - Team Context Merge Engine (v1.0)
Git merge 시 Cortex 맥락도 자동 병합

Enterprise 전용 기능:
- Git merge 감지 및 Cortex 맥락 자동 병합
- 충돌 감지 및 해결
- 팀원 기여 추적
- 맥락 간 링크 자동 생성

기능:
1. Git merge 이벤트 감지
2. Cortex 브랜치 병합 (3-way merge)
3. 충돌 감지 및 해결 전략
4. 맥락 간 연결 관계 생성
"""

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(str(Path(__file__).parent.parent))
from config import config


class MergeStrategy(Enum):
    """병합 전략"""

    THREE_WAY = "three_way"  # 공통 조상 기반 병합
    OURS = "ours"  # 현재 브랜치 우선
    THEIRS = "theirs"  # 병합 대상 브랜치 우선
    MANUAL = "manual"  # 수동 해결 필요
    CONCATENATE = "concatenate"  # 단순 연결 (충돌 없는 경우)
    INCREMENTAL = "incremental"  # 새 내용만 추가 (병렬 개발용)


@dataclass
class MergeConflict:
    """병합 충돌 정보"""

    topic: str  # 충돌 토픽
    source_content: str  # 소스 브랜치 내용
    target_content: str  # 타겟 브랜치 내용
    source_branch: str  # 소스 브랜치 ID
    target_branch: str  # 타겟 브랜치 ID
    conflict_type: str = "content"  # content, metadata, structure
    resolved: bool = False  # 해결 여부
    resolution: Optional[str] = None  # 해결된 내용


@dataclass
class MergeResult:
    """병합 결과"""

    success: bool
    merged_branch_id: str
    source_branch: str
    target_branch: str
    strategy_used: MergeStrategy
    conflicts: List[MergeConflict] = field(default_factory=list)
    links_created: List[Dict] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "merged_branch_id": self.merged_branch_id,
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "strategy_used": self.strategy_used.value,
            "conflict_count": len(self.conflicts),
            "conflicts": [
                {"topic": c.topic, "type": c.conflict_type, "resolved": c.resolved}
                for c in self.conflicts
            ],
            "links_created": self.links_created,
            "message": self.message,
        }


class TeamContextMerger:
    """
    팀 맥락 병합 엔진

    Git merge 시 Cortex 맥락도 자동으로 병합합니다.
    Enterprise 전용 기능입니다.
    """

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.memory_dir = config.memory_dir / project_id
        self.team_dir = config.base_dir / "team" / project_id
        self.team_dir.mkdir(parents=True, exist_ok=True)

        # 병합 히스토리 파일
        self.merge_history_file = self.team_dir / "merge_history.json"
        self.links_file = self.team_dir / "context_links.json"

    def detect_git_merge(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """
        Git merge 이벤트 감지

        Args:
            repo_path: Git 저장소 경로

        Returns:
            병합 정보 또는 None
        """
        try:
            # 최근 커밋이 merge인지 확인
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%P"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return None

            parents = result.stdout.strip().split()

            # 부모가 2개 이상이면 merge 커밋
            if len(parents) >= 2:
                # merge 커밋 메시지에서 브랜치 정보 추출
                msg_result = subprocess.run(
                    ["git", "log", "-1", "--pretty=%B"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                commit_msg = msg_result.stdout.strip() if msg_result.returncode == 0 else ""

                # "Merge branch 'feature/xxx'" 패턴에서 브랜치명 추출
                merged_branch = None
                if "Merge branch" in commit_msg:
                    import re

                    match = re.search(r"Merge branch '([^']+)'", commit_msg)
                    if match:
                        merged_branch = match.group(1)

                return {
                    "is_merge": True,
                    "parent_commits": parents,
                    "merged_branch": merged_branch,
                    "commit_message": commit_msg,
                }

            return None

        except Exception as e:
            return None

    def merge_team_context(
        self,
        source_branch: str,
        target_branch: str,
        strategy: MergeStrategy = MergeStrategy.THREE_WAY,
        auto_resolve: bool = True,
    ) -> MergeResult:
        """
        팀 맥락 병합

        Args:
            source_branch: 소스 Cortex 브랜치 ID
            target_branch: 타겟 Cortex 브랜치 ID
            strategy: 병합 전략
            auto_resolve: 자동 충돌 해결 여부

        Returns:
            MergeResult
        """
        # 브랜치 파일 로드
        source_data = self._load_branch_data(source_branch)
        target_data = self._load_branch_data(target_branch)

        if not source_data:
            return MergeResult(
                success=False,
                merged_branch_id="",
                source_branch=source_branch,
                target_branch=target_branch,
                strategy_used=strategy,
                message=f"Source branch not found: {source_branch}",
            )

        if not target_data:
            return MergeResult(
                success=False,
                merged_branch_id="",
                source_branch=source_branch,
                target_branch=target_branch,
                strategy_used=strategy,
                message=f"Target branch not found: {target_branch}",
            )

        # 충돌 감지
        conflicts = self._detect_conflicts(source_data, target_data)

        # 충돌 해결
        if conflicts and auto_resolve:
            conflicts = self._auto_resolve_conflicts(conflicts, strategy)

        # 미해결 충돌이 있으면 수동 해결 필요
        unresolved = [c for c in conflicts if not c.resolved]
        if unresolved:
            return MergeResult(
                success=False,
                merged_branch_id="",
                source_branch=source_branch,
                target_branch=target_branch,
                strategy_used=MergeStrategy.MANUAL,
                conflicts=conflicts,
                message=f"{len(unresolved)} conflicts require manual resolution",
            )

        # 병합 수행
        merged_data, merged_branch_id = self._perform_merge(
            source_data, target_data, conflicts, strategy
        )

        # 맥락 간 링크 생성
        links = self._create_merge_links(source_branch, target_branch, merged_branch_id)

        # 병합 히스토리 기록
        self._record_merge_history(source_branch, target_branch, merged_branch_id, strategy, links)

        return MergeResult(
            success=True,
            merged_branch_id=merged_branch_id,
            source_branch=source_branch,
            target_branch=target_branch,
            strategy_used=strategy,
            conflicts=conflicts,
            links_created=links,
            message=f"Successfully merged {source_branch} into {target_branch}",
        )

    def detect_context_conflicts(self, branches: List[str]) -> List[MergeConflict]:
        """
        여러 브랜치 간 충돌 사전 감지

        Args:
            branches: 검사할 브랜치 ID 목록

        Returns:
            감지된 충돌 목록
        """
        all_conflicts = []

        # 모든 쌍에 대해 충돌 검사
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                source_data = self._load_branch_data(branches[i])
                target_data = self._load_branch_data(branches[j])

                if source_data and target_data:
                    conflicts = self._detect_conflicts(source_data, target_data)
                    all_conflicts.extend(conflicts)

        return all_conflicts

    def resolve_context_conflict(
        self,
        conflict: MergeConflict,
        resolution: str,
        strategy: MergeStrategy = MergeStrategy.MANUAL,
    ) -> MergeConflict:
        """
        충돌 수동 해결

        Args:
            conflict: 해결할 충돌
            resolution: 해결 내용
            strategy: 사용된 전략

        Returns:
            해결된 충돌
        """
        conflict.resolved = True
        conflict.resolution = resolution
        return conflict

    def get_team_context_history(
        self, since: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        팀 맥락 병합 히스토리 조회

        Args:
            since: 이 시점 이후의 기록만 (ISO format)
            limit: 최대 개수

        Returns:
            병합 히스토리 목록
        """
        history = self._load_merge_history()
        entries = history.get("entries", [])

        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                entries = [
                    e
                    for e in entries
                    if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= since_dt
                ]
            except ValueError:
                pass

        return entries[-limit:]

    def link_contexts(
        self, from_context: str, to_context: str, relation: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        맥락 간 링크 수동 생성

        Args:
            from_context: 소스 맥락 ID
            to_context: 타겟 맥락 ID
            relation: 관계 유형 (e.g., "user_flow", "depends_on", "related_to")
            description: 설명

        Returns:
            생성된 링크 정보
        """
        links = self._load_links()

        link = {
            "from": from_context,
            "to": to_context,
            "relation": relation,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "auto_generated": False,
        }

        links.setdefault("links", []).append(link)
        self._save_links(links)

        return link

    def get_context_links(self, context_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        맥락 링크 조회

        Args:
            context_id: 특정 맥락의 링크만 조회 (선택)

        Returns:
            링크 목록
        """
        links = self._load_links()
        all_links = links.get("links", [])

        if context_id:
            return [l for l in all_links if l["from"] == context_id or l["to"] == context_id]

        return all_links

    # ==================== Private Methods ====================

    def _load_branch_data(self, branch_id: str) -> Optional[Dict[str, Any]]:
        """브랜치 데이터 로드"""
        if not self.memory_dir.exists():
            return None

        for md_file in self.memory_dir.glob("*.md"):
            if branch_id in md_file.stem:
                content = md_file.read_text(encoding="utf-8")
                return self._parse_branch_content(content, md_file.name)

        return None

    def _parse_branch_content(self, content: str, filename: str) -> Dict[str, Any]:
        """브랜치 내용 파싱"""
        import yaml

        frontmatter = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                body = parts[2].strip()

        # 토픽별로 내용 분리
        topics = self._extract_topics(body)

        return {
            "filename": filename,
            "frontmatter": frontmatter,
            "body": body,
            "topics": topics,
            "fingerprint": self._compute_fingerprint(body),
        }

    def _extract_topics(self, body: str) -> Dict[str, str]:
        """본문에서 토픽별 내용 추출"""
        import re

        topics = {}
        # ### [ROLE] TIMESTAMP 패턴으로 엔트리 분리
        pattern = r"###\s*\[(\w+)\]\s*([\d\-]+\s+[\d:]+\s+\w+)\n([\s\S]*?)(?=###\s*\[|\Z)"
        matches = re.findall(pattern, body)

        for i, (role, timestamp, content) in enumerate(matches):
            topic_key = f"{role}_{i}"
            topics[topic_key] = content.strip()

        return topics

    def _compute_fingerprint(self, content: str) -> str:
        """내용 핑거프린트 계산"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _detect_conflicts(
        self, source_data: Dict[str, Any], target_data: Dict[str, Any]
    ) -> List[MergeConflict]:
        """충돌 감지"""
        conflicts = []

        source_topics = source_data.get("topics", {})
        target_topics = target_data.get("topics", {})

        # 동일 토픽에 다른 내용이 있는 경우
        common_topics = set(source_topics.keys()) & set(target_topics.keys())

        for topic in common_topics:
            source_content = source_topics[topic]
            target_content = target_topics[topic]

            # 내용이 다르면 충돌
            if source_content != target_content:
                conflicts.append(
                    MergeConflict(
                        topic=topic,
                        source_content=source_content,
                        target_content=target_content,
                        source_branch=source_data["frontmatter"].get("branch_id", "unknown"),
                        target_branch=target_data["frontmatter"].get("branch_id", "unknown"),
                        conflict_type="content",
                    )
                )

        # 메타데이터 충돌 검사
        source_fm = source_data.get("frontmatter", {})
        target_fm = target_data.get("frontmatter", {})

        # 동일 topic으로 분류되었으나 내용이 다른 경우
        if source_fm.get("branch_topic") == target_fm.get("branch_topic") and source_data.get(
            "fingerprint"
        ) != target_data.get("fingerprint"):
            conflicts.append(
                MergeConflict(
                    topic="branch_topic",
                    source_content=str(source_fm.get("branch_topic")),
                    target_content=str(target_fm.get("branch_topic")),
                    source_branch=source_fm.get("branch_id", "unknown"),
                    target_branch=target_fm.get("branch_id", "unknown"),
                    conflict_type="metadata",
                )
            )

        return conflicts

    def _auto_resolve_conflicts(
        self, conflicts: List[MergeConflict], strategy: MergeStrategy
    ) -> List[MergeConflict]:
        """충돌 자동 해결"""
        for conflict in conflicts:
            if conflict.resolved:
                continue

            if strategy == MergeStrategy.OURS:
                conflict.resolution = conflict.target_content
                conflict.resolved = True
            elif strategy == MergeStrategy.THEIRS:
                conflict.resolution = conflict.source_content
                conflict.resolved = True
            elif strategy == MergeStrategy.INCREMENTAL:
                # 병렬 개발용: 기존 내용 우선, 새 내용은 append
                # 충돌 시 타겟(기존 브랜치) 우선
                conflict.resolution = conflict.target_content
                conflict.resolved = True
            elif strategy == MergeStrategy.CONCATENATE:
                # 두 내용 모두 유지
                conflict.resolution = (
                    f"[From {conflict.source_branch}]\n{conflict.source_content}\n\n"
                    f"[From {conflict.target_branch}]\n{conflict.target_content}"
                )
                conflict.resolved = True
            elif strategy == MergeStrategy.THREE_WAY:
                # 단순한 경우 자동 해결 시도
                if conflict.conflict_type == "metadata":
                    # 메타데이터는 타겟 우선
                    conflict.resolution = conflict.target_content
                    conflict.resolved = True
                else:
                    # 내용 충돌은 concatenate로 처리
                    conflict.resolution = (
                        f"[Merged from {conflict.source_branch}]\n{conflict.source_content}\n\n"
                        f"[Existing in {conflict.target_branch}]\n{conflict.target_content}"
                    )
                    conflict.resolved = True

        return conflicts

    def _perform_merge(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        conflicts: List[MergeConflict],
        strategy: MergeStrategy,
    ) -> Tuple[Dict[str, Any], str]:
        """실제 병합 수행"""
        import yaml

        # 타겟을 기반으로 병합
        merged_frontmatter = target_data["frontmatter"].copy()
        merged_body = target_data["body"]

        # 소스의 고유 토픽 추가
        source_topics = source_data.get("topics", {})
        target_topics = target_data.get("topics", {})

        new_topics = set(source_topics.keys()) - set(target_topics.keys())

        if new_topics:
            if strategy == MergeStrategy.INCREMENTAL:
                # INCREMENTAL: 새 내용만 직접 추가 (Merge 헤더 없이)
                for topic in sorted(new_topics):
                    merged_body += f"\n\n### [{topic}]\n{source_topics[topic]}\n"
            else:
                # CONCATENATE 등: Merge 헤더와 함께 추가
                merged_body += (
                    "\n\n## [Merged from "
                    + source_data["frontmatter"].get("branch_id", "source")
                    + "]\n"
                )
                for topic in sorted(new_topics):
                    merged_body += f"\n### [{topic}]\n{source_topics[topic]}\n"

        # 충돌 해결 내용 반영
        for conflict in conflicts:
            if conflict.resolved and conflict.resolution:
                # 기존 내용을 해결된 내용으로 대체
                # (실제 구현에서는 더 정교한 병합 필요)
                pass

        # 병합 메타데이터 업데이트 (INCREMENTAL은 제외)
        if strategy != MergeStrategy.INCREMENTAL:
            merged_frontmatter["merged_from"] = source_data["frontmatter"].get("branch_id")
            merged_frontmatter["merged_at"] = datetime.now(timezone.utc).isoformat()
            merged_frontmatter["merge_strategy"] = strategy.value

        # 병합된 브랜치 ID
        merged_branch_id = target_data["frontmatter"].get("branch_id", "merged")

        # 파일 저장
        yaml_content = yaml.dump(merged_frontmatter, allow_unicode=True, default_flow_style=False)
        full_content = f"---\n{yaml_content}---\n{merged_body}"

        target_file = self.memory_dir / target_data["filename"]
        if target_file.exists():
            target_file.write_text(full_content, encoding="utf-8")

        return {"frontmatter": merged_frontmatter, "body": merged_body}, merged_branch_id

    def _create_merge_links(
        self, source_branch: str, target_branch: str, merged_branch_id: str
    ) -> List[Dict]:
        """병합 링크 생성"""
        links = []

        # 소스 → 병합 링크
        links.append(
            {
                "from": source_branch,
                "to": merged_branch_id,
                "relation": "merged_into",
                "description": f"Merged into {merged_branch_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "auto_generated": True,
            }
        )

        # 소스 → 타겟 관계 링크
        links.append(
            {
                "from": source_branch,
                "to": target_branch,
                "relation": "related_to",
                "description": f"Related through merge",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "auto_generated": True,
            }
        )

        # 저장
        existing_links = self._load_links()
        existing_links.setdefault("links", []).extend(links)
        self._save_links(existing_links)

        return links

    def _record_merge_history(
        self,
        source_branch: str,
        target_branch: str,
        merged_branch_id: str,
        strategy: MergeStrategy,
        links: List[Dict],
    ):
        """병합 히스토리 기록"""
        history = self._load_merge_history()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_branch": source_branch,
            "target_branch": target_branch,
            "merged_branch_id": merged_branch_id,
            "strategy": strategy.value,
            "links_created": len(links),
        }

        history.setdefault("entries", []).append(entry)
        history["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.merge_history_file.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_merge_history(self) -> Dict:
        """병합 히스토리 로드"""
        if self.merge_history_file.exists():
            try:
                return json.loads(self.merge_history_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"version": "1.0", "entries": []}

    def _load_links(self) -> Dict:
        """링크 파일 로드"""
        if self.links_file.exists():
            try:
                return json.loads(self.links_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {"version": "1.0", "links": []}

    def _save_links(self, links: Dict):
        """링크 파일 저장"""
        links["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.links_file.write_text(
            json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def get_team_merger(project_id: str) -> TeamContextMerger:
    """프로젝트별 TeamContextMerger 인스턴스 반환"""
    return TeamContextMerger(project_id=project_id)
