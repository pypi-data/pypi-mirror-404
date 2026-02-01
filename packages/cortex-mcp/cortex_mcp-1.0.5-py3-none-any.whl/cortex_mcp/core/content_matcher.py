"""
Content Matcher - Claim-Diff 의미적 매칭 시스템

Cortex Phase 9.6: Path Confusion Bug Fix (Option 2)
Claim의 주장 내용과 실제 파일 diff를 비교하여 경로 혼동을 감지합니다.

전문가 패널 설계:
- Fast Path: Keyword-based Jaccard similarity (80% cases, 0.1ms)
- Slow Path: Semantic-based cosine similarity (20% cases, 15ms)
- Model caching으로 첫 로딩 후 빠른 추론

핵심 알고리즘:
1. Claim에서 키워드 추출
2. Diff에서 해당 키워드 출현 빈도 계산
3. Jaccard >= 0.3 → Fast Pass
4. Jaccard < 0.3 → Semantic 검증
5. Semantic >= threshold → Pass
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from pathlib import Path

# Phase 9.7: 중앙 상수 통일
from .hallucination_constants import SIMILARITY_THRESHOLDS as CENTRAL_SIMILARITY_THRESHOLDS


@dataclass
class MatchResult:
    """
    매칭 결과

    Attributes:
        matched: 매칭 성공 여부
        score: 유사도 점수 (0.0 ~ 1.0)
        method: 사용된 방법 ("keyword" | "semantic")
        details: 추가 정보
    """
    matched: bool
    score: float
    method: str
    details: Optional[Dict] = None


class ContentMatcher:
    """
    Claim-Diff 내용 매칭 클래스

    전문가 패널 설계 원칙:
    - 단일 책임 원칙 (SRP)
    - 성능 최적화 (Fast Path 우선)
    - 점진적 정확도 향상 (Keyword → Semantic)
    """

    # Phase 9.7: 중앙 상수 참조 (hallucination_constants.py)
    SIMILARITY_THRESHOLDS = CENTRAL_SIMILARITY_THRESHOLDS

    # 코드 관련 불용어 (Python 전문가 제안)
    CODE_STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "should", "could", "may", "might", "must", "can",
        # 한국어 불용어
        "을", "를", "이", "가", "은", "는", "에", "에서", "으로", "로",
        "의", "와", "과", "도", "만", "까지", "부터", "했습니다", "되었습니다",
    }

    # 일반적인 코드 키워드 (Phase 9.11 - 할루시네이션 감지 개선)
    # 이 키워드들만 매칭되면 의미있는 매칭으로 보지 않음
    GENERIC_CODE_KEYWORDS = {
        # Python 기본 키워드
        "def", "class", "return", "self", "init", "none", "true", "false",
        "import", "from", "if", "else", "elif", "for", "while", "try",
        "except", "finally", "with", "pass", "break", "continue", "raise",
        "yield", "lambda", "assert", "global", "nonlocal", "async", "await",
        # 일반적인 타입/함수
        "str", "int", "float", "bool", "list", "dict", "tuple", "set",
        "print", "len", "range", "type", "isinstance",
        # 일반적인 코드 용어
        "function", "method", "variable", "parameter", "argument",
        "code", "file", "line", "error", "exception",
    }

    # 한-영 키워드 번역 사전 (Phase 9.6 - Path Confusion Bug Fix)
    KEYWORD_TRANSLATION = {
        # 버그/수정 관련
        "버그": ["bug", "error", "issue", "defect"],
        "수정": ["fix", "fixed", "repair", "correct", "修正"],
        "고침": ["fix", "fixed", "repair"],

        # 구현/추가 관련
        "구현": ["implement", "implementation", "add", "create"],
        "추가": ["add", "added", "append", "insert"],
        "생성": ["create", "created", "generate", "make"],

        # 기능 관련
        "기능": ["feature", "function", "functionality", "capability"],
        "함수": ["function", "method", "def"],

        # 수정/변경 관련
        "변경": ["change", "changed", "modify", "update"],
        "업데이트": ["update", "updated", "upgrade"],

        # 삭제 관련
        "삭제": ["delete", "deleted", "remove", "removed"],
        "제거": ["remove", "removed", "delete"],

        # 검증 관련
        "테스트": ["test", "tested", "testing"],
        "검증": ["verify", "verified", "validation", "check"],
    }

    def __init__(self):
        """Content Matcher 초기화"""
        self._model_cache = None
        self._model_load_attempted = False

    def match(
        self,
        claim_text: str,
        diff_content: str,
        claim_type: str = "default",
        force_semantic: bool = False
    ) -> MatchResult:
        """
        Claim과 Diff 내용 매칭

        전문가 패널 합의 알고리즘:
        1. Fast Path (keyword-based Jaccard)
        2. Slow Path (semantic-based cosine)

        Args:
            claim_text: Claim 텍스트
            diff_content: Diff 내용
            claim_type: Claim 타입 (임계값 결정용)
            force_semantic: True이면 Fast Path 건너뛰기

        Returns:
            MatchResult 객체
        """
        if not claim_text or not diff_content:
            return MatchResult(
                matched=False,
                score=0.0,
                method="none",
                details={"error": "empty_input"}
            )

        # 임계값 결정
        threshold = self.SIMILARITY_THRESHOLDS.get(claim_type, 0.30)

        # Fast Path: Keyword-based (80% cases)
        if not force_semantic:
            keyword_result = self._keyword_matching(claim_text, diff_content, threshold)
            print(f"[ContentMatcher] Keyword matching: score={keyword_result.score:.3f}, matched={keyword_result.matched}, threshold={threshold}")
            print(f"[ContentMatcher]   - claim keywords: {keyword_result.details.get('claim_keywords', [])[:5]}")
            print(f"[ContentMatcher]   - diff keywords: {keyword_result.details.get('diff_keywords', [])[:5]}")
            print(f"[ContentMatcher]   - intersection: {keyword_result.details.get('intersection', [])}")
            if keyword_result.matched or keyword_result.score >= 0.8:
                # 높은 키워드 매칭이면 즉시 반환
                return keyword_result

        # Slow Path: Semantic-based (20% cases)
        semantic_result = self._semantic_matching(claim_text, diff_content, threshold)
        print(f"[ContentMatcher] Semantic matching: score={semantic_result.score:.3f}, matched={semantic_result.matched}, threshold={threshold}")
        return semantic_result

    def _keyword_matching(self, claim_text: str, diff_content: str, threshold: float) -> MatchResult:
        """
        Fast Path: Keyword-based Jaccard similarity

        알고리즘 전문가 + 데이터 사이언티스트 설계:
        - Claim에서 핵심 키워드 추출
        - Diff에서 해당 키워드 출현 확인
        - Jaccard similarity = |교집합| / |합집합|

        성능: 0.1ms (매우 빠름)
        """
        claim_keywords = self._extract_keywords(claim_text)
        diff_keywords = self._extract_keywords(diff_content)

        if not claim_keywords or not diff_keywords:
            return MatchResult(
                matched=False,
                score=0.0,
                method="keyword",
                details={"reason": "no_keywords"}
            )

        # Jaccard similarity
        intersection = claim_keywords & diff_keywords
        union = claim_keywords | diff_keywords

        jaccard_score = len(intersection) / len(union) if union else 0.0

        # Phase 9.11: 의미있는 키워드만 매칭으로 인정 (할루시네이션 감지 개선)
        # 일반적인 코드 키워드(def, return 등)는 제외하고 의미있는 키워드만 확인
        meaningful_intersection = intersection - self.GENERIC_CODE_KEYWORDS
        has_meaningful_intersection = len(meaningful_intersection) >= 1

        # 의미있는 키워드로 Jaccard score 재계산
        meaningful_jaccard = (
            len(meaningful_intersection) / len(union)
            if union and meaningful_intersection else 0.0
        )

        meets_threshold = meaningful_jaccard >= threshold

        # Phase 9.11: 의미있는 키워드가 있어야 매칭 성공
        # 일반 코드 키워드만 매칭되면 실패 (예: 'def'만 매칭)
        matched = has_meaningful_intersection and (meets_threshold or meaningful_jaccard >= 0.1)

        return MatchResult(
            matched=matched,
            score=round(meaningful_jaccard, 3),
            method="keyword",
            details={
                "claim_keywords": list(claim_keywords),
                "diff_keywords": list(diff_keywords),
                "intersection": list(intersection),
                "meaningful_intersection": list(meaningful_intersection),
                "threshold": threshold,
                "has_meaningful_intersection": has_meaningful_intersection,
                "meets_threshold": meets_threshold,
            }
        )

    def _semantic_matching(self, claim_text: str, diff_content: str, threshold: float) -> MatchResult:
        """
        Slow Path: Semantic-based cosine similarity

        AI 전문가 + 데이터 사이언티스트 설계:
        - sentence-transformers 사용
        - 코사인 유사도 계산
        - Model caching으로 성능 최적화

        성능: 첫 로딩 2초, 이후 15ms
        """
        # Model 로딩 (Lazy loading + caching)
        if not self._load_model():
            # Model 로딩 실패 시 keyword 결과 반환
            return self._keyword_matching(claim_text, diff_content, threshold)

        try:
            from sentence_transformers import util

            # 임베딩 생성
            claim_emb = self._model_cache.encode(claim_text, convert_to_tensor=True)
            diff_emb = self._model_cache.encode(diff_content, convert_to_tensor=True)

            # 코사인 유사도 계산
            cosine_score = util.cos_sim(claim_emb, diff_emb).item()

            return MatchResult(
                matched=cosine_score >= threshold,
                score=round(cosine_score, 3),
                method="semantic",
                details={
                    "threshold": threshold,
                    "model": "all-MiniLM-L6-v2",
                }
            )
        except Exception as e:
            # Semantic 실패 시 keyword로 폴백
            print(f"Warning: Semantic matching failed: {e}")
            return self._keyword_matching(claim_text, diff_content, threshold)

    def _extract_keywords(self, text: str) -> Set[str]:
        """
        텍스트에서 키워드 추출

        Python 전문가 설계:
        - 소문자 변환
        - 영숫자 + 한글만 추출
        - 불용어 제거
        - 2글자 이상만 포함
        - 한-영 번역 확장 (Phase 9.6)

        Args:
            text: 입력 텍스트

        Returns:
            키워드 집합
        """
        # 소문자 변환
        text = text.lower()

        # 영숫자 + 한글만 추출 (특수문자 제거)
        words = re.findall(r'[a-z0-9가-힣]+', text)

        # 불용어 제거 + 2글자 이상만
        keywords = {
            word for word in words
            if len(word) >= 2 and word not in self.CODE_STOPWORDS
        }

        # 한-영 번역 확장 (Phase 9.6 - Path Confusion Bug Fix)
        # 한국어 키워드를 영어 동의어로 확장하여 매칭률 향상
        # 부분 문자열 매칭: "수정했습니다"에서 "수정" 찾기
        expanded_keywords = set(keywords)
        for korean_word, english_synonyms in self.KEYWORD_TRANSLATION.items():
            # 조사가 붙은 경우를 처리하기 위해 부분 문자열 매칭
            for keyword in keywords:
                if korean_word in keyword:  # "수정" in "수정했습니다" = True
                    expanded_keywords.update(english_synonyms)
                    break  # 이미 찾았으니 다음 korean_word로

        return expanded_keywords

    def _load_model(self) -> bool:
        """
        sentence-transformers 모델 로딩

        운영 전문가 설계:
        - Lazy loading (필요할 때만)
        - Caching (한 번만 로드)
        - 실패 시 graceful degradation

        Returns:
            성공 여부
        """
        if self._model_cache is not None:
            return True  # 이미 로드됨

        if self._model_load_attempted:
            return False  # 이전에 실패함

        self._model_load_attempted = True

        try:
            from sentence_transformers import SentenceTransformer

            # 모델 로딩 (첫 실행 시 다운로드 발생 가능)
            self._model_cache = SentenceTransformer('all-MiniLM-L6-v2')

            print("[ContentMatcher] sentence-transformers 모델 로딩 완료")
            return True
        except ImportError:
            print("[ContentMatcher] Warning: sentence-transformers not installed")
            print("[ContentMatcher] Falling back to keyword-only matching")
            return False
        except Exception as e:
            print(f"[ContentMatcher] Warning: Model loading failed: {e}")
            return False

    def warm_up(self):
        """
        모델 사전 로딩 (warm-up)

        운영 전문가 제안:
        - 프로세스 시작 시 미리 호출
        - 첫 요청 latency 감소
        """
        if self._load_model():
            # Dummy 추론으로 모델 활성화
            try:
                self._model_cache.encode("warm up", convert_to_tensor=True)
                print("[ContentMatcher] Warm-up completed")
            except:
                pass


# ========================================
# 전역 인스턴스 (싱글톤 패턴)
# ========================================

_global_matcher = None


def get_content_matcher() -> ContentMatcher:
    """
    전역 ContentMatcher 인스턴스 반환

    SW 개발 전문가 설계:
    - 싱글톤 패턴으로 모델 중복 로딩 방지
    - 메모리 효율성 향상
    """
    global _global_matcher
    if _global_matcher is None:
        _global_matcher = ContentMatcher()
    return _global_matcher
