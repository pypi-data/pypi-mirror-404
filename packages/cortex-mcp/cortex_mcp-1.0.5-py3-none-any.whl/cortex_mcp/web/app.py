"""
Cortex MCP - Web Application
Flask 기반 사용자/관리자 대시보드 (수동 승인 방식)
"""

import logging
import os
import sys
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가 (import 오류 방지)
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import get_github_oauth
from web_config import get_database as get_db

# v3: 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# 환경 변수 검증
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    print("[WARNING] GitHub OAuth 환경 변수가 설정되지 않았습니다.")
    print("GITHUB_CLIENT_ID와 GITHUB_CLIENT_SECRET를 설정해주세요.")

# Admin 자격증명 (환경 변수)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cortex_sy0726!")

if ADMIN_PASSWORD == "cortex_sy0726!":
    print("[WARNING] Admin 비밀번호가 기본값으로 설정되어 있습니다.")
    print("보안을 위해 ADMIN_PASSWORD 환경 변수를 설정해주세요.")


# 데코레이터: 로그인 필요
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)

    return decorated_function


# 데코레이터: 승인된 사용자만
def approved_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))

        db = get_db()
        user = db.get_user_by_github_id(session["github_id"])

        if not user:
            return "Error: User not found", 404

        if user["approval_status"] != "approved":
            return redirect(url_for("pending_page"))

        return f(*args, **kwargs)

    return decorated_function


# 데코레이터: 관리자 권한 필요 (별도 인증 시스템)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin 세션 체크 (User 세션과 완전 분리)
        if "admin_authenticated" not in session or not session["admin_authenticated"]:
            return redirect(url_for("admin_login_page"))

        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    """랜딩 페이지 - Cortex MCP 소개"""
    return render_template("landing.html")


@app.route("/login")
def login_page():
    """로그인 페이지"""
    return render_template("login.html")


@app.route("/what-is-cortex")
def what_is_cortex():
    """What is Cortex 철학 페이지"""
    return render_template("what_is_cortex.html")


@app.route("/how-it-works")
def how_it_works():
    """How It Works 페이지"""
    return render_template("how_it_works.html")


@app.route("/features")
def features():
    """Features 페이지 - /how-it-works로 리다이렉트"""
    return redirect(url_for("how_it_works"))


@app.route("/trust")
def trust():
    """Hallucination & Trust 페이지 - /how-it-works로 리다이렉트"""
    return redirect(url_for("how_it_works"))


@app.route("/benchmarks")
def benchmarks():
    """Proof & Benchmarks 페이지"""
    return render_template("benchmarks.html")


@app.route("/guide")
def guide():
    """Getting Started Guide 페이지"""
    return render_template("guide.html")


@app.route("/pricing")
def pricing():
    """Pricing 페이지 (Open Beta 전까지 hidden)"""
    return render_template("pricing.html")


@app.route("/terms")
def terms():
    """서비스 이용약관 페이지"""
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    """개인정보 처리방침 페이지"""
    return render_template("privacy.html")


@app.route("/cookies")
def cookies():
    """쿠키 정책 페이지"""
    return render_template("cookies.html")


