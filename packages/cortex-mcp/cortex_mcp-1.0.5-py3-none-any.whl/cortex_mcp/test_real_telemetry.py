"""
실제 텔레메트리 수집 검증 테스트
Cortex 코드를 실제로 실행해서 텔레메트리가 수집되는지 확인
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import get_cortex_path

print("\n" + "=" * 60)
print("[REAL TEST] 실제 텔레메트리 수집 테스트")
print("=" * 60)

# 1. 텔레메트리 활성화
print("\n[1] 텔레메트리 초기화...")
try:
    from core.telemetry_client import enable_telemetry, get_telemetry_client

    # 테스트 라이센스 키 (test_api_integration.py에서 사용한 것과 동일)
    LICENSE_KEY = "test-key-alpha-user-004-20241216"

    enable_telemetry(LICENSE_KEY, "http://localhost:8000")
    client = get_telemetry_client()
    print(f"✓ 텔레메트리 활성화됨: enabled={client.enabled}")
except Exception as e:
    print(f"✗ 텔레메트리 초기화 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. memory_manager.update_memory 호출 (데코레이터가 자동으로 텔레메트리 수집해야 함)
print("\n[2] memory_manager.update_memory 호출...")
try:
    from core.memory_manager import MemoryManager

    manager = MemoryManager(project_id="test_telemetry_project")

    # create_branch 호출 (첫 번째 데코레이터 테스트)
    print("  - create_branch 호출...")
    result = manager.create_branch(
        project_id="test_telemetry_project",
        branch_topic="test_telemetry_branch"
    )
    print(f"  - create_branch 결과: {result.get('success', False)}")

    # update_memory 호출 (두 번째 데코레이터 테스트)
    print("  - update_memory 호출...")
    result = manager.update_memory(
        project_id="test_telemetry_project",
        branch_id=result.get("branch_id", "test_branch"),
        content="텔레메트리 테스트 메시지입니다.",
        role="assistant"
    )
    print(f"  - update_memory 결과: {result.get('success', False)}")

except Exception as e:
    print(f"✗ memory_manager 호출 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. rag_engine.search 호출
print("\n[3] rag_engine.search 호출...")
try:
    from core.rag_engine import RAGEngine

    engine = RAGEngine(project_id="test_telemetry_project")

    # search 호출 (세 번째 데코레이터 테스트)
    print("  - search 호출...")
    results = engine.search(query="test query", top_k=5)
    print(f"  - search 결과: {len(results)}개 검색됨")

except Exception as e:
    print(f"✗ rag_engine 호출 실패: {e}")
    import traceback
    traceback.print_exc()

# 4. 텔레메트리 전송 대기
print("\n[4] 텔레메트리 백그라운드 전송 대기 (10초)...")
time.sleep(10)

# 5. 즉시 전송 (flush)
print("\n[5] 텔레메트리 즉시 전송 (flush)...")
try:
    client._flush_stats()
    print("✓ flush 완료")
except Exception as e:
    print(f"✗ flush 실패: {e}")

# 6. 연구 메트릭 수집 테스트
print("\n[6] 연구 메트릭 수집 테스트...")
try:
    from core.telemetry_client import record_research_metric

    # context_stability_score 기록
    print("  - context_stability_score 기록...")
    record_research_metric(context_stability_score=0.95)

    # recovery_time_ms 기록
    print("  - recovery_time_ms 기록...")
    record_research_metric(recovery_time_ms=123.4)

    # intervention_precision 기록
    print("  - intervention_precision 기록...")
    record_research_metric(intervention_precision=0.88)

    # user_acceptance/rejection 기록
    print("  - user_acceptance/rejection 기록...")
    record_research_metric(user_acceptance_count=1, user_rejection_count=0)

    print("✓ 연구 메트릭 기록 완료")
except Exception as e:
    print(f"✗ 연구 메트릭 기록 실패: {e}")
    import traceback
    traceback.print_exc()

# 7. 텔레메트리 전송 대기
print("\n[7] 텔레메트리 백그라운드 전송 대기 (10초)...")
time.sleep(10)

# 8. 즉시 전송 (flush)
print("\n[8] 텔레메트리 즉시 전송 (flush)...")
try:
    client._flush_stats()
    print("✓ flush 완료")
except Exception as e:
    print(f"✗ flush 실패: {e}")

# 9. 데이터베이스 확인
print("\n[9] 데이터베이스 확인...")
try:
    sys.path.insert(0, str(Path(__file__).parent / "web"))
    from models import get_db

    db = get_db()

    # 사용자 통계 확인
    stats = db.get_user_stats(user_id=4)
    if stats:
        print(f"✓ 사용자 통계 발견: {len(stats)}개 모듈")
        for stat in stats:
            print(f"  - {stat['module_name']}: calls={stat['total_calls']}, success={stat['success_count']}, errors={stat['error_count']}")
    else:
        print("✗ 사용자 통계 없음")

    # 최근 에러 로그 확인
    errors = db.get_error_logs(limit=3)
    if errors:
        print(f"✓ 에러 로그 발견: {len(errors)}개")
        for err in errors[:3]:
            print(f"  - [{err['severity']}] {err['error_type']}: {err['error_message'][:50]}")
    else:
        print("✓ 에러 로그 없음 (정상)")

    # 연구 메트릭 확인 (신규)
    print("\n  [연구 메트릭 확인]")
    # research_metrics 테이블에서 최근 5개 조회
    import sqlite3
    db_path = get_cortex_path("web", "cortex_web.db")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM research_metrics
        WHERE user_id = 4
        ORDER BY recorded_at DESC
        LIMIT 5
    """)
    metrics = cursor.fetchall()

    if metrics:
        print(f"✓ 연구 메트릭 발견: {len(metrics)}개")
        for metric in metrics:
            print(f"  - context_stability={metric['context_stability_score']}, "
                  f"recovery_time={metric['recovery_time_ms']}, "
                  f"intervention_precision={metric['intervention_precision']}")
    else:
        print("✗ 연구 메트릭 없음")

    conn.close()

except Exception as e:
    print(f"✗ 데이터베이스 확인 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("[REAL TEST] 테스트 완료")
print("=" * 60)
