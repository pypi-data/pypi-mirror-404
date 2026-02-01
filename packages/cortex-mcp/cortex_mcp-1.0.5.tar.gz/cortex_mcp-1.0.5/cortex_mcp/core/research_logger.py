"""
Cortex MCP - Research Logger
논문 연구용 데이터 수집 시스템 (Phase 0)

설계 원칙 (세계 최고 석학 수준):
1. 데이터 품질: ISO 8601 timestamp, event completeness, schema validation
2. 윤리/프라이버시: GDPR 준수, SHA-256 익명화, explicit opt-in consent
3. 성능: Async logging, log rotation, batch writing, silent failure
4. 재현 가능성: Complete metadata, deterministic ordering, exportable format

목적: Silent Failure in LLM-assisted Development 연구를 위한 데이터 수집
"""

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import config


class EventType(Enum):
    """연구 이벤트 타입"""

    LLM_RESPONSE = "llm_response"  # LLM 응답 생성
    CLAIM_EXTRACTION = "claim_extraction"  # Claim 추출
    EVIDENCE_RETRIEVAL = "evidence_retrieval"  # Evidence 검색
    GROUNDING_VERIFICATION = "grounding_verification"  # Grounding 검증
    CORTEX_INTERVENTION = "cortex_intervention"  # Cortex 개입
    USER_RESPONSE = "user_response"  # 사용자 반응
    CONTEXT_DRIFT = "context_drift"  # Context Drift 감지
    SILENT_FAILURE = "silent_failure"  # Silent Failure 발생
    RECOVERY = "recovery"  # Silent Failure 복구


class InterventionType(Enum):
    """Cortex 개입 타입"""

    WARNING = "warning"  # 경고 표시
    BRANCH_SUGGESTION = "branch"  # 브랜치 생성 제안
    CONFIRMATION = "confirm"  # 사용자 확인 요청
    BLOCK = "block"  # 작업 차단 (critical)


class UserResponseType(Enum):
    """사용자 반응 타입"""

    ACCEPTED = "accepted"  # 수락
    REJECTED = "rejected"  # 거부
    IGNORED = "ignored"  # 무시
    MODIFIED = "modified"  # 수정 후 수락