@app.route("/mypage")
@approved_required
def mypage():
    """My Project Overview 페이지 (승인된 사용자만)"""
    db = get_db()

    # 현재 로그인한 사용자 정보 가져오기
    user = db.get_user_by_github_id(session["github_id"])

    if not user:
        return "Error: User not found", 404

    user_id = user["id"]

    # 사용자 통계 가져오기
    user_stats = db.get_user_stats(user_id)

    # 연구 메트릭 가져오기 (최근 30일)
    all_metrics = db.get_research_metrics()
    user_metrics = [m for m in all_metrics if m["user_id"] == user_id]

    # Context Stability Index 계산 (최근 10개 평균)
    recent_stability = [m["context_stability_score"] for m in user_metrics[-10:] if m["context_stability_score"]]
    context_stability = round(sum(recent_stability) / len(recent_stability) * 100, 0) if recent_stability else 0

    # Grounding Confidence 계산 (최근 10개 평균)
    recent_intervention = [m["intervention_precision"] for m in user_metrics[-10:] if m["intervention_precision"]]
    grounding_confidence = round(sum(recent_intervention) / len(recent_intervention) * 100, 0) if recent_intervention else 0

    # Hallucination Alerts 계산 (최근 30일간 낮은 stability score 개수)
    hallucination_alerts = sum(1 for m in user_metrics if m["context_stability_score"] and m["context_stability_score"] < 0.7)

    # Total References 계산 (user_stats의 total_calls 합계)
    total_references = sum(stat["total_calls"] for stat in user_stats)

    # 사용자 라이센스 정보
    license_info = {
        "license_key": user["license_key"],
        "license_type": user["license_type"] or "Free",
        "email": user["email"],
        "github_login": user["github_login"],
        "avatar_url": user["avatar_url"],
    }

    return render_template(
        "mypage.html",
        user=license_info,
        context_stability=int(context_stability),
        grounding_confidence=int(grounding_confidence),
        hallucination_alerts=hallucination_alerts,
        total_references=total_references,
    )


@app.route("/validation")
def validation():
    """Validation & Results 페이지"""
    return render_template("validation.html")


@app.route("/installation")
def installation():
    """Installation 페이지"""
    return render_template("installation.html")


@app.route("/auth/github")
def github_login():
    """GitHub OAuth 로그인 시작"""
    github_oauth = get_github_oauth()
    auth_url = github_oauth.get_authorization_url()
    return redirect(auth_url)


@app.route("/auth/github/callback")
def github_callback():
    """GitHub OAuth 콜백"""
    code = request.args.get("code")

    if not code:
        return "Error: No authorization code received", 400

    # 1. GitHub OAuth 인증
    github_oauth = get_github_oauth()
    user_info = github_oauth.authenticate(code)

    if not user_info:
        return "Error: Failed to authenticate with GitHub", 400

    # 2. DB에서 사용자 조회 또는 생성
    db = get_db()
    user = db.get_user_by_github_id(user_info["github_id"])

    if not user:
        # 신규 사용자 생성 (승인 대기 상태)
        result = db.create_user(
            github_id=user_info["github_id"],
            github_login=user_info["github_login"],
            email=user_info.get("email"),
            avatar_url=user_info.get("avatar_url"),
        )

        if not result["success"]:
            return f"Error: {result.get('error', 'Unknown error')}", 500

        user_id = result["user_id"]
        approval_status = result["approval_status"]

        # 신규 가입 메시지
        print(f"[NEW USER] {user_info['github_login']} (Status: {approval_status})")
    else:
        user_id = user["id"]
        approval_status = user["approval_status"]

        # 마지막 로그인 시간 업데이트
        db.update_last_login(user_id)

    # 3. 세션 생성
    session["user_id"] = user_id
    session["github_id"] = user_info["github_id"]
    session["github_login"] = user_info["github_login"]
    session["avatar_url"] = user_info.get("avatar_url")
    session["approval_status"] = approval_status

    # 4. 승인 상태에 따라 리다이렉트
    if approval_status == "approved":
        return redirect(url_for("dashboard"))
    elif approval_status == "rejected":
        return redirect(url_for("pending_page"))  # pending.html에서 rejected 처리
    else:  # pending
        return redirect(url_for("pending_page"))


@app.route("/pending")
@login_required
def pending_page():
    """승인 대기 페이지"""
    db = get_db()
    user = db.get_user_by_github_id(session["github_id"])

    if not user:
        return "Error: User not found", 404

    # 이미 승인된 경우 대시보드로 리다이렉트
    if user["approval_status"] == "approved":
        return redirect(url_for("dashboard"))

    return render_template("pending.html", user=user)


