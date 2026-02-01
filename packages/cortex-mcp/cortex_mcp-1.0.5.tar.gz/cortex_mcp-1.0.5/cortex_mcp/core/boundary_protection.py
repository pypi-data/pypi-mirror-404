"""
Cortex MCP - Context Boundary Protection (v1.0)
AI가 작업 범위 외 코드를 수정하지 못하도록 보호

핵심 기능:
1. 작업 경계 자동 추론 (맥락 분석 기반)
2. 명시적 경계 설정 (사용자 지정)
3. System Prompt 주입 (경계 규칙)
4. 위반 감지 및 차단
5. 사용자 승인 워크플로우

문제 해결:
- AI가 "관련 있어 보여서" 불필요한 파일 수정
- "코드 정리" 명목으로 무관한 코드 변경
- 요청한 범위 외 파일 삭제
"""

import fnmatch
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

sys.path.append(str(Path(__file__).parent.parent))
from config import config


class ViolationType(Enum):
    """경계 위반 유형"""

    FILE_OUTSIDE_SCOPE = "file_outside_scope"  # 범위 외 파일 접근
    UNAUTHORIZED_DELETE = "unauthorized_delete"  # 비승인 삭제
    SCOPE_EXPANSION = "scope_expansion"  # 범위 확장 시도
    UNRELATED_MODIFICATION = "unrelated_modification"  # 무관한 수정
    PROTECTED_FILE = "protected_file"  # 보호된 파일 접근


class ActionType(Enum):
    """파일 작업 유형"""

    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    MODIFY = "modify"


class ProtectionLevel(Enum):
    """보호 수준"""

    BLOCK_ALWAYS = "block_always"  # 항상 차단
    REQUIRE_APPROVAL = "require_approval"  # 승인 필요
    WARN = "warn"  # 경고만
    ALLOW = "allow"  # 허용


@dataclass
class Boundary:
    """작업 경계 정의"""

    task: str  # 작업 설명
    created_at: str  # 생성 시간
    allowed_files: List[str] = field(default_factory=list)  # 허용 파일
    allowed_patterns: List[str] = field(default_factory=list)  # 허용 패턴 (glob)
    allowed_actions: List[str] = field(default_factory=list)  # 허용 작업
    forbidden_files: List[str] = field(default_factory=list)  # 금지 파일
    forbidden_patterns: List[str] = field(default_factory=list)  # 금지 패턴
    exceptions: List[str] = field(default_factory=list)  # 예외 (승인 필요)
    strict_mode: bool = False  # 엄격 모드 (명시된 파일만 허용)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "created_at": self.created_at,
            "allowed_files": self.allowed_files,
            "allowed_patterns": self.allowed_patterns,
            "allowed_actions": self.allowed_actions,
            "forbidden_files": self.forbidden_files,
            "forbidden_patterns": self.forbidden_patterns,
            "exceptions": self.exceptions,
            "strict_mode": self.strict_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Boundary":
        return cls(
            task=data.get("task", ""),
            created_at=data.get("created_at", ""),
            allowed_files=data.get("allowed_files", []),
            allowed_patterns=data.get("allowed_patterns", []),
            allowed_actions=data.get("allowed_actions", ["read", "write", "create"]),
            forbidden_files=data.get("forbidden_files", []),
            forbidden_patterns=data.get("forbidden_patterns", []),
            exceptions=data.get("exceptions", []),
            strict_mode=data.get("strict_mode", False),
        )


@dataclass
class Violation:
    """경계 위반 기록"""

    file_path: str
    action: ActionType
    violation_type: ViolationType
    timestamp: str
    reason: str
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "action": self.action.value,
            "violation_type": self.violation_type.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }


