# 스킵된 테스트 목록

## 무한 대기/느린 테스트

### test_create_node
- **파일**: `tests/unit/test_memory_manager.py::TestMemoryManagerHierarchy::test_create_node`
- **문제**: 테스트 실행 시 무한 대기 또는 매우 느림 (10분+ 소요)
- **발견 시간**: 2025-12-23 00:12
- **상태**: Phase 2에서 원인 파악 및 수정 필요
- **추정 원인**: Node 생성 시 무한 루프 또는 대기, fixture 문제

### test_update_memory_long_content
- **파일**: `tests/unit/test_memory_manager.py::TestMemoryManagerUpdate::test_update_memory_long_content`
- **문제**: 테스트 실행 시 무한 대기 또는 매우 느림 (9분+ 소요, CPU 99%)
- **발견 시간**: 2025-12-23 00:29
- **상태**: Phase 2에서 원인 파악 및 수정 필요
- **추정 원인**: 긴 컨텐츠 처리 시 무한 루프, 메모리 문제, fixture 격리 문제

## 조치 필요
- [ ] test_create_node 테스트 원인 파악
- [ ] test_update_memory_long_content 테스트 원인 파악
- [ ] memory_manager.py의 create_node, update_memory 메서드 검토
- [ ] 테스트 fixture 격리 문제 확인
- [ ] 긴 컨텐츠 처리 로직 성능 검토
