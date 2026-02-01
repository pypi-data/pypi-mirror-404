"""
Claim 추출 시스템

Cortex Phase 9: Hallucination Detection System
LLM 응답에서 검증 가능한 주장(Claim)을 추출합니다.

핵심 기능:
- Regex + 룰 기반 Claim 추출 (경량, LLM 재호출 없음)
- 구현 완료, 확장, 기존 참조 등 주장 타입 분류
- 확신도 표현 감지 (퍼지 분석 연계)
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

# Phase 9.7: 중앙 상수 통일
from .hallucination_constants import CLAIM_TYPE_PRIORITY

# Research Logger import (Phase 9 integration - 논문 데이터 수집)
try:
    from .research_logger import log_event_sync, get_research_logger, EventType, ResearchEvent
    RESEARCH_LOGGER_AVAILABLE = True
except ImportError:
    RESEARCH_LOGGER_AVAILABLE = False
    log_event_sync = None
    get_research_logger = None
    EventType = None
    ResearchEvent = None


@dataclass
class Claim:
    """
    추출된 Claim 정보

    Attributes:
        claim_type: Claim 타입 (implementation_complete, extension, reference_existing 등)
        text: 추출된 텍스트
        start: 시작 위치
        end: 끝 위치
        confidence: 추출 신뢰도 (0.0-1.0)
        metadata: 추가 메타데이터
    """

    claim_type: str
    text: str
    start: int
    end: int
    confidence: float = 1.0
    metadata: Optional[Dict] = None


class ClaimExtractor:
    """
    Claim 추출 클래스

    LLM 응답에서 검증 가능한 주장을 regex + 룰 기반으로 추출합니다.
    외부 AI 호출 없이 경량으로 동작합니다.
    """

    # Claim 패턴 정의 (다국어 지원: 영어, 한국어, 스페인어, 프랑스어, 독일어, 일본어, 중국어)
    CLAIM_PATTERNS = {
        # 구현 완료 주장 (문장 전체 매칭 - 파일 참조 포함)
        "implementation_complete": [
            # Korean patterns (확장: 압축, 수정, 업데이트, 배포, 설치, 삭제, 변경 추가)
            r"([^\n]*?(구현|작성|생성|추가|개발|완성|제작|압축|수정|업데이트|배포|설치|삭제|변경|호출|실행).*?(완료|했습니다|되었습니다|끝났습니다|마쳤습니다)[^.\n]*?\.?)",
            r"([^\n]*?(코드|파일|함수|클래스|모듈|시스템).*?를?\s*(구현|작성|생성|추가|개발|압축|수정|업데이트).*?(완료|했습니다|되었습니다)[^.\n]*?\.?)",
            r"([^\n]*?(성공적으로|정상적으로)\s*(구현|작성|생성|추가|개발|완료|압축|수정|업데이트)[^.\n]*?\.?)",
            r"([^\n]*?(모든|전체)\s*(구현|작업|개발|압축|수정).*?(완료|끝)[^.\n]*?\.?)",
            # English patterns
            r"([^\n]*?(implement|creat|writ|generat|add|develop|finish|complet).*?(ed|done|finished|completed)[^.\n]*?\.?)",
            r"([^\n]*?(code|file|function|class|module|system).*?(implement|creat|writ|generat|add).*?(ed|done|completed)[^.\n]*?\.?)",
            r"([^\n]*?(successfully|properly)\s*(implement|creat|writ|generat|add|complet).*?(ed)?[^.\n]*?\.?)",
            r"([^\n]*?(all|entire|complete)\s*(implement|work|development).*?(done|finished|completed)[^.\n]*?\.?)",
            # Spanish patterns
            r"([^\n]*?(implement|cre|escrib|gener|añad|desarroll|termin|complet).*?(ado|ada|ó|aron)[^.\n]*?\.?)",
            r"([^\n]*?(exitosamente|correctamente)\s*(implement|cre|escrib|complet).*?(ado|ada)?[^.\n]*?\.?)",
            # French patterns
            r"([^\n]*?(implémen|cré|écri|génér|ajou|développ|termin|compl).*?(té|tée|és|ées)[^.\n]*?\.?)",
            r"([^\n]*?(avec succès|correctement)\s*(implémen|cré|compl).*?(té)?[^.\n]*?\.?)",
            # German patterns
            r"([^\n]*?(implementier|erstell|geschrieb|generier|hinzugefüg|entwickel|beend|abgeschloss).*?(t|en)[^.\n]*?\.?)",
            r"([^\n]*?(erfolgreich|korrekt)\s*(implementier|erstell|abgeschloss).*?(t)?[^.\n]*?\.?)",
            # Japanese patterns
            r"([^\n]*?(実装|作成|生成|追加|開発|完成|作製).*?(完了|しました|されました|終了)[^.\n]*?\.?)",
            r"([^\n]*?(成功的|正常)\s*(実装|作成|完了)[^.\n]*?\.?)",
            # Chinese patterns
            r"([^\n]*?(实现|实施|创建|生成|添加|开发|完成|制作).*?(完成|了|结束)[^.\n]*?\.?)",
            r"([^\n]*?(成功|正常)\s*(实现|创建|完成)[^.\n]*?\.?)",
        ],
        # 기존 코드 확장 주장
        "extension": [
            # Korean patterns
            r"(확장|반영|적용|통합|연동|병합).*?(했습니다|되었습니다|완료)",
            r"(기존|이전).*?(코드|로직|시스템).*?를?\s*(확장|개선|수정|업데이트)",
            r"(새로운|추가)\s*(기능|함수|메서드).*?를?\s*(기존|이전).*?(통합|연동|추가)",
            # English patterns
            r"(extend|reflect|apply|integrat|connect|merg).*?(ed|done|completed)",
            r"(existing|previous).*?(code|logic|system).*?(extend|improv|modif|updat).*?(ed)?",
            r"(new|additional)\s*(feature|function|method).*?(existing|previous).*?(integrat|connect|add).*?(ed)?",
        ],
        # 기존 참조 주장
        "reference_existing": [
            # Korean patterns
            r"(기존|이미|그대로|원래).*?(사용|유지|활용|참조|적용)",
            r"(이미|이전에)\s*(구현|작성|생성).*?(코드|함수|로직|시스템)",
            r"(기존|현재|원래)\s*(코드|구조|로직|시스템).*?를?\s*(그대로|계속|유지)",
            # English patterns
            r"(existing|already|as\s*is|original).*?(use|maintain|utiliz|refer|apply)",
            r"(already|previously)\s*(implement|writ|creat).*?(code|function|logic|system)",
            r"(existing|current|original)\s*(code|structure|logic|system).*?(as\s*is|continu|maintain)",
        ],
        # 파일/코드 수정 주장 (문장 전체 매칭 - 파일명 포함)
        "modification": [
            # Korean patterns (문장 전체 매칭)
            r"([^\n]*?(수정|변경|업데이트|개선).*?(했습니다|되었습니다|완료)[^.\n]*?\.?)",
            r"([^\n]*?(파일|코드|함수|클래스|변수).*?를?\s*(수정|변경|업데이트|개선)[^.\n]*?\.?)",
            r"([^\n]*?(라인|줄)\s*\d+.*?를?\s*(수정|변경|업데이트)[^.\n]*?\.?)",
            # English patterns (문장 전체 매칭)
            r"([^\n]*?(modif|chang|updat|improv).*?(ied|ed|done|completed)[^.\n]*?\.?)",
            r"([^\n]*?(file|code|function|class|variable).*?(modif|chang|updat|improv).*?(ied|ed)?[^.\n]*?\.?)",
            r"([^\n]*?(line)\s*\d+.*?(modif|chang|updat).*?(ied|ed)?[^.\n]*?\.?)",
        ],
        # 테스트/검증 주장
        "verification": [
            # Korean patterns
            r"(테스트|검증|확인).*?(완료|성공|통과|했습니다)",
            r"(정상|올바르게|성공적으로)\s*(작동|동작|실행|테스트)",
            r"(모든|전체)\s*(테스트|검증).*?(통과|성공)",
            # English patterns
            r"(test|verif|check).*?(ed|done|completed|success|passed)",
            r"(properly|correctly|successfully)\s*(work|run|execut|test).*?(ed|s)?",
            r"(all|entire)\s*(test|verification).*?(passed|success)",
        ],
        # 버그 수정 주장
        "bug_fix": [
            # Korean patterns
            r"(버그|오류|에러|문제).*?를?\s*(수정|해결|고치|fix)",
            r"(수정|해결|고치|fix).*?(버그|오류|에러|문제)",
            r"(정상|올바르게)\s*작동하도록\s*(수정|변경)",
            # English patterns
            r"(bug|error|issue|problem).*?(fix|resolv|correct).*?(ed)?",
            r"(fix|resolv|correct).*?(bug|error|issue|problem)",
            r"(properly|correctly)\s*work.*?(fix|modif|chang).*?(ed)?",
        ],
        # 성능 주장 (정보 제공용 - 검증 대상 아님)
        "performance_claim": [
            # Korean patterns
            r"(\d+x|(\d+)배)\s*(향상|개선|빠름|증가|속도)",
            r"(\d+(?:\.\d+)?)\s*(초|ms|밀리초|마이크로초|us)\s*(소요|걸림|단축|감소|절감)",
            r"(\d+(?:\.\d+)?%)\s*(절감|감소|향상|개선|증가|빠름)",
            r"(토큰|메모리|디스크|네트워크).*?(\d+(?:\.\d+)?%)\s*(절감|감소|향상)",
            # English patterns
            r"(\d+x|(\d+)\s*times)\s*(faster|improvement|increase|speedup|speed)",
            r"(\d+(?:\.\d+)?)\s*(second|ms|millisecond|microsecond|us)\s*(reduction|saved|faster|decreased)",
            r"(\d+(?:\.\d+)?%)\s*(reduction|decrease|improvement|increase|faster)",
            r"(token|memory|disk|network).*?(\d+(?:\.\d+)?%)\s*(reduction|saved|improvement)",
            # Spanish patterns
            r"(\d+x|(\d+)\s*veces)\s*(más rápido|mejora|aumento)",
            r"(\d+(?:\.\d+)?)\s*(segundo|ms|milisegundo)\s*(reducción|guardado)",
            r"(\d+(?:\.\d+)?%)\s*(reducción|disminución|mejora)",
            # French patterns
            r"(\d+x|(\d+)\s*fois)\s*(plus rapide|amélioration|augmentation)",
            r"(\d+(?:\.\d+)?)\s*(seconde|ms|milliseconde)\s*(réduction|économisé)",
            r"(\d+(?:\.\d+)?%)\s*(réduction|diminution|amélioration)",
            # German patterns
            r"(\d+x|(\d+)\s*mal)\s*(schneller|Verbesserung|Erhöhung)",
            r"(\d+(?:\.\d+)?)\s*(Sekunde|ms|Millisekunde)\s*(Reduzierung|gespart)",
            r"(\d+(?:\.\d+)?%)\s*(Reduzierung|Abnahme|Verbesserung)",
            # Japanese patterns
            r"(\d+倍)\s*(向上|改善|高速化)",
            r"(\d+(?:\.\d+)?)\s*(秒|ミリ秒)\s*(短縮|削減)",
            r"(\d+(?:\.\d+)?%)\s*(削減|減少|改善|向上)",
            # Chinese patterns
            r"(\d+倍)\s*(提升|改善|加速)",
            r"(\d+(?:\.\d+)?)\s*(秒|毫秒)\s*(缩短|减少)",
            r"(\d+(?:\.\d+)?%)\s*(减少|降低|改善|提升)",
        ],
    }

    # 확신도 표현 패턴 (퍼지 분석 연계용 - 다국어 지원)
    CONFIDENCE_EXPRESSIONS = {
        "very_high": [
            # Korean
            r"(반드시|확실히|분명히|명백히|틀림없이)",
            r"(100%|확실|완전)",
            r"(보장|약속|단언)",
            # English
            r"(definitely|certainly|clearly|obviously|undoubtedly)",
            r"(100%|sure|complete|absolute)",
            r"(guarantee|promise|assert)",
            # Spanish
            r"(definitivamente|ciertamente|claramente|obviamente)",
            r"(seguro|completo|absoluto)",
            # French
            r"(définitivement|certainement|clairement|évidemment)",
            r"(sûr|complet|absolu)",
            # German
            r"(definitiv|sicherlich|klar|offensichtlich|zweifellos)",
            r"(sicher|vollständig|absolut)",
            # Japanese
            r"(必ず|確実|明白|間違いなく)",
            r"(確実|完全)",
            # Chinese
            r"(必定|确定|明确|显然|毫无疑问)",
            r"(确定|完全|绝对)",
        ],
        "high": [
            # Korean
            r"(아마도|거의|대부분|높은\s*확률)",
            r"(일반적으로|보통|주로)",
            # English
            r"(likely|probable|almost|mostly|highly\s*likely)",
            r"(generally|usually|typically)",
            r"(high\s*probability|confident)",
            # Spanish
            r"(probablemente|casi|la mayoría)",
            r"(generalmente|usualmente)",
            # French
            r"(probablement|presque|la plupart)",
            r"(généralement|habituellement)",
            # German
            r"(wahrscheinlich|fast|meistens)",
            r"(im Allgemeinen|üblicherweise)",
            # Japanese
            r"(おそらく|ほとんど|大部分)",
            r"(一般的|通常)",
            # Chinese
            r"(可能|几乎|大部分)",
            r"(一般|通常)",
        ],
        "medium": [
            # Korean
            r"(가능성|추측|예상|생각)",
            r"(\~일\s*수\s*있|것으로\s*보임)",
            # English
            r"(maybe|perhaps|possibly|might|could)",
            r"(may\s*be|seems|appears|looks\s*like)",
            r"(potential|assume|expect)",
            # Spanish
            r"(quizás|tal vez|posiblemente|podría)",
            r"(puede ser|parece)",
            # French
            r"(peut-être|possiblement|pourrait)",
            r"(semble|paraît)",
            # German
            r"(vielleicht|möglicherweise|könnte)",
            r"(scheint|erscheint)",
            # Japanese
            r"(おそらく|もしかして|かもしれない)",
            r"(ように見える)",
            # Chinese
            r"(也许|可能|或许)",
            r"(似乎|看起来)",
        ],
        "low": [
            # Korean
            r"(아닐\s*수도|불확실|모호|확신\s*없)",
            r"(의심|회의적)",
            # English
            r"(unlikely|uncertain|unsure|doubtful)",
            r"(not\s*sure|unclear|ambiguous)",
            r"(skeptical|questionable)",
            # Spanish
            r"(poco probable|incierto|dudoso)",
            r"(no seguro|poco claro)",
            # French
            r"(peu probable|incertain|douteux)",
            r"(pas sûr|peu clair)",
            # German
            r"(unwahrscheinlich|unsicher|zweifelhaft)",
            r"(nicht sicher|unklar)",
            # Japanese
            r"(あり得ない|不確実|疑わしい)",
            r"(確信がない|不明確)",
            # Chinese
            r"(不太可能|不确定|可疑)",
            r"(不确定|不清楚)",
        ],
    }

    def __init__(self):
        """Claim Extractor 초기화"""
        # 패턴 컴파일 (성능 최적화)
        self._compiled_patterns = {}
        for claim_type, patterns in self.CLAIM_PATTERNS.items():
            self._compiled_patterns[claim_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        self._compiled_confidence = {}
        for confidence_level, patterns in self.CONFIDENCE_EXPRESSIONS.items():
            self._compiled_confidence[confidence_level] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

    def extract_claims(self, text: str) -> List[Claim]:
        """
        텍스트에서 Claim 추출

        BUG FIX (Phase 9.5): 패턴 우선순위 변경
        - 더 구체적인 패턴(bug_fix, modification)을 먼저 검사
        - 일반적인 패턴(implementation_complete)은 나중에 검사
        - 예: "버그를 수정했습니다" → bug_fix (O), implementation_complete (X)

        Args:
            text: LLM 응답 텍스트

        Returns:
            추출된 Claim 목록
        """
        claims = []

        # Phase 9.7: 중앙 상수 사용 (hallucination_constants.py)
        # bug_fix가 최우선 (더 구체적인 패턴이므로 먼저 검사)
        priority_order = CLAIM_TYPE_PRIORITY

        for claim_type in priority_order:
            compiled_patterns = self._compiled_patterns.get(claim_type, [])
            for pattern in compiled_patterns:
                matches = pattern.finditer(text)

                for match in matches:
                    # 중복 제거 (같은 위치의 Claim)
                    if self._is_duplicate_position(claims, match.start(), match.end()):
                        continue

                    # Claim 생성
                    claim = Claim(
                        claim_type=claim_type,
                        text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        confidence=1.0,  # 패턴 매칭 성공 시 기본값
                        metadata={
                            "pattern": pattern.pattern,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

                    # 확신도 표현 감지
                    confidence_level = self._detect_confidence_expression(
                        text, match.start(), match.end()
                    )
                    if confidence_level:
                        claim.metadata["confidence_expression"] = confidence_level

                    claims.append(claim)

        # 위치 순으로 정렬
        claims.sort(key=lambda c: c.start)

        # Research Logger Integration (Phase 9 - 논문 데이터 수집)
        if RESEARCH_LOGGER_AVAILABLE and log_event_sync and get_research_logger:
            try:
                logger = get_research_logger()
                if logger.enabled:
                    # Claim Extraction Event 생성 및 로깅
                    event = ResearchEvent(
                        event_id=logger._generate_event_id(),
                        event_type=EventType.CLAIM_EXTRACTION,
                        timestamp=datetime.now().isoformat(),
                        user_hash=logger.current_user_hash or "unknown",
                        session_id=logger.current_session_id or "unknown",
                        task_id=None,
                        context_state={
                            "text_length": len(text),
                            "claims_count": len(claims),
                        },
                        metrics={
                            "claims_extracted": len(claims),
                            "claim_types": list(set(c.claim_type for c in claims)),
                            "average_confidence": (
                                sum(c.confidence for c in claims) / len(claims) if claims else 0.0
                            ),
                            "extraction_success": len(claims) > 0,
                        },
                    )
                    log_event_sync(event)
            except Exception as log_err:
                # Silent failure: 로깅 실패해도 Claim 추출은 계속 진행
                pass

        return claims

    def extract_claims_by_type(self, text: str, claim_types: List[str]) -> List[Claim]:
        """
        특정 타입의 Claim만 추출

        Args:
            text: LLM 응답 텍스트
            claim_types: 추출할 Claim 타입 목록

        Returns:
            추출된 Claim 목록
        """
        all_claims = self.extract_claims(text)
        return [claim for claim in all_claims if claim.claim_type in claim_types]

    def get_implementation_claims(self, text: str) -> List[Claim]:
        """
        구현 완료 관련 Claim만 추출

        Args:
            text: LLM 응답 텍스트

        Returns:
            구현 완료 Claim 목록
        """
        return self.extract_claims_by_type(text, ["implementation_complete", "modification"])

    def get_reference_claims(self, text: str) -> List[Claim]:
        """
        기존 참조 관련 Claim만 추출

        Args:
            text: LLM 응답 텍스트

        Returns:
            기존 참조 Claim 목록
        """
        return self.extract_claims_by_type(text, ["reference_existing", "extension"])

    def _is_duplicate_position(self, claims: List[Claim], start: int, end: int) -> bool:
        """
        중복 위치 확인

        Args:
            claims: 기존 Claim 목록
            start: 새 Claim 시작 위치
            end: 새 Claim 끝 위치

        Returns:
            중복 여부
        """
        for claim in claims:
            # 50% 이상 겹치면 중복으로 판단
            overlap_start = max(claim.start, start)
            overlap_end = min(claim.end, end)
            overlap_length = max(0, overlap_end - overlap_start)

            claim_length = claim.end - claim.start
            new_length = end - start

            if overlap_length > 0:
                overlap_ratio = overlap_length / min(claim_length, new_length)
                if overlap_ratio > 0.5:
                    return True

        return False

    def _detect_confidence_expression(
        self, text: str, claim_start: int, claim_end: int
    ) -> Optional[str]:
        """
        Claim 주변의 확신도 표현 감지

        Args:
            text: 전체 텍스트
            claim_start: Claim 시작 위치
            claim_end: Claim 끝 위치

        Returns:
            확신도 레벨 (very_high, high, medium, low) 또는 None
        """
        # Claim 전후 50자 범위 검사
        context_start = max(0, claim_start - 50)
        context_end = min(len(text), claim_end + 50)
        context = text[context_start:context_end]

        for confidence_level, patterns in self._compiled_confidence.items():
            for pattern in patterns:
                if pattern.search(context):
                    return confidence_level

        return None

    def get_stats(self, claims: List[Claim]) -> Dict:
        """
        Claim 통계 반환

        Args:
            claims: Claim 목록

        Returns:
            통계 딕셔너리
        """
        stats = {"total_claims": len(claims), "by_type": {}, "confidence_distribution": {}}

        # 타입별 카운트
        for claim in claims:
            claim_type = claim.claim_type
            stats["by_type"][claim_type] = stats["by_type"].get(claim_type, 0) + 1

            # 확신도 표현 분포
            if claim.metadata and "confidence_expression" in claim.metadata:
                conf_expr = claim.metadata["confidence_expression"]
                stats["confidence_distribution"][conf_expr] = (
                    stats["confidence_distribution"].get(conf_expr, 0) + 1
                )

        return stats
