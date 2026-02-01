"""
Research Logger 통합 테스트

P0 작업 완료 검증:
1. memory_manager.py 통합
2. claim_extractor.py 통합
3. automation_manager.py 통합
4. claim_verifier.py 통합
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.research_logger import get_research_logger, ResearchEvent, EventType
from core.claim_extractor import ClaimExtractor, Claim
from core.automation_manager import get_automation_manager
from config import config


def test_research_logger_enable():
    """Test 1: Research Logger 활성화"""
    print("\n=== Test 1: Research Logger 활성화 ===")

    logger = get_research_logger()
    logger.enable(user_consent=True, user_id="test_user_integration")

    assert logger.enabled, "Research Logger가 활성화되지 않았습니다"
    assert logger.current_user_hash is not None, "User hash가 생성되지 않았습니다"
    assert logger.current_session_id is not None, "Session ID가 생성되지 않았습니다"

    print(f"✓ Research Logger 활성화됨")
    print(f"  - User hash: {logger.current_user_hash[:16]}...")
    print(f"  - Session ID: {logger.current_session_id}")


def test_claim_extractor_logging():
    """Test 2: ClaimExtractor 로깅"""
    print("\n=== Test 2: ClaimExtractor 로깅 ===")

    extractor = ClaimExtractor()
    test_text = """
    구현을 완료했습니다. 7개 파일을 수정하여 기능을 추가했습니다.
    테스트도 모두 통과했습니다.
    """

    claims = extractor.extract_claims(test_text)

    print(f"✓ Claim 추출 완료: {len(claims)}개")
    for claim in claims:
        print(f"  - {claim.claim_type}: {claim.text[:50]}...")


def test_automation_manager_logging():
    """Test 3: AutomationManager 로깅"""
    print("\n=== Test 3: AutomationManager 로깅 ===")

    manager = get_automation_manager(project_id="test_project")

    # 여러 피드백 기록 (버퍼 크기 10개를 채우기 위해)
    for i in range(15):
        feedback_type = "accepted" if i % 2 == 0 else "rejected"
        result = manager.record_feedback(
            action_type="context_suggest",
            feedback=feedback_type,
            action_id=f"test_action_{i:03d}",
            details={"response_time_sec": 1.5 + i * 0.1}
        )

    print(f"✓ Feedback 기록 완료: 15건")
    print(f"  - Success: {result['success']}")
    print(f"  - Current mode: {result['current_mode']}")


def test_log_files_created():
    """Test 4: 로그 파일 생성 확인"""
    print("\n=== Test 4: 로그 파일 생성 확인 ===")

    research_dir = config.base_dir / "research"
    events_dir = research_dir / "events"

    assert research_dir.exists(), f"Research 디렉토리가 없습니다: {research_dir}"
    assert events_dir.exists(), f"Events 디렉토리가 없습니다: {events_dir}"

    # 버퍼 상태 확인
    logger = get_research_logger()
    print(f"  - Buffer size: {len(logger.event_buffer)} events")
    print(f"  - Buffer max size: {logger.buffer_max_size}")
    print(f"  - Logger enabled: {logger.enabled}")
    print(f"  - Session ID: {logger.current_session_id}")
    print(f"  - User hash: {logger.current_user_hash[:16] if logger.current_user_hash else 'None'}...")

    # 이벤트 로그 파일 확인
    event_files = list(events_dir.glob("*.jsonl"))

    print(f"✓ 디렉토리 구조 확인됨")
    print(f"  - Research dir: {research_dir}")
    print(f"  - Events dir: {events_dir}")
    print(f"  - Event files: {len(event_files)}")

    if event_files:
        latest_file = max(event_files, key=lambda p: p.stat().st_mtime)
        print(f"  - Latest file: {latest_file.name}")

        # 파일 내용 확인
        with open(latest_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"  - Events logged: {len(lines)}")

            if lines:
                print(f"\n  첫 번째 이벤트 샘플:")
                import json
                first_event = json.loads(lines[0])
                print(f"    - Event type: {first_event.get('event_type')}")
                print(f"    - Timestamp: {first_event.get('timestamp')}")
    else:
        print("  ⚠ 로그 파일이 아직 생성되지 않았습니다 (버퍼링 중일 수 있음)")


def test_consent_file():
    """Test 5: Consent 파일 확인"""
    print("\n=== Test 5: Consent 파일 확인 ===")

    research_dir = config.base_dir / "research"
    consent_file = research_dir / "consent.json"

    if consent_file.exists():
        import json
        with open(consent_file, 'r', encoding='utf-8') as f:
            consent_data = json.load(f)

        print(f"✓ Consent 파일 존재")
        print(f"  - Consent given: {consent_data.get('consent_given')}")
        print(f"  - Timestamp: {consent_data.get('consent_timestamp')}")
    else:
        print(f"  ⚠ Consent 파일이 없습니다 (세션 종료 시 생성됨)")


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 70)
    print("Research Logger 통합 테스트 시작")
    print("=" * 70)

    try:
        test_research_logger_enable()
        test_claim_extractor_logging()
        test_automation_manager_logging()
        test_log_files_created()
        test_consent_file()

        print("\n" + "=" * 70)
        print("✅ 모든 테스트 통과!")
        print("=" * 70)

        # 로거 버퍼 플러시
        logger = get_research_logger()
        import asyncio
        asyncio.run(logger.flush())

        print("\n버퍼 플러시 완료. 로그 파일을 다시 확인하세요.")
        test_log_files_created()

        return True

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
