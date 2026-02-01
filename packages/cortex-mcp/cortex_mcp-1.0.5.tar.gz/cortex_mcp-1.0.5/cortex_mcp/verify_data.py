"""
데이터베이스에 저장된 테스트 데이터 검증
"""

import sys
from pathlib import Path

# web 모듈 경로 추가
web_path = Path(__file__).parent / "web"
sys.path.insert(0, str(web_path))

from models import get_db

def verify_data():
    """저장된 데이터 검증"""
    db = get_db()

    print("\n" + "="*60)
    print("데이터베이스 검증")
    print("="*60)

    # 1. 사용자 통계 확인
    print("\n[1] 사용자 통계 (user_stats)")
    print("-"*60)

    user_stats = db.get_user_stats(user_id=4)
    if user_stats:
        print(f"총 통계 항목: {len(user_stats)}")
        for stat in user_stats:
            print(f"  - {stat['module_name']}: "
                  f"calls={stat['total_calls']}, "
                  f"success={stat['success_count']}, "
                  f"errors={stat['error_count']}, "
                  f"latency={stat['total_latency_ms']:.1f}ms")
    else:
        print("  통계 데이터 없음")

    # 2. 에러 로그 확인
    print("\n[2] 에러 로그 (error_logs)")
    print("-"*60)

    error_logs = db.get_error_logs(limit=10)
    if error_logs:
        print(f"총 에러 로그: {len(error_logs)}")
        for log in error_logs[:5]:  # 최근 5개만 출력
            print(f"  - [{log['severity']}] {log['error_type']}: {log['error_message'][:50]}")
    else:
        print("  에러 로그 없음")

    # 3. 연구 메트릭 확인
    print("\n[3] 연구 메트릭 (research_metrics)")
    print("-"*60)

    # get_research_metrics 메서드가 없으므로 직접 쿼리
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM research_metrics
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT 10
    """, (4,))

    metrics = cursor.fetchall()
    conn.close()

    if metrics:
        print(f"총 연구 메트릭: {len(metrics)}")
        for metric in metrics[:3]:  # 최근 3개만 출력
            print(f"  - 안정성: {metric['context_stability_score']:.2f}, "
                  f"복구시간: {metric['recovery_time_ms']:.1f}ms, "
                  f"정밀도: {metric['intervention_precision']:.2f}, "
                  f"수락/거부: {metric['user_acceptance_count']}/{metric['user_rejection_count']}")
    else:
        print("  연구 메트릭 없음")

    # 4. Admin 통계 확인
    print("\n[4] Admin 전체 통계")
    print("-"*60)

    all_stats = db.get_all_stats()
    if all_stats:
        print(f"  전체 모듈 통계: {len(all_stats)}")
        total_calls = sum(s['total_calls'] for s in all_stats)
        total_success = sum(s['success_count'] for s in all_stats)
        total_errors = sum(s['error_count'] for s in all_stats)
        avg_latency = sum(s['total_latency_ms'] for s in all_stats) / len(all_stats)
        print(f"  총 호출 수: {total_calls}")
        print(f"  총 성공: {total_success}")
        print(f"  총 실패: {total_errors}")
        print(f"  평균 지연시간: {avg_latency:.1f}ms")
    else:
        print("  통계 없음")

    print("\n" + "="*60)
    print("검증 완료!")
    print("="*60)
    print("\n다음 단계:")
    print("  1. http://localhost:8000/admin/stats - Admin 대시보드 확인")
    print("  2. http://localhost:8000/dashboard - 유저 대시보드 확인")
    print()

if __name__ == "__main__":
    verify_data()