@dataclass
class ResearchEvent:
    """
    연구 이벤트 데이터 클래스

    Silent Failure 연구를 위한 모든 필요 데이터를 포함
    """

    # Event identification
    event_id: str
    event_type: EventType
    timestamp: str  # ISO 8601 format, UTC

    # Session identification (anonymized)
    user_hash: str
    session_id: str
    task_id: Optional[str] = None

    # Context state
    context_state: Dict[str, Any] = field(default_factory=dict)

    # LLM response data
    llm_response_data: Optional[Dict[str, Any]] = None

    # Cortex intervention data
    intervention_data: Optional[Dict[str, Any]] = None

    # User response data
    user_response_data: Optional[Dict[str, Any]] = None

    # Silent Failure data
    silent_failure_data: Optional[Dict[str, Any]] = None

    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResearchLogger:
    """
    Research data logger for academic paper

    Non-intrusive, separated, anonymized, ethical data collection
    for Silent Failure in LLM-assisted Development research.

    Design Principles:
    1. Non-intrusive: Does not modify existing functionality
    2. Separated: Research logs != Product logs
    3. Anonymized: User identity protected (SHA-256 hash)
    4. Ethical: Explicit opt-in consent required, GDPR compliant
    5. Performance: Async logging, log rotation, batch writing
    6. Reproducibility: Complete metadata, deterministic ordering

    Usage:
        logger = get_research_logger()
        logger.enable(user_consent=True)

        event = ResearchEvent(...)
        await logger.log_event(event)
    """

    def __init__(self):
        """Initialize research logger"""
        self.enabled = False  # Disabled by default (opt-in)

        # Directory structure
        self.research_dir = config.base_dir / "research"
        self.events_dir = self.research_dir / "events"
        self.aggregated_dir = self.research_dir / "aggregated"
        self.consent_file = self.research_dir / "consent.json"

        # Create directories
        self.research_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.aggregated_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.current_session_id: Optional[str] = None
        self.current_user_hash: Optional[str] = None

        # Buffering for batch writing
        self.event_buffer: List[ResearchEvent] = []
        self.buffer_max_size = 10  # Write every 10 events

        # Log rotation
        self.max_file_size_mb = 10

        # Metadata
        self.version = "1.0.0"
        self.schema_version = "1.0"

    def enable(self, user_consent: bool = False, user_id: Optional[str] = None):
        """
        Enable research logging (requires explicit consent)

        Args:
            user_consent: Explicit user consent (must be True)
            user_id: User identifier (will be anonymized)

        GDPR Compliance:
        - Article 5: Lawfulness, fairness, transparency
        - Article 6: Consent as legal basis
        - Article 7: Conditions for consent
        """
        if not user_consent:
            return  # No consent, no logging

        self.enabled = True

        # Anonymize user ID
        if user_id:
            self.current_user_hash = self._anonymize_user_id(user_id)
        else:
            # Generate random hash if no user ID provided
            import uuid

            self.current_user_hash = self._anonymize_user_id(str(uuid.uuid4()))

        # Generate session ID
        self.current_session_id = self._generate_session_id()

        # Log consent
        self._log_consent()

    def disable(self):
        """
        Disable research logging

        GDPR Compliance:
        - Article 7(3): Right to withdraw consent
        """
        self.enabled = False
        self.current_session_id = None
        self.current_user_hash = None

    def _anonymize_user_id(self, user_id: str) -> str:
        """
        Generate SHA-256 hash for user anonymization

        GDPR Compliance:
        - Article 4(5): Pseudonymization
        - SHA-256 is one-way, cannot reverse to original

        Args:
            user_id: Original user identifier

        Returns:
            16-character hexadecimal hash (first 16 chars of SHA-256)
        """
        # Add salt for additional security
        salt = "cortex_research_2025"
        salted_id = f"{salt}:{user_id}"

        # SHA-256 hash
        hash_object = hashlib.sha256(salted_id.encode("utf-8"))
        hash_hex = hash_object.hexdigest()

        # Return first 16 characters (sufficient for uniqueness)
        return hash_hex[:16]

    def _generate_session_id(self) -> str:
        """
        Generate unique session ID

        Format: sess_YYYYMMDD_HHMMSS_random
        """
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Add random component for uniqueness
        import uuid

        random_suffix = str(uuid.uuid4())[:8]

        return f"sess_{timestamp}_{random_suffix}"

    def _generate_event_id(self) -> str:
        """
        Generate unique event ID

        Format: evt_YYYYMMDD_HHMMSS_random
        """
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Add random component for uniqueness
        import uuid

        random_suffix = str(uuid.uuid4())[:8]

        return f"evt_{timestamp}_{random_suffix}"

    def _get_event_file_path(self, user_hash: str, session_id: str) -> Path:
        """
        Get event log file path for a session

        Directory structure:
        ~/.cortex/research/events/{user_hash}/session_{session_id}.jsonl

        Args:
            user_hash: Anonymized user hash
            session_id: Session identifier

        Returns:
            Path to event log file
        """
        user_dir = self.events_dir / user_hash
        user_dir.mkdir(parents=True, exist_ok=True)

        return user_dir / f"session_{session_id}.jsonl"

    async def log_event(self, event: ResearchEvent):
        """
        Log a research event (async, non-blocking)

        Design:
        - Async to avoid blocking main thread
        - Buffered writing for performance
        - Automatic log rotation
        - Silent failure (no exceptions propagated)

        Args:
            event: ResearchEvent to log
        """
        if not self.enabled:
            return  # Logging disabled, silently return

        try:
            # Add to buffer
            self.event_buffer.append(event)

            # Write buffer if full
            if len(self.event_buffer) >= self.buffer_max_size:
                await self._write_buffer()
        except Exception as e:
            # Silent failure: log error but do not disrupt product functionality
            self._log_error(f"Failed to log event: {e}")

    async def _write_buffer(self):
        """
        Write buffered events to file

        Performance optimization:
        - Batch writing reduces I/O operations
        - Async to avoid blocking
        """
        if not self.event_buffer:
            return

        try:
            # Get file path
            if not self.current_user_hash or not self.current_session_id:
                return

            file_path = self._get_event_file_path(self.current_user_hash, self.current_session_id)

            # Check file size for rotation
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > self.max_file_size_mb:
                    # Rotate log file
                    self._rotate_log_file(file_path)

            # Write events to file (JSONLines format)
            with open(file_path, "a", encoding="utf-8") as f:
                for event in self.event_buffer:
                    # Convert event to dict
                    event_dict = asdict(event)

                    # Convert Enum to string
                    if isinstance(event_dict.get("event_type"), EventType):
                        event_dict["event_type"] = event_dict["event_type"].value

                    # Write as JSON line
                    f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

            # Clear buffer
            self.event_buffer.clear()
        except Exception as e:
            self._log_error(f"Failed to write buffer: {e}")

    def _rotate_log_file(self, file_path: Path):
        """
        Rotate log file when it exceeds max size

        Strategy:
        - Rename current file with timestamp suffix
        - New events will go to new file

        Args:
            file_path: Path to log file to rotate
        """
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            rotated_path = file_path.with_suffix(f".{timestamp}.jsonl")
            file_path.rename(rotated_path)
        except Exception as e:
            self._log_error(f"Failed to rotate log file: {e}")

    def _log_consent(self):
        """
        Log user consent for research data collection

        GDPR Compliance:
        - Article 7: Conditions for consent
        - Article 13: Information to be provided (transparency)
        """
        try:
            consent_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": self.version,
                "schema_version": self.schema_version,
                "user_hash": self.current_user_hash,
                "session_id": self.current_session_id,
                "agreed_to_terms": True,
                "data_collection_purpose": "Silent Failure in LLM-assisted Development research",
                "data_types_collected": [
                    "llm_response_metadata",
                    "claim_verification_results",
                    "cortex_intervention_events",
                    "user_response_actions",
                    "context_drift_detection",
                    "silent_failure_instances",
                ],
                "data_anonymization": "SHA-256 hash with salt",
                "data_retention": "Until paper publication + 1 year",
                "right_to_withdraw": True,
                "right_to_delete": True,
                "contact_email": "research@cortex-mcp.org",
            }

            with open(self.consent_file, "w", encoding="utf-8") as f:
                json.dump(consent_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log_error(f"Failed to log consent: {e}")

    def _log_error(self, error_message: str):
        """
        Log error to product logs (not research logs)

        Silent failure principle:
        - Research logging errors do not disrupt product
        - Errors logged to separate error log
        """
        try:
            error_log_file = self.research_dir / "errors.log"
            timestamp = datetime.now(timezone.utc).isoformat()

            with open(error_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {error_message}\n")
        except:
            pass  # Ultimate silent failure

    async def flush(self):
        """
        Flush buffered events to disk

        Call this:
        - Before session end
        - Periodically (e.g., every 5 minutes)
        - On application shutdown
        """
        await self._write_buffer()

    def export_session_data(self, session_id: str, output_format: str = "jsonl") -> Optional[Path]:
        """
        Export session data for analysis

        GDPR Compliance:
        - Article 20: Right to data portability

        Args:
            session_id: Session identifier
            output_format: Output format ("jsonl" or "json")

        Returns:
            Path to exported file, or None if failed
        """
        try:
            if not self.current_user_hash:
                return None

            file_path = self._get_event_file_path(self.current_user_hash, session_id)

            if not file_path.exists():
                return None

            if output_format == "jsonl":
                return file_path
            elif output_format == "json":
                # Convert JSONLines to single JSON array
                events = []
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))

                output_path = file_path.with_suffix(".json")
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2, ensure_ascii=False)

                return output_path
            else:
                return None
        except Exception as e:
            self._log_error(f"Failed to export session data: {e}")
            return None

    def delete_all_data(self):
        """
        Delete all research data for current user

        GDPR Compliance:
        - Article 17: Right to erasure ("right to be forgotten")

        This is permanent and cannot be undone.
        """
        try:
            if not self.current_user_hash:
                return

            user_dir = self.events_dir / self.current_user_hash
            if user_dir.exists():
                import shutil

                shutil.rmtree(user_dir)

            # Disable logging
            self.disable()
        except Exception as e:
            self._log_error(f"Failed to delete data: {e}")


