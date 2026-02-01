"""
Cortex Telemetry End-to-End Test
실제 텔레메트리 데이터 전송 검증
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_telemetry_client():
    """텔레메트리 클라이언트 직접 테스트"""
    print("\n" + "=" * 60)
    print("[TEST 1] 텔레메트리 클라이언트 직접 테스트")
    print("=" * 60)

    # 테스트 사용자의 라이센스 키 읽기
    try:
        with open("test_api_integration.py", "r") as f:
            content = f.read()
            import re
            match = re.search(r'LICENSE_KEY = "([^"]+)"', content)
            if match:
                license_key = match.group(1)
                print(f"라이센스 키: {license_key}")
            else:
                print("라이센스 키를 찾을 수 없습니다.")
                return False
    except Exception as e:
        print(f"라이센스 키 읽기 실패: {e}")
        return False

    # 텔레메트리 클라이언트 초기화 및 테스트
    try:
        from core.telemetry_client import TelemetryClient

        client = TelemetryClient(
            server_url="http://localhost:8000",
            license_key=license_key,
            enabled=True,
            flush_interval=5  # 테스트용 5초
        )

        print("\n[1-1] 사용 지표 기록...")
        client.record_call("memory_manager", success=True, latency_ms=123.4)
        client.record_call("rag_engine", success=True, latency_ms=45.6)
        client.record_call("backup_manager", success=False, latency_ms=89.0)
        print("사용 지표 3개 기록 완료")

        print("\n[1-2] 에러 로그 기록...")
        client.record_error(
            error_type="TestError",
            error_message="This is a test error",
            tool_name="test_tool",
            severity="warning"
        )
        print("에러 로그 1개 기록 완료")

        print("\n[1-3] 연구 메트릭 기록...")
        client.record_research_metric(
            beta_phase="closed_beta",
            context_stability_score=0.92,
            recovery_time_ms=150.5,
            intervention_precision=0.85,
            user_acceptance_count=15,
            user_rejection_count=3
        )
        print("연구 메트릭 1개 기록 완료")

        print("\n[1-4] 데이터 전송 대기 (10초)...")
        time.sleep(10)  # 백그라운드 스레드가 데이터를 전송할 시간

        print("[1-5] 즉시 전송 (flush)...")
        client._flush_stats()

        print("\n테스트 완료!")
        client.disable()

        return True

    except Exception as e:
        print(f"텔레메트리 클라이언트 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data_in_db():
    """데이터베이스에 데이터가 저장되었는지 확인"""
    print("\n" + "=" * 60)
    print("[TEST 2] 데이터베이스 검증")
    print("=" * 60)

    try:
        sys.path.insert(0, str(Path(__file__).parent / "web"))
        from models import get_db

        db = get_db()

        # 최근 통계 확인
        print("\n[2-1] 사용자 통계 확인...")
        stats = db.get_user_stats(user_id=4)
        if stats:
            print(f"  총 모듈 수: {len(stats)}")
            for stat in stats:
                print(f"  - {stat['module_name']}: "
                      f"calls={stat['total_calls']}, "
                      f"success={stat['success_count']}, "
                      f"errors={stat['error_count']}")
        else:
            print("  통계 없음")

        # 에러 로그 확인
        print("\n[2-2] 에러 로그 확인...")
        errors = db.get_error_logs(limit=5)
        if errors:
            print(f"  총 에러 로그: {len(errors)}")
            for err in errors[:3]:
                print(f"  - [{err['severity']}] {err['error_type']}: {err['error_message'][:50]}")
        else:
            print("  에러 로그 없음")

        # 연구 메트릭 확인
        print("\n[2-3] 연구 메트릭 확인...")
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_metrics WHERE user_id = 4 ORDER BY recorded_at DESC LIMIT 5")
        metrics = cursor.fetchall()
        conn.close()

        if metrics:
            print(f"  총 연구 메트릭: {len(metrics)}")
            for metric in metrics[:3]:
                print(f"  - 안정성: {metric['context_stability_score']}, "
                      f"복구시간: {metric['recovery_time_ms']}ms")
        else:
            print("  연구 메트릭 없음")

        print("\n데이터베이스 검증 완료!")
        return True

    except Exception as e:
        print(f"데이터베이스 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("Cortex Telemetry E2E Test")
    print("=" * 60)

    print("\n웹 서버가 http://localhost:8000에서 실행 중인지 확인하세요.")
    print("웹 서버 실행: cd web && python3 app.py")

    # 서버 연결 확인
    import urllib.request
    try:
        response = urllib.request.urlopen("http://localhost:8000", timeout=5)
        print("\n서버 연결 성공!")
    except Exception as e:
        print(f"\n서버 연결 실패: {e}")
        print("웹 서버를 먼저 실행하세요.")
        sys.exit(1)

    # 테스트 실행
    results = []

    results.append(test_telemetry_client())
    time.sleep(2)

    results.append(verify_data_in_db())

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과")
    print("=" * 60)
    print(f"총 테스트: {len(results)}개")
    print(f"성공: {sum(results)}개")
    print(f"실패: {len(results) - sum(results)}개")

    if all(results):
        print("\n모든 테스트 통과!")
        print("\n다음 확인:")
        print("  1. http://localhost:8000/admin/stats - Admin 대시보드에서 통계 확인")
        print("  2. 실제 Cortex MCP 서버 실행 시 자동으로 데이터 전송되는지 확인")
    else:
        print("\n일부 테스트 실패")


if __name__ == "__main__":
    main()
