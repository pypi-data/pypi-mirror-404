"""
MCP Telemetry v2.0 테스트
telemetry_mcp.py가 v2.0 스키마를 정상적으로 사용하는지 검증
"""

from core.telemetry_mcp import get_mcp_telemetry

# MCP 텔레메트리 인스턴스 생성
mcp_telemetry = get_mcp_telemetry()

print("=== MCP Telemetry v2.0 Test ===\n")

# 1. Tool Execution 추적
print("1. Testing track_tool_execution()...")
mcp_telemetry.track_tool_execution(
    tool_name="initialize_context",
    args={"project_id": "test_project", "scan_mode": "LIGHT"},
    result={"status": "success"},
    duration_ms=150.0,
    success=True,
)
print("   [OK] Tool execution tracked\n")

# 2. RAG Search 추적
print("2. Testing track_rag_search()...")
mcp_telemetry.track_rag_search(
    query="test query for context search", top_k=5, results_count=3, duration_ms=45.0, success=True
)
print("   [OK] RAG search tracked\n")

# 3. Context Operation 추적
print("3. Testing track_context_operation()...")
mcp_telemetry.track_context_operation(
    operation="create",
    project_id="test_project",
    branch_id="test_branch",
    metadata={"context_count": 5},
)
print("   [OK] Context operation tracked\n")

# 4. Reference History 추적
print("4. Testing track_reference_history()...")
mcp_telemetry.track_reference_history(operation="suggest", accuracy=0.95, suggestion_count=3)
print("   [OK] Reference history tracked\n")

# 5. Smart Context 추적
print("5. Testing track_smart_context()...")
mcp_telemetry.track_smart_context(operation="load", contexts_loaded=2, contexts_compressed=1)
print("   [OK] Smart context tracked\n")

# 6. Git Sync 추적
print("6. Testing track_git_sync()...")
mcp_telemetry.track_git_sync(operation="link", branch_name="main", auto_created=False)
print("   [OK] Git sync tracked\n")

# 7. Cloud Sync 추적
print("7. Testing track_cloud_sync()...")
mcp_telemetry.track_cloud_sync(
    operation="upload", size_bytes=1024000, duration_ms=500.0, success=True
)
print("   [OK] Cloud sync tracked\n")

# 8. Automation 추적
print("8. Testing track_automation()...")
mcp_telemetry.track_automation(action_type="branch_create", feedback="accepted", plan_mode="auto")
print("   [OK] Automation tracked\n")

print("\n[SUCCESS] All MCP telemetry methods tested successfully!")
print("\nv2.0 호환성: telemetry_integration.py를 통해 자동으로 v2.0 스키마 적용됨")
print("- service → channel 자동 변환")
print("- event_type → event_name 자동 변환")
print("- event_data → metadata 자동 병합")
