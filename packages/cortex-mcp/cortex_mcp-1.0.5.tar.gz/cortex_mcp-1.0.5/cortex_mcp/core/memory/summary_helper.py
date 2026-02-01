"""
Cortex MCP - Summary Helper
요약 관련 헬퍼 메서드

기능:
- 대화 엔트리 파싱
- 추출적 요약 생성
- 핵심 정보 추출
- 요약 업데이트 조건 확인
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

# Hallucination Detection Thresholds
HALLUCINATION_THRESHOLDS = {
    "reject_below": 0.4,
    "warn_range": (0.4, 0.6),
    "accept_above": 0.6,
}


class SummaryHelper:
    """요약 생성 및 관리 헬퍼"""

    def __init__(self):
        pass

    def should_update_summary(self, frontmatter: Dict, body: str) -> bool:
        """
        요약 업데이트가 필요한지 판단

        조건:
        1. 아직 요약이 초기값인 경우
        2. 마지막 요약 후 새 엔트리가 5개 이상 추가된 경우
        3. 요약이 비어있는 경우
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
            return len(entries) >= 1

        # 새 엔트리가 5개 이상이면 요약 갱신
        new_entries_count = self.count_entries_after(entries, last_summarized)
        return new_entries_count >= 5

    def count_entries_after(self, entries: List[Dict], timestamp_str: str) -> int:
        """특정 시간 이후 추가된 엔트리 개수"""
        try:
            threshold = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return len(entries)

        count = 0
        for entry in entries:
            entry_time_str = entry.get("timestamp", "")
            try:
                entry_time = datetime.strptime(
                    entry_time_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                if entry_time > threshold:
                    count += 1
            except (ValueError, AttributeError):
                count += 1

        return count

    def parse_conversation_entries(self, body: str) -> List[Dict]:
        """
        대화 본문에서 개별 엔트리 파싱

        형식: ### [ROLE] TIMESTAMP
        """
        entries = []
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
        """
        entries = self.parse_conversation_entries(body)
        if not entries:
            return f"브랜치 주제: {branch_topic}"

        summary_parts = []

        # 1. 브랜치 주제
        summary_parts.append(f"## 브랜치: {branch_topic}")

        # 2. 핵심 정보 추출
        key_info = self.extract_key_information(entries)
        if key_info:
            summary_parts.append("\n## 핵심 정보")
            summary_parts.append(key_info)

        # 3. 최근 대화 요약 (마지막 5개 엔트리)
        recent_entries = entries[-5:] if len(entries) > 5 else entries
        recent_summary = self.summarize_recent_entries(recent_entries)
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
            full_summary = self.truncate_to_size(full_summary, max_length)

        return full_summary

    def extract_key_information(self, entries: List[Dict]) -> str:
        """
        대화에서 핵심 정보 추출

        키워드 기반:
        - 결정/결론: "결정", "완료", "해결", "수정"
        - 문제/이슈: "문제", "오류", "에러", "이슈", "버그"
        - 작업: "구현", "개발", "추가", "변경", "삭제"
        """
        key_patterns = {
            "결정/완료": ["결정", "완료", "해결", "수정", "fix", "done", "resolved"],
            "문제/이슈": ["문제", "오류", "에러", "이슈", "버그", "error", "bug", "issue"],
            "작업": [
                "구현", "개발", "추가", "변경", "삭제",
                "implement", "add", "update", "remove",
            ],
        }

        extracted = {category: [] for category in key_patterns}

        for entry in entries:
            content = entry.get("content", "").lower()

            for category, keywords in key_patterns.items():
                for keyword in keywords:
                    if keyword in content:
                        sentences = self.extract_sentences_with_keyword(
                            entry.get("content", ""), keyword
                        )
                        for sentence in sentences[:2]:
                            if sentence and sentence not in extracted[category]:
                                extracted[category].append(sentence[:300])
                        break

        # 포맷팅
        result_parts = []
        for category, items in extracted.items():
            if items:
                result_parts.append(f"### {category}")
                for item in items[:3]:
                    result_parts.append(f"- {item}")

        return "\n".join(result_parts)

    def extract_sentences_with_keyword(self, text: str, keyword: str) -> List[str]:
        """키워드가 포함된 문장 추출"""
        sentences = []
        for line in text.split("\n"):
            line = line.strip()
            if keyword.lower() in line.lower() and len(line) > 10:
                clean_line = re.sub(r"^#+\s*", "", line)
                clean_line = re.sub(r"^\*+\s*", "", clean_line)
                clean_line = re.sub(r"^-\s*", "", clean_line)
                if clean_line:
                    sentences.append(clean_line)

        return sentences

    def summarize_recent_entries(self, entries: List[Dict]) -> str:
        """최근 대화 엔트리 요약"""
        if not entries:
            return ""

        summary_parts = []
        for entry in entries:
            role = entry.get("role", "unknown").upper()
            content = entry.get("content", "")

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

    def truncate_to_size(self, text: str, max_bytes: int) -> str:
        """텍스트를 바이트 크기에 맞게 자르기"""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text

        truncated = encoded[:max_bytes]
        while truncated:
            try:
                return truncated.decode("utf-8") + "\n\n[... 요약 크기 제한으로 일부 생략 ...]"
            except UnicodeDecodeError:
                truncated = truncated[:-1]

        return ""


# 모듈 레벨 싱글톤 인스턴스
_summary_helper_instance = None


def get_summary_helper() -> SummaryHelper:
    """SummaryHelper 싱글톤 인스턴스 반환"""
    global _summary_helper_instance
    if _summary_helper_instance is None:
        _summary_helper_instance = SummaryHelper()
    return _summary_helper_instance