class BoundaryProtection:
    """
    컨텍스트 경계 보호 시스템

    AI가 작업 범위를 벗어난 코드 수정을 방지합니다.
    """

    # 기본 보호 파일 패턴
    DEFAULT_PROTECTED_PATTERNS = [
        # 환경 설정 파일
        "*.env*",
        ".env",
        ".env.*",
        # 자격 증명 및 비밀 파일
        "**/credentials.*",
        "**/secrets.*",
        "**/*.key",
        "**/*.pem",
        "**/*private*key*",
        # SSH/AWS 관련
        "**/.ssh/**",
        "**/.aws/**",
        # Git 내부
        "**/.git/**",
        # 데이터베이스 설정
        "**/database.yml",
        "**/database.yaml",
        # 패키지/캐시 디렉토리
        "**/node_modules/**",
        "**/__pycache__/**",
    ]

    # 경계 추론 키워드
    INFERENCE_KEYWORDS = {
        "auth": ["auth", "login", "session", "token", "password", "credential"],
        "payment": ["payment", "checkout", "billing", "invoice", "subscription"],
        "api": ["api", "endpoint", "route", "controller", "handler"],
        "database": ["database", "db", "query", "migration", "model", "schema"],
        "test": ["test", "spec", "fixture", "mock", "pytest", "jest"],
        "config": ["config", "setting", "env", "environment"],
        "frontend": ["component", "page", "view", "template", "css", "style"],
        "backend": ["service", "worker", "job", "queue", "celery"],
    }

    def __init__(self, project_id: str, project_path: Optional[str] = None):
        self.project_id = project_id
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.boundary_dir = config.base_dir / "boundaries" / project_id
        self.boundary_dir.mkdir(parents=True, exist_ok=True)

        # 현재 경계
        self._current_boundary: Optional[Boundary] = None

        # 위반 기록
        self.violations_file = self.boundary_dir / "violations.json"

        # 프로젝트 규칙 로드
        self._project_rules = self._load_project_rules()

    def set_boundary(
        self,
        task: str,
        files: Optional[List[str]] = None,
        patterns: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        strict_mode: bool = False,
    ) -> Boundary:
        """
        작업 경계 수동 설정

        Args:
            task: 작업 설명
            files: 허용 파일 목록
            patterns: 허용 패턴 목록 (glob)
            actions: 허용 작업 목록
            strict_mode: 엄격 모드 (명시된 파일만 허용)

        Returns:
            설정된 Boundary
        """
        boundary = Boundary(
            task=task,
            created_at=datetime.now(timezone.utc).isoformat(),
            allowed_files=files or [],
            allowed_patterns=patterns or [],
            allowed_actions=actions or ["read", "write", "create"],
            forbidden_files=self._get_default_forbidden(),
            forbidden_patterns=self.DEFAULT_PROTECTED_PATTERNS.copy(),
            strict_mode=strict_mode,
        )

        self._current_boundary = boundary
        self._save_current_boundary()

        return boundary

    def infer_boundary(
        self, task: str, context: Optional[str] = None, recent_files: Optional[List[str]] = None
    ) -> Boundary:
        """
        작업 설명에서 경계 자동 추론

        Args:
            task: 작업 설명
            context: 추가 컨텍스트
            recent_files: 최근 작업 파일 목록

        Returns:
            추론된 Boundary
        """
        full_text = f"{task} {context or ''}".lower()

        # 키워드 매칭으로 도메인 추론
        matched_domains = []
        for domain, keywords in self.INFERENCE_KEYWORDS.items():
            if any(kw in full_text for kw in keywords):
                matched_domains.append(domain)

        # 도메인별 허용 패턴 생성
        allowed_patterns = []
        for domain in matched_domains:
            patterns = self._get_domain_patterns(domain)
            allowed_patterns.extend(patterns)

        # 최근 작업 파일 기반 패턴 추가
        if recent_files:
            for file_path in recent_files[:10]:  # 최근 10개만
                # 파일이 속한 디렉토리 패턴 추가
                parent = str(Path(file_path).parent)
                if parent and parent != ".":
                    allowed_patterns.append(f"{parent}/**")

        # 중복 제거
        allowed_patterns = list(set(allowed_patterns))

        boundary = Boundary(
            task=task,
            created_at=datetime.now(timezone.utc).isoformat(),
            allowed_files=recent_files or [],
            allowed_patterns=allowed_patterns or ["**/*"],  # 기본값: 전체
            allowed_actions=["read", "write", "create"],
            forbidden_files=self._get_default_forbidden(),
            forbidden_patterns=self.DEFAULT_PROTECTED_PATTERNS.copy(),
            strict_mode=False,
        )

        self._current_boundary = boundary
        self._save_current_boundary()

        return boundary

    def get_current_boundary(self) -> Optional[Boundary]:
        """현재 경계 조회"""
        return self._current_boundary

    def validate_action(self, file_path: str, action: ActionType) -> Dict[str, Any]:
        """
        파일 작업 유효성 검증

        Args:
            file_path: 대상 파일 경로
            action: 작업 유형

        Returns:
            검증 결과 (allowed, violation, reason)
        """
        # 경계가 설정되지 않으면 기본 규칙만 적용
        if not self._current_boundary:
            return self._validate_default_rules(file_path, action)

        boundary = self._current_boundary
        normalized_path = self._normalize_path(file_path)

        # 1. 금지 파일/패턴 체크 (최우선)
        if self._matches_patterns(normalized_path, boundary.forbidden_patterns):
            return self._create_violation_result(
                file_path, action, ViolationType.PROTECTED_FILE, f"File matches forbidden pattern"
            )

        if normalized_path in boundary.forbidden_files:
            return self._create_violation_result(
                file_path, action, ViolationType.PROTECTED_FILE, f"File is in forbidden list"
            )

        # 2. 삭제 작업 특별 검증
        if action == ActionType.DELETE:
            if not self._is_delete_allowed(normalized_path, boundary):
                return self._create_violation_result(
                    file_path,
                    action,
                    ViolationType.UNAUTHORIZED_DELETE,
                    "Delete requires explicit approval",
                )

        # 3. 예외 목록 체크 (모든 모드에서 우선 적용)
        if normalized_path in boundary.exceptions:
            return self._create_exception_result(file_path, action)

        # 4. 엄격 모드에서는 명시된 파일만 허용
        if boundary.strict_mode:
            if normalized_path not in boundary.allowed_files:
                if not self._matches_patterns(normalized_path, boundary.allowed_patterns):
                    return self._create_violation_result(
                        file_path,
                        action,
                        ViolationType.FILE_OUTSIDE_SCOPE,
                        "Strict mode: file not in allowed list",
                    )

        # 5. 허용 패턴 체크
        if boundary.allowed_patterns:
            if not self._matches_patterns(normalized_path, boundary.allowed_patterns):
                return self._create_violation_result(
                    file_path,
                    action,
                    ViolationType.FILE_OUTSIDE_SCOPE,
                    f"File outside allowed patterns: {boundary.allowed_patterns}",
                )

        # 6. 작업 유형 체크
        if action.value not in boundary.allowed_actions:
            return self._create_violation_result(
                file_path,
                action,
                ViolationType.SCOPE_EXPANSION,
                f"Action '{action.value}' not in allowed actions",
            )

        return {
            "allowed": True,
            "file_path": file_path,
            "action": action.value,
            "reason": "Within boundary",
        }

    def request_boundary_exception(self, file_path: str, reason: str) -> Dict[str, Any]:
        """
        경계 예외 요청

        Args:
            file_path: 파일 경로
            reason: 예외 필요 이유

        Returns:
            예외 요청 결과 (사용자 승인 필요)
        """
        if not self._current_boundary:
            return {"success": False, "error": "No boundary set"}

        # 예외 요청 기록
        exception_request = {
            "file_path": file_path,
            "reason": reason,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
        }

        return {
            "success": True,
            "requires_approval": True,
            "request": exception_request,
            "message": f"Exception requested for {file_path}. Awaiting user approval.",
        }

    def approve_exception(self, file_path: str, approver: str = "user") -> Dict[str, Any]:
        """
        예외 승인

        Args:
            file_path: 승인할 파일 경로
            approver: 승인자

        Returns:
            승인 결과
        """
        if not self._current_boundary:
            return {"success": False, "error": "No boundary set"}

        # 예외 목록에 추가
        if file_path not in self._current_boundary.exceptions:
            self._current_boundary.exceptions.append(file_path)
            self._save_current_boundary()

        return {
            "success": True,
            "file_path": file_path,
            "approved_by": approver,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Exception approved for {file_path}",
        }

    def get_boundary_violations(
        self, since: Optional[str] = None, severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        위반 이력 조회

        Args:
            since: 이 시점 이후의 기록만
            severity: 심각도 필터

        Returns:
            위반 목록
        """
        violations = self._load_violations()

        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                violations = [
                    v
                    for v in violations
                    if datetime.fromisoformat(v["timestamp"].replace("Z", "+00:00")) >= since_dt
                ]
            except ValueError:
                pass

        return violations

    def generate_boundary_protocol(self) -> str:
        """
        System Prompt용 경계 프로토콜 생성

        Returns:
            CONTEXT_BOUNDARY_PROTOCOL 문자열
        """
        if not self._current_boundary:
            return self._generate_default_protocol()

        boundary = self._current_boundary

        # 허용 범위 문자열
        allowed_files_str = ", ".join(boundary.allowed_files[:5]) or "None specified"
        if len(boundary.allowed_files) > 5:
            allowed_files_str += f" (+{len(boundary.allowed_files) - 5} more)"

        allowed_patterns_str = ", ".join(boundary.allowed_patterns[:5]) or "**/*"
        if len(boundary.allowed_patterns) > 5:
            allowed_patterns_str += f" (+{len(boundary.allowed_patterns) - 5} more)"

        forbidden_str = ", ".join(boundary.forbidden_patterns[:3]) or "None"

        protocol = f"""[CONTEXT_BOUNDARY_PROTOCOL - MANDATORY]

Current Task: {boundary.task}
Boundary Mode: {"STRICT" if boundary.strict_mode else "STANDARD"}

## Allowed Scope
- Files: {allowed_files_str}
- Patterns: {allowed_patterns_str}
- Actions: {", ".join(boundary.allowed_actions)}

## Forbidden (NEVER modify)
- Patterns: {forbidden_str}

## Behavior Rules
1. ONLY modify files within the allowed scope
2. NEVER modify files matching forbidden patterns
3. If you need to modify a file outside scope:
   - STOP and ask: "[Boundary Exception] I need to modify {{file}}. Reason: {{reason}}. May I proceed?"
4. DO NOT assume "related" files should be modified
5. DO NOT perform "cleanup" or "refactoring" outside scope

## Violation Response
If you detect yourself about to violate these boundaries:
"[BOUNDARY CHECK] The file {{path}} is outside my current work scope. Skipping modification."

[/CONTEXT_BOUNDARY_PROTOCOL]"""

        return protocol

    def clear_boundary(self) -> Dict[str, Any]:
        """경계 해제"""
        self._current_boundary = None

        boundary_file = self.boundary_dir / "current_boundary.json"
        if boundary_file.exists():
            boundary_file.unlink()

        return {"success": True, "message": "Boundary cleared"}

    # ==================== Private Methods ====================

    def _normalize_path(self, file_path: str) -> str:
        """경로 정규화 (Path Traversal 방지 포함)"""
        # 1. 기본 정규화: ./ 및 ../ 해석
        import os

        normalized = os.path.normpath(file_path)

        # 2. Path Traversal 탐지: ..이 포함된 경로 차단
        if ".." in normalized:
            # 경로가 프로젝트 외부로 나가려는 시도 감지
            return f"__BLOCKED_PATH_TRAVERSAL__/{file_path}"

        path = Path(normalized)

        # 3. 상대 경로로 변환 시도
        try:
            if path.is_absolute() and self.project_path:
                path = path.relative_to(self.project_path)
        except ValueError:
            pass

        return str(path).replace("\\", "/")

    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """파일이 패턴과 매치되는지 확인"""
        for pattern in patterns:
            # 단순 패턴 (/ 또는 ** 없음)은 현재 디렉토리만 매칭
            if "/" not in pattern and "**" not in pattern:
                # 파일이 하위 디렉토리에 있으면 매칭 안됨
                if "/" in file_path:
                    continue
                if fnmatch.fnmatch(file_path, pattern):
                    return True
                continue

            # **가 없는 경로 패턴 (예: config/*.yaml)
            # *가 디렉토리 구분자를 넘지 않도록 정규식 사용
            if "**" not in pattern:
                # 정규식으로 변환 (* -> [^/]*)
                regex_pattern = pattern.replace(".", r"\.")
                regex_pattern = regex_pattern.replace("*", "[^/]*")
                regex_pattern = f"^{regex_pattern}$"
                if re.match(regex_pattern, file_path):
                    return True
                continue

            # **/ 패턴 처리 (glob 스타일)
            # glob 스타일 패턴을 정규식으로 변환
            # ** = 0개 이상의 디렉토리 (빈 문자열 포함)
            regex_pattern = pattern.replace("**", "__DOUBLESTAR__")
            regex_pattern = regex_pattern.replace(".", r"\.")
            regex_pattern = regex_pattern.replace("*", "[^/]*")
            # **/ 는 "(디렉토리/)* 또는 빈 문자열" 의미 -> (?:.*/)?
            regex_pattern = regex_pattern.replace("__DOUBLESTAR__/", "(?:.*/)?")
            # 끝에 남은 ** 처리 (하위 모든 경로)
            regex_pattern = regex_pattern.replace("__DOUBLESTAR__", ".*")
            regex_pattern = f"^{regex_pattern}$"
            if re.match(regex_pattern, file_path):
                return True
        return False

    def _get_domain_patterns(self, domain: str) -> List[str]:
        """도메인별 기본 패턴"""
        patterns = {
            "auth": ["**/auth/**", "**/login/**", "**/session/**", "**/*auth*"],
            "payment": ["**/payment/**", "**/checkout/**", "**/billing/**"],
            "api": ["**/api/**", "**/routes/**", "**/controllers/**", "**/handlers/**"],
            "database": ["**/models/**", "**/db/**", "**/migrations/**", "**/schema/**"],
            "test": ["**/tests/**", "**/test/**", "**/*_test.*", "**/*_spec.*"],
            "config": ["**/config/**", "**/*.config.*", "**/settings/**"],
            "frontend": ["**/components/**", "**/pages/**", "**/views/**", "**/*.css", "**/*.scss"],
            "backend": ["**/services/**", "**/workers/**", "**/jobs/**"],
        }
        return patterns.get(domain, [])

    def _get_default_forbidden(self) -> List[str]:
        """기본 금지 파일 목록"""
        return [".env", ".env.local", ".env.production", "credentials.json", "secrets.yaml"]

    def _is_delete_allowed(self, file_path: str, boundary: Boundary) -> bool:
        """삭제 작업 허용 여부"""
        # 삭제는 명시적으로 허용된 경우만 가능
        if "delete" not in boundary.allowed_actions:
            return False

        # 명시적으로 허용된 파일인지
        if file_path in boundary.allowed_files:
            return True

        # 예외 목록에 있는지
        if file_path in boundary.exceptions:
            return True

        return False

    def _validate_default_rules(self, file_path: str, action: ActionType) -> Dict[str, Any]:
        """기본 규칙으로 검증"""
        normalized_path = self._normalize_path(file_path)

        # 기본 보호 패턴 체크
        if self._matches_patterns(normalized_path, self.DEFAULT_PROTECTED_PATTERNS):
            return self._create_violation_result(
                file_path,
                action,
                ViolationType.PROTECTED_FILE,
                "File matches default protected patterns",
            )

        # 프로젝트 규칙 체크
        for rule in self._project_rules:
            if self._matches_patterns(normalized_path, [rule["pattern"]]):
                if rule["action"] == "block_always":
                    return self._create_violation_result(
                        file_path,
                        action,
                        ViolationType.PROTECTED_FILE,
                        rule.get("reason", "Blocked by project rules"),
                    )

        return {
            "allowed": True,
            "file_path": file_path,
            "action": action.value,
            "reason": "Allowed by default rules",
        }

    def _create_violation_result(
        self, file_path: str, action: ActionType, violation_type: ViolationType, reason: str
    ) -> Dict[str, Any]:
        """위반 결과 생성 및 기록"""
        violation = Violation(
            file_path=file_path,
            action=action,
            violation_type=violation_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )

        # 기록 저장
        self._record_violation(violation)

        return {
            "allowed": False,
            "violation": violation.to_dict(),
            "file_path": file_path,
            "action": action.value,
            "reason": reason,
            "requires_approval": True,
        }

    def _create_exception_result(self, file_path: str, action: ActionType) -> Dict[str, Any]:
        """예외 허용 결과"""
        return {
            "allowed": True,
            "exception": True,
            "file_path": file_path,
            "action": action.value,
            "reason": "Allowed by exception",
        }

    def _record_violation(self, violation: Violation):
        """위반 기록"""
        violations = self._load_violations()
        violations.append(violation.to_dict())

        # 최대 1000개만 유지
        if len(violations) > 1000:
            violations = violations[-1000:]

        self.violations_file.write_text(
            json.dumps(violations, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_violations(self) -> List[Dict]:
        """위반 기록 로드"""
        if self.violations_file.exists():
            try:
                return json.loads(self.violations_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return []

    def _save_current_boundary(self):
        """현재 경계 저장"""
        if self._current_boundary:
            boundary_file = self.boundary_dir / "current_boundary.json"
            boundary_file.write_text(
                json.dumps(self._current_boundary.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def _load_project_rules(self) -> List[Dict]:
        """프로젝트 규칙 로드 (.cortex/boundary_rules.yaml)"""
        rules_file = self.project_path / ".cortex" / "boundary_rules.yaml"

        if rules_file.exists():
            try:
                import yaml

                content = rules_file.read_text(encoding="utf-8")
                rules = yaml.safe_load(content)
                return rules.get("default_rules", [])
            except Exception:
                pass

        return []

    def _generate_default_protocol(self) -> str:
        """기본 경계 프로토콜"""
        return """[CONTEXT_BOUNDARY_PROTOCOL - DEFAULT]

No specific boundary is set. Apply these default rules:

## Default Protection
- NEVER modify: *.env*, credentials.*, secrets.*, .git/**
- ASK before modifying: config/*, migrations/*

## General Rules
1. Only modify files directly related to the current task
2. Do not "clean up" or "refactor" unrelated code
3. If unsure whether a file is in scope, ask first

[/CONTEXT_BOUNDARY_PROTOCOL]"""


def get_boundary_protection(
    project_id: str, project_path: Optional[str] = None
) -> BoundaryProtection:
    """BoundaryProtection 인스턴스 반환"""
    return BoundaryProtection(project_id=project_id, project_path=project_path)


# ============================================================================
# MCP Tool Interface Functions (6개)
# memory_manager.py에서 호출하는 모듈 레벨 함수들
# ============================================================================


def set_boundary(
    project_id: str,
    task: str,
    project_path: Optional[str] = None,
    allowed_files: Optional[List[str]] = None,
    allowed_patterns: Optional[List[str]] = None,
    allowed_actions: Optional[List[str]] = None,
    strict_mode: bool = False,
) -> Dict[str, Any]:
    """
    작업 경계 수동 설정 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        task: 현재 작업 설명
        project_path: 프로젝트 루트 경로 (선택)
        allowed_files: 허용된 파일 목록
        allowed_patterns: 허용된 파일 패턴
        allowed_actions: 허용된 작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)
        strict_mode: 엄격 모드 활성화

    Returns:
        경계 설정 결과
    """
    bp = get_boundary_protection(project_id, project_path)
    boundary = bp.set_boundary(
        task=task,
        files=allowed_files,  # 파라미터명 매핑
        patterns=allowed_patterns,  # 파라미터명 매핑
        actions=allowed_actions,  # 파라미터명 매핑
        strict_mode=strict_mode,
    )
    return boundary.to_dict()  # Dict로 변환


def infer_boundary(
    project_id: str,
    task: str,
    project_path: Optional[str] = None,
    recent_files: Optional[List[str]] = None,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """
    작업 경계 자동 추론 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        task: 현재 작업 설명
        project_path: 프로젝트 루트 경로 (선택)
        recent_files: 최근 작업한 파일 목록 (선택)
        context: 추가 맥락 정보 (선택)

    Returns:
        추론된 경계 설정
    """
    bp = get_boundary_protection(project_id, project_path)
    boundary = bp.infer_boundary(task=task, recent_files=recent_files or [], context=context or "")
    return boundary.to_dict()  # Dict로 변환


def validate_boundary_action(
    project_id: str, file_path: str, action: str, project_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    파일 작업 유효성 검증 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        file_path: 검증할 파일 경로
        action: 작업 유형 (READ, WRITE, CREATE, DELETE, MODIFY)
        project_path: 프로젝트 루트 경로 (선택)

    Returns:
        유효성 검증 결과
    """
    bp = get_boundary_protection(project_id, project_path)
    return bp.validate_action(file_path, action)


def get_boundary_protocol(project_id: str, project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    System Prompt용 경계 프로토콜 생성 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        project_path: 프로젝트 루트 경로 (선택)

    Returns:
        경계 프로토콜 문자열
    """
    bp = get_boundary_protection(project_id, project_path)
    protocol = bp.generate_boundary_protocol()
    return {"protocol": protocol, "has_boundary": bp.get_current_boundary() is not None}


def get_boundary_violations(project_id: str, project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    경계 위반 이력 조회 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        project_path: 프로젝트 루트 경로 (선택)

    Returns:
        위반 이력 목록
    """
    bp = get_boundary_protection(project_id, project_path)
    violations = bp.get_boundary_violations()
    return {"violations": violations, "count": len(violations)}


def clear_boundary(project_id: str, project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    경계 설정 초기화 (MCP 인터페이스)

    Args:
        project_id: 프로젝트 ID
        project_path: 프로젝트 루트 경로 (선택)

    Returns:
        초기화 결과
    """
    bp = get_boundary_protection(project_id, project_path)
    return bp.clear_boundary()