# Singleton instance
_research_logger: Optional[ResearchLogger] = None


def get_research_logger() -> ResearchLogger:
    """
    Get research logger singleton

    Returns:
        ResearchLogger instance
    """
    global _research_logger
    if _research_logger is None:
        _research_logger = ResearchLogger()
    return _research_logger


# Helper functions for creating events


def create_llm_response_event(
    response_text: str,
    response_length: int,
    claims_extracted: List[Dict[str, Any]],
    grounding_score: float,
    evidence_count: int,
    contradiction_detected: bool,
    context_state: Dict[str, Any],
    task_id: Optional[str] = None,
) -> ResearchEvent:
    """
    Create LLM response event

    Args:
        response_text: LLM response (first 100 chars for privacy)
        response_length: Length of response in characters
        claims_extracted: List of extracted claims
        grounding_score: Grounding score (0-1)
        evidence_count: Number of evidence files found
        contradiction_detected: Whether contradiction was detected
        context_state: Current context state
        task_id: Optional task identifier

    Returns:
        ResearchEvent
    """
    logger = get_research_logger()

    return ResearchEvent(
        event_id=logger._generate_event_id(),
        event_type=EventType.LLM_RESPONSE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        user_hash=logger.current_user_hash or "unknown",
        session_id=logger.current_session_id or "unknown",
        task_id=task_id,
        context_state=context_state,
        llm_response_data={
            "response_preview": (
                response_text[:100] if response_text else ""
            ),  # Privacy: only first 100 chars
            "response_length_chars": response_length,
            "claims_extracted": claims_extracted,
            "grounding_score": grounding_score,
            "evidence_count": evidence_count,
            "contradiction_detected": contradiction_detected,
        },
    )