@app.route("/dashboard")
@approved_required
def dashboard():
    """사용자 대시보드 (승인된 사용자만)"""
    db = get_db()

    # 사용자 정보
    user = db.get_user_by_github_id(session["github_id"])

    if not user:
        return "Error: User not found", 404

    # 사용자 통계
    stats = db.get_user_stats(user["id"])

    # 통계 요약 계산
    total_calls = sum(s["total_calls"] for s in stats)
    total_errors = sum(s["error_count"] for s in stats)
    success_rate = ((total_calls - total_errors) / total_calls * 100) if total_calls > 0 else 0

    return render_template(
        "dashboard.html",
        user=user,
        stats=stats,
        total_calls=total_calls,
        total_errors=total_errors,
        success_rate=round(success_rate, 2),
    )


@app.route("/admin", strict_slashes=False)
@admin_required
def admin_dashboard():
    """관리자 대시보드"""
    db = get_db()

    # 승인 대기 목록
    pending_users = db.get_pending_users()

    # 전체 사용자 목록
    all_users = db.list_all_users()

    # 승인된 사용자만 필터
    approved_users = [u for u in all_users if u["approval_status"] == "approved"]

    # 거절된 사용자 필터
    rejected_users = [u for u in all_users if u["approval_status"] == "rejected"]

    # 전체 통계 계산
    total_users = len(all_users)
    approved_count = len(approved_users)
    pending_count = len(pending_users)
    rejected_count = len(rejected_users)

    # 라이센스 타입별 통계 (승인된 사용자만)
    license_stats = {}
    for user in approved_users:
        license_type = user["license_type"] or "none"
        license_stats[license_type] = license_stats.get(license_type, 0) + 1

    # ========== M&A 비즈니스 지표 계산 ==========
    dau = db.calculate_dau()
    mau = db.calculate_mau()
    retention_d7 = db.calculate_retention_d7()
    active_projects = db.calculate_active_projects()
    avg_session_duration = db.calculate_avg_session_duration()

    # ========== 제품 품질 지표 계산 ==========
    hallucination_success_rate = db.calculate_hallucination_detection_rate()
    reference_accuracy = db.calculate_reference_accuracy()
    context_stability = db.calculate_context_stability()
    rag_search_recall = db.calculate_rag_search_recall()
    automation_success_rate = db.calculate_automation_success_rate()

    # 퍼센트 형식으로 변환 (0.0~1.0 → 0~100)
    hallucination_success_rate_pct = round(hallucination_success_rate * 100, 1)
    reference_accuracy_pct = round(reference_accuracy * 100, 1)
    context_stability_pct = round(context_stability * 100, 1)
    rag_search_recall_pct = round(rag_search_recall * 100, 1)
    automation_success_rate_pct = round(automation_success_rate * 100, 1)
    retention_d7_pct = round(retention_d7 * 100, 1)

    return render_template(
        "admin_dashboard.html",
        pending_users=pending_users,
        approved_users=approved_users,
        rejected_users=rejected_users,
        total_users=total_users,
        approved_count=approved_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        license_stats=license_stats,
        # M&A 비즈니스 지표
        dau=dau,
        mau=mau,
        retention_d7=retention_d7_pct,
        active_projects=active_projects,
        avg_session_duration=round(avg_session_duration, 1),
        # 제품 품질 지표
        hallucination_success_rate=hallucination_success_rate_pct,
        reference_accuracy=reference_accuracy_pct,
        context_stability=context_stability_pct,
        rag_search_recall=rag_search_recall_pct,
        automation_success_rate=automation_success_rate_pct,
    )


@app.route("/admin/approve/<int:user_id>", methods=["POST"])
@admin_required
def approve_user(user_id):
    """사용자 승인"""
    db = get_db()

    # 라이센스 타입 선택 (기본: closed_beta)
    license_type = request.form.get("license_type", "closed_beta")

    result = db.approve_user(user_id, license_type)

    if result["success"]:
        print(f"[APPROVED] User ID {user_id} - License: {result['license_key']}")
        return redirect(url_for("admin_dashboard"))
    else:
        return f"Error: {result.get('error', 'Unknown error')}", 500


