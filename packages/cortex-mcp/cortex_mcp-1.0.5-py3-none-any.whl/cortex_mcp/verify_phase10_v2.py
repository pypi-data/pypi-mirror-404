"""
Phase 10.2 할루시네이션 검증 v2
실제 파일 증거를 포함하여 검증
"""
from core.auto_verifier import AutoVerifier
import subprocess
import os

# 검증할 응답 텍스트
response_text = '''
Phase 10.2 구현 완료:

1. CONTEXT_AWARE_TOOLS 확장 완료
   - 기존 3개 → 14개로 확장 (4.6배 증가)
   - Edit, Write, Grep, Glob, Read, load_context, create_node, search_context 추가
   - link_git_branch, create_snapshot, record_reference 추가

2. SessionCache pending_suggestions 추적 시스템 구현
   - add_pending_suggestion() 메서드 추가
   - remove_pending_suggestion() 메서드 추가
   - has_pending_suggestions() 메서드 추가
   - get_pending_suggestions() 메서드 추가

3. auto_trigger.py pre_hook에서 pending 추가
   - need_ai_review 발생 시 자동으로 pending 추가
   - session_id, project_id, suggestion_data 저장

4. cortex_tools.py에서 pending 제거
   - accept_suggestions 성공 시 pending 제거
   - reject_suggestions 성공 시 pending 제거

5. 도구 실행 전 pending 검증 경고
   - 미처리 pending이 있으면 경고 메시지 출력

테스트 결과:
- test_phase10_reject_enforcement.py: 8/8 통과
- test_auto_trigger_automation.py: 11/11 통과
- 총 19/19 테스트 통과 (100%)
'''

# 실제 파일 증거 수집
project_path = '/Users/kimjaeheung/Desktop/Desktop/Dev/project9_cortex_mcp/cortex_mcp'

# 1. CONTEXT_AWARE_TOOLS 확장 증거
with open(f'{project_path}/core/auto_trigger.py', 'r') as f:
    auto_trigger_content = f.read()

# 2. SessionCache pending 메서드 증거
session_cache_methods = []
if 'def add_pending_suggestion' in auto_trigger_content:
    session_cache_methods.append('add_pending_suggestion')
if 'def remove_pending_suggestion' in auto_trigger_content:
    session_cache_methods.append('remove_pending_suggestion')
if 'def has_pending_suggestions' in auto_trigger_content:
    session_cache_methods.append('has_pending_suggestions')
if 'def get_pending_suggestions' in auto_trigger_content:
    session_cache_methods.append('get_pending_suggestions')

# 3. cortex_tools.py pending 제거 증거
with open(f'{project_path}/tools/cortex_tools.py', 'r') as f:
    cortex_tools_content = f.read()

pending_removal_found = 'auto_trigger.cache.remove_pending_suggestion' in cortex_tools_content

# 4. 테스트 실행 증거
test_result = subprocess.run(
    ['/Library/Frameworks/Python.framework/Versions/3.11/bin/python3', '-m', 'pytest',
     'tests/unit/test_phase10_reject_enforcement.py', 'tests/unit/test_auto_trigger_automation.py',
     '-v', '--tb=no', '-q'],
    cwd=project_path,
    capture_output=True,
    text=True
)

# 증거 컨텍스트 구성
context = {
    'project_id': '4d8e58aea4b0',
    'project_path': project_path,

    # 파일 증거
    'file_evidence': {
        'auto_trigger.py': {
            'content_sample': auto_trigger_content[:5000],  # 처음 5000자
            'session_cache_methods': session_cache_methods,
            'CONTEXT_AWARE_TOOLS_found': 'CONTEXT_AWARE_TOOLS = {' in auto_trigger_content
        },
        'cortex_tools.py': {
            'pending_removal_found': pending_removal_found,
            'accept_suggestions_found': 'accept_suggestions' in cortex_tools_content,
            'reject_suggestions_found': 'reject_suggestions' in cortex_tools_content
        }
    },

    # 테스트 결과 증거
    'test_evidence': {
        'exit_code': test_result.returncode,
        'stdout': test_result.stdout,
        'stderr': test_result.stderr,
        'tests_passed': 'passed' in test_result.stdout.lower()
    },

    # 코드 변경 증거
    'code_changes': {
        'session_cache_extended': len(session_cache_methods) == 4,
        'pending_removal_implemented': pending_removal_found,
        'test_files_exist': all([
            os.path.exists(f'{project_path}/tests/unit/test_phase10_reject_enforcement.py'),
            os.path.exists(f'{project_path}/tests/unit/test_auto_trigger_automation.py')
        ])
    }
}

# AutoVerifier 실행
print('=' * 80)
print('Phase 10.2 할루시네이션 검증 v2 (증거 포함)')
print('=' * 80)

verifier = AutoVerifier()
result = verifier.verify_response(response_text, context=context)

# 결과 출력
print('\n[기본 정보]')
print(f'  - verified: {result.verified}')
print(f'  - grounding_score: {result.grounding_score:.2%}')
print(f'  - confidence_level: {result.confidence_level}')
print(f'  - requires_retry: {result.requires_retry}')

if hasattr(result, 'claims') and result.claims:
    print(f'\n[추출된 Claim: {len(result.claims)}개]')
    for i, claim in enumerate(result.claims[:5], 1):  # 최대 5개만
        print(f'  {i}. {claim.claim_type}: {claim.text[:60]}...')

if hasattr(result, 'verified_claims'):
    print(f'\n[검증 통계]')
    print(f'  - 총 Claim 수: {len(result.claims)}')
    print(f'  - 검증된 Claim: {len(result.verified_claims)}')
    print(f'  - 검증 안된 Claim: {len(result.unverified_claims)}')

if hasattr(result, 'unverified_claims') and result.unverified_claims:
    print(f'\n[검증 실패한 Claim: {len(result.unverified_claims)}개]')
    for claim in result.unverified_claims[:3]:  # 최대 3개만
        print(f'  - {claim.get("claim_type", "unknown")}: {claim.get("reason", "no reason")}')

# 최종 판정
print('\n' + '=' * 80)
print('최종 판정')
print('=' * 80)

if result.verified:
    print('✅ 검증 통과 - 모든 주장이 증거에 기반함')
    print(f'   Grounding Score: {result.grounding_score:.2%}')
else:
    print('⚠️  검증 실패')
    print(f'   Grounding Score: {result.grounding_score:.2%}')
    if result.requires_retry:
        print('   ⚠️  재작업 필요')

print('=' * 80)
