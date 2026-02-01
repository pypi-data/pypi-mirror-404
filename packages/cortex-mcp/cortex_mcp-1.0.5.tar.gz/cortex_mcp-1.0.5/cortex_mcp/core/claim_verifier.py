"""
Claim-Evidence 검증 시스템

Cortex Phase 9: Hallucination Detection System
추출된 Claim에 대한 증거 존재 여부를 검증합니다.

핵심 기능:
- Claim과 Evidence Graph 매칭
- Git diff 기반 구현 완료 검증
- File 참조 기반 기존 코드 검증
- 검증 결과 상세 리포트 생성
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .bayesian_updater import BayesianUpdater
from .claim_extractor import Claim
from .content_matcher import get_content_matcher, MatchResult
from .evidence_graph import EvidenceGraph, get_evidence_graph
from .reference_history import ReferenceHistory

# Phase 9.7: 중앙 상수 통일
from .hallucination_constants import BAYESIAN_VERIFICATION_THRESHOLD

# Research Logger import (Phase 9 integration - 논문 데이터 수집)
try:
    from .research_logger import log_event_sync, get_research_logger, EventType, ResearchEvent
    RESEARCH_LOGGER_AVAILABLE = True
except ImportError:
    RESEARCH_LOGGER_AVAILABLE = False


class ClaimVerifier:
    """
    Claim 검증 클래스

    Evidence Graph와 Git diff를 활용하여
    LLM의 주장에 대한 증거를 검증합니다.

    Phase 1 통합: Bayesian Claim Confidence
    - 기존 confidence를 likelihood로 사용
    - Reference History 반영하여 posterior 계산
    - False Positive 감소
    """

    def __init__(
        self,
        project_id: str,
        project_path: str,
        reference_history: Optional[ReferenceHistory] = None,
    ):
        """
        Claim Verifier 초기화

        Args:
            project_id: 프로젝트 식별자
            project_path: 프로젝트 루트 경로
            reference_history: Reference History 시스템 (선택적)
        """
        self.project_id = project_id
        self.project_path = Path(project_path)
        # PERFORMANCE: 싱글톤 패턴 사용 (~80ms 절감)
        self.evidence_graph = get_evidence_graph(project_id, project_path=project_path)

        # Phase 1: Bayesian Updater 통합
        self.bayesian_updater = BayesianUpdater(
            project_id=project_id, reference_history=reference_history
        )

    def verify_claim(self, claim: Claim, context_history: Optional[Dict] = None) -> Dict:
        """
        단일 Claim 검증 (Phase 1: Bayesian Confidence 적용)

        Args:
            claim: 검증할 Claim
            context_history: Context 이력 정보 (선택적)

        Returns:
            검증 결과 딕셔너리
        """
        # DEBUG: verify_claim 진입 시 파라미터 확인
        print(f"[DEBUG-VERIFY_CLAIM] verify_claim 메서드 진입")
        print(f"[DEBUG-VERIFY_CLAIM]   - claim.claim_type: {claim.claim_type}")
        print(f"[DEBUG-VERIFY_CLAIM]   - context_history type: {type(context_history)}")
        print(f"[DEBUG-VERIFY_CLAIM]   - context_history is None: {context_history is None}")
        if context_history:
            print(f"[DEBUG-VERIFY_CLAIM]   - context_history keys: {context_history.keys()}")
            print(f"[DEBUG-VERIFY_CLAIM]   - 'files_modified' in context_history: {'files_modified' in context_history}")

        result = {
            "claim": claim,
            "verified": False,
            "reason": "no_evidence",
            "evidence": [],
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

        # Claim 타입별 검증
        if claim.claim_type == "implementation_complete":
            result = self._verify_implementation_claim(claim, context_history)
        elif claim.claim_type == "extension":
            result = self._verify_extension_claim(claim)
        elif claim.claim_type == "reference_existing":
            result = self._verify_reference_claim(claim)
        elif claim.claim_type == "modification":
            result = self._verify_modification_claim(claim, context_history)
        elif claim.claim_type == "verification":
            result = self._verify_verification_claim(claim, context_history)
        elif claim.claim_type == "bug_fix":
            result = self._verify_bugfix_claim(claim, context_history)

        # Phase 1: Bayesian Posterior 계산
        # 기존 confidence를 likelihood로, evidence를 evidence_list로 변환
        evidence_list = self._convert_evidence_to_bayesian_format(result["evidence"])
        print(f"[DEBUG] Bayesian Evidence List: {evidence_list}")

        bayesian_result = self.bayesian_updater.update_posterior(
            claim=claim, evidence_list=evidence_list, context_history=context_history
        )

        print(f"[DEBUG] Bayesian Calculation:")
        print(f"  - Prior: {bayesian_result.prior} (source: {bayesian_result.prior_source})")
        print(f"  - Likelihood: {bayesian_result.likelihood}")
        print(f"  - Posterior: {bayesian_result.posterior}")
        print(f"  - Verified: {bayesian_result.posterior >= BAYESIAN_VERIFICATION_THRESHOLD}")  # Phase 9.7: 중앙 상수 사용

        # Posterior를 최종 confidence로 사용
        result["confidence"] = bayesian_result.posterior
        result["verified"] = bayesian_result.posterior >= BAYESIAN_VERIFICATION_THRESHOLD  # Phase 9.7: 중앙 상수 (0.6)

        # Bayesian 계산 과정 추가 (디버깅/연구용)
        result["bayesian_analysis"] = {
            "prior": bayesian_result.prior,
            "prior_source": bayesian_result.prior_source,
            "likelihood": bayesian_result.likelihood,
            "posterior": bayesian_result.posterior,
            "confidence_level": bayesian_result.confidence_level,
        }

        return result

    def _convert_evidence_to_bayesian_format(self, evidence: List[Dict]) -> List[Dict]:
        """
        ClaimVerifier의 evidence를 BayesianUpdater 형식으로 변환

        Args:
            evidence: ClaimVerifier evidence 목록

        Returns:
            BayesianUpdater 형식의 evidence 목록
        """
        bayesian_evidence = []

        for ev in evidence:
            ev_type = ev.get("type", "indirect_reference")
            weight = ev.get("weight", 0.5)

            # Evidence 타입 매핑
            if ev_type == "git_diff" or ev_type == "file_specific_diff":
                bayesian_type = "git_diff"
            elif ev_type == "codebase_verified":
                # 코드베이스 완전 스캔 = 매우 강력한 증거
                bayesian_type = "code_content"
            elif ev_type == "evidence_graph_diff" or ev_type == "modified_files" or ev_type == "evidence_graph_files":
                bayesian_type = "file_exists"
            elif ev_type == "context_match":
                bayesian_type = "context_match"
            else:
                bayesian_type = "indirect_reference"

            bayesian_evidence.append(
                {"type": bayesian_type, "quality_score": weight, "original_evidence": ev}
            )

        return bayesian_evidence

    def verify_claims(self, claims: List[Claim]) -> List[Dict]:
        """
        여러 Claim 일괄 검증

        Args:
            claims: 검증할 Claim 목록

        Returns:
            검증 결과 목록
        """
        results = [self.verify_claim(claim) for claim in claims]

        # Research Logger integration (Phase 9 - 논문 데이터 수집)
        if RESEARCH_LOGGER_AVAILABLE and log_event_sync and get_research_logger:
            try:
                res_logger = get_research_logger()
                if res_logger.enabled:
                    # 통계 계산
                    total_claims = len(results)
                    verified_count = sum(1 for r in results if r.get("verified", False))
                    evidence_count = sum(len(r.get("evidence", [])) for r in results)

                    claim_types = {}
                    for r in results:
                        claim = r.get("claim")
                        claim_type = claim.claim_type if hasattr(claim, "claim_type") else "unknown"
                        if claim_type not in claim_types:
                            claim_types[claim_type] = {"total": 0, "verified": 0}
                        claim_types[claim_type]["total"] += 1
                        if r.get("verified", False):
                            claim_types[claim_type]["verified"] += 1

                    event = ResearchEvent(
                        event_id=res_logger._generate_event_id(),
                        event_type=EventType.CLAIM_VERIFICATION,
                        timestamp=datetime.now().isoformat(),
                        user_hash=res_logger.current_user_hash or "unknown",
                        session_id=res_logger.current_session_id or "unknown",
                        task_id=None,
                        context_state={
                            "project_id": self.project_id,
                            "total_claims": total_claims,
                        },
                        metrics={
                            "verification_success_rate": (
                                verified_count / total_claims if total_claims > 0 else 0.0
                            ),
                            "verified_count": verified_count,
                            "evidence_count": evidence_count,
                            "claim_types": claim_types,
                        },
                    )
                    log_event_sync(event)
            except Exception as log_err:
                pass  # Silent failure

        return results

    def _verify_implementation_claim(self, claim: Claim, context_history: Optional[Dict] = None) -> Dict:
        """
        구현 완료 Claim 검증

        최소 조건:
        1. Claim에서 파일 참조 추출
        2. 해당 파일들이 Evidence Graph에 Diff 노드를 가지고 있는지 확인
        3. 파일별 검증 통과 비율 계산

        Args:
            claim: 검증할 Claim
            context_history: Context 이력 정보 (files_modified 포함)

        Returns:
            검증 결과
        """
        evidence = []
        confidence = 0.0

        # Claim에서 파일 참조 추출
        referenced_files = self._extract_file_references(claim.text)

        if not referenced_files:
            # 파일 참조가 없으면 전체 Git diff 확인 (기존 로직)
            has_git_diff = self._check_git_diff()
            if has_git_diff:
                evidence.append(
                    {
                        "type": "git_diff",
                        "description": "Git diff 확인됨 (파일 참조 없음)",
                        "weight": 0.9,  # Phase 9.5 개선: 0.7 → 0.9 (직접 증거, 95% 신뢰도)
                    }
                )
                confidence += 0.5

            # 보조 증거는 파일 참조가 없을 때만 사용
            # Evidence Graph에서 전체 Diff 노드 확인
            diff_nodes = self._find_diff_nodes_in_graph()
            if diff_nodes:
                evidence.append(
                    {
                        "type": "evidence_graph_diff",
                        "description": f"{len(diff_nodes)}개의 Diff 노드 발견 (전체)",
                        "nodes": diff_nodes,
                        "weight": 0.8,  # Phase 9.5 개선: 0.2 → 0.8 (구조적 증거, 85% 신뢰도)
                    }
                )
                confidence += 0.2

            # Evidence Graph에서 File 노드 확인 (ContentMatcher로 의미적 필터링)
            # 전문가 패널 합의: 파일 존재만 확인하지 말고, Claim과 Diff의 의미적 유사도 검증
            # MEDIUM #2: context_history 처리 통일

            # 파일 목록 결정 (우선순위: context_history > Evidence Graph)
            file_nodes = []
            context_source = None  # 파일 출처 추적

            # 1. context_history에서 files_modified 확인 (우선순위 1)
            if context_history and isinstance(context_history, dict) and "files_modified" in context_history:
                files_modified = context_history["files_modified"]
                if files_modified and isinstance(files_modified, dict):
                    file_nodes = list(files_modified.keys())
                    context_source = "context_history"

            # 2. context_history에 없으면 Evidence Graph 사용 (fallback)
            if not file_nodes:
                file_nodes = self._find_file_nodes_in_graph()
                context_source = "evidence_graph"

            # DEBUG: 파일 출처 및 목록 출력
            print(f"[DEBUG] File source: {context_source}")
            print(f"[DEBUG] File count: {len(file_nodes)}")
            if file_nodes and len(file_nodes) <= 5:
                print(f"[DEBUG] File nodes: {file_nodes}")

            matched_files = []

            if file_nodes:
                # ContentMatcher로 각 파일의 diff와 claim을 의미적으로 매칭
                matcher = get_content_matcher()

                for file_path in file_nodes:
                    # 파일의 diff content 가져오기 (context 우선 확인)
                    diff_content = self._get_file_diff_content(file_path, context_history)
                    if not diff_content:
                        continue

                    # Claim text와 diff content 의미적 매칭
                    match_result = matcher.match(
                        claim_text=claim.text,
                        diff_content=diff_content,
                        claim_type=claim.claim_type
                    )

                    if match_result.matched:
                        matched_files.append(file_path)

                # 매칭된 파일에 대한 evidence 생성
                if matched_files:
                    if len(matched_files) >= 3:
                        # 3개 이상 매칭 = 강한 증거 (Grounded 응답)
                        evidence.append(
                            {
                                "type": "content_matched_files",
                                "description": f"{len(matched_files)}개 파일이 내용 매칭 성공",
                                "files": matched_files[:10],
                                "total_count": len(matched_files),
                                "weight": 0.9,
                            }
                        )
                        confidence += 0.9
                    else:
                        # 1-2개 매칭 = 중간 증거
                        evidence.append(
                            {
                                "type": "content_matched_files",
                                "description": f"{len(matched_files)}개 파일이 내용 매칭 성공",
                                "files": matched_files,
                                "total_count": len(matched_files),
                                "weight": 0.7,
                            }
                        )
                        confidence += 0.7
                else:
                    # 매칭 실패 = 할루시네이션 가능성 높음
                    evidence.append(
                        {
                            "type": "no_content_match",
                            "description": f"{len(file_nodes)}개 파일 확인했으나 내용 매칭 실패",
                            "total_count": len(file_nodes),
                            "weight": 0.0,
                        }
                    )
                    confidence += 0.0

            # File 변경 노드 확인
            modified_files = self._find_modified_files_in_graph()
            if modified_files:
                evidence.append(
                    {
                        "type": "modified_files",
                        "description": f"{len(modified_files)}개의 파일 변경 확인",
                        "files": modified_files,
                        "weight": 0.1,
                    }
                )
                confidence += 0.1
        else:
            # 파일 참조가 있으면 파일별로 Diff 노드 확인
            print(f"[DEBUG] ClaimVerifier: 파일 참조 추출 결과: {referenced_files}")
            verified_files = []
            for file_path in referenced_files:
                # Evidence Graph에서 해당 파일의 Diff 노드 확인
                has_diff = self._has_file_diff(file_path, claim=claim)
                print(f"[DEBUG] ClaimVerifier: _has_file_diff('{file_path}') = {has_diff}")
                if has_diff:
                    verified_files.append(file_path)

            print(f"[DEBUG] ClaimVerifier: 검증된 파일: {verified_files}")

            if verified_files:
                verification_rate = len(verified_files) / len(referenced_files)
                evidence.append(
                    {
                        "type": "file_specific_diff",
                        "description": f"{len(verified_files)}/{len(referenced_files)} 파일 Diff 확인",
                        "verified_files": verified_files,
                        "all_referenced": referenced_files,
                        "weight": verification_rate * 0.7,
                    }
                )
                confidence += verification_rate * 0.7
            else:
                # 파일 참조가 있지만 하나도 검증되지 않음 → 실패
                evidence.append(
                    {
                        "type": "file_specific_diff",
                        "description": f"0/{len(referenced_files)} 파일 Diff 확인 (모두 미검증)",
                        "verified_files": [],
                        "all_referenced": referenced_files,
                        "weight": 0.0,
                    }
                )
                # confidence는 그대로 0.0 유지 (보조 증거 사용하지 않음)

        verified = confidence >= 0.5  # 50% 이상이면 검증 통과

        return {
            "claim": claim,
            "verified": verified,
            "reason": "sufficient_evidence" if verified else "insufficient_evidence",
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _verify_extension_claim(self, claim: Claim) -> Dict:
        """
        기존 코드 확장 Claim 검증

        최소 조건:
        1. 기존 파일 참조 확인
        2. 해당 파일에 변경 발생
        3. Evidence Graph에서 연결 확인

        Args:
            claim: 검증할 Claim

        Returns:
            검증 결과
        """
        evidence = []
        confidence = 0.0

        # 기존 파일 참조 확인
        referenced_files = self._extract_file_references(claim.text)
        if referenced_files:
            # Evidence Graph에서 File 노드 확인
            existing_files = self._check_files_in_graph(referenced_files)
            if existing_files:
                evidence.append(
                    {
                        "type": "existing_files",
                        "description": f"{len(existing_files)}개의 기존 파일 확인",
                        "files": existing_files,
                        "weight": 0.4,
                    }
                )
                confidence += 0.4

            # 해당 파일의 변경 확인
            modified = self._check_files_modified(referenced_files)
            if modified:
                evidence.append(
                    {
                        "type": "file_modifications",
                        "description": "기존 파일 변경 확인",
                        "files": modified,
                        "weight": 0.4,
                    }
                )
                confidence += 0.4

        # Git diff로 확장 패턴 확인
        has_additions = self._check_git_additions()
        if has_additions:
            evidence.append(
                {"type": "code_additions", "description": "코드 추가 확인", "weight": 0.2}
            )
            confidence += 0.2

        verified = confidence >= 0.5

        return {
            "claim": claim,
            "verified": verified,
            "reason": "sufficient_evidence" if verified else "insufficient_evidence",
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _verify_reference_claim(self, claim: Claim) -> Dict:
        """
        기존 참조 Claim 검증

        최소 조건:
        1. 참조된 파일/함수가 Evidence Graph에 존재
        2. Context에서 해당 파일 참조 이력 확인

        Args:
            claim: 검증할 Claim

        Returns:
            검증 결과
        """
        evidence = []
        confidence = 0.0

        # 파일 참조 추출
        referenced_files = self._extract_file_references(claim.text)
        if referenced_files:
            # Evidence Graph에서 존재 확인
            existing_files = self._check_files_in_graph(referenced_files)
            if existing_files:
                evidence.append(
                    {
                        "type": "referenced_files_exist",
                        "description": f"{len(existing_files)}개의 참조 파일 확인",
                        "files": existing_files,
                        "weight": 0.6,
                    }
                )
                confidence += 0.6

            # Context 연결 확인
            context_links = self._check_context_file_links(referenced_files)
            if context_links:
                evidence.append(
                    {
                        "type": "context_references",
                        "description": "Context에서 파일 참조 확인",
                        "links": context_links,
                        "weight": 0.4,
                    }
                )
                confidence += 0.4

        verified = confidence >= 0.5

        return {
            "claim": claim,
            "verified": verified,
            "reason": "sufficient_evidence" if verified else "insufficient_evidence",
            "evidence": evidence,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }

    def _verify_modification_claim(self, claim: Claim, context_history: Optional[Dict] = None) -> Dict:
        """
        수정 Claim 검증

        Args:
            claim: 검증할 Claim
            context_history: Context 이력 정보 (선택적)

        Returns:
            검증 결과
        """
        # 구현 완료와 유사한 검증
        return self._verify_implementation_claim(claim, context_history)

    def _verify_verification_claim(self, claim: Claim, context_history: Optional[Dict] = None) -> Dict:
        """
        테스트/검증 Claim 검증

        파일 참조가 있으면 implementation_complete와 동일한 로직 사용
        (예: "test.py 테스트 통과" → test.py 파일 검증)

        FIX: pytest 출력 인식 추가

        Args:
            claim: 검증할 Claim
            context_history: Context 이력 정보 (선택적)

        Returns:
            검증 결과
        """
        import re

        # pytest 출력 패턴 검사
        if context_history and "file_contents" in context_history:
            file_contents = context_history["file_contents"]

            # 모든 파일 내용에서 pytest 출력 찾기
            for file_path, content in file_contents.items():
                if not isinstance(content, str):
                    continue

                # pytest 통과 패턴: "X passed"
                passed_match = re.search(r'(\d+)\s+passed', content)
                if passed_match:
                    passed_count = int(passed_match.group(1))

                    # Claim 텍스트에서 테스트 개수 추출
                    claim_match = re.search(r'(\d+)', claim.text)
                    if claim_match:
                        claimed_count = int(claim_match.group(1))

                        if passed_count >= claimed_count:
                            return {
                                "claim": claim,
                                "verified": True,
                                "reason": "pytest_output_confirmed",
                                "evidence": [{
                                    "type": "test_output",
                                    "source": file_path,
                                    "passed_count": passed_count,
                                    "weight": 1.0
                                }],
                                "confidence": 1.0,
                                "timestamp": datetime.now().isoformat(),
                            }

        # 파일 참조가 있으면 구현 완료 검증과 동일한 로직 사용
        return self._verify_implementation_claim(claim, context_history)

    def _verify_bugfix_claim(self, claim: Claim, context_history: Optional[Dict] = None) -> Dict:
        """
        버그 수정 Claim 검증

        Args:
            claim: 검증할 Claim
            context_history: Context 이력 정보 (선택적)

        Returns:
            검증 결과
        """
        # 구현 완료와 유사한 검증
        return self._verify_implementation_claim(claim, context_history)

    # ========================================
    # Helper Methods
    # ========================================

    def _check_git_diff(self) -> bool:
        """
        Git diff 존재 여부 확인

        Returns:
            Git diff 존재 여부
        """
        # 우선 Evidence Graph에서 Diff 노드 확인 (테스트 환경 대응)
        diff_nodes = self._find_diff_nodes_in_graph()
        if diff_nodes:
            return True

        # Fallback: 실제 Git diff 확인
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return bool(result.stdout.strip())
        except Exception as e:
            print(f"Warning: Git diff check failed: {e}")
            return False

    def _check_git_additions(self) -> bool:
        """
        Git diff에서 코드 추가 확인

        Returns:
            코드 추가 존재 여부
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            # '+' 로 시작하는 라인이 있으면 추가로 간주
            return any(
                line.startswith("+") and not line.startswith("+++")
                for line in result.stdout.split("\n")
            )
        except Exception as e:
            print(f"Warning: Git additions check failed: {e}")
            return False

    def _find_diff_nodes_in_graph(self) -> List[Dict]:
        """
        Evidence Graph에서 Diff 노드 찾기

        Returns:
            Diff 노드 목록
        """
        diff_nodes = []
        for node_id, node_data in self.evidence_graph.graph.nodes(data=True):
            if node_data.get("type") == "Diff":
                diff_nodes.append(
                    {
                        "id": node_id,
                        "commit_hash": node_data.get("commit_hash"),
                        "file_path": node_data.get("file_path"),
                    }
                )
        return diff_nodes

    def _find_file_nodes_in_graph(self) -> List[str]:
        """
        Evidence Graph에서 File 노드 찾기

        Returns:
            File 노드 경로 목록
        """
        file_nodes = []
        for node_id, node_data in self.evidence_graph.graph.nodes(data=True):
            if node_data.get("type") == "File":
                file_nodes.append(node_id)
        return file_nodes

    def _get_file_diff_content(self, file_path: str, context_history: Optional[Dict] = None) -> Optional[str]:
        """
        파일의 Diff 내용 추출 (Phase 9.6 - Context 우선)

        전문가 패널 설계 (Git 전문가 + MCP 전문가):
        1. Context parameter 우선 확인 (테스트/실제 호출에서 전달된 diff)
        2. Evidence Graph 확인 (파싱된 데이터, 빠름)
        3. Git diff 폴백 (subprocess 오버헤드, 느림)

        Args:
            file_path: 파일 경로
            context_history: Context 이력 정보 (files_modified 포함)

        Returns:
            Diff 내용 (없으면 None)
        """
        # Priority 1: Context parameter에서 diff 확인 (테스트 케이스용)
        if context_history:
            files_modified = context_history.get("files_modified", {})
            if file_path in files_modified:
                diff = files_modified[file_path].get("diff", "")
                if diff:
                    print(f"[HALLUCINATION_LOG] Diff found in context for '{file_path}'")
                    return diff

        # Priority 2: Evidence Graph에서 Diff 노드 찾기
        for node_id, node_data in self.evidence_graph.graph.nodes(data=True):
            if node_data.get("type") == "Diff":
                evidence_file = node_data.get("file_path", "")

                # 파일 경로 매칭
                if evidence_file == file_path or evidence_file.endswith(file_path):
                    diff_content = node_data.get("diff_content", "")
                    if diff_content:
                        print(f"[HALLUCINATION_LOG] Diff found in Evidence Graph for '{file_path}'")
                        return diff_content

        # 2. Git diff 폴백 (Evidence Graph에 없을 때만)
        try:
            # Git diff 실행 (unstaged + staged changes)
            result = subprocess.run(
                ['git', 'diff', 'HEAD', file_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                print(f"[HALLUCINATION_LOG] Diff found via Git for '{file_path}'")
                return result.stdout

            # Staged changes만 확인
            result = subprocess.run(
                ['git', 'diff', '--cached', file_path],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                print(f"[HALLUCINATION_LOG] Staged diff found via Git for '{file_path}'")
                return result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"[HALLUCINATION_LOG] Git diff failed for '{file_path}': {e}")

        # Priority 4: 파일 내용 직접 읽기 Fallback (Phase 9.11 - Evidence Matching 개선)
        # diff가 없어도 파일이 존재하면 내용을 읽어서 ContentMatcher가 매칭할 수 있게 함
        import os

        search_paths = [
            self.project_path,                      # 기본 프로젝트 경로
            Path(os.getcwd()),                      # 현재 작업 디렉토리
            Path(os.getcwd()) / "cortex_mcp",       # 프로젝트 루트/cortex_mcp
        ]

        for search_path in search_paths:
            try:
                full_path = Path(search_path) / file_path
                if full_path.exists() and full_path.is_file():
                    # 파일 크기 제한 (1MB 이상은 스킵)
                    if full_path.stat().st_size > 1024 * 1024:
                        print(f"[HALLUCINATION_LOG] File too large, skipping direct read: '{file_path}'")
                        continue

                    # 파일 내용 읽기
                    try:
                        content = full_path.read_text(encoding='utf-8')
                        print(f"[HALLUCINATION_LOG] File content loaded directly (fallback) for '{file_path}'")
                        # 파일 내용을 diff 형식으로 변환 (추가된 라인처럼 표시)
                        # ContentMatcher가 + 접두사 라인을 분석하므로 호환성 유지
                        diff_like_content = "\n".join(f"+{line}" for line in content.split("\n"))
                        return diff_like_content
                    except UnicodeDecodeError:
                        print(f"[HALLUCINATION_LOG] File encoding error, skipping: '{file_path}'")
                        continue
            except (OSError, ValueError) as e:
                print(f"[HALLUCINATION_LOG] File read failed: {search_path / file_path} - {e}")
                continue

        print(f"[HALLUCINATION_LOG] No diff content found for '{file_path}'")
        return None

    def _has_file_diff(self, file_path: str, claim: Optional[Claim] = None) -> bool:
        """
        특정 파일이 Evidence Graph에 있는지 확인 (Diff 노드 또는 File 노드)

        Phase 9.6 - Option 2 확장:
        - claim이 제공되면 파일 내용과 Claim 텍스트 매칭 검증
        - ContentMatcher를 사용하여 의미적 유사도 계산

        Fallback: Evidence Graph에 없으면 실제 파일 시스템에서 확인

        Args:
            file_path: 확인할 파일 경로
            claim: Claim 객체 (Option 2 내용 검증용, 선택적)

        Returns:
            Evidence 노드 존재 여부 또는 파일 존재 여부
        """
        # Evidence Graph에서 해당 파일의 Diff 또는 File 노드 찾기
        print(f"[HALLUCINATION_LOG] _has_file_diff: 검색 중 file_path='{file_path}'")
        evidence_nodes_found = []

        # file:// 접두사 추가 버전도 확인
        search_patterns = [file_path, f"file://{file_path}"]

        for node_id, node_data in self.evidence_graph.graph.nodes(data=True):
            node_type = node_data.get("type")

            # Diff 노드 또는 File 노드 확인
            if node_type in ["Diff", "File"]:
                # 노드 ID 자체가 파일 경로일 수 있음 (File 노드의 경우)
                # 또는 node_data에 file_path 필드가 있을 수 있음 (Diff 노드의 경우)
                evidence_file = node_data.get("file_path", node_id)
                evidence_nodes_found.append((node_id, evidence_file, node_type))

                # 파일 경로 매칭 (여러 패턴 시도)
                for pattern in search_patterns:
                    if (evidence_file == pattern or
                        evidence_file.endswith(pattern) or
                        node_id == pattern or
                        node_id.endswith(pattern)):
                        print(f"[HALLUCINATION_LOG] _has_file_diff: Evidence Graph에서 매칭 성공! node_id={node_id}, type={node_type}")

                        # Option 2: Claim 제공 시 내용 검증 (Phase 9.6)
                        if claim is not None:
                            print(f"[HALLUCINATION_LOG] Option 2: Claim 내용 검증 시작 for '{file_path}'")

                            # Diff 내용 추출
                            diff_content = self._get_file_diff_content(file_path)

                            if diff_content:
                                # ContentMatcher로 의미적 유사도 계산
                                matcher = get_content_matcher()
                                match_result = matcher.match(
                                    claim_text=claim.text,
                                    diff_content=diff_content,
                                    claim_type=claim.claim_type
                                )

                                print(f"[HALLUCINATION_LOG] Match result: matched={match_result.matched}, "
                                      f"score={match_result.score}, method={match_result.method}")

                                if not match_result.matched:
                                    # 경로 혼동 감지!
                                    print(f"[HALLUCINATION_LOG] PATH CONFUSION DETECTED!")
                                    print(f"[HALLUCINATION_LOG] Claim: '{claim.text}'")
                                    print(f"[HALLUCINATION_LOG] File: '{file_path}'")
                                    print(f"[HALLUCINATION_LOG] Similarity: {match_result.score}")
                                    print(f"[HALLUCINATION_LOG] Threshold: {matcher.SIMILARITY_THRESHOLDS.get(claim.claim_type, 0.30)}")
                                    return False  # 내용 불일치 → 검증 실패

                                print(f"[HALLUCINATION_LOG] Content matched successfully (score={match_result.score})")
                            else:
                                # Diff 없으면 파일 존재만 확인 (기존 로직)
                                print(f"[HALLUCINATION_LOG] No diff content, fallback to file existence check")

                        return True

        print(f"[HALLUCINATION_LOG] _has_file_diff: Evidence Graph 매칭 실패. 발견된 노드: {evidence_nodes_found}")

        # Fallback: 실제 파일 시스템에서 다중 경로 확인
        import os

        search_paths = [
            self.project_path,                      # memory_dir.parent (기본)
            Path(os.getcwd()),                      # 현재 작업 디렉토리
            Path(os.getcwd()) / "cortex_mcp",       # 프로젝트 루트/cortex_mcp
            Path(os.getcwd()) / "cortex_mcp" / "tools",  # 프로젝트 루트/cortex_mcp/tools
        ]

        # 순환 참조 방지: 이미 확인한 실제 경로 추적
        visited_paths = set()

        for search_path in search_paths:
            try:
                # 실제 경로로 변환 (심볼릭 링크 해소)
                real_path = os.path.realpath(search_path)

                # 이미 확인한 경로면 스킵 (순환 참조 방지)
                if real_path in visited_paths:
                    print(f"[HALLUCINATION_LOG] _has_file_diff: 순환 참조 감지, 스킵: {search_path} -> {real_path}")
                    continue

                visited_paths.add(real_path)

                full_path = Path(real_path) / file_path
                if full_path.exists():
                    # HIGH #3: modification 타입 Claim에 대해 Git diff 확인
                    if claim is not None and claim.claim_type == "modification":
                        print(f"[HALLUCINATION_LOG] HIGH #3: modification Claim 감지, Git diff 확인 시작 for '{file_path}'")

                        # Git diff로 실제 수정 여부 확인
                        git_diff = self._get_file_diff_content(file_path)

                        if git_diff:
                            print(f"[HALLUCINATION_LOG] HIGH #3: Git diff 확인됨 for '{file_path}' → 검증 성공")
                            return True
                        else:
                            print(f"[HALLUCINATION_LOG] HIGH #3: 파일 존재하지만 수정 내역 없음 for '{file_path}' → 검증 실패")
                            return False

                    # modification이 아니거나 claim 없으면 기존 로직
                    # BUG FIX #11: 파일 존재 ≠ 파일 수정
                    # Evidence Graph에도 없고, Git에도 없으면 수정 여부를 확인할 방법이 없음
                    # 따라서 파일 존재만으로는 검증 성공으로 간주할 수 없음
                    print(f"[HALLUCINATION_LOG] _has_file_diff: Fallback - 파일 시스템 확인 '{full_path}': exists=True")
                    print(f"[HALLUCINATION_LOG] _has_file_diff: 파일 존재하지만 수정 여부 확인 불가 → 검증 실패")
                    # 파일이 존재하지만 수정 여부를 확인할 수 없으므로 False 반환
                    # (파일 존재 ≠ 파일 수정)
            except (OSError, ValueError) as e:
                # realpath 실패 시 (권한 문제 등) 해당 경로 스킵
                print(f"[HALLUCINATION_LOG] _has_file_diff: 경로 확인 실패, 스킵: {search_path} - {e}")
                continue

        # 모든 경로에서 찾지 못함
        print(f"[HALLUCINATION_LOG] _has_file_diff: Fallback - 모든 경로에서 파일을 찾지 못함")
        print(f"[HALLUCINATION_LOG] _has_file_diff: 시도한 경로: {[str(p / file_path) for p in search_paths]}")
        print(f"[HALLUCINATION_LOG] _has_file_diff: 검증 실패 (Evidence Graph 및 파일 시스템 모두 없음)")
        return False

    def _find_modified_files_in_graph(self) -> List[str]:
        """
        Evidence Graph에서 수정된 파일 찾기

        Returns:
            수정된 파일 경로 목록
        """
        modified_files = []

        # MODIFIED 엣지로 연결된 File 노드 찾기
        for source, target, edge_data in self.evidence_graph.graph.edges(data=True):
            if edge_data.get("type") == "MODIFIED":
                target_data = self.evidence_graph.graph.nodes[target]
                if target_data.get("type") == "File":
                    modified_files.append(target)

        return modified_files

    def _extract_file_references(self, text: str) -> List[str]:
        """
        텍스트에서 파일 참조 추출

        Args:
            text: 분석할 텍스트

        Returns:
            파일 경로 목록
        """
        import re

        # 파일 경로 패턴 (예: path/to/file.py, core/module.py, config.yaml)
        pattern = r"(?:[\w./]+/)?[\w.]+\.(?:py|js|ts|tsx|jsx|java|cpp|c|h|go|rs|md|yaml|yml|json|xml|toml|ini|cfg|conf|txt)"
        matches = re.findall(pattern, text, re.IGNORECASE)

        return list(set(matches))  # 중복 제거

    def _check_files_in_graph(self, file_paths: List[str]) -> List[str]:
        """
        Evidence Graph에 파일 노드 존재 확인

        Args:
            file_paths: 확인할 파일 경로 목록

        Returns:
            존재하는 파일 경로 목록
        """
        existing = []

        for file_path in file_paths:
            if file_path in self.evidence_graph.graph:
                node_data = self.evidence_graph.graph.nodes[file_path]
                if node_data.get("type") == "File":
                    existing.append(file_path)

        return existing

    def _check_files_modified(self, file_paths: List[str]) -> List[str]:
        """
        파일들이 수정되었는지 확인

        Args:
            file_paths: 확인할 파일 경로 목록

        Returns:
            수정된 파일 경로 목록
        """
        modified = []

        for file_path in file_paths:
            # Evidence Graph에서 MODIFIED 엣지 확인
            if file_path in self.evidence_graph.graph:
                # 해당 파일로 향하는 MODIFIED 엣지 확인
                for source, target, edge_data in self.evidence_graph.graph.edges(data=True):
                    if target == file_path and edge_data.get("type") == "MODIFIED":
                        modified.append(file_path)
                        break

        return modified

    def _check_context_file_links(self, file_paths: List[str]) -> List[Dict]:
        """
        Context와 File 간 연결 확인

        Args:
            file_paths: 확인할 파일 경로 목록

        Returns:
            연결 정보 목록
        """
        links = []

        for file_path in file_paths:
            if file_path in self.evidence_graph.graph:
                # REFERENCED 엣지로 연결된 Context 찾기
                for source, target, edge_data in self.evidence_graph.graph.edges(data=True):
                    if target == file_path and edge_data.get("type") == "REFERENCED":
                        source_data = self.evidence_graph.graph.nodes[source]
                        if source_data.get("type") == "Context":
                            links.append(
                                {
                                    "context_id": source,
                                    "file_path": file_path,
                                    "edge_type": "REFERENCED",
                                }
                            )

        return links

    def get_verification_summary(self, results: List[Dict]) -> Dict:
        """
        검증 결과 요약

        Args:
            results: 검증 결과 목록

        Returns:
            요약 딕셔너리
        """
        total = len(results)
        verified = sum(1 for r in results if r["verified"])
        unverified = total - verified

        avg_confidence = sum(r["confidence"] for r in results) / total if total > 0 else 0.0

        by_claim_type = {}
        for result in results:
            claim_type = result["claim"].claim_type
            if claim_type not in by_claim_type:
                by_claim_type[claim_type] = {"total": 0, "verified": 0, "avg_confidence": 0.0}

            by_claim_type[claim_type]["total"] += 1
            if result["verified"]:
                by_claim_type[claim_type]["verified"] += 1
            by_claim_type[claim_type]["avg_confidence"] += result["confidence"]

        # 평균 계산
        for claim_type in by_claim_type:
            count = by_claim_type[claim_type]["total"]
            by_claim_type[claim_type]["avg_confidence"] /= count

        return {
            "total_claims": total,
            "verified_claims": verified,
            "unverified_claims": unverified,
            "verification_rate": verified / total if total > 0 else 0.0,
            "average_confidence": avg_confidence,
            "by_claim_type": by_claim_type,
            "timestamp": datetime.now().isoformat(),
        }