def create_cortex_intervention_event(
    intervention_type: InterventionType,
    reason: str,
    grounding_score: float,
    evidence_count: int,
    context_state: Dict[str, Any],
    task_id: Optional[str] = None,
) -> ResearchEvent:
    """
    Create Cortex intervention event

    Args:
        intervention_type: Type of intervention
        reason: Reason for intervention
        grounding_score: Grounding score that triggered intervention
        evidence_count: Number of evidence files
        context_state: Current context state
        task_id: Optional task identifier

    Returns:
        ResearchEvent
    """
    logger = get_research_logger()

    return ResearchEvent(
        event_id=logger._generate_event_id(),
        event_type=EventType.CORTEX_INTERVENTION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        user_hash=logger.current_user_hash or "unknown",
        session_id=logger.current_session_id or "unknown",
        task_id=task_id,
        context_state=context_state,
        intervention_data={
            "intervention_type": intervention_type.value,
            "reason": reason,
            "grounding_score": grounding_score,
            "evidence_count": evidence_count,
            "timestamp_ms": datetime.now(timezone.utc).timestamp() * 1000,
        },
    )


def create_user_response_event(
    response_type: UserResponseType,
    intervention_event_id: str,
    time_to_response_sec: float,
    context_state: Dict[str, Any],
    task_id: Optional[str] = None,
) -> ResearchEvent:
    """
    Create user response event

    Args:
        response_type: Type of user response
        intervention_event_id: ID of intervention event this responds to
        time_to_response_sec: Time from intervention to response
        context_state: Current context state
        task_id: Optional task identifier

    Returns:
        ResearchEvent
    """
    logger = get_research_logger()

    return ResearchEvent(
        event_id=logger._generate_event_id(),
        event_type=EventType.USER_RESPONSE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        user_hash=logger.current_user_hash or "unknown",
        session_id=logger.current_session_id or "unknown",
        task_id=task_id,
        context_state=context_state,
        user_response_data={
            "response_type": response_type.value,
            "intervention_event_id": intervention_event_id,
            "time_to_response_sec": time_to_response_sec,
        },
        metrics={"recovery_time_sec": time_to_response_sec},
    )


def log_event_sync(event: ResearchEvent):
    """
    Synchronous wrapper for log_event (for use in sync contexts)

    This creates a new event loop if needed and logs the event.
    Safe to call from synchronous code.

    Args:
        event: ResearchEvent to log
    """
    logger = get_research_logger()
    if not logger.enabled:
        return

    try:
        # Try to get running event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            asyncio.create_task(logger.log_event(event))
        else:
            # If no loop, run sync
            loop.run_until_complete(logger.log_event(event))
    except RuntimeError:
        # No event loop, create new one
        asyncio.run(logger.log_event(event))
    except Exception as e:
        # Silent failure
        logger._log_error(f"Failed to log event sync: {e}")


def create_silent_failure_event(
    failure_type: str,
    detected: bool,
    detection_latency_sec: Optional[float],
    grounding_score: float,
    context_state: Dict[str, Any],
    task_id: Optional[str] = None,
) -> ResearchEvent:
    """
    Create Silent Failure event

    Args:
        failure_type: Type of failure (context_drift, delayed_constraint, false_progress)
        detected: Whether failure was detected by Cortex
        detection_latency_sec: Time from failure to detection (None if undetected)
        grounding_score: Grounding score at failure point
        context_state: Current context state
        task_id: Optional task identifier

    Returns:
        ResearchEvent
    """
    logger = get_research_logger()

    return ResearchEvent(
        event_id=logger._generate_event_id(),
        event_type=EventType.SILENT_FAILURE,
        timestamp=datetime.now(timezone.utc).isoformat(),
        user_hash=logger.current_user_hash or "unknown",
        session_id=logger.current_session_id or "unknown",
        task_id=task_id,
        context_state=context_state,
        silent_failure_data={
            "failure_type": failure_type,
            "detected": detected,
            "detection_latency_sec": detection_latency_sec,
            "grounding_score": grounding_score,
        },
        metrics={
            "detection_latency_sec": (
                detection_latency_sec if detection_latency_sec else float("inf")
            ),
            "silent_failure_rate": 0.0 if detected else 1.0,
        },
    )
