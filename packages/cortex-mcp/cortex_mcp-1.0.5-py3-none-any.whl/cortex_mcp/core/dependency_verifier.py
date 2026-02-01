"""
의존성 검증 시스템 (Dependency Verification System)

Cortex Phase 9.x: 의존성 Claim 검증
LLM이 "라이브러리를 추가했다"고 주장할 때, 실제로 추가되었는지 검증합니다.

핵심 기능:
- 다양한 언어/패키지 매니저 지원 (Python, Node.js, Go, Rust 등)
- 버전 지정자 파싱 및 검증
- 선택적 의존성 (optional, dev) 처리
- 잘못된 파일에 추가된 경우 감지
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# TOML 파서 (Python 3.11+ 내장, 이전 버전은 tomli 사용)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None
        logger.warning("tomllib/tomli not available - TOML parsing disabled")


@dataclass
class DependencyInfo:
    """의존성 정보"""
    name: str
    version: Optional[str] = None
    version_operator: str = ""
    source_file: str = ""
    section: str = "main"  # main, dev, optional
    extras: List[str] = field(default_factory=list)


@dataclass
class DependencyClaimResult:
    """의존성 Claim 검증 결과"""
    verified: bool
    package_name: str
    claimed_version: Optional[str]
    actual_version: Optional[str]
    found_in_file: Optional[str]
    expected_files: List[str]
    reason: str
    confidence: float


class DependencyVerifier:
    """
    의존성 Claim 검증 클래스

    지원 파일 형식:
    - Python: requirements.txt, pyproject.toml, Pipfile
    - Node.js: package.json
    - Go: go.mod
    - Rust: Cargo.toml
    - Ruby: Gemfile
    - Java: pom.xml, build.gradle
    """

    DEPENDENCY_FILES = {
        # Python
        "requirements.txt": "python",
        "requirements-dev.txt": "python",
        "requirements-test.txt": "python",
        "pyproject.toml": "python",
        "Pipfile": "python",
        "setup.py": "python",
        # Node.js
        "package.json": "nodejs",
        # Go
        "go.mod": "go",
        # Rust
        "Cargo.toml": "rust",
        # Ruby
        "Gemfile": "ruby",
        # Java
        "pom.xml": "java",
        "build.gradle": "java",
        "build.gradle.kts": "java",
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self._dependency_cache: Dict[str, List[DependencyInfo]] = {}

    def verify_dependency_claim(
        self,
        package_name: str,
        claimed_version: Optional[str] = None,
        expected_ecosystem: Optional[str] = None,
        context_history: Optional[Dict] = None,
    ) -> DependencyClaimResult:
        """
        의존성 추가 Claim 검증

        Args:
            package_name: 패키지명 (예: "requests", "lodash")
            claimed_version: 주장된 버전 (예: ">=2.0.0")
            expected_ecosystem: 예상 생태계 ("python", "nodejs" 등)
            context_history: Context 이력 (files_modified 포함)

        Returns:
            DependencyClaimResult
        """
        logger.info(f"[DEP_VERIFY] Verifying dependency claim: {package_name}")

        # 1. 프로젝트에서 의존성 파일 찾기
        dep_files = self._find_dependency_files(expected_ecosystem)

        if not dep_files:
            logger.warning(f"[DEP_VERIFY] No dependency files found for ecosystem: {expected_ecosystem}")
            return DependencyClaimResult(
                verified=False,
                package_name=package_name,
                claimed_version=claimed_version,
                actual_version=None,
                found_in_file=None,
                expected_files=[],
                reason="no_dependency_files_found",
                confidence=0.0,
            )

        # 2. 각 파일에서 패키지 검색
        found_deps: List[Tuple[str, DependencyInfo]] = []

        for file_path in dep_files:
            deps = self._parse_dependency_file(file_path)
            for dep in deps:
                if self._package_name_matches(dep.name, package_name):
                    found_deps.append((str(file_path), dep))
                    logger.info(f"[DEP_VERIFY] Found '{package_name}' in {file_path}")

        if not found_deps:
            logger.warning(f"[DEP_VERIFY] Package '{package_name}' not found in any dependency file")
            return DependencyClaimResult(
                verified=False,
                package_name=package_name,
                claimed_version=claimed_version,
                actual_version=None,
                found_in_file=None,
                expected_files=[str(f) for f in dep_files],
                reason="package_not_found",
                confidence=0.0,
            )

        # 3. 버전 검증 (있는 경우)
        best_match = found_deps[0]
        found_file, found_dep = best_match

        if claimed_version:
            version_match = self._version_matches(
                claimed_version,
                found_dep.version,
                found_dep.version_operator
            )
            if not version_match:
                actual_ver = f"{found_dep.version_operator}{found_dep.version}" if found_dep.version else None
                logger.warning(f"[DEP_VERIFY] Version mismatch: claimed={claimed_version}, actual={actual_ver}")
                return DependencyClaimResult(
                    verified=False,
                    package_name=package_name,
                    claimed_version=claimed_version,
                    actual_version=actual_ver,
                    found_in_file=found_file,
                    expected_files=[str(f) for f in dep_files],
                    reason="version_mismatch",
                    confidence=0.3,
                )

        # 4. 검증 성공
        actual_ver = f"{found_dep.version_operator}{found_dep.version}" if found_dep.version else "any"
        logger.info(f"[DEP_VERIFY] Dependency verified: {package_name} ({actual_ver}) in {found_file}")

        return DependencyClaimResult(
            verified=True,
            package_name=package_name,
            claimed_version=claimed_version,
            actual_version=actual_ver,
            found_in_file=found_file,
            expected_files=[str(f) for f in dep_files],
            reason="dependency_verified",
            confidence=1.0,
        )

    def _find_dependency_files(self, ecosystem: Optional[str] = None) -> List[Path]:
        """의존성 파일 찾기"""
        found = []

        for filename, eco in self.DEPENDENCY_FILES.items():
            if ecosystem and eco != ecosystem:
                continue

            # 프로젝트 루트에서 찾기
            file_path = self.project_path / filename
            if file_path.exists():
                found.append(file_path)

            # 하위 디렉토리에서도 찾기 (1단계까지만)
            for subdir in self.project_path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    subfile = subdir / filename
                    if subfile.exists():
                        found.append(subfile)

        return found

    def _parse_dependency_file(self, file_path: Path) -> List[DependencyInfo]:
        """파일 형식에 따라 파싱"""
        # 캐시 확인
        cache_key = str(file_path)
        if cache_key in self._dependency_cache:
            return self._dependency_cache[cache_key]

        filename = file_path.name.lower()
        deps = []

        try:
            if filename.startswith("requirements") and filename.endswith(".txt"):
                deps = self._parse_requirements_txt(file_path)
            elif filename == "pyproject.toml":
                deps = self._parse_pyproject_toml(file_path)
            elif filename == "pipfile":
                deps = self._parse_pipfile(file_path)
            elif filename == "package.json":
                deps = self._parse_package_json(file_path)
            elif filename == "go.mod":
                deps = self._parse_go_mod(file_path)
            elif filename == "cargo.toml":
                deps = self._parse_cargo_toml(file_path)
            elif filename == "gemfile":
                deps = self._parse_gemfile(file_path)
        except Exception as e:
            logger.error(f"[DEP_VERIFY] Error parsing {file_path}: {e}")

        # 캐시 저장
        self._dependency_cache[cache_key] = deps
        return deps

    def _parse_requirements_txt(self, file_path: Path) -> List[DependencyInfo]:
        """requirements.txt 파싱"""
        deps = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        # 패턴: package_name[extras]operator version
        pattern = r'^([a-zA-Z0-9_-]+)(\[[^\]]+\])?\s*(==|>=|<=|~=|!=|>|<|@)?\s*(.+)?$'

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue

            match = re.match(pattern, line)
            if match:
                name = match.group(1)
                extras_str = match.group(2)
                operator = match.group(3) or ""
                version = match.group(4) or ""

                extras = []
                if extras_str:
                    extras = [e.strip() for e in extras_str[1:-1].split(',')]

                deps.append(DependencyInfo(
                    name=name.lower(),
                    version=version.strip() if version else None,
                    version_operator=operator,
                    source_file=str(file_path),
                    extras=extras,
                ))

        return deps

    def _parse_pyproject_toml(self, file_path: Path) -> List[DependencyInfo]:
        """pyproject.toml 파싱"""
        if tomllib is None:
            logger.warning("[DEP_VERIFY] TOML parser not available")
            return []

        deps = []
        content = file_path.read_text(encoding='utf-8')

        try:
            data = tomllib.loads(content)
        except Exception as e:
            logger.error(f"[DEP_VERIFY] TOML parse error: {e}")
            return deps

        # [project] dependencies
        project = data.get("project", {})
        for dep_str in project.get("dependencies", []):
            dep_info = self._parse_pep508_dependency(dep_str)
            if dep_info:
                dep_info.source_file = str(file_path)
                dep_info.section = "main"
                deps.append(dep_info)

        # [project.optional-dependencies]
        for section_name, section_deps in project.get("optional-dependencies", {}).items():
            for dep_str in section_deps:
                dep_info = self._parse_pep508_dependency(dep_str)
                if dep_info:
                    dep_info.source_file = str(file_path)
                    dep_info.section = section_name
                    deps.append(dep_info)

        # [tool.poetry.dependencies] (Poetry 지원)
        poetry = data.get("tool", {}).get("poetry", {})
        for name, value in poetry.get("dependencies", {}).items():
            if name == "python":
                continue
            version = value if isinstance(value, str) else value.get("version", "") if isinstance(value, dict) else ""
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version.lstrip("^~>=<") if version else None,
                source_file=str(file_path),
                section="main",
            ))

        return deps

    def _parse_pep508_dependency(self, dep_str: str) -> Optional[DependencyInfo]:
        """PEP 508 형식 의존성 파싱"""
        # 예: "mcp>=1.0.0,<2.0.0", "chromadb>=1.0.0", "numpy==1.26.4"
        pattern = r'^([a-zA-Z0-9_-]+)(\[[^\]]+\])?\s*(==|>=|<=|~=|!=|>|<)?\s*([^\s,;]+)?'

        match = re.match(pattern, dep_str.strip())
        if match:
            extras = []
            if match.group(2):
                extras = [e.strip() for e in match.group(2)[1:-1].split(',')]

            return DependencyInfo(
                name=match.group(1).lower(),
                version=match.group(4) if match.group(4) else None,
                version_operator=match.group(3) or "",
                extras=extras,
            )
        return None

    def _parse_pipfile(self, file_path: Path) -> List[DependencyInfo]:
        """Pipfile 파싱"""
        if tomllib is None:
            return []

        deps = []
        content = file_path.read_text(encoding='utf-8')

        try:
            data = tomllib.loads(content)
        except Exception:
            return deps

        # [packages]
        for name, value in data.get("packages", {}).items():
            version = value if isinstance(value, str) else value.get("version", "*") if isinstance(value, dict) else "*"
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version.lstrip("~>=<*") if version and version != "*" else None,
                source_file=str(file_path),
                section="main",
            ))

        # [dev-packages]
        for name, value in data.get("dev-packages", {}).items():
            version = value if isinstance(value, str) else value.get("version", "*") if isinstance(value, dict) else "*"
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version.lstrip("~>=<*") if version and version != "*" else None,
                source_file=str(file_path),
                section="dev",
            ))

        return deps

    def _parse_package_json(self, file_path: Path) -> List[DependencyInfo]:
        """package.json 파싱"""
        deps = []
        content = file_path.read_text(encoding='utf-8')

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return deps

        # dependencies
        for name, version in data.get("dependencies", {}).items():
            version_op, version_num = self._parse_npm_version(version)
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version_num,
                version_operator=version_op,
                source_file=str(file_path),
                section="main",
            ))

        # devDependencies
        for name, version in data.get("devDependencies", {}).items():
            version_op, version_num = self._parse_npm_version(version)
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version_num,
                version_operator=version_op,
                source_file=str(file_path),
                section="dev",
            ))

        # peerDependencies
        for name, version in data.get("peerDependencies", {}).items():
            version_op, version_num = self._parse_npm_version(version)
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version_num,
                version_operator=version_op,
                source_file=str(file_path),
                section="peer",
            ))

        return deps

    def _parse_npm_version(self, version: str) -> Tuple[str, Optional[str]]:
        """npm 버전 문자열 파싱"""
        version = version.strip()

        if version.startswith("^"):
            return ("^", version[1:])
        elif version.startswith("~"):
            return ("~", version[1:])
        elif version.startswith(">="):
            return (">=", version[2:])
        elif version.startswith(">"):
            return (">", version[1:])
        elif version.startswith("<="):
            return ("<=", version[2:])
        elif version.startswith("<"):
            return ("<", version[1:])
        elif version.startswith("="):
            return ("=", version[1:])
        elif version == "*" or version == "latest":
            return ("", None)
        else:
            return ("", version)

    def _parse_go_mod(self, file_path: Path) -> List[DependencyInfo]:
        """go.mod 파싱"""
        deps = []
        content = file_path.read_text(encoding='utf-8')

        in_require_block = False

        for line in content.splitlines():
            line = line.strip()

            if line.startswith("require ("):
                in_require_block = True
                continue
            elif line == ")":
                in_require_block = False
                continue

            if in_require_block or line.startswith("require "):
                # 예: "github.com/pkg/errors v0.9.1"
                parts = line.replace("require ", "").strip().split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1].lstrip("v")
                    deps.append(DependencyInfo(
                        name=name.lower(),
                        version=version,
                        version_operator="",
                        source_file=str(file_path),
                    ))

        return deps

    def _parse_cargo_toml(self, file_path: Path) -> List[DependencyInfo]:
        """Cargo.toml 파싱"""
        if tomllib is None:
            return []

        deps = []
        content = file_path.read_text(encoding='utf-8')

        try:
            data = tomllib.loads(content)
        except Exception:
            return deps

        # [dependencies]
        for name, value in data.get("dependencies", {}).items():
            if isinstance(value, str):
                version_op, version_num = self._parse_cargo_version(value)
            elif isinstance(value, dict):
                version = value.get("version", "")
                version_op, version_num = self._parse_cargo_version(version)
            else:
                continue

            deps.append(DependencyInfo(
                name=name.lower(),
                version=version_num,
                version_operator=version_op,
                source_file=str(file_path),
                section="main",
            ))

        # [dev-dependencies]
        for name, value in data.get("dev-dependencies", {}).items():
            if isinstance(value, str):
                version = value
            elif isinstance(value, dict):
                version = value.get("version", "")
            else:
                continue

            version_op, version_num = self._parse_cargo_version(version)
            deps.append(DependencyInfo(
                name=name.lower(),
                version=version_num,
                version_operator=version_op,
                source_file=str(file_path),
                section="dev",
            ))

        return deps

    def _parse_cargo_version(self, version: str) -> Tuple[str, Optional[str]]:
        """Cargo 버전 문자열 파싱"""
        version = version.strip()

        if version.startswith("^"):
            return ("^", version[1:])
        elif version.startswith("~"):
            return ("~", version[1:])
        elif version.startswith(">="):
            return (">=", version[2:])
        elif version.startswith("="):
            return ("=", version[1:])
        elif version == "*":
            return ("", None)
        else:
            return ("", version if version else None)

    def _parse_gemfile(self, file_path: Path) -> List[DependencyInfo]:
        """Gemfile 파싱 (기본)"""
        deps = []
        content = file_path.read_text(encoding='utf-8', errors='ignore')

        # gem 'name', 'version' 또는 gem 'name'
        pattern = r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?"

        for match in re.finditer(pattern, content):
            name = match.group(1)
            version = match.group(2) if match.group(2) else None

            deps.append(DependencyInfo(
                name=name.lower(),
                version=version.lstrip("~>=<") if version else None,
                source_file=str(file_path),
            ))

        return deps

    def _package_name_matches(self, dep_name: str, claim_name: str) -> bool:
        """패키지명 매칭 (대소문자 무시, 하이픈/언더스코어 정규화)"""
        def normalize(name: str) -> str:
            return name.lower().replace("-", "_").replace(".", "_")

        return normalize(dep_name) == normalize(claim_name)

    def _version_matches(
        self,
        claimed: str,
        actual: Optional[str],
        operator: str
    ) -> bool:
        """버전 매칭 검증 (간단한 비교)"""
        if not actual:
            return True  # 버전 없으면 any로 간주

        # 간단한 버전 비교 (정확한 비교는 packaging 라이브러리 필요)
        claimed_clean = claimed.lstrip(">=<~^!=")
        actual_clean = actual.lstrip(">=<~^!=")

        # 정확히 같은 버전이면 OK
        if claimed_clean == actual_clean:
            return True

        # 메이저 버전만 비교 (loose matching)
        claimed_major = claimed_clean.split('.')[0] if '.' in claimed_clean else claimed_clean
        actual_major = actual_clean.split('.')[0] if '.' in actual_clean else actual_clean

        if claimed_major == actual_major:
            return True

        return False

    def clear_cache(self):
        """의존성 캐시 초기화"""
        self._dependency_cache.clear()


# 싱글톤 인스턴스 관리
_global_verifier: Dict[str, DependencyVerifier] = {}


def get_dependency_verifier(project_path: str) -> DependencyVerifier:
    """전역 DependencyVerifier 인스턴스 반환"""
    global _global_verifier

    if project_path not in _global_verifier:
        _global_verifier[project_path] = DependencyVerifier(project_path)

    return _global_verifier[project_path]


def clear_dependency_verifier_cache():
    """전역 캐시 초기화"""
    global _global_verifier
    _global_verifier.clear()
