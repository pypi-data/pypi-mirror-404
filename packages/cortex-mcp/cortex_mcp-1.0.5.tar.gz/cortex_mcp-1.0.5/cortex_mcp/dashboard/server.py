"""
Cortex MCP - Audit Dashboard Server
localhost:8080에서 실행되는 로컬 대시보드 서버

기능:
- 프로젝트/브랜치 계층 구조 시각화
- 맥락 사용 통계
- Reference History 추천 이력
- 실시간 로그 모니터링
"""

import json
import sys
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

# 프로젝트 루트를 path에 추가
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from config import config


class DashboardHandler(SimpleHTTPRequestHandler):
    """대시보드 HTTP 요청 핸들러"""

    def __init__(self, *args, **kwargs):
        # 템플릿 디렉토리를 기본 디렉토리로 설정
        self.directory = str(Path(__file__).parent / "templates")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """GET 요청 처리"""
        parsed = urlparse(self.path)
        path = parsed.path

        # API 엔드포인트
        if path.startswith("/api/"):
            self._handle_api(path, parse_qs(parsed.query))
        elif path.startswith("/static/"):
            self._serve_static(path)
        elif path == "/" or path == "/index.html":
            self._serve_dashboard()
        elif path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
        else:
            super().do_GET()

    def _handle_api(self, path: str, params: dict):
        """API 요청 처리"""
        try:
            if path == "/api/projects":
                data = self._get_projects()
            elif path == "/api/branches":
                project_id = params.get("project_id", [None])[0]
                data = self._get_branches(project_id)
            elif path == "/api/contexts":
                project_id = params.get("project_id", [None])[0]
                branch_id = params.get("branch_id", [None])[0]
                data = self._get_contexts(project_id, branch_id)
            elif path == "/api/stats":
                data = self._get_stats()
            elif path == "/api/reference-history":
                project_id = params.get("project_id", [None])[0]
                data = self._get_reference_history(project_id)
            elif path == "/api/logs":
                limit = int(params.get("limit", [50])[0])
                data = self._get_logs(limit)
            elif path == "/api/activity":
                project_id = params.get("project_id", [None])[0]
                data = self._get_activity(project_id)
            elif path == "/api/research-stats":
                data = self._get_research_stats()
            else:
                data = {"error": "Unknown API endpoint"}

            self._send_json(data)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def _send_json(self, data: dict, status: int = 200):
        """JSON 응답 전송"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))

    def _serve_dashboard(self):
        """메인 대시보드 페이지 제공"""
        template_path = Path(__file__).parent / "templates" / "index.html"

        if template_path.exists():
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(template_path.read_bytes())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Dashboard template not found</h1></body></html>")

    def _serve_static(self, path: str):
        """정적 파일 제공"""
        # 경로에서 /static/ 제거
        relative_path = path.replace("/static/", "", 1)
        static_dir = Path(__file__).parent / "static"
        file_path = static_dir / relative_path

        # 보안: 상위 디렉토리 접근 방지
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(static_dir.resolve())):
                self.send_error(403, "Access denied")
                return
        except ValueError:
            self.send_error(404, "File not found")
            return

        if file_path.exists() and file_path.is_file():
            # Content-Type 결정
            ext = file_path.suffix.lower()
            content_types = {
                ".css": "text/css",
                ".js": "application/javascript",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".svg": "image/svg+xml"
            }
            content_type = content_types.get(ext, "application/octet-stream")

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self.send_error(404, "File not found")

    def _get_projects(self) -> dict:
        """프로젝트 목록 조회"""
        projects = []
        memory_dir = config.memory_dir

        if memory_dir.exists():
            for project_dir in memory_dir.iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith("_"):
                    index_file = project_dir / "_index.json"
                    project_info = {
                        "id": project_dir.name,
                        "path": str(project_dir),
                        "created_at": datetime.fromtimestamp(
                            project_dir.stat().st_ctime
                        ).isoformat(),
                    }

                    if index_file.exists():
                        try:
                            with open(index_file, "r", encoding="utf-8") as f:
                                index_data = json.load(f)
                                project_info.update(
                                    {
                                        "branch_count": len(index_data.get("branches", {})),
                                        "active_branch": index_data.get("active_branch"),
                                    }
                                )
                        except:
                            pass

                    projects.append(project_info)

        return {"projects": projects, "count": len(projects)}

    def _get_branches(self, project_id: Optional[str]) -> dict:
        """브랜치 목록 조회"""
        if not project_id:
            return {"error": "project_id required"}

        branches = []
        project_dir = config.memory_dir / project_id
        index_file = project_dir / "_index.json"

        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    index_data = json.load(f)

                for branch_id, branch_data in index_data.get("branches", {}).items():
                    branches.append(
                        {
                            "id": branch_id,
                            "topic": branch_data.get("topic", ""),
                            "created_at": branch_data.get("created_at"),
                            "context_count": branch_data.get("context_count", 0),
                            "is_active": branch_id == index_data.get("active_branch"),
                        }
                    )
            except:
                pass

        return {"branches": branches, "count": len(branches)}

    def _get_contexts(self, project_id: Optional[str], branch_id: Optional[str]) -> dict:
        """컨텍스트 목록 조회"""
        if not project_id or not branch_id:
            return {"error": "project_id and branch_id required"}

        contexts = []
        contexts_dir = config.memory_dir / project_id / "contexts" / branch_id

        if contexts_dir.exists():
            for context_file in contexts_dir.glob("*.md"):
                try:
                    content = context_file.read_text(encoding="utf-8")
                    # YAML frontmatter 파싱
                    metadata = {}
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml

                            metadata = yaml.safe_load(parts[1]) or {}

                    contexts.append(
                        {
                            "id": context_file.stem,
                            "file": context_file.name,
                            "status": metadata.get("status", "unknown"),
                            "summary": metadata.get("summary", "")[:200],
                            "last_modified": datetime.fromtimestamp(
                                context_file.stat().st_mtime
                            ).isoformat(),
                            "size_bytes": context_file.stat().st_size,
                        }
                    )
                except:
                    pass

        return {"contexts": contexts, "count": len(contexts)}

    def _get_stats(self) -> dict:
        """전체 통계 조회"""
        stats = {
            "total_projects": 0,
            "total_branches": 0,
            "total_contexts": 0,
            "total_size_mb": 0,
            "memory_dir": str(config.memory_dir),
        }

        memory_dir = config.memory_dir
        if memory_dir.exists():
            total_size = 0
            for project_dir in memory_dir.iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith("_"):
                    stats["total_projects"] += 1

                    index_file = project_dir / "_index.json"
                    if index_file.exists():
                        try:
                            with open(index_file, "r", encoding="utf-8") as f:
                                index_data = json.load(f)
                                stats["total_branches"] += len(index_data.get("branches", {}))
                        except:
                            pass

                    contexts_dir = project_dir / "contexts"
                    if contexts_dir.exists():
                        for md_file in contexts_dir.rglob("*.md"):
                            stats["total_contexts"] += 1
                            total_size += md_file.stat().st_size

            stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)

        return stats

    def _get_reference_history(self, project_id: Optional[str]) -> dict:
        """Reference History 조회"""
        if not project_id:
            return {"error": "project_id required"}

        history_file = config.memory_dir / project_id / "_reference_history.json"

        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"error": "Failed to read reference history"}

        return {"co_references": {}, "feedback": {}}

    def _get_logs(self, limit: int = 50) -> dict:
        """최근 로그 조회"""
        logs = []
        log_file = config.logs_dir / "cortex.log"

        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    logs = [line.strip() for line in lines[-limit:] if line.strip()]
            except:
                pass

        # Audit 로그도 확인
        audit_file = config.logs_dir / "audit.json"
        audit_entries = []

        if audit_file.exists():
            try:
                with open(audit_file, "r", encoding="utf-8") as f:
                    audit_data = json.load(f)
                    audit_entries = audit_data.get("entries", [])[-limit:]
            except:
                pass

        return {
            "logs": logs,
            "audit_entries": audit_entries,
            "log_file": str(log_file),
        }

    def _get_activity(self, project_id: Optional[str]) -> dict:
        """실시간 활동 모니터링"""
        if not project_id:
            return {"error": "project_id required"}

        sessions = []
        sessions_dir = config.base_dir / "sessions" / project_id

        if sessions_dir.exists():
            for session_file in sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, "r", encoding="utf-8") as f:
                        session_data = json.load(f)
                        sessions.append(
                            {
                                "session_id": session_data.get("session_id", "unknown"),
                                "branch_id": session_data.get("branch_id", "unknown"),
                                "status": session_data.get("status", "unknown"),
                                "pid": session_data.get("pid", 0),
                                "last_activity": session_data.get("last_activity", "unknown"),
                                "contexts_created": len(session_data.get("contexts_created", [])),
                                "merge_count": session_data.get("merge_count", 0),
                            }
                        )
                except:
                    pass

        active_sessions = [s for s in sessions if s["status"] == "active"]

        return {
            "total_sessions": len(sessions),
            "active_sessions": len(active_sessions),
            "sessions": sessions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_research_stats(self) -> dict:
        """AlphaLogger 연구 데이터 통계 조회 (논문용)"""
        stats_file = config.logs_dir / "alpha_test" / "stats.json"

        if not stats_file.exists():
            return {
                "error": "No research data available",
                "stats_file": str(stats_file),
                "modules": {},
            }

        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            modules = data.get("modules", {})

            # 각 모듈별 통계 계산
            enriched_modules = {}
            total_calls = 0
            total_errors = 0

            for module_name, module_data in modules.items():
                calls = module_data.get("total_calls", 0)
                success = module_data.get("success_count", 0)
                errors = module_data.get("error_count", 0)
                latency = module_data.get("total_latency_ms", 0)

                total_calls += calls
                total_errors += errors

                # 평균 latency 계산
                avg_latency = round(latency / calls, 2) if calls > 0 else 0

                # 성공률 계산
                success_rate = round((success / calls * 100), 2) if calls > 0 else 0

                enriched_modules[module_name] = {
                    "total_calls": calls,
                    "success_count": success,
                    "error_count": errors,
                    "success_rate": success_rate,
                    "total_latency_ms": latency,
                    "avg_latency_ms": avg_latency,
                }

            # 전체 통계
            overall_success_rate = (
                round(((total_calls - total_errors) / total_calls * 100), 2)
                if total_calls > 0
                else 0
            )

            return {
                "session_start": data.get("session_start", "unknown"),
                "modules": enriched_modules,
                "summary": {
                    "total_calls": total_calls,
                    "total_errors": total_errors,
                    "overall_success_rate": overall_success_rate,
                    "modules_count": len(modules),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "error": f"Failed to read research stats: {str(e)}",
                "stats_file": str(stats_file),
            }

    def log_message(self, format, *args):
        """로그 메시지 포맷 (기본 로깅 비활성화)"""
        pass  # 조용한 서버


class DashboardServer:
    """대시보드 서버 클래스"""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, open_browser: bool = True) -> dict:
        """서버 시작"""
        if self._running:
            return {"success": False, "error": "Server already running", "url": self.get_url()}

        try:
            self.server = HTTPServer((self.host, self.port), DashboardHandler)
            self._running = True

            # 백그라운드 스레드에서 서버 실행
            self.thread = threading.Thread(target=self._run_server, daemon=True)
            self.thread.start()

            url = self.get_url()

            if open_browser:
                webbrowser.open(url)

            return {"success": True, "url": url, "message": f"Dashboard server started at {url}"}
        except Exception as e:
            self._running = False
            return {"success": False, "error": str(e)}

    def _run_server(self):
        """서버 실행 (백그라운드)"""
        if self.server:
            self.server.serve_forever()

    def stop(self) -> dict:
        """서버 중지"""
        if not self._running:
            return {"success": False, "error": "Server not running"}

        try:
            if self.server:
                self.server.shutdown()
                self.server = None
            self._running = False
            return {"success": True, "message": "Server stopped"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_url(self) -> str:
        """대시보드 URL 반환"""
        return f"http://{self.host}:{self.port}"

    @property
    def is_running(self) -> bool:
        """서버 실행 상태"""
        return self._running


# 전역 서버 인스턴스
_dashboard_server: Optional[DashboardServer] = None


def get_dashboard_server() -> DashboardServer:
    """대시보드 서버 싱글톤"""
    global _dashboard_server
    if _dashboard_server is None:
        _dashboard_server = DashboardServer()
    return _dashboard_server


def start_dashboard(open_browser: bool = True) -> dict:
    """대시보드 시작 (편의 함수)"""
    return get_dashboard_server().start(open_browser)


def get_dashboard_url(
    start_if_not_running: bool = True, open_browser: bool = False
) -> Dict[str, Any]:
    """
    Audit Dashboard URL 반환 (MCP 인터페이스)

    Args:
        start_if_not_running: 서버가 실행 중이 아니면 자동 시작
        open_browser: 브라우저 자동 열기

    Returns:
        Dashboard URL 및 상태
    """
    try:
        server = get_dashboard_server()

        # 서버가 실행 중이 아니고 자동 시작이 활성화된 경우
        if not server.is_running and start_if_not_running:
            result = server.start(open_browser=open_browser)
            return result

        # 서버가 이미 실행 중인 경우
        if server.is_running:
            url = server.get_url()
            return {
                "success": True,
                "url": url,
                "running": True,
                "message": f"Dashboard is already running at {url}",
            }

        # 서버가 실행 중이 아니고 자동 시작이 비활성화된 경우
        return {
            "success": False,
            "running": False,
            "message": "Dashboard server is not running. Use start_if_not_running=True to start it.",
        }
    except Exception as e:
        return {
            "success": False,
            "running": False,
            "error": str(e),
            "message": f"Dashboard URL 조회 실패: {str(e)}",
        }


if __name__ == "__main__":
    print("Starting Cortex Dashboard Server...")
    result = start_dashboard(open_browser=True)
    print(f"Result: {result}")

    if result["success"]:
        print(f"Dashboard running at: {result['url']}")
        print("Press Ctrl+C to stop...")
        try:
            # 메인 스레드 유지
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            get_dashboard_server().stop()
