"""
Cortex MCP - Summary Generator

요약 생성 및 관리:
- 추출적 요약 생성 (Zero-Trust: 로컬 처리)
- 대화 엔트리 파싱
- 핵심 정보 추출
- 요약 업데이트 트리거 판단
"""

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .file_io import FileIO

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """요약 생성 및 관리 담당"""

    def __init__(self, memory_dir: Path, file_io: FileIO):
        """
        Args:
            memory_dir: 메모리 저장 디렉토리
            file_io: 파일 I/O 유틸리티
        """
        self.memory_dir = memory_dir
        self.file_io = file_io

    def should_update_summary(self, frontmatter: Dict, body: str) -> bool:
        """
        요약 업데이트가 필요한지 판단

        조건:
        1. 아직 요약이 초기값인 경우
        2. 마지막 요약 후 새 엔트리가 5개 이상 추가된 경우
        3. 요약이 비어있는 경우

        Args:
            frontmatter: Context frontmatter
            body: Context body

        Returns:
            업데이트 필요 여부
        """
        current_summary = frontmatter.get("summary", "")

        # 초기값이거나 비어있으면 업데이트 필요
        if not current_summary or current_summary == "새로운 브랜치가 생성되었습니다.":
            return True

        # 최소한의 내용이 있어야 요약 생성
        entries = self.parse_conversation_entries(body)
        if len(entries) < 1:
            return False

        # 마지막 요약 이후 새 엔트리 개수 확인
        last_summarized = frontmatter.get("last_summarized")
        if not last_summarized:
            return len(entries) >= 1  # 요약 기록이 없으면 1개 이상일 때 생성

        # 새 엔트리가 5개 이상이면 요약 갱신
        new_entries_count = self._count_entries_after(entries, last_summarized)
        return new_entries_count >= 5

    def _count_entries_after(self, entries: List[Dict], timestamp_str: str) -> int:
        """특정 시간 이후 추가된 엔트리 개수"""
        try:
            threshold = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return len(entries)

        count = 0
        for entry in entries:
            entry_time_str = entry.get("timestamp", "")
            try:
                # "2025-12-10 13:33:36 UTC" 형식 파싱
                entry_time = datetime.strptime(
                    entry_time_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                if entry_time > threshold:
                    count += 1
            except (ValueError, AttributeError):
                count += 1  # 파싱 실패시 새 엔트리로 간주

        return count

    def parse_conversation_entries(self, body: str) -> List[Dict]:
        """
        대화 본문에서 개별 엔트리 파싱

        형식: ### [ROLE] TIMESTAMP

        Args:
            body: Context body

        Returns:
            엔트리 리스트 (role, timestamp, content)
        """
        entries = []
        # ### [ASSISTANT] 2025-12-10 13:33:36 UTC 또는 ### [USER] ... 패턴 매칭
        pattern = r"###\s*\[(\w+)\]\s*([\d\-]+\s+[\d:]+\s+\w+)\n([\s\S]*?)(?=###\s*\[|\Z)"
        matches = re.findall(pattern, body)

        for role, timestamp, content in matches:
            entries.append(
                {"role": role.lower(), "timestamp": timestamp, "content": content.strip()}
            )

        return entries

    def generate_extractive_summary(
        self, body: str, branch_topic: str, max_length: int = 20480
    ) -> str:
        """
        추출적 요약 생성 (Zero-Trust: 외부 API 없이 로컬에서 처리)

        전략:
        1. 대화 엔트리 파싱
        2. 핵심 정보 추출 (결정사항, 작업내용, 문제/해결)
        3. 최근 대화 요약
        4. 목표 크기에 맞게 압축

        Args:
            body: Context body
            branch_topic: 브랜치 주제
            max_length: 최대 바이트 크기

        Returns:
            생성된 요약
        """
        entries = self.parse_conversation_entries(body)
        if not entries:
            return f"브랜치 주제: {branch_topic}"

        summary_parts = []

        # 1. 브랜치 주제
        summary_parts.append(f"## 브랜치: {branch_topic}")

        # 2. 핵심 정보 추출
        key_info = self._extract_key_information(entries)
        if key_info:
            summary_parts.append("\n## 핵심 정보")
            summary_parts.append(key_info)

        # 3. 최근 대화 요약 (마지막 5개 엔트리)
        recent_entries = entries[-5:] if len(entries) > 5 else entries
        recent_summary = self._summarize_recent_entries(recent_entries)
        if recent_summary:
            summary_parts.append("\n## 최근 대화")
            summary_parts.append(recent_summary)

        # 4. 통계 정보
        summary_parts.append(f"\n## 통계")
        summary_parts.append(f"- 총 대화 수: {len(entries)}개")
        summary_parts.append(f"- 마지막 업데이트: {entries[-1]['timestamp'] if entries else 'N/A'}")

        full_summary = "\n".join(summary_parts)

        # 크기 제한 적용
        if len(full_summary.encode("utf-8")) > max_length:
            full_summary = self._truncate_to_size(full_summary, max_length)

        return full_summary

    def _extract_key_information(self, entries: List[Dict]) -> str:
        """
        대화에서 핵심 정보 추출

        키워드 기반:
        - 결정/완료: "결정", "완료", "해결", "수정"
        - 문제/이슈: "문제", "오류", "에러", "이슈", "버그"
        - 작업: "구현", "개발", "추가", "변경", "삭제"

        Args:
            entries: 대화 엔트리 리스트

        Returns:
            추출된 핵심 정보 (마크다운 형식)
        """
        key_patterns = {
            "결정/완료": ["결정", "완료", "해결", "수정", "fix", "done", "resolved"],
            "문제/이슈": ["문제", "오류", "에러", "이슈", "버그", "error", "bug", "issue"],
            "작업": [
                "구현",
                "개발",
                "추가",
                "변경",
                "삭제",
                "implement",
                "add",
                "update",
                "remove",
            ],
        }

        extracted = {category: [] for category in key_patterns}

        for entry in entries:
            content = entry.get("content", "").lower()

            for category, keywords in key_patterns.items():
                for keyword in keywords:
                    if keyword in content:
                        # 키워드가 포함된 문장 추출
                        sentences = self._extract_sentences_with_keyword(
                            entry.get("content", ""), keyword
                        )
                        for sentence in sentences[:2]:  # 카테고리당 최대 2개
                            if sentence and sentence not in extracted[category]:
                                extracted[category].append(sentence[:300])
                        break

        # 포맷팅
        result_parts = []
        for category, items in extracted.items():
            if items:
                result_parts.append(f"### {category}")
                for item in items[:3]:  # 카테고리당 최대 3개
                    result_parts.append(f"- {item}")

        return "\n".join(result_parts)

    def _extract_sentences_with_keyword(self, text: str, keyword: str) -> List[str]:
        """키워드가 포함된 문장 추출"""
        sentences = []
        # 문장 분리 (마침표, 줄바꿈 기준)
        for line in text.split("\n"):
            line = line.strip()
            if keyword.lower() in line.lower() and len(line) > 10:
                # 마크다운 헤더 제거
                clean_line = re.sub(r"^#+\s*", "", line)
                clean_line = re.sub(r"^\*+\s*", "", clean_line)
                clean_line = re.sub(r"^-\s*", "", clean_line)
                if clean_line:
                    sentences.append(clean_line)

        return sentences

    def _summarize_recent_entries(self, entries: List[Dict]) -> str:
        """최근 대화 엔트리 요약"""
        if not entries:
            return ""

        summary_parts = []
        for entry in entries:
            role = entry.get("role", "unknown").upper()
            content = entry.get("content", "")

            # 내용 압축 (첫 200자 또는 첫 3줄)
            lines = content.split("\n")
            compressed = []
            char_count = 0
            for line in lines[:5]:
                line = line.strip()
                if line and not line.startswith("#"):
                    compressed.append(line)
                    char_count += len(line)
                    if char_count > 200:
                        break

            if compressed:
                summary_parts.append(f"- [{role}] {' | '.join(compressed[:2])}")

        return "\n".join(summary_parts)

    def _truncate_to_size(self, text: str, max_bytes: int) -> str:
        """텍스트를 바이트 크기에 맞게 자르기"""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        # 바이트 단위로 자르고 디코딩
        truncated = encoded[:max_bytes]
        # UTF-8 바운더리에서 자르기
        while truncated:
            try:
                return truncated.decode("utf-8") + "\n\n[... 요약 크기 제한으로 일부 생략 ...]"
            except UnicodeDecodeError:
                truncated = truncated[:-1]

        return ""

    def get_active_summary(
        self, project_id: str, branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        현재 활성 브랜치의 요약 정보 반환

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID (없으면 최신 활성 브랜치)

        Returns:
            요약 정보
        """
        # 브랜치 경로 찾기
        if branch_id:
            branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        else:
            # 최신 활성 브랜치 찾기
            index = self.file_io.load_project_index(project_id)
            active_branches = [
                (k, v)
                for k, v in index.get("branches", {}).items()
                if v.get("status") == "active"
            ]
            if not active_branches:
                return {"success": False, "error": "활성 브랜치를 찾을 수 없습니다.", "summary": None}

            latest = max(active_branches, key=lambda x: x[1].get("created_at", ""))
            branch_dir = self.memory_dir / project_id / "contexts" / latest[0]

        if not branch_dir.exists():
            return {"success": False, "error": "브랜치를 찾을 수 없습니다.", "summary": None}

        # Context 파일 찾기 (첫 번째 .md 파일)
        md_files = list(branch_dir.glob("*.md"))
        if not md_files:
            return {"success": False, "error": "브랜치 파일을 찾을 수 없습니다.", "summary": None}

        frontmatter, body = self.file_io.parse_md_file(md_files[0])

        return {
            "success": True,
            "branch_id": frontmatter.get("branch_id"),
            "branch_topic": frontmatter.get("branch_topic"),
            "summary": frontmatter.get("summary", ""),
            "last_summarized": frontmatter.get("last_summarized"),
            "status": frontmatter.get("status"),
        }

    def update_summary(self, project_id: str, branch_id: str, new_summary: str) -> Dict[str, Any]:
        """
        브랜치 요약 갱신

        Args:
            project_id: 프로젝트 ID
            branch_id: 브랜치 ID
            new_summary: 새 요약 내용

        Returns:
            갱신 결과
        """
        branch_dir = self.memory_dir / project_id / "contexts" / branch_id
        if not branch_dir.exists():
            return {"success": False, "error": "브랜치를 찾을 수 없습니다."}

        # Context 파일 찾기
        md_files = list(branch_dir.glob("*.md"))
        if not md_files:
            return {"success": False, "error": "브랜치 파일을 찾을 수 없습니다."}

        branch_path = md_files[0]
        frontmatter, body = self.file_io.parse_md_file(branch_path)

        # 요약 갱신
        frontmatter["summary"] = new_summary
        frontmatter["last_summarized"] = datetime.now(timezone.utc).isoformat()

        # 파일 저장
        full_content = self.file_io.create_md_content(frontmatter, body)
        branch_path.write_text(full_content, encoding="utf-8")

        return {
            "success": True,
            "message": "요약 갱신 완료",
            "last_summarized": frontmatter["last_summarized"],
        }