@app.route("/admin/reject/<int:user_id>", methods=["POST"])
@admin_required
def reject_user(user_id):
    """사용자 승인 거부"""
    db = get_db()
    result = db.reject_user(user_id)

    if result["success"]:
        print(f"[REJECTED] User ID {user_id}")
        return redirect(url_for("admin_dashboard"))
    else:
        return f"Error: {result.get('error', 'Unknown error')}", 500


@app.route("/admin/reset/<int:user_id>", methods=["POST"])
@admin_required
def reset_to_pending(user_id):
    """거절된 사용자를 다시 승인 대기 상태로 변경"""
    db = get_db()
    result = db.reset_to_pending(user_id)

    if result["success"]:
        print(f"[RESET TO PENDING] User ID {user_id}")
        return redirect(url_for("admin_dashboard"))
    else:
        return f"Error: {result.get('error', 'Unknown error')}", 500


@app.route("/admin/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    """사용자 완전 삭제 (Admin 전용)"""
    db = get_db()
    result = db.delete_user(user_id)

    if result["success"]:
        print(f"[DELETED] User ID {user_id}")
        return redirect(url_for("admin_dashboard"))
    else:
        return f"Error: {result.get('error', 'Unknown error')}", 500


@app.route("/logout")
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/admin/login")
def admin_login_page():
    """Admin 로그인 페이지 (User 로그인과 완전 분리)"""
    return render_template("admin_login.html")


@app.route("/admin/auth", methods=["POST"])
def admin_auth():
    """Admin 인증 처리"""
    username = request.form.get("username")
    password = request.form.get("password")

    # 디버깅 로그
    logger.info(f"[DEBUG] Received username: '{username}'")
    logger.info(f"[DEBUG] Received password: '{password}'")
    logger.info(f"[DEBUG] Expected username: '{ADMIN_USERNAME}'")
    logger.info(f"[DEBUG] Expected password: '{ADMIN_PASSWORD}'")
    logger.info(f"[DEBUG] Username match: {username == ADMIN_USERNAME}")
    logger.info(f"[DEBUG] Password match: {password == ADMIN_PASSWORD}")

    # 자격증명 검증
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # Admin 세션 생성 (User 세션과 별도)
        session["admin_authenticated"] = True
        session["admin_username"] = username
        return redirect(url_for("admin_dashboard"))
    else:
        return render_template("admin_login.html", error="Invalid credentials")


@app.route("/admin/logout")
def admin_logout():
    """Admin 로그아웃"""
    session.pop("admin_authenticated", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin_login_page"))


@app.route("/api/stats")
@approved_required
def api_stats():
    """사용자 통계 API (JSON)"""
    db = get_db()
    user = db.get_user_by_github_id(session["github_id"])

    if not user:
        return jsonify({"error": "User not found"}), 404

    stats = db.get_user_stats(user["id"])

    return jsonify(
        {
            "user_id": user["id"],
            "github_login": user["github_login"],
            "license_type": user["license_type"],
            "stats": stats,
        }
    )


# ============================================
# Cortex 클라이언트 → 웹서버 데이터 수집 API
# ============================================


@app.route("/api/user/experiment_group", methods=["GET"])
def api_get_experiment_group():
    """사용자 실험 그룹 조회 (Phase 9 조건부 활성화용)

    Query Parameters:
        license_key: 사용자 라이센스 키

    Returns:
        {
            "experiment_group": "control" | "treatment1" | "treatment2",
            "beta_phase": "control" | "closed_beta" | "theory_enhanced"
        }
    """
    try:
        license_key = request.args.get("license_key")

        if not license_key:
            return jsonify({"error": "license_key required"}), 400

        # Test license key 처리 (테스트용 기본값: treatment1)
        if license_key.startswith("test_"):
            return jsonify({
                "experiment_group": "treatment1",
                "beta_phase": "closed_beta"
            })

        # 라이센스로 사용자 조회
        db = get_db()
        users = db.list_all_users()
        user = next((u for u in users if u.get("license_key") == license_key), None)

        if not user:
            logger.warning(f"Invalid license key for experiment_group query from {request.remote_addr}")
            return jsonify({"error": "Invalid license key"}), 401

        # experiment_group -> beta_phase 매핑
        group_to_phase = {
            "control": "control",
            "treatment1": "closed_beta",
            "treatment2": "theory_enhanced"
        }

        experiment_group = user.get("experiment_group", "treatment1")
        beta_phase = group_to_phase.get(experiment_group, "closed_beta")

        return jsonify({
            "experiment_group": experiment_group,
            "beta_phase": beta_phase
        })

    except Exception as e:
        logger.error(f"Error in get_experiment_group: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/telemetry", methods=["POST"])
def api_telemetry():
    """Cortex 클라이언트로부터 사용 지표 수집

    Request Body:
    {
        "license_key": "cortex_...",
        "module_name": "memory_manager",
        "project_id": "optional_project_id",
        "total_calls": 10,
        "success_count": 9,
        "error_count": 1,
        "total_latency_ms": 1234.5
    }
    """
    try:
        data = request.json

        if not data or "license_key" not in data:
            logger.warning(f"Telemetry request missing license_key from {request.remote_addr}")
            return jsonify({"error": "license_key required"}), 400

        license_key = data["license_key"]

        # 라이센스로 사용자 조회
        db = get_db()
        users = db.list_all_users()
        user = next((u for u in users if u.get("license_key") == license_key), None)

        if not user:
            logger.warning(f"Invalid license key attempt from {request.remote_addr}: {license_key[:10]}...")
            return jsonify({"error": "Invalid license key"}), 401

        # 통계 업데이트 (v2: project_id 추가)
        db.update_user_stats(
            user_id=user["id"],
            module_name=data.get("module_name", "unknown"),
            total_calls=data.get("total_calls", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
            total_latency_ms=data.get("total_latency_ms", 0.0),
            project_id=data.get("project_id"),  # v2 추가
        )

        logger.info(f"Telemetry updated for user {user['id']}, module: {data.get('module_name')}, project: {data.get('project_id')}")

        return jsonify({"status": "ok", "user_id": user["id"]})

    except Exception as e:
        logger.error(f"api_telemetry error from {request.remote_addr}: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/errors", methods=["POST"])
def api_errors():
    """Cortex 클라이언트로부터 에러 로그 수집

    Request Body:
    {
        "license_key": "cortex_...",
        "error_type": "mcp_tool_error",
        "tool_name": "update_memory",
        "error_message": "Failed to update",
        "stack_trace": "...",
        "context": "...",
        "severity": "error"
    }
    """
    try:
        data = request.json

        if not data or "license_key" not in data:
            logger.warning(f"Error log request missing license_key from {request.remote_addr}")
            return jsonify({"error": "license_key required"}), 400

        license_key = data["license_key"]

        # 라이센스로 사용자 조회
        db = get_db()
        users = db.list_all_users()
        user = next((u for u in users if u.get("license_key") == license_key), None)

        user_id = user["id"] if user else None

        if not user:
            logger.warning(f"Error log from unknown license key from {request.remote_addr}: {license_key[:10]}...")

        # 에러 로그 기록 (user_id 없어도 기록 가능)
        db.record_error_log(
            user_id=user_id,
            error_type=data.get("error_type", "unknown"),
            tool_name=data.get("tool_name"),
            error_message=data.get("error_message", ""),
            stack_trace=data.get("stack_trace"),
            context=data.get("context"),
            severity=data.get("severity", "error"),
        )

        logger.info(f"Error log recorded for user {user_id}, error_type: {data.get('error_type')}, severity: {data.get('severity')}")

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"api_errors error from {request.remote_addr}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/research_metrics", methods=["POST"])
def api_research_metrics():
    """Cortex 클라이언트로부터 연구 메트릭 수집 (논문용 데이터)

    Request Body:
    {
        "license_key": "cortex_...",
        "beta_phase": "closed_beta",
        "context_stability_score": 0.95,
        "recovery_time_ms": 123.4,
        "intervention_precision": 0.88,
        "user_acceptance_count": 10,
        "user_rejection_count": 2,
        "session_id": "session_123"
    }
    """
    try:
        data = request.json

        if not data or "license_key" not in data:
            logger.warning(f"Research metrics request missing license_key from {request.remote_addr}")
            return jsonify({"error": "license_key required"}), 400

        license_key = data["license_key"]

        # 라이센스로 사용자 조회
        db = get_db()
        users = db.list_all_users()
        user = next((u for u in users if u.get("license_key") == license_key), None)

        # 테스트 라이센스키 허용 (E2E 테스트용)
        if not user and license_key.startswith("test_"):
            logger.info(f"Test license key detected: {license_key}, creating mock user")
            user = {"id": "test_user_id", "license_key": license_key, "tier": "closed_beta"}

        if not user:
            logger.warning(f"Invalid license key attempt in research metrics from {request.remote_addr}: {license_key[:10]}...")
            return jsonify({"error": "Invalid license key"}), 401

        # 연구 메트릭 기록 (Phase 9 필드 포함)
        db.record_research_metric(
            user_id=user["id"],
            beta_phase=data.get("beta_phase", "closed_beta"),
            context_stability_score=data.get("context_stability_score"),
            recovery_time_ms=data.get("recovery_time_ms"),
            intervention_precision=data.get("intervention_precision"),
            user_acceptance_count=data.get("user_acceptance_count", 0),
            user_rejection_count=data.get("user_rejection_count", 0),
            session_id=data.get("session_id"),
            # Phase 9 Hallucination Detection 필드
            grounding_score=data.get("grounding_score"),
            confidence_level=data.get("confidence_level"),
            total_claims=data.get("total_claims"),
            unverified_claims=data.get("unverified_claims"),
            hallucination_detected=data.get("hallucination_detected"),
            hallucination_occurred_at=data.get("hallucination_occurred_at"),
            hallucination_detected_at=data.get("hallucination_detected_at"),
            drift_occurred_at=data.get("drift_occurred_at"),
            drift_detected_at=data.get("drift_detected_at"),
            requires_retry=data.get("requires_retry"),
            retry_reason=data.get("retry_reason"),
            claim_types_json=data.get("claim_types_json"),
            context_depth_avg=data.get("context_depth_avg"),
        )

        logger.info(f"Research metrics recorded for user {user['id']}, session: {data.get('session_id')}, beta_phase: {data.get('beta_phase')}")

        return jsonify({"status": "ok", "user_id": user["id"]})

    except Exception as e:
        logger.error(f"api_research_metrics error from {request.remote_addr}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/license/verify", methods=["POST"])
def api_license_verify():
    """라이센스 검증 API

    Request Body:
    {
        "license_key": "cortex_..."
    }

    Response:
    {
        "valid": true,
        "tier": "closed_beta",
        "github_login": "username"
    }
    """
    try:
        data = request.json

        if not data or "license_key" not in data:
            return jsonify({"error": "license_key required"}), 400

        license_key = data["license_key"]

        # 라이센스로 사용자 조회
        db = get_db()
        users = db.list_all_users()
        user = next((u for u in users if u.get("license_key") == license_key), None)

        if not user or user.get("approval_status") != "approved":
            return jsonify({"valid": False})

        return jsonify({
            "valid": True,
            "tier": user.get("license_type", "free"),
            "github_login": user.get("github_login"),
            "user_id": user["id"],
        })

    except Exception as e:
        print(f"[ERROR] api_license_verify: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/admin/errors", strict_slashes=False)
@admin_required
def admin_errors():
    """Admin 에러 & 크래시 리포트"""
    db = get_db()

    # 필터 파라미터
    severity = request.args.get("severity")
    error_type = request.args.get("error_type")
    limit = int(request.args.get("limit", 100))

    # 오류 로그 조회
    error_logs = db.get_error_logs(limit=limit, severity=severity, error_type=error_type)

    # 오류 통계
    error_stats = db.get_error_stats()

    return render_template(
        "admin_errors.html",
        error_logs=error_logs,
        error_stats=error_stats,
        selected_severity=severity,
        selected_error_type=error_type,
        limit=limit,
    )


@app.route("/admin/insights", strict_slashes=False)
@admin_required
def admin_insights():
    """관리자 인사이트 - 베타 사용 데이터 및 논문용 통계"""
    db = get_db()

    # 베타 페이즈 선택 (쿼리 파라미터)
    selected_phase = request.args.get("phase", "closed_beta")

    # 현재 활성 베타 페이즈
    current_phase = db.get_current_beta_phase()

    # 전체 사용자 목록
    all_users = db.list_all_users()

    # 승인된 사용자만
    approved_users = [u for u in all_users if u["approval_status"] == "approved"]

    # 전체 통계 집계
    total_stats = db.get_all_stats()

    # 도구별 사용 빈도 집계
    tool_usage = {}
    error_count = 0
    success_count = 0

    for stat in total_stats:
        module_name = stat["module_name"]
        if module_name not in tool_usage:
            tool_usage[module_name] = {
                "total_calls": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_latency_ms": 0,
                "user_count": 0,
            }

        tool_usage[module_name]["total_calls"] += stat["total_calls"]
        tool_usage[module_name]["success_count"] += stat["success_count"]
        tool_usage[module_name]["error_count"] += stat["error_count"]
        tool_usage[module_name]["user_count"] += 1

        error_count += stat["error_count"]
        success_count += stat["success_count"]

    # 평균 레이턴시 계산
    for tool in tool_usage:
        if tool_usage[tool]["total_calls"] > 0:
            tool_stats = [s for s in total_stats if s["module_name"] == tool]
            total_latency = sum(s["total_latency_ms"] for s in tool_stats)
            tool_usage[tool]["avg_latency_ms"] = round(
                total_latency / tool_usage[tool]["total_calls"], 2
            )

    # 에러율 계산
    total_calls = error_count + success_count
    error_rate = (error_count / total_calls * 100) if total_calls > 0 else 0

    # 도구별 사용 빈도 정렬 (호출 횟수 기준)
    sorted_tools = sorted(tool_usage.items(), key=lambda x: x[1]["total_calls"], reverse=True)

    # 연구 메트릭 조회 (structure.md 6.5 - 실제 측정 데이터 우선, 없으면 근사치)
    research_metrics = db.get_research_metrics(beta_phase=selected_phase)

    if research_metrics:
        # 실제 측정 데이터가 있으면 평균 계산
        context_stability_score = round(
            sum(m["context_stability_score"] or 0 for m in research_metrics)
            / len(research_metrics),
            2,
        )
        avg_recovery_time = round(
            sum(m["recovery_time_ms"] or 0 for m in research_metrics) / len(research_metrics), 2
        )
        intervention_precision = round(
            sum(m["intervention_precision"] or 0 for m in research_metrics) / len(research_metrics),
            2,
        )
        total_acceptances = sum(m["user_acceptance_count"] for m in research_metrics)
        total_rejections = sum(m["user_rejection_count"] for m in research_metrics)
        user_acceptance_ratio = (
            round((total_acceptances / (total_acceptances + total_rejections) * 100), 2)
            if (total_acceptances + total_rejections) > 0
            else 0
        )
    else:
        # 실제 데이터 없으면 근사치 사용 (Phase 1)
        context_stability_score = (
            round((success_count / total_calls * 100), 2) if total_calls > 0 else 0
        )
        user_acceptance_ratio = (
            round((success_count / total_calls * 100), 2) if total_calls > 0 else 0
        )
        total_latency = sum(s["total_latency_ms"] for s in total_stats)
        avg_recovery_time = round(total_latency / total_calls, 2) if total_calls > 0 else 0
        intervention_precision = round(100 - error_rate, 2)

    return render_template(
        "admin_insights.html",
        all_users=all_users,
        approved_users=approved_users,
        total_users=len(all_users),
        approved_count=len(approved_users),
        total_calls=total_calls,
        success_count=success_count,
        error_count=error_count,
        error_rate=round(error_rate, 2),
        sorted_tools=sorted_tools,
        # 연구 메트릭 (structure.md 6.5)
        context_stability_score=context_stability_score,
        user_acceptance_ratio=user_acceptance_ratio,
        avg_recovery_time=avg_recovery_time,
        intervention_precision=intervention_precision,
        # 베타 페이즈 정보
        selected_phase=selected_phase,
        current_phase=current_phase,
        has_real_metrics=len(research_metrics) > 0,
    )


@app.route("/admin/stats", strict_slashes=False)
@admin_required
def admin_stats():
    """관리자 통계 대시보드 - 일반 사용 지표"""
    db = get_db()

    # 전체 사용자 목록
    all_users = db.list_all_users()
    approved_users = [u for u in all_users if u["approval_status"] == "approved"]

    # 전체 통계 조회
    total_stats = db.get_all_stats()

    # 기본 통계 계산
    total_calls = sum(s["total_calls"] for s in total_stats)
    error_count = sum(s["error_count"] for s in total_stats)
    success_count = total_calls - error_count
    success_rate = (success_count / total_calls * 100) if total_calls > 0 else 0

    # 도구별 사용 빈도
    tool_usage = {}
    for stat in total_stats:
        module = stat["module_name"]
        if module not in tool_usage:
            tool_usage[module] = {
                "total_calls": 0,
                "success_count": 0,
                "error_count": 0,
            }
        tool_usage[module]["total_calls"] += stat["total_calls"]
        tool_usage[module]["error_count"] += stat["error_count"]
        tool_usage[module]["success_count"] += (stat["total_calls"] - stat["error_count"])

    # 사용 빈도순 정렬
    sorted_tools = sorted(tool_usage.items(), key=lambda x: x[1]["total_calls"], reverse=True)

    # 사용자당 평균 API 호출
    avg_calls_per_user = round(total_calls / len(approved_users), 2) if len(approved_users) > 0 else 0

    # 최근 24시간 활동 (임시로 전체 통계 사용)
    recent_24h_calls = total_calls  # TODO: DB에 시간 필터 추가 필요

    return render_template(
        "admin_stats.html",
        total_users=len(all_users),
        approved_users=len(approved_users),
        pending_users=len([u for u in all_users if u["approval_status"] == "pending"]),
        total_calls=total_calls,
        success_count=success_count,
        error_count=error_count,
        success_rate=round(success_rate, 2),
        sorted_tools=sorted_tools[:10],  # Top 10만
        avg_calls_per_user=avg_calls_per_user,
        recent_24h_calls=recent_24h_calls,
    )


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("Cortex MCP Web Dashboard (Manual Approval)")
    print("=" * 60)
    print(f"Flask Secret Key: {'Set' if app.secret_key else 'Not Set'}")
    print(f"GitHub Client ID: {'Set' if GITHUB_CLIENT_ID else 'Not Set'}")
    print(f"GitHub Client Secret: {'Set' if GITHUB_CLIENT_SECRET else 'Not Set'}")
    print("=" * 60)

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        print("\n[WARNING] GitHub OAuth 환경 변수가 설정되지 않았습니다.")
        print("OAuth 로그인은 비활성화되지만, 웹페이지는 정상적으로 볼 수 있습니다.")
        print("=" * 60)

    # Flask 서버 실행
    app.run(host="0.0.0.0", port=8000, debug=True)


if __name__ == "__main__":
    main()
