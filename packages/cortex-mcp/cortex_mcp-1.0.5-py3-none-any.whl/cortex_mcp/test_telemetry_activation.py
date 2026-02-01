"""
Test Telemetry Client Activation
Admin 라이센스 키로 텔레메트리 클라이언트를 활성화하고 테스트합니다.
"""
import time
from core.telemetry_client import get_telemetry_client

# Admin license key
LICENSE_KEY = "ctx_admin_fab159c2a27d78f42487abe1d9c85559"
SERVER_URL = "http://localhost:8000"

def test_telemetry():
    """텔레메트리 클라이언트 활성화 및 테스트"""
    print(f"[TEST] Activating telemetry client...")
    print(f"[TEST] License Key: {LICENSE_KEY}")
    print(f"[TEST] Server URL: {SERVER_URL}")

    # Get client and enable
    client = get_telemetry_client()
    client.enable(LICENSE_KEY, SERVER_URL)

    print(f"[TEST] Telemetry enabled: {client.enabled}")
    print(f"[TEST] License key set: {client.license_key == LICENSE_KEY}")

    # Test 1: Record module calls
    print(f"\n[TEST] Recording module calls...")
    client.record_call("memory_manager", success=True, latency_ms=45.2, project_id="test_project")
    client.record_call("rag_engine", success=True, latency_ms=120.5, project_id="test_project")
    client.record_call("reference_history", success=True, latency_ms=30.1, project_id="test_project")
    print(f"[TEST] Recorded 3 module calls")

    # Test 2: Record error
    print(f"\n[TEST] Recording error...")
    client.record_error(
        error_type="TestError",
        error_message="This is a test error",
        tool_name="test_tool",
        stack_trace="Traceback (test)",
        context="Test context",
        severity="warning"
    )
    print(f"[TEST] Recorded 1 error")

    # Test 3: Record research metric
    print(f"\n[TEST] Recording research metric...")
    client.record_research_metric(
        beta_phase="closed_beta",
        context_stability_score=0.95,
        recovery_time_ms=150.0,
        intervention_precision=0.88,
        user_acceptance_count=10,
        user_rejection_count=2,
        session_id="test_session_001",
        grounding_score=0.82,
        confidence_level="high",
        total_claims=5,
        unverified_claims=1,
        hallucination_detected=False
    )
    print(f"[TEST] Recorded 1 research metric")

    # Force flush
    print(f"\n[TEST] Flushing data to server...")
    client._flush_stats()

    # Wait for background threads
    print(f"[TEST] Waiting for background threads...")
    time.sleep(3)

    print(f"\n[TEST] Test completed!")
    print(f"[TEST] Check the web server database for telemetry data.")

    # Disable client
    client.disable()
    print(f"[TEST] Telemetry client disabled")

if __name__ == "__main__":
    test_telemetry()
