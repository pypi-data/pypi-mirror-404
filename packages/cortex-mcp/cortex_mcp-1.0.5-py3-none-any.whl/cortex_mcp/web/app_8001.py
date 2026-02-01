"""
Cortex MCP - Web Application
Flask 기반 사용자/관리자 대시보드 (수동 승인 방식)
"""

import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import get_github_oauth
from models import get_db

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
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cortex_admin_2025")

if ADMIN_PASSWORD == "cortex_admin_2025":
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
    """Features 페이지 - 4대 핵심 기능"""
    return render_template("features.html")


@app.route("/trust")
def trust():
    """Hallucination & Trust 페이지"""
    return render_template("trust.html")


@app.route("/benchmarks")
def benchmarks():
    """Proof & Benchmarks 페이지"""
    return render_template("benchmarks.html")


@app.route("/pricing")
def pricing():
    """Pricing 페이지 (Open Beta 전까지 hidden)"""
    return render_template("pricing.html")


@app.route("/mypage")
@approved_required
def mypage():
    """My Project Overview 페이지 (승인된 사용자만)"""
    return render_template("mypage.html")


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

    # 전체 통계 계산
    total_users = len(all_users)
    approved_count = len(approved_users)
    pending_count = len(pending_users)
    rejected_count = sum(1 for u in all_users if u["approval_status"] == "rejected")

    # 라이센스 타입별 통계 (승인된 사용자만)
    license_stats = {}
    for user in approved_users:
        license_type = user["license_type"] or "none"
        license_stats[license_type] = license_stats.get(license_type, 0) + 1

    return render_template(
        "admin_dashboard.html",
        pending_users=pending_users,
        approved_users=approved_users,
        total_users=total_users,
        approved_count=approved_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        license_stats=license_stats,
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
    app.run(host="0.0.0.0", port=8001, debug=True)


if __name__ == "__main__":
    main()
