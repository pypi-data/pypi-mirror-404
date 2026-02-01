"""
Cortex MCP - Phase 9 Hallucination Detection Tools

Phase 9 할루시네이션 감지 시스템의 MCP 도구 인터페이스

핵심 도구:
1. verify_response - LLM 응답 전체 검증
2. extract_claims - Claim 추출
3. detect_contradictions - 자기 모순 감지
4. analyze_confidence - 확신도 분석
5. verify_code_references - 코드 참조 검증
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Phase 9 모듈 import (선택적)
try:
    from core.claim_extractor import ClaimExtractor
    from core.claim_verifier import ClaimVerifier
    from core.code_structure_analyzer import CodeStructureAnalyzer
    from core.contradiction_detector import ContradictionDetector
    from core.fuzzy_claim_analyzer import FuzzyClaimAnalyzer
    from core.grounding_scorer import GroundingScorer

    HALLUCINATION_DETECTION_AVAILABLE = True
except ImportError:
    HALLUCINATION_DETECTION_AVAILABLE = False
    ClaimExtractor = None
    ClaimVerifier = None
    FuzzyClaimAnalyzer = None
    ContradictionDetector = None
    GroundingScorer = None
    CodeStructureAnalyzer = None

logger = logging.getLogger(__name__)


# ============================================================
# Tool 1: verify_response - LLM 응답 전체 검증
# ============================================================


def verify_response(
    response_text: str, project_path: str, context_text: Optional[str] = None, project_id: Optional[str] = None
) -> Dict:
    """
    LLM 응답 전체에 대한 할루시네이션 검증

    Args:
        response_text: 검증할 LLM 응답 텍스트
        project_path: 프로젝트 루트 경로 (코드 구조 분석용)
        context_text: 참조 맥락 텍스트 (선택적)
        project_id: 프로젝트 ID (선택적, 없으면 project_path 기반 생성)

    Returns:
        종합 검증 결과
    """
    if not HALLUCINATION_DETECTION_AVAILABLE:
        return {
            "success": False,
            "error": "Phase 9 Hallucination Detection is not available",
            "available": False,
        }

    try:
        logger.info(
            f"[verify_response] Starting verification for response ({len(response_text)} chars)"
        )

        # project_id 생성 (없으면 project_path 기반)
        if not project_id:
            import hashlib
            project_id = hashlib.md5(project_path.encode()).hexdigest()[:12]

        # 1. Claim 추출
        extractor = ClaimExtractor()
        claims = extractor.extract_claims(response_text)
        logger.info(f"[verify_response] Extracted {len(claims)} claims")

        # 2. Claim 검증
        verifier = ClaimVerifier(project_id=project_id, project_path=project_path)
        verified_claims = []
        for claim in claims:
            verification = verifier.verify_claim(claim, context_text or response_text)
            verified_claims.append(
                {
                    "claim": {
                        "text": claim.text,
                        "type": claim.claim_type,
                        "confidence_level": claim.confidence_level,
                    },
                    "verification": verification,
                }
            )

        # 3. 모순 검사
        contradiction_detector = ContradictionDetector()
        contradictions = contradiction_detector.detect_contradictions(response_text)
        logger.info(
            f"[verify_response] Found {contradictions['contradictions_found']} contradictions"
        )

        # 4. 확신도 분석
        fuzzy_analyzer = FuzzyClaimAnalyzer()
        confidence_analysis = fuzzy_analyzer.analyze_response(response_text)
        logger.info(
            f"[verify_response] Average confidence: {confidence_analysis['average_confidence']:.3f}"
        )

        # 5. Grounding Score 계산
        grounding_scorer = GroundingScorer()
        evidences = [vc["verification"].get("evidence", {}) for vc in verified_claims]
        grounding_score = grounding_scorer.calculate_score(
            claims=claims, evidences=evidences, context_metadata={"project_path": project_path}
        )
        logger.info(f"[verify_response] Grounding score: {grounding_score['grounding_score']:.2f}")

        # 종합 평가
        overall_risk = _calculate_overall_risk(
            grounding_score=grounding_score["grounding_score"],
            contradictions=contradictions["contradictions_found"],
            average_confidence=confidence_analysis["average_confidence"],
        )

        result = {
            "success": True,
            "available": True,
            "total_claims": len(claims),
            "verified_claims": len(
                [vc for vc in verified_claims if vc["verification"].get("grounded", False)]
            ),
            "contradictions_found": contradictions["contradictions_found"],
            "average_confidence": round(confidence_analysis["average_confidence"], 3),
            "grounding_score": round(grounding_score["grounding_score"], 2),
            "overall_risk": overall_risk,
            "detailed_results": {
                "claims": verified_claims,
                "contradictions": contradictions,
                "confidence_analysis": confidence_analysis,
                "grounding_score": grounding_score,
            },
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[verify_response] Verification complete: risk={overall_risk}")
        return result

    except Exception as e:
        logger.error(f"[verify_response] Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "available": True}


# ============================================================
# Tool 2: extract_claims - Claim 추출
# ============================================================


def extract_claims(response_text: str) -> Dict:
    """
    LLM 응답에서 Claim 추출

    Args:
        response_text: 분석할 LLM 응답 텍스트

    Returns:
        추출된 Claim 목록
    """
    if not HALLUCINATION_DETECTION_AVAILABLE:
        return {
            "success": False,
            "error": "Phase 9 Hallucination Detection is not available",
            "available": False,
        }

    try:
        logger.info(
            f"[extract_claims] Extracting claims from response ({len(response_text)} chars)"
        )

        extractor = ClaimExtractor()
        claims = extractor.extract_claims(response_text)

        result = {
            "success": True,
            "available": True,
            "total_claims": len(claims),
            "claims": [
                {
                    "text": claim.text,
                    "type": claim.claim_type,
                    "confidence_level": claim.confidence_level,
                    "start": claim.start,
                    "end": claim.end,
                    "metadata": claim.metadata,
                }
                for claim in claims
            ],
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[extract_claims] Extracted {len(claims)} claims")
        return result

    except Exception as e:
        logger.error(f"[extract_claims] Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "available": True}


# ============================================================
# Tool 3: detect_contradictions - 자기 모순 감지
# ============================================================


def detect_contradictions(response_text: str) -> Dict:
    """
    LLM 응답에서 자기 모순 감지

    Args:
        response_text: 분석할 LLM 응답 텍스트

    Returns:
        모순 감지 결과
    """
    if not HALLUCINATION_DETECTION_AVAILABLE:
        return {
            "success": False,
            "error": "Phase 9 Hallucination Detection is not available",
            "available": False,
        }

    try:
        logger.info(f"[detect_contradictions] Analyzing response ({len(response_text)} chars)")

        detector = ContradictionDetector()
        result_data = detector.detect_contradictions(response_text)

        result = {
            "success": True,
            "available": True,
            "total_claims": result_data["total_claims"],
            "contradictions_found": result_data["contradictions_found"],
            "severity": result_data["severity"],
            "has_critical": result_data["has_critical_contradictions"],
            "contradictions": [
                {
                    "type": c["type"],
                    "severity": c["severity"],
                    "description": c["description"],
                    "claim1_text": (
                        c["claim1"].text if hasattr(c["claim1"], "text") else str(c["claim1"])
                    ),
                    "claim2_text": (
                        c["claim2"].text if hasattr(c["claim2"], "text") else str(c["claim2"])
                    ),
                    "evidence": c.get("evidence", ""),
                }
                for c in result_data["contradictions"]
            ],
            "interpretation": result_data["interpretation"],
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"[detect_contradictions] Found {result_data['contradictions_found']} contradictions (severity: {result_data['severity']})"
        )
        return result

    except Exception as e:
        logger.error(f"[detect_contradictions] Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "available": True}


# ============================================================
# Tool 4: analyze_confidence - 확신도 분석
# ============================================================


def analyze_confidence(response_text: str) -> Dict:
    """
    LLM 응답의 확신도 분석 (퍼지 로직 기반)

    Args:
        response_text: 분석할 LLM 응답 텍스트

    Returns:
        확신도 분석 결과
    """
    if not HALLUCINATION_DETECTION_AVAILABLE:
        return {
            "success": False,
            "error": "Phase 9 Hallucination Detection is not available",
            "available": False,
        }

    try:
        logger.info(f"[analyze_confidence] Analyzing confidence ({len(response_text)} chars)")

        analyzer = FuzzyClaimAnalyzer()
        result_data = analyzer.analyze_response(response_text)

        result = {
            "success": True,
            "available": True,
            "total_claims": result_data["total_claims"],
            "average_confidence": round(result_data["average_confidence"], 3),
            "vague_expression_count": result_data["vague_expression_count"],
            "risk_level": result_data["risk_level"],
            "interpretation": result_data["interpretation"],
            "claim_analyses": [
                {
                    "claim_text": (
                        ca["claim"].text if hasattr(ca["claim"], "text") else str(ca["claim"])
                    ),
                    "confidence_level": ca["confidence_level"],
                    "fuzzy_score": ca["fuzzy_score"],
                    "has_vague": ca["has_vague_expression"],
                }
                for ca in result_data["claim_analyses"]
            ],
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"[analyze_confidence] Average confidence: {result_data['average_confidence']:.3f}, risk: {result_data['risk_level']}"
        )
        return result

    except Exception as e:
        logger.error(f"[analyze_confidence] Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "available": True}


# ============================================================
# Tool 5: verify_code_references - 코드 참조 검증
# ============================================================


def verify_code_references(response_text: str, project_path: str) -> Dict:
    """
    LLM 응답에서 언급된 코드 참조 검증

    Args:
        response_text: 검증할 LLM 응답 텍스트
        project_path: 프로젝트 루트 경로

    Returns:
        코드 참조 검증 결과
    """
    if not HALLUCINATION_DETECTION_AVAILABLE:
        return {
            "success": False,
            "error": "Phase 9 Hallucination Detection is not available",
            "available": False,
        }

    try:
        logger.info(
            f"[verify_code_references] Verifying code references in project: {project_path}"
        )

        # 1. Claim 추출 (코드 참조 타입만)
        extractor = ClaimExtractor()
        all_claims = extractor.extract_claims(response_text)
        code_claims = [
            claim
            for claim in all_claims
            if claim.claim_type in ["reference_existing", "implementation_complete", "modification"]
        ]
        logger.info(f"[verify_code_references] Found {len(code_claims)} code-related claims")

        # 2. Code Structure Analyzer로 검증
        analyzer = CodeStructureAnalyzer(project_path=project_path)

        # 파일 참조 추출 및 검증
        file_paths = _extract_file_paths(response_text)
        file_verification = analyzer.verify_file_references(file_paths) if file_paths else None

        # 함수/클래스 참조 추출 및 검증
        function_refs = _extract_function_references(response_text)
        class_refs = _extract_class_references(response_text)

        result = {
            "success": True,
            "available": True,
            "code_claims": len(code_claims),
            "file_references": {
                "total": len(file_paths),
                "verified": file_verification["verified"] if file_verification else 0,
                "verification_rate": (
                    file_verification["verification_rate"] if file_verification else 0.0
                ),
                "results": file_verification["results"] if file_verification else [],
            },
            "function_references": {
                "total": sum(len(refs) for refs in function_refs.values()),
                "by_file": function_refs,
            },
            "class_references": {
                "total": sum(len(refs) for refs in class_refs.values()),
                "by_file": class_refs,
            },
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[verify_code_references] Verified {len(file_paths)} file references")
        return result

    except Exception as e:
        logger.error(f"[verify_code_references] Error: {e}", exc_info=True)
        return {"success": False, "error": str(e), "available": True}


# ============================================================
# Helper Functions
# ============================================================


def _calculate_overall_risk(
    grounding_score: float, contradictions: int, average_confidence: float
) -> str:
    """
    종합 할루시네이션 위험도 계산

    Args:
        grounding_score: Grounding Score (0-100)
        contradictions: 모순 개수
        average_confidence: 평균 확신도 (0.0-1.0)

    Returns:
        위험도 (low, medium, high, critical)
    """
    # Grounding Score 기반 기본 위험도
    if grounding_score >= 75:
        risk = "low"
    elif grounding_score >= 50:
        risk = "medium"
    elif grounding_score >= 25:
        risk = "high"
    else:
        risk = "critical"

    # 모순 개수로 위험도 상향
    if contradictions >= 3:
        if risk == "low":
            risk = "medium"
        elif risk == "medium":
            risk = "high"
        elif risk == "high":
            risk = "critical"
    elif contradictions >= 1:
        if risk == "low":
            risk = "medium"

    # 확신도로 위험도 조정
    if average_confidence < 0.3 and risk == "medium":
        risk = "high"
    elif average_confidence < 0.3 and risk == "low":
        risk = "medium"

    return risk


def _extract_file_paths(text: str) -> List[str]:
    """
    텍스트에서 파일 경로 추출

    Args:
        text: 분석할 텍스트

    Returns:
        추출된 파일 경로 목록
    """
    import re

    # 파일 경로 패턴 (확장자 포함)
    patterns = [
        r"[a-zA-Z_][a-zA-Z0-9_/\.]*\.(py|js|ts|tsx|jsx|java|cpp|c|h|go|rs)",
        r"`([^`]+\.(py|js|ts|tsx|jsx|java|cpp|c|h|go|rs))`",
        r'"([^"]+\.(py|js|ts|tsx|jsx|java|cpp|c|h|go|rs))"',
        r"'([^']+\.(py|js|ts|tsx|jsx|java|cpp|c|h|go|rs))'",
    ]

    paths = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                paths.append(match[0])
            else:
                paths.append(match)

    # 중복 제거 및 정렬
    return sorted(list(set(paths)))


def _extract_function_references(text: str) -> Dict[str, List[str]]:
    """
    텍스트에서 함수 참조 추출

    Args:
        text: 분석할 텍스트

    Returns:
        파일별 함수 목록
    """
    import re

    # 함수 참조 패턴 (파일:함수 형식)
    pattern = r"([a-zA-Z_][a-zA-Z0-9_/\.]*\.(py|js|ts)):([a-zA-Z_][a-zA-Z0-9_]*)"
    matches = re.findall(pattern, text)

    function_refs = {}
    for match in matches:
        file_path = match[0]
        function_name = match[2]
        if file_path not in function_refs:
            function_refs[file_path] = []
        if function_name not in function_refs[file_path]:
            function_refs[file_path].append(function_name)

    return function_refs


def _extract_class_references(text: str) -> Dict[str, List[str]]:
    """
    텍스트에서 클래스 참조 추출

    Args:
        text: 분석할 텍스트

    Returns:
        파일별 클래스 목록
    """
    import re

    # 클래스 참조 패턴 (대문자로 시작하는 이름)
    pattern = r"\b([A-Z][a-zA-Z0-9_]*)\b"
    matches = re.findall(pattern, text)

    # 일반적인 영어 단어 제외 (간단한 필터링)
    common_words = {
        "The",
        "This",
        "That",
        "These",
        "Those",
        "It",
        "Is",
        "Are",
        "Was",
        "Were",
        "Be",
        "Been",
        "Being",
    }
    class_names = [name for name in matches if name not in common_words and len(name) > 1]

    # 파일별로 그룹화하지 않고 전체 목록 반환
    return {"all": sorted(list(set(class_names)))}


# ============================================================
# MCP Tool Definitions
# ============================================================

PHASE9_TOOLS = [
    {
        "name": "verify_response",
        "description": "LLM 응답 전체에 대한 할루시네이션 검증 (Claim 추출, 검증, 모순 감지, 확신도 분석, Grounding Score 계산)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "response_text": {"type": "string", "description": "검증할 LLM 응답 텍스트"},
                "project_path": {
                    "type": "string",
                    "description": "프로젝트 루트 경로 (코드 구조 분석용)",
                },
                "context_text": {"type": "string", "description": "참조 맥락 텍스트 (선택적)"},
            },
            "required": ["response_text", "project_path"],
        },
    },
    {
        "name": "extract_claims",
        "description": "LLM 응답에서 Claim 추출 (6가지 타입: implementation_complete, extension, reference_existing, modification, verification, bug_fix)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "response_text": {"type": "string", "description": "분석할 LLM 응답 텍스트"}
            },
            "required": ["response_text"],
        },
    },
    {
        "name": "detect_contradictions",
        "description": "LLM 응답에서 자기 모순 감지 (직접 부정, 시간 순서, 비교, 타입 불일치)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "response_text": {"type": "string", "description": "분석할 LLM 응답 텍스트"}
            },
            "required": ["response_text"],
        },
    },
    {
        "name": "analyze_confidence",
        "description": "LLM 응답의 확신도 분석 (퍼지 로직 기반, 모호한 표현 감지)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "response_text": {"type": "string", "description": "분석할 LLM 응답 텍스트"}
            },
            "required": ["response_text"],
        },
    },
    {
        "name": "verify_code_references",
        "description": "LLM 응답에서 언급된 코드 참조 검증 (파일, 함수, 클래스 존재 여부)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "response_text": {"type": "string", "description": "검증할 LLM 응답 텍스트"},
                "project_path": {"type": "string", "description": "프로젝트 루트 경로"},
            },
            "required": ["response_text", "project_path"],
        },
    },
]
