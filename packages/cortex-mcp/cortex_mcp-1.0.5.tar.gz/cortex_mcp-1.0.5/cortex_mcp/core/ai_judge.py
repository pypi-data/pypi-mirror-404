"""
AI 판단 인터페이스

Cortex MCP의 핵심 원칙:
- Cortex는 유저의 정보를 수집하지 않음
- 판단이 필요한 곳에서는 유저가 사용하는 AI를 활용

이 모듈은 유저의 AI(Claude, GPT 등)에게 판단을 요청하는 인터페이스를 제공합니다.
"""

import json
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class ClaimResult:
    """AI가 추출한 Claim 결과"""
    claim_type: str
    text: str
    confidence: float
    reasoning: str


@dataclass
class UncertaintyResult:
    """AI가 판단한 불확실성 결과"""
    confidence_level: str  # very_high, high, medium, low
    score: float  # 0.0 ~ 1.0
    reasoning: str
    is_factual: bool


class AIJudge:
    """
    유저의 AI를 활용한 판단 인터페이스

    MCP 프로토콜을 통해 유저의 AI에게 판단을 요청합니다.
    Cortex는 프롬프트만 전송하고 응답만 수신합니다.
    유저의 데이터는 수집하지 않습니다.
    """

    # Claim 타입 정의
    CLAIM_TYPES = [
        "implementation_complete",  # 구현/생성/추가 완료
        "modification",             # 수정/변경 완료
        "verification",             # 테스트/검증 완료
        "bug_fix",                  # 버그/오류 수정
        "existence_claim",          # 파일/함수 존재 주장
        "numeric_prediction",       # 수치 예측
        "reference_existing",       # 기존 코드 참조
        "extension",                # 기능 확장
    ]

    # 확신도 수준 정의
    CONFIDENCE_LEVELS = {
        "very_high": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.3,
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        AIJudge 초기화

        Args:
            cache_dir: 캐시 디렉토리 (기본: ~/.cortex/cache/ai_judgments)
        """
        if cache_dir is None:
            try:
                from cortex_mcp.config import get_cortex_path
                cache_dir = str(get_cortex_path("cache", "ai_judgments"))
            except ImportError:
                cache_dir = str(Path.home() / ".cortex" / "cache" / "ai_judgments")

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 메모리 캐시
        self._memory_cache: Dict[str, Any] = {}

        # 통계
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "ai_calls": 0,
        }

    def _get_cache_key(self, prompt_type: str, text: str) -> str:
        """캐시 키 생성"""
        content = f"{prompt_type}|||{text}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """캐시에서 결과 로드"""
        # 메모리 캐시 확인
        if cache_key in self._memory_cache:
            self._stats["cache_hits"] += 1
            return self._memory_cache[cache_key]

        # 디스크 캐시 확인
        cache_file = self._cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                self._memory_cache[cache_key] = result
                self._stats["cache_hits"] += 1
                return result
            except Exception as e:
                logger.debug(f"Cache load failed: {e}")

        return None

    def _save_to_cache(self, cache_key: str, result: Dict):
        """결과를 캐시에 저장"""
        self._memory_cache[cache_key] = result

        cache_file = self._cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"Cache save failed: {e}")

    def _build_claim_extraction_prompt(self, text: str) -> str:
        """Claim 추출용 프롬프트 생성"""
        return f"""다음 텍스트에서 검증 가능한 주장(Claim)을 추출해주세요.

## 추출 규칙

### 추출해야 하는 것 (확정된 과거형 주장):
- "구현했습니다", "완료했습니다", "수정했습니다"
- "테스트가 통과했습니다", "버그를 고쳤습니다"
- "파일을 생성했습니다", "함수를 추가했습니다"

### 제외해야 하는 것:
- 미래형: "할 예정입니다", "할 것입니다", "하겠습니다"
- 부정문: "안 했습니다", "하지 않았습니다"
- 조건문: "하면 될 것입니다", "할 수 있습니다"
- 추측: "것 같습니다", "아마도", "maybe"

## Claim 타입
- implementation_complete: 구현/생성/추가 완료
- modification: 수정/변경 완료
- verification: 테스트/검증 완료
- bug_fix: 버그/오류 수정
- existence_claim: 파일/함수 존재 주장
- numeric_prediction: 수치 예측 (예: "50% 절감")

## 응답 형식 (JSON)
```json
{{
  "claims": [
    {{
      "type": "claim_type",
      "text": "추출된 주장 원문",
      "confidence": 0.0-1.0,
      "reasoning": "왜 이것이 검증 가능한 주장인지"
    }}
  ],
  "excluded": [
    {{
      "text": "제외된 문장",
      "reason": "제외 이유 (미래형/부정문/조건문/추측)"
    }}
  ]
}}
```

## 분석할 텍스트
{text}

위 텍스트를 분석하고 JSON 형식으로만 응답해주세요."""

    def _build_uncertainty_detection_prompt(self, text: str) -> str:
        """불확실성 감지용 프롬프트 생성"""
        return f"""다음 텍스트의 확신도(confidence level)를 분석해주세요.

## 확신도 수준

### very_high (1.0) - 확실한 단정
- 표현: "확실히", "반드시", "100%", "definitely"
- 예: "이 코드는 확실히 작동합니다"

### high (0.8) - 높은 확신
- 표현: "거의", "대부분", "아마도", "likely"
- 예: "거의 완벽하게 구현되었습니다"

### medium (0.5) - 중간 확신
- 표현: "것 같다", "아마", "perhaps", "maybe"
- 예: "이렇게 하면 될 것 같습니다"

### low (0.3) - 낮은 확신
- 표현: "모르겠다", "확실하지 않다", "uncertain"
- 예: "잘 모르겠지만 시도해볼 수 있습니다"

## 사실 진술 vs 주장 구분

### 사실 진술 (검증 불필요)
- 테스트 결과: "[PASS]", "pytest output:"
- 측정값: "3.5초 소요", "95%"
- 로그 출력: "[INFO]", "[ERROR]"

### 주장 (검증 필요)
- 구현 완료 주장
- 버그 수정 주장
- 성능 개선 주장

## 응답 형식 (JSON)
```json
{{
  "confidence_level": "very_high|high|medium|low",
  "score": 0.0-1.0,
  "is_factual": true/false,
  "reasoning": "판단 근거",
  "uncertainty_indicators": ["발견된 불확실성 표현들"],
  "certainty_indicators": ["발견된 확신 표현들"]
}}
```

## 분석할 텍스트
{text}

위 텍스트를 분석하고 JSON 형식으로만 응답해주세요."""

    async def extract_claims(self, text: str, use_cache: bool = True) -> List[ClaimResult]:
        """
        AI를 활용한 Claim 추출

        Args:
            text: 분석할 텍스트
            use_cache: 캐시 사용 여부

        Returns:
            추출된 Claim 목록
        """
        self._stats["total_requests"] += 1

        # 캐시 확인
        if use_cache:
            cache_key = self._get_cache_key("claim_extraction", text)
            cached = self._load_from_cache(cache_key)
            if cached:
                return [ClaimResult(**c) for c in cached.get("claims", [])]

        # AI 호출용 프롬프트 생성
        prompt = self._build_claim_extraction_prompt(text)

        # AI 응답을 기다리는 구조 반환
        # 실제 AI 호출은 MCP 도구를 통해 수행됨
        self._stats["ai_calls"] += 1

        return {
            "prompt": prompt,
            "response_parser": self._parse_claim_response,
            "cache_key": cache_key if use_cache else None,
        }

    async def detect_uncertainty(self, text: str, use_cache: bool = True) -> UncertaintyResult:
        """
        AI를 활용한 불확실성 감지

        Args:
            text: 분석할 텍스트
            use_cache: 캐시 사용 여부

        Returns:
            불확실성 분석 결과
        """
        self._stats["total_requests"] += 1

        # 캐시 확인
        if use_cache:
            cache_key = self._get_cache_key("uncertainty_detection", text)
            cached = self._load_from_cache(cache_key)
            if cached:
                return UncertaintyResult(**cached)

        # AI 호출용 프롬프트 생성
        prompt = self._build_uncertainty_detection_prompt(text)

        self._stats["ai_calls"] += 1

        return {
            "prompt": prompt,
            "response_parser": self._parse_uncertainty_response,
            "cache_key": cache_key if use_cache else None,
        }

    def _parse_claim_response(self, ai_response: str) -> List[ClaimResult]:
        """AI 응답에서 Claim 결과 파싱"""
        try:
            # JSON 블록 추출
            json_str = ai_response
            if "```json" in ai_response:
                start = ai_response.find("```json") + 7
                end = ai_response.find("```", start)
                json_str = ai_response[start:end].strip()
            elif "```" in ai_response:
                start = ai_response.find("```") + 3
                end = ai_response.find("```", start)
                json_str = ai_response[start:end].strip()

            data = json.loads(json_str)
            claims = []

            for c in data.get("claims", []):
                claims.append(ClaimResult(
                    claim_type=c.get("type", "unknown"),
                    text=c.get("text", ""),
                    confidence=float(c.get("confidence", 0.5)),
                    reasoning=c.get("reasoning", ""),
                ))

            return claims

        except Exception as e:
            logger.error(f"Failed to parse claim response: {e}")
            return []

    def _parse_uncertainty_response(self, ai_response: str) -> UncertaintyResult:
        """AI 응답에서 불확실성 결과 파싱"""
        try:
            # JSON 블록 추출
            json_str = ai_response
            if "```json" in ai_response:
                start = ai_response.find("```json") + 7
                end = ai_response.find("```", start)
                json_str = ai_response[start:end].strip()
            elif "```" in ai_response:
                start = ai_response.find("```") + 3
                end = ai_response.find("```", start)
                json_str = ai_response[start:end].strip()

            data = json.loads(json_str)

            return UncertaintyResult(
                confidence_level=data.get("confidence_level", "medium"),
                score=float(data.get("score", 0.5)),
                reasoning=data.get("reasoning", ""),
                is_factual=data.get("is_factual", False),
            )

        except Exception as e:
            logger.error(f"Failed to parse uncertainty response: {e}")
            return UncertaintyResult(
                confidence_level="medium",
                score=0.5,
                reasoning=f"Parse error: {e}",
                is_factual=False,
            )

    def save_ai_response(self, cache_key: str, parsed_result: Any):
        """AI 응답 결과를 캐시에 저장"""
        if cache_key:
            if isinstance(parsed_result, list):
                # ClaimResult 리스트
                result = {"claims": [
                    {
                        "claim_type": c.claim_type,
                        "text": c.text,
                        "confidence": c.confidence,
                        "reasoning": c.reasoning,
                    } for c in parsed_result
                ]}
            elif isinstance(parsed_result, UncertaintyResult):
                result = {
                    "confidence_level": parsed_result.confidence_level,
                    "score": parsed_result.score,
                    "reasoning": parsed_result.reasoning,
                    "is_factual": parsed_result.is_factual,
                }
            else:
                result = parsed_result

            self._save_to_cache(cache_key, result)

    def get_stats(self) -> Dict:
        """통계 반환"""
        total = self._stats["total_requests"]
        return {
            **self._stats,
            "cache_hit_rate": round(
                self._stats["cache_hits"] / total, 3
            ) if total > 0 else 0.0,
        }


# 싱글톤 인스턴스
_ai_judge_instance: Optional[AIJudge] = None


def get_ai_judge() -> AIJudge:
    """AIJudge 싱글톤 인스턴스 반환"""
    global _ai_judge_instance
    if _ai_judge_instance is None:
        _ai_judge_instance = AIJudge()
    return _ai_judge_instance
